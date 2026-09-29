"""Re-run IndicTrans2 (same INT8 ONNX setup as verify_translation.py) on every sentence from the earlier
feasibility runs (tools/santali_tts_test/prototype_audio/feasibility_mt_consistency.txt) and compare
with the output documented there.

A sentence is a candidate for the prototype only if all of these hold:
  - documented output was identical in >= 9/10 earlier runs,
  - its documented back-translation keeps the source meaning,
  - today's run reproduces it exactly (ignoring only the trailing Ol Chiki full stop ᱾),
  - today's run is identical across REPEATS repeated runs (greedy decoding should be deterministic).
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "model"))
from translate import IndicTransONNX  # noqa: E402

FEAS = os.path.join(HERE, "..", "santali_tts_test", "prototype_audio", "feasibility_mt_consistency.txt")
REPEATS = 3


def strip_end(s):
    return s.rstrip().rstrip("᱾᱿।॥.!?").rstrip()


def main():
    rows = []
    for line in open(FEAS, encoding="utf-8"):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) == 4 and "identical" in parts[1]:
            rows.append((parts[0], int(parts[1].split("/")[0]), parts[2], parts[3]))
    m = IndicTransONNX(os.path.join(HERE, "model"))
    # Record the greedy token ids the decoder picks (same method as verify_translation.py).
    ids = []

    def wrap(run):
        def inner(outs, feed):
            r = run(outs, feed)
            ids.append(int(np.argmax(r[0][0, -1, :])))
            return r
        return inner

    m._dec.run = wrap(m._dec.run)
    m._dec_past.run = wrap(m._dec_past.run)
    results = []
    for hindi, n_same, documented, back in rows:
        outs, id_runs = [], []
        for _ in range(REPEATS):
            ids.clear()
            outs.append(m.translate(hindi, src_lang="hin_Deva", tgt_lang="sat_Olck"))
            id_runs.append(list(ids))
        stable = len(set(outs)) == 1
        reproduces = strip_end(outs[0]) == strip_end(documented)
        results.append({"hindi": hindi, "documented": documented, "documented_runs_identical": n_same,
                        "documented_back_translation": back, "today": outs[0], "today_tgt_ids": id_runs[0], "today_stable": stable and len({tuple(i) for i in id_runs}) == 1,
                        "reproduces_documented": reproduces})
        print(f"{hindi} | documented {n_same}/10: {documented[:60]} | today: {outs[0][:60]} | "
              f"stable x{REPEATS}: {stable} | reproduces: {reproduces}")
    json.dump(results, open(os.path.join(HERE, "verify_sentences_result.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
