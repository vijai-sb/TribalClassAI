"""Generate pre-generated Santali speech for the prototype's sentence-level phrases.

Same model, voice and settings as generate_prototype_audio.py (kaushalkrishnax/santali-piper-vits,
commit ba883eed, speaker 7, scales 0.333/1.15/0.333), and the same quality filter: keep the first take
the independent Santali ASR (AI4Bharat IndicConformer, sat) transcribes exactly (Ol Chiki letters
compared, spaces ignored). A filter, not proof of correct pronunciation. If no take passes, the
sentence is skipped and nothing is written.

Writes the unprocessed take as <name>_raw.wav; process_audio.py makes the app-ready file.

Usage (from this folder):
  ..\\.venv\\Scripts\\python.exe generate_sentence_audio.py <IndicConformer sat model.int8.onnx> <tokens.txt>
"""
import json
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort
import sherpa_onnx
import soundfile as sf

from generate_prototype_audio import MDIR, SCALES, SPEAKER, ol_chiki, santhali_to_ipa

HERE = Path(__file__).parent

# Only sentences whose IndicTrans2 output is documented and reproduced; see
# tools/indictrans2_test/verify_sentences_log.txt and verify_log.txt. Text without the trailing ᱾.
# अपना नाम लिखो। -> ᱟᱢᱟᱜ ᱧᱩᱛᱩᱢ ᱚᱞ ᱢᱮ failed this gate 0/20 (generate_sentence_log.txt) and is not retried.
# The rest passed translation verification in tools/indictrans2_test/verify_candidates_log.txt.
SENTENCES = [
    ("santali_close_book", "किताब बंद करो।", "ᱯᱚᱛᱚᱵ ᱫᱚ ᱵᱚᱱᱚᱫᱚᱞ ᱢᱮ"),
    ("santali_come_here", "इधर आओ।", "ᱱᱚᱶᱟ ᱨᱮ ᱦᱮᱡ ᱢᱮ"),
    ("santali_drink_water", "पानी पियो।", "ᱫᱟᱜᱧᱟᱢ ᱢᱮ"),
    ("santali_raise_hand", "हाथ उठाओ।", "ᱛᱤ ᱪᱮᱛᱟᱱ ᱨᱮ ᱫᱚᱦᱚ ᱢᱮ"),
    ("santali_close_door", "दरवाज़ा बंद करो।", "ᱫᱟᱹᱨᱟᱹ ᱫᱚ ᱵᱚᱱᱚᱫᱚᱞ ᱢᱮ"),
    ("santali_look_board", "बोर्ड देखो।", "ᱵᱳᱨᱰ ᱫᱚ ᱧᱮᱞ ᱢᱮ"),
    ("santali_this_is_water", "यह पानी है।", "ᱱᱚᱶᱟ ᱫᱚ ᱫᱟᱜ"),
    ("santali_very_good", "बहुत अच्छा।", "ᱟᱹᱰᱤ ᱱᱟᱯᱟᱭ"),
    ("santali_your_name", "तुम्हारा नाम क्या है?", "ᱟᱢᱟᱜ ᱧᱩᱛᱩᱢ ᱪᱮᱫ"),
    ("santali_how_are_you", "तुम कैसे हो?", "ᱟᱢ ᱪᱮᱫ ᱞᱮᱠᱟ"),
    ("santali_what_is_this", "यह क्या है?", "ᱱᱚᱶᱟ ᱫᱚ ᱪᱮᱫ"),
]
MAX_TAKES = 20


def main():
    cfg = json.loads((MDIR / "model" / "santali_piper_vits.onnx.json").read_text(encoding="utf-8"))
    sr, idm = cfg["audio"]["sample_rate"], cfg["phoneme_id_map"]
    sess = ort.InferenceSession(str(MDIR / "model" / "santali_piper_vits.onnx"), providers=["CPUExecutionProvider"])
    rec = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
        model=sys.argv[1], tokens=sys.argv[2], num_threads=4, sample_rate=16000, feature_dim=80,
        decoding_method="greedy_search")

    for name, hindi, text in SENTENCES:
        ids = idm["^"] + [x for ch in santhali_to_ipa(text) for x in idm[ch] + idm["_"]] + idm["$"]
        feed = {"input": np.array([ids], np.int64), "input_lengths": np.array([len(ids)], np.int64),
                "scales": np.array(SCALES, np.float32), "sid": np.array([SPEAKER], np.int64)}
        heard_all = []
        for take in range(1, MAX_TAKES + 1):
            a = sess.run(None, feed)[0].squeeze()
            a = (a / (np.abs(a).max() + 1e-9) * 0.9).astype(np.float32)
            s = rec.create_stream()
            s.accept_waveform(sr, a)
            rec.decode_stream(s)
            heard = s.result.text.strip()
            heard_all.append(heard)
            if ol_chiki(heard) == ol_chiki(text):
                sf.write(HERE / f"{name}_raw.wav", a, sr, subtype="PCM_16")
                print(f"{name}: {hindi} -> {text} | kept take {take} of up to {MAX_TAKES} | ASR heard '{heard}' | "
                      f"{len(a) / sr:.3f} s")
                break
        else:
            print(f"{name}: {hindi} -> {text} | SKIPPED: no take out of {MAX_TAKES} transcribed exactly")
        print("  all takes heard: " + " | ".join(heard_all))


if __name__ == "__main__":
    main()
