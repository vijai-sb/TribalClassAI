"""Verify IndicTrans2 hin_Deva -> sat_Olck on the two prototype phrases.

Runs the model repo's own reference inference (model/translate.py, unmodified) on the INT8 ONNX
bundle in model/ (hari31416/indictrans2-indic-indic-dist-320M-ONNX-int8), greedy decoding.
Nothing here looks up a stored translation: the output is whatever the decoder produces.

Also logs the intermediate steps (preprocessed string, source token ids, raw decoder token ids)
so the Android port can be checked against them token for token.
"""
import json
import os
import sys
import time

import numpy as np
import onnxruntime as ort

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "model")
sys.path.insert(0, MODEL)
from translate import IndicTransONNX  # noqa: E402

EXPECTED = {"किताब": "ᱯᱚᱛᱚᱵ", "एक": "ᱢᱤᱫᱴᱟᱝ",
            # Sentence from the earlier feasibility runs (9/10 identical there); the Hindi ASR emits no
            # danda, so the form without it is checked too. See verify_sentences.py.
            "अपना नाम लिखो।": "ᱟᱢᱟᱜ ᱧᱩᱛᱩᱢ ᱚᱞ ᱢᱮ", "अपना नाम लिखो": "ᱟᱢᱟᱜ ᱧᱩᱛᱩᱢ ᱚᱞ ᱢᱮ"}
# Not part of the prototype; shown only so it is visible the model is translating, not echoing.
EXTRA = ["पानी", "घर", "मछली", "पेड़"]


def rss_mb():
    import psutil
    mi = psutil.Process().memory_info()
    return mi.rss / 2**20, mi.peak_wset / 2**20


def main():
    print("onnxruntime", ort.__version__)
    print("RSS before load: %.0f MB (peak %.0f MB)" % rss_mb())
    t0 = time.time()
    m = IndicTransONNX(MODEL)
    print("load: %.1f s; RSS after load: %.0f MB (peak %.0f MB)" % ((time.time() - t0), *rss_mb()))

    # Wrap the decoder sessions to record the raw greedy token ids.
    trace = {}

    def wrap(sess, name):
        orig = sess.run

        def run(outs, feed):
            r = orig(outs, feed)
            if name != "enc":
                trace.setdefault("tgt_ids", []).append(int(np.argmax(r[0][0, -1, :])))
            else:
                trace["src_ids"] = feed["input_ids"][0].tolist()
            return r
        return run

    m._enc.run = wrap(m._enc, "enc")
    m._dec.run = wrap(m._dec, "dec")
    m._dec_past.run = wrap(m._dec_past, "dec")

    results = {}
    ok = True
    for hi in list(EXPECTED) + EXTRA:
        trace.clear()
        pre = m._ip.preprocess_batch([hi], src_lang="hin_Deva", tgt_lang="sat_Olck")[0]
        m._ip._placeholder_entity_maps.queue.clear() if hasattr(m._ip, "_placeholder_entity_maps") else None
        t = time.time()
        out = m.translate(hi, src_lang="hin_Deva", tgt_lang="sat_Olck")
        ms = (time.time() - t) * 1000
        raw = m._tgt_tok.decode([2] + trace.get("tgt_ids", []), skip_special_tokens=True)
        exp = EXPECTED.get(hi)
        if exp is None:
            verdict = ""
        elif out == exp:
            verdict = "MATCH"
        elif out.rstrip("᱾ ") == exp:
            verdict = "MATCH except the trailing Ol Chiki full stop ᱾ added by the model"
        else:
            verdict = "MISMATCH (expected %s)" % exp
            ok = False
        print("\n%s -> %s   [%s] %.0f ms" % (hi, out, verdict or "not a prototype phrase", ms))
        print("  preprocessed: %r" % pre)
        print("  src ids:      %s" % trace.get("src_ids"))
        print("  tgt ids:      %s" % trace.get("tgt_ids"))
        print("  raw decoded:  %r" % raw)
        print("  codepoints:   %s" % " ".join("U+%04X" % ord(c) for c in out))
        results[hi] = {"output": out, "preprocessed": pre, "src_ids": trace.get("src_ids"),
                       "tgt_ids": trace.get("tgt_ids"), "raw_decoded": raw, "ms": round(ms)}
    print("\nRSS end: %.0f MB (peak %.0f MB)" % rss_mb())
    with open(os.path.join(HERE, "verify_result.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print("\nPROTOTYPE PHRASES:", "ALL MATCH" if ok else "NOT ALL MATCH")


if __name__ == "__main__":
    main()
