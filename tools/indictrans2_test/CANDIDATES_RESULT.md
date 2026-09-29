# Classroom sentence candidates — verification (2026-09-29)

Translation: `verify_candidates.py` → `verify_candidates_log.txt` / `verify_candidates_result.json`
(IndicTrans2 320M INT8 ONNX; greedy ×3, beam-4, with/without final punctuation, script check, back-translation
with the same model). Meaning is judged from the back-translation only; nobody who speaks Santali has checked it.
TTS: `tools/santali_tts_test/prototype_audio/generate_sentence_audio.py` (same voice/settings as the word clips,
≤ 20 takes, Santali ASR must transcribe exactly; the processed app file is re-checked).

Note: an earlier version of the beam search used `decoder_model.onnx` with a multi-token prefix, which does not
reproduce the cached decoder; it was replaced by a KV-cache beam search (beam-1 == greedy for all 25).

| Hindi | IndicTrans2 output | Consistent | Back-translation | Translation | TTS gate | In app |
|---|---|---|---|---|---|---|
| अपना नाम लिखो। | ᱟᱢᱟᱜ ᱧᱩᱛᱩᱢ ᱚᱞ ᱢᱮ ᱾ | yes (+9/10 earlier) | अपना नाम लिखें | ✅ | ❌ 0/20 | text only |
| किताब खोलो। | ᱯᱚᱛᱚᱵ ᱫᱚ ᱮᱦᱚᱵ ᱢᱮ ᱾ | yes | किताब शुरू करें | ❌ meaning (open→start) | – | no |
| किताब बंद करो। | ᱯᱚᱛᱚᱵ ᱫᱚ ᱵᱚᱱᱚᱫᱚᱞ ᱢᱮ ᱾ | yes | किताब को बंद कर दें | ✅ | ❌ 0/20 | no |
| इधर आओ। | ᱱᱚᱶᱟ ᱨᱮ ᱦᱮᱡ ᱢᱮ ᱾ | yes | यहाँ आओ | ✅ | ❌ 0/20 | no |
| बैठ जाओ। | ᱥᱮᱱ ᱢᱮ ᱾ | no | जाओ | ❌ | – | no |
| खड़े हो जाओ। | ᱛᱷᱟᱯᱚᱱ ᱢᱮ ᱾ | yes | स्थापित करें | ❌ meaning | – | no |
| ध्यान से सुनो। | ᱢᱚᱱᱮ ᱠᱟᱛᱮ ᱵᱟᱰᱟᱭ ᱢᱮ ᱾ | no (4/10 earlier) | ध्यान से सुनें | ❌ | – | no |
| पानी पियो। | ᱫᱟᱜᱧᱟᱢ ᱢᱮ ᱾ | yes | पानी पीना | ✅ | ❌ 0/20 | no |
| मेरे साथ बोलो। | ᱤᱧ ᱥᱟᱶ ᱠᱟᱛᱷᱟ ᱞᱟᱹᱭ ᱢᱮ ᱾ | yes | मुझसे बात करें | ❌ meaning uncertain | – | no |
| सब बच्चे बैठो। | ᱥᱟᱱᱟᱢ ᱜᱤᱫᱽᱨᱟᱹ ᱠᱚ ᱥᱮᱱ ᱢᱮ ᱾ | yes | सभी बच्चों को जाने दें | ❌ meaning | – | no |
| चुप रहो। | ᱥᱩᱛᱚ ᱢᱮ ᱾ | no | शांत हो जाओ | ❌ | – | no |
| हाथ उठाओ। | ᱛᱤ ᱪᱮᱛᱟᱱ ᱨᱮ ᱫᱚᱦᱚ ᱢᱮ ᱾ | yes | हाथ ऊपर रखें | ✅ | ❌ 0/20 | no |
| दरवाज़ा बंद करो। | ᱫᱟᱹᱨᱟᱹ ᱫᱚ ᱵᱚᱱᱚᱫᱚᱞ ᱢᱮ ᱾ | yes | दरवाजा बंद कर दें | ✅ | ❌ 0/20 | no |
| बोर्ड देखो। | ᱵᱳᱨᱰ ᱫᱚ ᱧᱮᱞ ᱢᱮ ᱾ | yes | बोर्ड को देखें | ✅ | ❌ 0/20 | no |
| यह किताब है। | ᱱᱚᱶᱟ ᱫᱚ ᱢᱤᱫᱴᱟᱝ ᱯᱚᱛᱚᱵ ᱾ | no | यह एक किताब है | ❌ | – | no |
| यह कलम है। | ᱱᱚᱶᱟ ᱫᱚ ᱢᱤᱫᱴᱟᱝ ᱯᱮᱱ ᱾ | no | यह एक पैन है | ❌ | – | no |
| यह पानी है। | ᱱᱚᱶᱟ ᱫᱚ ᱫᱟᱜ ᱾ | yes | यह पानी है | ✅ | ❌ 0/20 (ᱶ heard as ᱣ) | no |
| नमस्ते। | ᱦᱚᱞᱮᱹᱣ, ᱦᱚᱞᱮᱹᱣ ᱾ | no (loops) | हैलो, हैलो | ❌ | – | no |
| सुप्रभात। | ᱟᱹᱰᱤ ᱱᱟᱯᱟᱭ ꯑꯌꯨꯛ ᱾ | no (Meitei/Urdu script) | – | ❌ | – | no |
| धन्यवाद। | ᱥᱟᱨᱦᱟᱰ ᱮᱢ ᱢᱮ ᱾ | no | धन्यवाद | ❌ | – | no |
| बहुत अच्छा। | ᱟᱹᱰᱤ ᱱᱟᱯᱟᱭ ᱾ | yes | बहुत अच्छा है | ✅ | ✅ take 1; app file exact | **audio** |
| शाबाश। | ᱥᱟᱵᱟᱥ ᱾ | yes | सुभाष | ❌ meaning | – | no |
| तुम्हारा नाम क्या है? | ᱟᱢᱟᱜ ᱧᱩᱛᱩᱢ ᱪᱮᱫ? | yes | आपका नाम क्या है? | ✅ | ✅ take 1; app file exact (fragile) | **audio** |
| तुम कैसे हो? | ᱟᱢ ᱪᱮᱫ ᱞᱮᱠᱟ? | words yes (final ?/᱾ varies) | आप कैसे हैं? | ✅ | ✅ take 1, ❌ processed app file | no |
| यह क्या है? | ᱱᱚᱶᱟ ᱫᱚ ᱪᱮᱫ? | yes | यह क्या है? | ✅ | ❌ 0/20 (ᱶ heard as ᱣ) | no |
| बच्चों, अपनी किताब खोलो। (checked separately: `verify_one.py`, `verify_one_children_open_book_log.txt`) | ᱜᱤᱫᱽᱨᱟᱹᱠᱚ, ᱟᱢᱟᱜ ᱯᱚᱛᱚᱵ ᱫᱚ ᱮᱦᱚᱵ ᱢᱮ ᱾ | no: without "।" and with beam-4 it is ᱜᱤᱫᱽᱨᱟᱹᱠᱚ, ᱟᱢᱟᱜ ᱯᱚᱛᱚᱵ ᱮᱦᱚᱵ ᱢᱮ ᱾; earlier runs 2/10 identical with a third form (ᱮᱛᱚᱦᱚᱵ) | बच्चों, अपनी किताब शुरू करें | ❌ inconsistent + meaning (open→start) | not run | no |
