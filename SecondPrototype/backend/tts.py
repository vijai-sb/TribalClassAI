"""Stage 5: Text-to-speech for Santali using AI4Bharat's Indic Parler-TTS.

CPU-only note: this is a 0.9B parameter model (~3.6GB download). It is the
slowest stage in the pipeline on CPU -- expect several seconds of generation
time per sentence. There is currently no lighter self-hosted TTS model with
Santali support, so this is the best available option for this MVP.
"""

import logging
from typing import Tuple

import numpy as np
import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

logger = logging.getLogger("classroom_translator.tts")

_MODEL_NAME = "ai4bharat/indic-parler-tts"
_DEFAULT_DESCRIPTION = (
    "A clear, calm, female voice speaks slowly and clearly in a quiet room, "
    "suitable for a primary school classroom."
)

_model = None
_tokenizer = None
_description_tokenizer = None

# Measured on real output: raw peak/RMS vary wildly between phrases (peak from
# -0.1 to -10.5 dBFS, RMS from -15.9 to -25.2 dBFS seen across a handful of
# generated clips), so a fixed multiplier either does nothing for quiet clips
# or clips loud ones. Instead: compute the gain that would bring this clip's
# RMS up to _TARGET_RMS_DBFS, but cap it so the resulting peak never exceeds
# _PEAK_CEILING_DBFS -- a gain-staged limiter, not per-sample clipping, so
# there's no distortion, just less boost for already-loud clips.
_TARGET_RMS_DBFS = -14.0
_PEAK_CEILING_DBFS = -1.0


def _normalize_loudness(audio: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(np.square(audio))))
    if peak < 1e-6 or rms < 1e-6:
        return audio  # silence; nothing to normalize

    target_rms = 10 ** (_TARGET_RMS_DBFS / 20)
    peak_ceiling = 10 ** (_PEAK_CEILING_DBFS / 20)

    rms_gain = target_rms / rms
    max_safe_gain = peak_ceiling / peak
    gain = min(rms_gain, max_safe_gain)

    return (audio * gain).astype(np.float32)


def _load():
    global _model, _tokenizer, _description_tokenizer
    if _model is None:
        logger.info("Loading Indic Parler-TTS model (large download on first run)...")
        _model = ParlerTTSForConditionalGeneration.from_pretrained(_MODEL_NAME).to("cpu")
        _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
        _description_tokenizer = AutoTokenizer.from_pretrained(_model.config.text_encoder._name_or_path)
        logger.info("Indic Parler-TTS loaded.")
    return _model, _tokenizer, _description_tokenizer


def preload() -> None:
    _load()
    # Same rationale as translate.py's warmup: pay the one-time first-call
    # tax at startup, not on the first live (uncached) user request. Use a
    # short phrase since generation time scales with output audio length.
    logger.info("Warming up Indic Parler-TTS...")
    synthesize("ᱦᱮᱞᱳ")
    logger.info("Indic Parler-TTS warmed up.")


def synthesize(text: str, description: str = _DEFAULT_DESCRIPTION) -> Tuple[np.ndarray, int]:
    """Returns (audio_samples float32, sample_rate)."""
    model, tokenizer, description_tokenizer = _load()

    description_ids = description_tokenizer(description, return_tensors="pt")
    prompt_ids = tokenizer(text, return_tensors="pt")

    with torch.inference_mode():
        generation = model.generate(
            input_ids=description_ids.input_ids,
            attention_mask=description_ids.attention_mask,
            prompt_input_ids=prompt_ids.input_ids,
            prompt_attention_mask=prompt_ids.attention_mask,
        )

    audio = generation.cpu().numpy().squeeze().astype(np.float32)
    audio = _normalize_loudness(audio)
    return audio, model.config.sampling_rate
