"""FastAPI backend for the classroom translation MVP.

Pipeline: browser mic audio -> WebSocket -> Whisper STT -> IndicTrans2 ->
displays Santali text immediately -> Indic Parler-TTS audio follows
separately (cached instantly for a fixed classroom phrasebook, or generated
live in the background for anything else).

Why text and audio are split into two messages: Indic Parler-TTS takes
~30-90s per sentence on this CPU (see README "Known limitations" -- no
faster self-hosted Santali TTS model exists). Blocking the UI on that would
make the tool unusable, so translated text is shown the moment it's ready,
and audio follows: instantly if the phrase matches the pre-cached
phrasebook (see scripts/build_phrasebook.py), otherwise generated live in
the background without blocking anything else.

The frontend streams raw MediaRecorder chunks as binary WebSocket frames as
they're produced (matching the "stream chunks" design), and the backend
concatenates them into one buffer per connection. Concatenated webm chunks
from a single MediaRecorder session reconstruct a valid decodable file, so
processing only happens once the frontend sends a {"type": "end"} control
message on push-to-talk release -- Whisper needs the complete utterance
anyway, so there is no benefit to decoding partial chunks mid-stream.
"""

import asyncio
import base64
import io
import json
import logging
import os
import tempfile
import time
import uuid
from pathlib import Path

import soundfile as sf
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import stt
import translate
import tts

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("classroom_translator.main")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
BACKEND_DIR = Path(__file__).resolve().parent
PHRASEBOOK_DIR = BACKEND_DIR / "phrasebook"
PHRASEBOOK_AUDIO_DIR = PHRASEBOOK_DIR / "audio"
PHRASEBOOK_MANIFEST_PATH = PHRASEBOOK_DIR / "manifest.json"

# WebSocket configuration
MAX_AUDIO_BUFFER_SIZE = 10 * 1024 * 1024  # 10 MB max per utterance
WS_RECEIVE_TIMEOUT = 30.0  # seconds to wait for "end" message after first chunk
WS_PROCESSING_TIMEOUT = 60.0  # seconds for STT + translation

app = FastAPI(title="Classroom Translator MVP")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
if PHRASEBOOK_AUDIO_DIR.exists():
    app.mount("/phrasebook_audio", StaticFiles(directory=str(PHRASEBOOK_AUDIO_DIR)), name="phrasebook_audio")

PHRASEBOOK: list = []
PHRASEBOOK_BY_NORM: dict = {}

# Track model initialization status for health endpoint
_models_loaded = {"stt": False, "translate": False, "tts": False}


def _normalize(text: str) -> str:
    # Remove common punctuation including commas, then normalize whitespace
    text = text.lower().strip()
    text = text.replace(",", " ")
    text = text.rstrip(".?!")
    return " ".join(text.split())


# Romanized Hindi aliases for phrasebook matching
# Maps normalized romanized text -> canonical Devanagari phrase
_ROMANIZED_HINDI_ALIASES = {
    # GREETINGS
    "suprabhat bachchon": "सुप्रभात बच्चों।",
    "namaste bachchon": "नमस्ते बच्चों।",
    "aap kaise hain": "आज आप कैसे हैं?",
    "kya aap seekhne ke liye taiyar hain": "क्या आप सीखने के लिए तैयार हैं?",
    # CLASSROOM MANAGEMENT
    "kripya baith jaiye": "कृपया बैठ जाइए।",
    "kripaya baith jaiye": "कृपया बैठ जाइए।",
    "krupaya bait jaiye": "कृपया बैठ जाइए।",
    "krupaya baith jaiye": "कृपया बैठ जाइए।",
    "krabil baj chaiye": "कृपया बैठ जाइए।",
    "khade ho jaiye": "खड़े हो जाइए।",
    "dhyan se suniye": "ध्यान से सुनिए।",
    "shant rahiye": "शांत रहिए।",
    "meri baat dhyan se suniye": "मेरी बात ध्यान से सुनिए।",
    # LEARNING MATERIALS
    "apni kitaben nikalie": "अपनी किताबें निकालिए।",
    "apni kitab band kijiye": "अपनी किताब बंद कीजिए।",
    "apni copy nikalie": "अपनी कॉपी निकालिए।",
    "apna pen nikalie": "अपना पेन निकालिए।",
    "board ki or dekhiye": "बोर्ड की ओर देखिए।",
    "board ki aur dekhiye": "बोर्ड की ओर देखिए।",
    # TEACHING INSTRUCTIONS
    "aaj hum kuch naya seekhenge": "आज हम कुछ नया सीखेंगे।",
    "aaj ka path shuru karte hain": "आज का पाठ शुरू करते हैं।",
    "board par dekhiye": "बोर्ड पर देखिए।",
    "mere baad dohraiye": "मेरे बाद दोहराइए।",
    "ise padhiye": "इसे पढ़िए।",
    "ise likhiye": "इसे लिखिए।",
    "iska uttar dijiye": "इसका उत्तर दीजिए।",
    # QUESTIONS
    "kya aapko samajh aaya": "क्या आपको समझ आया?",
    "kya aap samajh gaye": "क्या आप समझ गए?",
    "kya kisi ko koi sawal hai": "क्या किसी को कोई सवाल है?",
    "kya aap iska uttar de sakte hain": "क्या आप इसका उत्तर दे सकते हैं?",
    # ENCOURAGEMENT
    "bahut achha": "बहुत अच्छा।",
    "bahut accha": "बहुत अच्छा।",
    "achha prayas": "अच्छा प्रयास।",
    "phir se koshish kijiye": "फिर से कोशिश कीजिए।",
    "shabash": "शाबाश।",
    # CLASS CLOSING
    "aaj ke liye itna hi": "आज के लिए इतना ही।",
    "dhanyavad bachchon": "धन्यवाद बच्चों।",
    "kal milte hain": "कल मिलते हैं।",
}


def _normalize_devanagari(text: str) -> str:
    """Normalize Devanagari text: NFC, strip punctuation/whitespace.
    Matches the normalize() function used in build_phrasebook.py which strips .?! only.
    """
    import unicodedata
    text = unicodedata.normalize("NFC", text)
    return " ".join(text.strip().rstrip(".?!").split())


def _load_phrasebook() -> None:
    global PHRASEBOOK, PHRASEBOOK_BY_NORM, PHRASEBOOK_BY_NORM_LANG
    if not PHRASEBOOK_MANIFEST_PATH.exists():
        logger.warning(
            "No phrasebook found at %s -- Demo Mode will be empty. "
            "Run scripts/build_phrasebook.py to generate it.",
            PHRASEBOOK_MANIFEST_PATH,
        )
        PHRASEBOOK, PHRASEBOOK_BY_NORM, PHRASEBOOK_BY_NORM_LANG = [], {}, {}
        return
    manifest = json.loads(PHRASEBOOK_MANIFEST_PATH.read_text(encoding="utf-8"))
    PHRASEBOOK = manifest
    # Key: (source_lang, normalized_source_text) -> phrase entry
    PHRASEBOOK_BY_NORM_LANG = {}
    for p in manifest:
        key = (p.get("source_lang", "en"), p["source_text_normalized"])
        PHRASEBOOK_BY_NORM_LANG[key] = p
    logger.info("Loaded phrasebook with %d phrases.", len(PHRASEBOOK))


_load_phrasebook()


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return JSONResponse({
        "status": "ok",
        "models_loaded": _models_loaded,
        "phrasebook_phrases": len(PHRASEBOOK),
    })


@app.get("/")
async def index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/api/phrasebook")
async def get_phrasebook():
    return JSONResponse(
        [
            {
                "category": p.get("category", "OTHER"),
                "source_text": p["source_text"],
                "source_lang": p.get("source_lang", "en"),
                "santali_text": p["santali_text"],
                "audio_url": f"/phrasebook_audio/{p['audio_file']}",
            }
            for p in PHRASEBOOK
        ]
    )


@app.post("/api/phrasebook/reload")
async def reload_phrasebook():
    """Reload phrasebook from disk without restarting the server."""
    _load_phrasebook()
    return JSONResponse({"status": "ok", "phrases_loaded": len(PHRASEBOOK)})


@app.on_event("startup")
async def preload_models():
    if os.environ.get("PRELOAD_MODELS", "true").lower() != "true":
        logger.info("PRELOAD_MODELS=false, models will load lazily on first request.")
        return
    logger.info("Preloading models at startup (STT, translation, TTS) ...")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, stt.preload)
    _models_loaded["stt"] = True
    await loop.run_in_executor(None, translate.preload)
    _models_loaded["translate"] = True
    await loop.run_in_executor(None, tts.preload)
    _models_loaded["tts"] = True
    logger.info("All models preloaded. Ready for requests.")


def _run_stt_and_translate(
    audio_bytes: bytes, source_language: str, mime_type: str, chunk_count: int, chunk_sizes: list
) -> dict:
    """Whisper STT -> IndicTrans2 translation. Fast (a few seconds on CPU).

    source_language: "en" or "hi", selected explicitly by the teacher in the
    UI and passed straight to Whisper -- no auto-detection.

    Blocking/CPU-bound; call via run_in_executor so the event loop stays free.
    """
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        t0 = time.time()
        stt_result = stt.transcribe(tmp_path, language=source_language)
        source_text = stt_result["text"].strip()
        lang_code = stt_result["language"]
        t1 = time.time()

        if not source_text:
            return {"type": "error", "message": "No speech detected. Please try again.", "error_code": "NO_SPEECH"}

        santali_text = translate.translate_to_santali(source_text, lang_code)
        t2 = time.time()

        logger.info("stt=%.2fs translate=%.2fs", t1 - t0, t2 - t1)

        return {
            "type": "text_result",
            "source_text": source_text,
            "source_language": lang_code,
            "text": santali_text,
            "timing": {"stt": t1 - t0, "translate": t2 - t1},
        }
    except Exception as e:
        logger.exception("STT/translation failed: %s", e)
        return {
            "type": "error",
            "message": "Something went wrong understanding that utterance.",
            "error_code": "STT_TRANSLATE_FAILED",
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _synthesize_audio_message(santali_text: str, request_id: str, source: str) -> dict:
    """Runs live Parler-TTS. Slow (~30-90s on CPU) -- call in the background,
    never inline in the request/response path."""
    try:
        t0 = time.time()
        audio_arr, sample_rate = tts.synthesize(santali_text)
        dt = time.time() - t0
        buf = io.BytesIO()
        sf.write(buf, audio_arr, sample_rate, format="WAV")
        audio_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        logger.info("live tts=%.2fs request_id=%s", dt, request_id)
        return {
            "type": "audio_result",
            "request_id": request_id,
            "audio": audio_b64,
            "sample_rate": sample_rate,
            "source": source,
            "timing": {"tts": dt},
        }
    except Exception:
        logger.exception("Live TTS failed")
        return {
            "type": "audio_error",
            "request_id": request_id,
            "message": "Live audio generation failed for this phrase.",
        }


async def _generate_live_audio_and_send(websocket: WebSocket, santali_text: str, request_id: str):
    """Fire-and-forget background task: generate audio, then push it over the
    websocket if the connection is still open."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _synthesize_audio_message, santali_text, request_id, "live")
    try:
        await websocket.send_json(result)
    except Exception:
        logger.info("Could not deliver live audio for request_id=%s (client disconnected?)", request_id)


@app.websocket("/ws/translate")
async def ws_translate(websocket: WebSocket):
    await websocket.accept()
    buffer = bytearray()
    recv_start: float = 0.0
    chunk_sizes: list = []
    logger.info("Client connected")
    try:
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive(), timeout=WS_RECEIVE_TIMEOUT)
            except asyncio.TimeoutError:
                logger.warning("WebSocket receive timeout, closing connection")
                await websocket.send_json({"type": "error", "message": "Connection timed out. Please try again.", "error_code": "WS_TIMEOUT"})
                break

            if message.get("bytes") is not None:
                chunk_size = len(message["bytes"])
                if len(buffer) + chunk_size > MAX_AUDIO_BUFFER_SIZE:
                    logger.warning("Audio buffer size exceeded, resetting")
                    await websocket.send_json({"type": "error", "message": "Audio too long. Please record a shorter utterance.", "error_code": "AUDIO_TOO_LONG"})
                    buffer = bytearray()
                    chunk_sizes = []
                    recv_start = 0.0
                    continue
                if not buffer:
                    recv_start = time.time()
                    chunk_sizes = []
                chunk_sizes.append(chunk_size)
                buffer.extend(message["bytes"])
                continue

            if message.get("text") is not None:
                try:
                    payload = json.loads(message["text"])
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON received: %s", message["text"][:100])
                    await websocket.send_json({"type": "error", "message": "Invalid message format.", "error_code": "INVALID_JSON"})
                    continue

                msg_type = payload.get("type")
                if msg_type == "end":
                    if not buffer:
                        await websocket.send_json({"type": "error", "message": "No audio received.", "error_code": "NO_AUDIO"})
                        continue
                    source_language = payload.get("language", "en")
                    if source_language not in ("en", "hi"):
                        source_language = "en"
                    mime_type = payload.get("mimeType", "unknown")
                    t_recv_end = time.time()
                    audio_upload_s = t_recv_end - recv_start if recv_start else 0.0
                    audio_bytes = bytes(buffer)
                    this_recording_chunk_sizes = chunk_sizes
                    buffer = bytearray()
                    chunk_sizes = []
                    recv_start = 0.0
                    await websocket.send_json({"type": "processing"})

                    t_pipeline_start = time.time()
                    loop = asyncio.get_event_loop()
                    try:
                        text_result = await asyncio.wait_for(
                            loop.run_in_executor(
                                None,
                                _run_stt_and_translate,
                                audio_bytes,
                                source_language,
                                mime_type,
                                len(this_recording_chunk_sizes),
                                this_recording_chunk_sizes,
                            ),
                            timeout=WS_PROCESSING_TIMEOUT,
                        )
                    except asyncio.TimeoutError:
                        logger.error("STT/translation timeout")
                        await websocket.send_json({"type": "error", "message": "Processing took too long. Please try again.", "error_code": "PROCESSING_TIMEOUT"})
                        continue
                    except Exception as e:
                        logger.exception("STT/translation executor error: %s", e)
                        await websocket.send_json({"type": "error", "message": "Processing failed. Please try again.", "error_code": "PROCESSING_ERROR"})
                        continue

                    if text_result["type"] == "error":
                        await websocket.send_json(text_result)
                        continue

                    request_id = uuid.uuid4().hex[:8]
                    text_result["request_id"] = request_id

                    t_match_start = time.time()
                    source_lang = text_result.get("source_language", "en")
                    source_text = text_result["source_text"]
                    normalized = _normalize(source_text)
                    
                    # Step 1: Try exact canonical phrase match with language
                    cached = PHRASEBOOK_BY_NORM_LANG.get((source_lang, normalized))
                    
                    # Step 2: Try known phrasebook aliases (for Romanized Hindi)
                    canonical_text = None
                    if not cached and source_lang == "hi":
                        canonical_text = _ROMANIZED_HINDI_ALIASES.get(normalized)
                        if canonical_text:
                            # Look up the canonical Devanagari phrase
                            canonical_norm = _normalize_devanagari(canonical_text)
                            cached = PHRASEBOOK_BY_NORM_LANG.get(("hi", canonical_norm))
                    
                    # Step 3: Conservative fuzzy matching for English (optional, minimal)
                    # Only for very close matches to avoid false positives
                    if not cached and source_lang == "en":
                        # Could add difflib-based matching here if needed
                        pass
                    
                    match_s = time.time() - t_match_start

                    text_result["cached"] = cached is not None
                    if cached:
                        text_result["text"] = cached["santali_text"]
                        # Use canonical source text for display (especially important for Romanized Hindi)
                        if canonical_text:
                            text_result["source_text"] = canonical_text
                    santali_text = text_result["text"]

                    text_latency_s = time.time() - t_pipeline_start
                    text_result["timing"] = {
                        **text_result["timing"],
                        "audio_upload": audio_upload_s,
                        "phrase_matching": match_s,
                        "total_text_latency": text_latency_s,
                    }
                    await websocket.send_json(text_result)
                    logger.info(
                        "upload=%.2fs stt=%.2fs translate=%.2fs match=%.3fs total_text=%.2fs cached=%s",
                        audio_upload_s,
                        text_result["timing"]["stt"],
                        text_result["timing"]["translate"],
                        match_s,
                        text_latency_s,
                        text_result["cached"],
                    )

                    if cached:
                        t_audio_start = time.time()
                        try:
                            audio_bytes_cached = (PHRASEBOOK_AUDIO_DIR / cached["audio_file"]).read_bytes()
                        except FileNotFoundError:
                            logger.error("Cached audio file not found: %s", cached["audio_file"])
                            await websocket.send_json({"type": "error", "message": "Cached audio unavailable.", "error_code": "CACHE_MISSING"})
                            continue
                        audio_b64 = base64.b64encode(audio_bytes_cached).decode("ascii")
                        audio_serve_s = time.time() - t_audio_start
                        total_cached_audio_s = time.time() - t_pipeline_start
                        await websocket.send_json(
                            {
                                "type": "audio_result",
                                "request_id": request_id,
                                "audio": audio_b64,
                                "sample_rate": None,
                                "source": "cache",
                                "timing": {
                                    "tts": 0.0,
                                    "audio_serve": audio_serve_s,
                                    "total_cached_audio_latency": total_cached_audio_s,
                                },
                            }
                        )
                        logger.info("total_cached_audio=%.2fs", total_cached_audio_s)
                    else:
                        await websocket.send_json(
                            {
                                "type": "audio_pending",
                                "request_id": request_id,
                                "message": "Generating audio live (not cached, ~30-90s on this CPU)...",
                            }
                        )
                        asyncio.create_task(
                            _generate_live_audio_and_send(websocket, santali_text, request_id)
                        )

                elif msg_type == "reset":
                    buffer = bytearray()
                    chunk_sizes = []
                    recv_start = 0.0
                else:
                    logger.warning("Unknown message type: %s", msg_type)

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.exception("WebSocket error: %s", e)
        try:
            await websocket.send_json({"type": "error", "message": "Server error. Please reconnect.", "error_code": "SERVER_ERROR"})
        except Exception:
            pass
