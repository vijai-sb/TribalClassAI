"""Stage 3: Speech-to-text for Hindi/English using faster-whisper (CTranslate2 backend).

Runs entirely on CPU. Benchmarked on this machine (Ryzen 5 3450U) with short
push-to-talk clips: tiny ~1.5s, base ~3.6s, small ~9.5s per utterance. Using
"base" -- a ~60% latency cut vs "small" with none of "tiny"'s well-documented
non-English/Hindi accuracy drop (unverified locally: no Hindi TTS voice
available on this machine to test against). Override with WHISPER_MODEL if
you want to try "tiny" or go back to "small" after testing real Hindi speech.
"""

import logging
import os
from typing import Optional

# Must be set before ctranslate2's native library loads (i.e. before the
# faster_whisper import below). Works around "OMP: Error #15: Initializing
# libiomp5md.dll, but found libiomp5md.dll already initialized" -- a
# duplicate-OpenMP-runtime conflict seen on at least some Windows/AMD CPU
# combinations (reproduced on a Ryzen 5 3450U) when ctranslate2's bundled
# OpenMP runtime and another library's collide in the same process.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from faster_whisper import WhisperModel  # noqa: E402

logger = logging.getLogger("classroom_translator.stt")

_MODEL_SIZE = os.environ.get("WHISPER_MODEL", "base")
# Benchmarked: explicit cpu_threads matching physical core count was never
# worse than the library default (cpu_threads=0, "auto") and meaningfully
# faster for the "tiny" model. Override via WHISPER_CPU_THREADS if needed.
_CPU_THREADS = int(os.environ.get("WHISPER_CPU_THREADS", "4"))
_model: Optional[WhisperModel] = None


def load_model() -> WhisperModel:
    global _model
    if _model is None:
        logger.info(
            "Loading faster-whisper model '%s' (CPU, int8, %d threads)...", _MODEL_SIZE, _CPU_THREADS
        )
        _model = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8", cpu_threads=_CPU_THREADS)
        logger.info("Whisper model loaded.")
    return _model


def preload() -> None:
    load_model()


def transcribe(audio_path: str, language: str = "en") -> dict:
    """Transcribe an audio file (any format ffmpeg/PyAV can decode, e.g. webm/wav).

    language: "en" or "hi" -- the teacher selects this explicitly in the UI
    (see frontend language selector), so Whisper is never left to guess.

    Returns {"text": str, "language": str} -- language just echoes back what
    was passed in (Whisper doesn't re-detect when language is given
    explicitly), kept for contract compatibility with existing callers.

    Previously this did a two-pass detect-then-force-language call (to fix a
    real failure: "Today we will learn something new." produced a long
    incorrect/repetitive transcription, caused by decoding with
    language=None leaving the model free to switch languages mid-decode).
    That auto-detect pass is no longer needed now that the UI has the teacher
    select the source language up front -- removed for latency (was adding
    a redundant encoder pass, ~3s, on top of every request). The other fixes
    for that failure (explicit language, tighter beam, no repetition-prone
    fallback sampling) are unaffected and still applied below.
    """
    model = load_model()
    # Hindi benefits from slightly different settings than English
    if language == "hi":
        # For Hindi: slightly higher beam, allow some temperature for
        # Devanagari script variability, stricter thresholds to avoid
        # hallucinations on short utterances.
        segments, info = model.transcribe(
            audio_path,
            language=language,
            vad_filter=False,
            beam_size=5,
            condition_on_previous_text=False,
            temperature=0.2,
            compression_ratio_threshold=2.4,
            log_prob_threshold=-1.0,
            no_speech_threshold=0.6,
        )
    else:
        # English: keep original conservative settings
        segments, info = model.transcribe(
            audio_path,
            language=language,
            vad_filter=False,
            beam_size=3,
            condition_on_previous_text=False,
            temperature=0,
        )
    text = " ".join(segment.text.strip() for segment in segments).strip()
    return {"text": text, "language": info.language}
