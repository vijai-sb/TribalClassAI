"""Run the verify_candidates.py checks on one Hindi sentence given on the command line.

Same checks and model as verify_candidates.py (greedy x3 with token ids, no final punctuation, beam-4,
Ol Chiki-only script check, back-translation), plus the earlier feasibility result if there is one.
Writes verify_one_<n>.json next to this script; does not touch verify_candidates_result.json.

Usage: .venv\\Scripts\\python.exe verify_one.py "<Hindi sentence>"
"""
import json
import os
import sys
import unicodedata

import numpy as np

import verify_candidates as V


def main():
    hindi = sys.argv[1]
    m = V.IndicTransONNX(os.path.join(V.HERE, "model"))
    ids = []

    def wrap(run):
        def inner(outs, feed):
            r = run(outs, feed)
            ids.append(int(np.argmax(r[0][0, -1, :])))
            return r
        return inner

    dec, past = m._dec.run, m._dec_past.run
    m._dec.run, m._dec_past.run = wrap(dec), wrap(past)
    runs, id_runs = [], []
    for _ in range(3):
        ids.clear()
        runs.append(m.translate(hindi, src_lang="hin_Deva", tgt_lang="sat_Olck"))
        id_runs.append(list(ids))
    no_punct = m.translate(V.strip_final(hindi), src_lang="hin_Deva", tgt_lang="sat_Olck")
    m._dec.run, m._dec_past.run = dec, past
    beam4 = V.beam_search(m, hindi)
    out = runs[0]
    words = lambda s: s.rstrip("᱾?। ").strip()
    result = {
        "hindi": hindi, "output": out, "tgt_ids": id_runs[0],
        "greedy_x3_identical": len(set(runs)) == 1 and all(i == id_runs[0] for i in id_runs),
        "no_punct_output": no_punct, "no_punct_same": no_punct == out,
        "beam4_output": beam4, "beam4_same": beam4 == out, "beam4_same_words": words(beam4) == words(out),
        "ol_chiki_only": all(c in V.OL_CHIKI_OK | {",", "?"} for c in unicodedata.normalize("NFC", out).replace("᱾", "")),
        "back_translation": m.translate(out, src_lang="sat_Olck", tgt_lang="hin_Deva"),
    }
    for line in open(V.FEAS, encoding="utf-8"):
        p = [x.strip() for x in line.split("|")]
        if len(p) == 4 and p[0] == hindi:
            result["earlier_feasibility"] = {"runs_identical": p[1], "output": p[2], "back_translations": p[3],
                                             "agrees_today": words(p[2]) == words(out)}
    for k, v in result.items():
        print(f"{k}: {v}")
    n = len([f for f in os.listdir(V.HERE) if f.startswith("verify_one_")]) + 1
    with open(os.path.join(V.HERE, f"verify_one_{n}.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
