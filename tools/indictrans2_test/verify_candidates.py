"""Verify candidate classroom sentences for the prototype with IndicTrans2 (same INT8 ONNX setup as
verify_translation.py; the model repo's own translate.py for preprocessing and greedy decoding).

For each candidate (Hindi with its final punctuation) it records:
  - greedy output, 3 runs, and the target token ids
  - greedy output for the same Hindi without the final punctuation (what the Hindi ASR emits)
  - beam-4 output (a second decoding method; the earlier feasibility runs also compared methods)
  - whether the output is Ol Chiki only (letters, spaces, ᱾) - earlier runs leaked other scripts
  - back-translation sat_Olck -> hin_Deva with the same model, for a meaning check
  - the documented earlier feasibility result, if the sentence was in those runs
"Consistent" means every one of those outputs is identical. Meaning is judged by reading the
back-translation; that judgement is recorded in the result table, not here.
"""
import json
import os
import sys
import unicodedata

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "model"))
from translate import IndicTransONNX, _past_feed  # noqa: E402

FEAS = os.path.join(HERE, "..", "santali_tts_test", "prototype_audio", "feasibility_mt_consistency.txt")

CANDIDATES = [
    # A. classroom instructions
    "अपना नाम लिखो।", "किताब खोलो।", "किताब बंद करो।", "इधर आओ।", "बैठ जाओ।", "खड़े हो जाओ।",
    "ध्यान से सुनो।", "पानी पियो।", "मेरे साथ बोलो।", "सब बच्चे बैठो।", "चुप रहो।", "हाथ उठाओ।",
    "दरवाज़ा बंद करो।", "बोर्ड देखो।",
    # C. classroom objects
    "यह किताब है।", "यह कलम है।", "यह पानी है।",
    # D. greetings / praise
    "नमस्ते।", "सुप्रभात।", "धन्यवाद।", "बहुत अच्छा।", "शाबाश।",
    # E. simple questions
    "तुम्हारा नाम क्या है?", "तुम कैसे हो?", "यह क्या है?",
]
FINAL_PUNCT = "।॥.?!"
OL_CHIKI_OK = set(chr(c) for c in range(0x1C50, 0x1C80)) | {" "}


def strip_final(s):
    return s.rstrip().rstrip(FINAL_PUNCT).rstrip()


def beam_search(m, text, beam=4, max_len=64):
    """Beam search using the same KV-cache decoders as the greedy path (one new token per step, each beam
    with its own cache). The no-cache decoder_model.onnx does not reproduce the cached path when fed a
    multi-token prefix, so it is only used for the first step, exactly as translate.py does."""
    if hasattr(m._ip, "_placeholder_entity_maps"):
        m._ip._placeholder_entity_maps.queue.clear()
    pre = m._ip.preprocess_batch([text], src_lang="hin_Deva", tgt_lang="sat_Olck")[0]
    enc = m._src_tok.encode(pre)
    ids = np.array([[i if i < m._meta["src_dict_size"] else m._meta["unk_id"] for i in enc.ids]], np.int64)
    mask = np.array([enc.attention_mask], np.int64)
    hid = m._enc.run(["last_hidden_state"], {"input_ids": ids, "attention_mask": mask})[0]

    def log_softmax(v):
        v = v - v.max()
        return v - np.log(np.exp(v).sum())

    first = m._dec.run(None, {"input_ids": np.array([[m._decoder_start_id]], np.int64),
                              "encoder_hidden_states": hid, "encoder_attention_mask": mask})
    # beam: (token sequence, summed log-prob, past KV list, log-probs for the next token)
    beams = [([m._decoder_start_id], 0.0, list(first[1:]), log_softmax(first[0][0, -1]))]
    done = []
    for _ in range(max_len):
        cand = []
        for bi, (seq, score, past, lp) in enumerate(beams):
            for t in np.argsort(lp)[-beam:]:
                cand.append((score + float(lp[t]), bi, int(t)))
        cand.sort(reverse=True)
        new_beams = []
        for score, bi, t in cand:
            seq = beams[bi][0] + [t]
            if t == m._eos_id:
                done.append((seq, score / (len(seq) - 1)))  # length-normalised, like HF length_penalty=1
                continue
            out = m._dec_past.run(None, {"input_ids": np.array([[t]], np.int64), "encoder_attention_mask": mask,
                                         **_past_feed(beams[bi][2], m._num_layers)})
            new_beams.append((seq, score, list(out[1:]), log_softmax(out[0][0, -1])))
            if len(new_beams) == beam:
                break
        beams = new_beams
        # Stop when no live beam can beat the best finished hypothesis (scores only decrease).
        if not beams or (done and max(d[1] for d in done) >= max(b[1] / len(b[0]) for b in beams)):
            break
    best = max(done or [(b[0], b[1] / len(b[0])) for b in beams], key=lambda d: d[1])[0]
    safe = [i if i < m._meta["tgt_dict_size"] else m._meta["unk_id"] for i in best]
    raw = m._tgt_tok.decode(safe, skip_special_tokens=True)
    return m._ip.postprocess_batch([raw], lang="sat_Olck")[0]


def main():
    documented = {}
    for line in open(FEAS, encoding="utf-8"):
        p = [x.strip() for x in line.split("|")]
        if len(p) == 4 and "identical" in p[1]:
            documented[p[0]] = (p[1], p[2], p[3])

    m = IndicTransONNX(os.path.join(HERE, "model"))
    ids = []

    def wrap(run):
        def inner(outs, feed):
            r = run(outs, feed)
            ids.append(int(np.argmax(r[0][0, -1, :])))
            return r
        return inner

    greedy_dec, greedy_past = m._dec.run, m._dec_past.run
    results = []
    for hindi in CANDIDATES:
        m._dec.run, m._dec_past.run = wrap(greedy_dec), wrap(greedy_past)
        runs, id_runs = [], []
        for _ in range(3):
            ids.clear()
            runs.append(m.translate(hindi, src_lang="hin_Deva", tgt_lang="sat_Olck"))
            id_runs.append(list(ids))
        no_punct = m.translate(strip_final(hindi), src_lang="hin_Deva", tgt_lang="sat_Olck")
        m._dec.run, m._dec_past.run = greedy_dec, greedy_past
        beam4 = beam_search(m, hindi)
        out = runs[0]
        variants = {"greedy x3": runs, "no final punctuation": [no_punct], "beam-4": [beam4]}
        consistent = all(v == out for vs in variants.values() for v in vs) and all(i == id_runs[0] for i in id_runs)
        ol_chiki_only = all(c in OL_CHIKI_OK for c in unicodedata.normalize("NFC", out).replace("᱾", ""))
        back = m.translate(out, src_lang="sat_Olck", tgt_lang="hin_Deva")
        doc = documented.get(hindi)
        doc_agrees = None if doc is None else strip_final(doc[1].replace("᱾", "")) == out.rstrip("᱾ ").strip()
        r = {"hindi": hindi, "output": out, "tgt_ids": id_runs[0], "no_punct_output": no_punct, "beam4_output": beam4,
             "consistent": consistent, "ol_chiki_only": ol_chiki_only, "back_translation": back,
             "documented": doc, "documented_agrees": doc_agrees}
        results.append(r)
        print(f"{hindi} -> {out} | consistent {consistent} | Ol Chiki only {ol_chiki_only} | back: {back}"
              + ("" if consistent else f"\n    no-punct: {no_punct} | beam-4: {beam4}")
              + ("" if doc is None else f"\n    earlier feasibility: {doc[0]}: {doc[1][:50]} | agrees today: {doc_agrees}"))
    json.dump(results, open(os.path.join(HERE, "verify_candidates_result.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
