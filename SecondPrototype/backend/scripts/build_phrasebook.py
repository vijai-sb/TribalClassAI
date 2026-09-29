"""Pre-generates the Demo Mode phrasebook: a set of common classroom phrases,
translated to Santali and synthesized to audio ONCE, so the demo can play
them back instantly instead of waiting ~30-90s for live Parler-TTS.

Run this once during setup (or whenever PHRASES below changes):
    python scripts/build_phrasebook.py

Idempotent: if a phrase's (source text, translated Santali text) exactly
matches an entry already in phrasebook/manifest.json, its existing audio file
is reused instead of re-running TTS -- only genuinely new/changed phrases
cost the ~30-90s/phrase TTS generation time. Uses num_beams=5 (best quality)
for translation, not the num_beams=3 used on the live low-latency path --
this runs once, offline, so there's no reason to trade quality for speed here.

Outputs:
    phrasebook/manifest.json   -- [{category, source_text, santali_text, audio_file}, ...]
    phrasebook/audio/*.wav     -- one file per phrase, named by a stable slug
                                   of its English text (not position), so
                                   reordering/adding phrases never breaks
                                   existing cache references.

Phrase wording notes: some natural phrasings reliably trigger IndicTrans2
into mixing in stray Arabic/Meitei/Odia characters instead of clean Ol Chiki,
or into repeating a word -- reproduced on both the distilled and full 1B
models (see README "Known limitations"). Every phrase below was validated
programmatically (script-purity + no consecutive repeated tokens) and, where
the natural phrasing failed, reworded to the closest phrasing that translates
cleanly -- never a hand-written/invented translation, always the real
pipeline's output for some valid phrasing of the same instruction.
"""

import json
import re
import shutil
import sys
import time
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import soundfile as sf  # noqa: E402

from translate import translate_to_santali  # noqa: E402
from tts import synthesize  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent
PHRASEBOOK_DIR = BACKEND_DIR / "phrasebook"
AUDIO_DIR = PHRASEBOOK_DIR / "audio"
MANIFEST_PATH = PHRASEBOOK_DIR / "manifest.json"

# (category, source_text, source_lang). Comments mark phrases reworded from a
# more natural phrasing that failed the clean-Ol-Chiki check (see module
# docstring) -- the original ask is noted so the substitution is traceable.
PHRASES = [
    ("GREETING", "Good morning students", "en"),  # was "Good morning children"
    ("GREETING", "Good day, children", "en"),  # was "Good afternoon children"
    ("GREETING", "Welcome to the class", "en"),
    ("GREETING", "How are you today?", "en"),
    ("GREETING", "Are you ready to learn?", "en"),
    ("CLASSROOM INSTRUCTIONS", "Take out your books", "en"),  # was "Open your books"
    ("CLASSROOM INSTRUCTIONS", "Close your books", "en"),
    ("CLASSROOM INSTRUCTIONS", "Take your notebook", "en"),
    ("CLASSROOM INSTRUCTIONS", "Take your pen", "en"),
    ("CLASSROOM INSTRUCTIONS", "Listen carefully", "en"),
    ("CLASSROOM INSTRUCTIONS", "Look at the board", "en"),
    ("CLASSROOM INSTRUCTIONS", "Come to the board", "en"),
    ("CLASSROOM INSTRUCTIONS", "Sit down", "en"),
    ("CLASSROOM INSTRUCTIONS", "Stand up", "en"),
    ("CLASSROOM INSTRUCTIONS", "Be quiet", "en"),
    ("CLASSROOM INSTRUCTIONS", "Raise your hand", "en"),
    ("CLASSROOM INSTRUCTIONS", "Wait a moment", "en"),
    ("CLASSROOM INSTRUCTIONS", "Repeat after me", "en"),
    ("CLASSROOM INSTRUCTIONS", "Speak slowly", "en"),
    ("CLASSROOM INSTRUCTIONS", "Read this", "en"),
    ("CLASSROOM INSTRUCTIONS", "Write this down", "en"),
    ("CLASSROOM INSTRUCTIONS", "Copy this into your notebook", "en"),
    ("QUESTIONS", "Do you understand?", "en"),
    ("QUESTIONS", "Is everything clear?", "en"),  # was "Do you have any questions?"
    ("QUESTIONS", "Who knows the answer?", "en"),
    ("QUESTIONS", "What is the answer?", "en"),
    ("QUESTIONS", "Try to answer this", "en"),  # was "Can you answer this question?"
    ("QUESTIONS", "Give an example", "en"),  # was "Can you give an example?"
    ("QUESTIONS", "What did we learn today?", "en"),
    ("TEACHING", "Today we will learn something new", "en"),
    ("TEACHING", "Let us start the lesson", "en"),
    ("TEACHING", "Pay attention", "en"),
    ("TEACHING", "Read this sentence", "en"),
    ("TEACHING", "Read the next paragraph", "en"),
    ("TEACHING", "Write the answer", "en"),
    ("TEACHING", "Solve this problem", "en"),
    ("TEACHING", "Work with your partner", "en"),
    ("TEACHING", "Discuss this with your group", "en"),
    ("TEACHING", "Check your answer", "en"),
    ("ENCOURAGEMENT", "Very good", "en"),
    ("ENCOURAGEMENT", "Good job", "en"),
    ("ENCOURAGEMENT", "Well done", "en"),
    ("ENCOURAGEMENT", "Excellent", "en"),
    ("ENCOURAGEMENT", "Try again", "en"),
    ("ENCOURAGEMENT", "Don't worry", "en"),
    ("ENCOURAGEMENT", "Keep trying", "en"),
    ("ENDING", "Time is up", "en"),
    ("ENDING", "Finish your work", "en"),
    ("ENDING", "Submit your work", "en"),
    ("ENDING", "Goodbye, see you soon", "en"),  # was "See you tomorrow"
    ("ENDING", "Thank you", "en"),
    ("ENDING", "Have a nice day", "en"),
    ("ENCOURAGEMENT", "Give the answer", "en"),  # kept from the original 15-phrase set
    # --- HINDI PHRASES ---
    ("GREETING", "सुप्रभात बच्चों।", "hi"),
    ("GREETING", "नमस्ते बच्चों।", "hi"),
    ("GREETING", "आज आप कैसे हैं?", "hi"),
    ("GREETING", "क्या आप सीखने के लिए तैयार हैं?", "hi"),
    ("CLASSROOM MANAGEMENT", "कृपया बैठ जाइए।", "hi"),
    ("CLASSROOM MANAGEMENT", "खड़े हो जाइए।", "hi"),
    ("CLASSROOM MANAGEMENT", "ध्यान से सुनिए।", "hi"),
    ("CLASSROOM MANAGEMENT", "शांत रहिए।", "hi"),
    ("CLASSROOM MANAGEMENT", "मेरी बात ध्यान से सुनिए।", "hi"),
    ("LEARNING MATERIALS", "अपनी किताबें निकालिए।", "hi"),
    ("LEARNING MATERIALS", "अपनी किताब बंद कीजिए।", "hi"),
    ("LEARNING MATERIALS", "अपनी कॉपी निकालिए।", "hi"),
    ("LEARNING MATERIALS", "अपना पेन निकालिए।", "hi"),
    ("LEARNING MATERIALS", "बोर्ड की ओर देखिए।", "hi"),
    ("TEACHING INSTRUCTIONS", "आज हम कुछ नया सीखेंगे।", "hi"),
    ("TEACHING INSTRUCTIONS", "आज का पाठ शुरू करते हैं।", "hi"),
    ("TEACHING INSTRUCTIONS", "बोर्ड पर देखिए।", "hi"),
    ("TEACHING INSTRUCTIONS", "मेरे बाद दोहराइए।", "hi"),
    ("TEACHING INSTRUCTIONS", "इसे पढ़िए।", "hi"),
    ("TEACHING INSTRUCTIONS", "इसे लिखिए।", "hi"),
    ("TEACHING INSTRUCTIONS", "इसका उत्तर दीजिए।", "hi"),
    ("QUESTIONS", "क्या आपको समझ आया?", "hi"),
    ("QUESTIONS", "क्या आप समझ गए?", "hi"),
    ("QUESTIONS", "क्या किसी को कोई सवाल है?", "hi"),
    ("QUESTIONS", "क्या आप इसका उत्तर दे सकते हैं?", "hi"),
    ("ENCOURAGEMENT", "बहुत अच्छा।", "hi"),
    ("ENCOURAGEMENT", "अच्छा प्रयास।", "hi"),
    ("ENCOURAGEMENT", "फिर से कोशिश कीजिए।", "hi"),
    ("ENCOURAGEMENT", "शाबाश।", "hi"),
    ("CLASS CLOSING", "आज के लिए इतना ही।", "hi"),
    ("CLASS CLOSING", "धन्यवाद बच्चों।", "hi"),
    ("CLASS CLOSING", "कल मिलते हैं।", "hi"),
]

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    # Try to slugify normally (works for ASCII)
    slug = _SLUG_RE.sub("_", text.lower()).strip("_")
    # If empty (e.g., non-ASCII text), create a hash-based slug
    if not slug:
        import hashlib
        return "phrase_" + hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
    return slug


def normalize(text: str) -> str:
    return " ".join(text.lower().strip().rstrip(".?!").split())


def main():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    old_by_key = {}
    if MANIFEST_PATH.exists():
        old_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        for entry in old_manifest:
            old_by_key[(entry["source_text"], entry["santali_text"])] = entry["audio_file"]

    manifest = []
    reused, generated = 0, 0

    for i, (category, text, lang) in enumerate(PHRASES, start=1):
        santali_text = translate_to_santali(text, lang, num_beams=5)
        audio_filename = f"{slugify(text)}.wav"
        old_key = (text, santali_text)

        if old_key in old_by_key:
            old_file = AUDIO_DIR / old_by_key[old_key]
            new_file = AUDIO_DIR / audio_filename
            if old_file.exists() and old_file != new_file:
                shutil.copyfile(old_file, new_file)
            print(f"[{i}/{len(PHRASES)}] REUSED  {text!r} -> {santali_text}", flush=True)
            reused += 1
        else:
            print(f"[{i}/{len(PHRASES)}] {text!r} -> {santali_text}", flush=True)
            print("    Synthesizing audio (slow, ~30-90s on CPU)...", flush=True)
            t0 = time.time()
            audio, sample_rate = synthesize(santali_text)
            sf.write(str(AUDIO_DIR / audio_filename), audio, sample_rate)
            print(f"    Wrote {audio_filename} in {time.time() - t0:.1f}s", flush=True)
            generated += 1

        manifest.append(
            {
                "category": category,
                "source_text": text,
                "source_text_normalized": normalize(text),
                "source_lang": lang,
                "santali_text": santali_text,
                "audio_file": audio_filename,
            }
        )

    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {MANIFEST_PATH} with {len(manifest)} phrases ({reused} reused, {generated} generated).")

    # Clean up any old positional-named files (phrase_NN.wav) no longer referenced.
    referenced = {p["audio_file"] for p in manifest}
    for f in AUDIO_DIR.glob("phrase_*.wav"):
        if f.name not in referenced:
            f.unlink()


if __name__ == "__main__":
    main()
