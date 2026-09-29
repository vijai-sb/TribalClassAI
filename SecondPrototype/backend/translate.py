"""Stage 4: Translate Hindi/English text to Santali (Ol Chiki script) using IndicTrans2.

Uses AI4Bharat's *distilled* IndicTrans2 checkpoints instead of the 1B models:
  - en -> indic: ai4bharat/indictrans2-en-indic-dist-200M
  - indic -> indic: ai4bharat/indictrans2-indic-indic-dist-320M (used for hi -> sat)

The distilled models are ~4x smaller than the 1B variants and run at usable
speed on CPU; the 1B models are impractically slow for near-real-time use
without a GPU.
"""

import logging
from typing import Optional

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from indic_processor import IndicProcessor

logger = logging.getLogger("classroom_translator.translate")

_EN_INDIC_MODEL = "ai4bharat/indictrans2-en-indic-dist-200M"
_INDIC_INDIC_MODEL = "ai4bharat/indictrans2-indic-indic-dist-320M"
_TARGET_LANG = "sat_Olck"  # Santali, Ol Chiki script

_ip: Optional[IndicProcessor] = None
_models: dict = {}
_tokenizers: dict = {}


def _get_processor() -> IndicProcessor:
    global _ip
    if _ip is None:
        _ip = IndicProcessor(inference=True)
    return _ip


def _load(model_name: str):
    if model_name not in _models:
        logger.info("Loading translation model %s ...", model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name, trust_remote_code=True)
        model.eval()
        _tokenizers[model_name] = tokenizer
        _models[model_name] = model
        logger.info("Loaded %s", model_name)
    return _models[model_name], _tokenizers[model_name]


def preload() -> None:
    _load(_EN_INDIC_MODEL)
    _load(_INDIC_INDIC_MODEL)
    # Loading weights alone isn't enough -- the *first* model.generate() call
    # pays a one-time PyTorch warmup cost independent of model size (measured
    # ~6s here vs <1s on the next call with identical settings). Eat that cost
    # now, at startup, instead of on the first real user request.
    logger.info("Warming up translation models...")
    translate_to_santali("warm up", "en")
    translate_to_santali("गरम अप", "hi")
    logger.info("Translation models warmed up.")


def translate_to_santali(text: str, source_lang: str, num_beams: int = 3) -> str:
    """source_lang: 'en' or 'hi'. Returns Santali text in Ol Chiki script.

    num_beams defaults to 3: benchmarked 5 vs 3 vs 1 on 10 classroom sentences,
    beam=1 was ~2.5x faster than beam=5 but introduced a real defect (a
    repeated word) on one sentence; beam=3 + early_stopping=True was ~35%
    faster than beam=5 with no regressions observed, so that's the default for
    the latency-sensitive live path. The phrasebook builder (no latency
    pressure, runs once offline) explicitly passes num_beams=5 for best
    quality instead -- pass it explicitly here too if you need that tradeoff.
    """
    if source_lang == "en":
        model_name, src_code = _EN_INDIC_MODEL, "eng_Latn"
    elif source_lang == "hi":
        model_name, src_code = _INDIC_INDIC_MODEL, "hin_Deva"
    else:
        raise ValueError(f"Unsupported source language: {source_lang!r}")

    model, tokenizer = _load(model_name)

    ip = _get_processor()

    batch, placeholder_maps = ip.preprocess_batch([text], src_lang=src_code, tgt_lang=_TARGET_LANG)
    inputs = tokenizer(batch, padding="longest", truncation=True, max_length=256, return_tensors="pt")

    with torch.inference_mode():
        outputs = model.generate(
            **inputs, num_beams=num_beams, early_stopping=True, max_length=256, num_return_sequences=1
        )

    decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True, clean_up_tokenization_spaces=True)
    result = ip.postprocess_batch(decoded, lang=_TARGET_LANG, placeholder_maps=placeholder_maps)
    return result[0]
