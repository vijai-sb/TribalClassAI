# Phase 1.5 Hindi Bug Fix Report

## Summary

Fixed two critical Hindi-related bugs identified during real browser testing:

1. **Bug 1 - Real Hindi Microphone Cache Miss**: Whisper output "Krabil, Baj Chaiye." for canonical phrase "कृपया बैठ जाइए।" was not matching any alias, causing live TTS instead of cached audio.

2. **Bug 2 - Hindi Demo Mode Showing English Phrases**: Demo Mode language selector wasn't filtering phrases correctly (root cause: server hadn't picked up code changes until reload).

Both bugs are now fixed and verified.

---

## A. Root Cause of "Krabil, Baj Chaiye." Cache Miss

**Root Cause**: 
1. Missing alias: "krabil baj chaiye" was not in `_ROMANIZED_HINDI_ALIASES` dictionary
2. Normalization issue: `_normalize()` function only stripped trailing `.?!` but not commas in the middle of text, so "Krabil, Baj Chaiye." normalized to "krabil, baj chaiye" (with comma) instead of "krabil baj chaiye" (without comma)

**Fix Applied**:
1. Added `"krabil baj chaiye": "कृपया बैठ जाइए।"` to `_ROMANIZED_HINDI_ALIASES`
2. Updated `_normalize()` to replace commas with spaces and strip all trailing punctuation: `.?!` + commas

---

## B. Files Changed

| File | Changes |
|------|---------|
| `backend/main.py` | Added "krabil baj chaiye" alias; updated `_normalize()` to handle commas; verified phrasebook matching logic |
| (No other files needed) | Bug 2 was a server caching issue - resolved by `/api/phrasebook/reload` |

---

## C. Hindi Aliases Added

```python
"krabil baj chaiye": "कृपया बैठ जाइए।"
```

Now supports these variations for "कृपया बैठ जाइए।":
- "krupaya bait jaiye"
- "kripaya baith jaiye" 
- "krupaya baith jaiye"
- "krabil baj chaiye" ← **NEW**

---

## D. Canonical Hindi Display Behavior

**Verified Working**: When an alias matches:
- Backend sets `text_result["source_text"] = canonical_text` (line 415-416 in main.py)
- UI displays: "कृपया बैठ जाइए।" (canonical Devanagari)
- NOT: "Krabil, Baj Chaiye." (raw Whisper output)

**Test Results**:
| Whisper Input | Normalized | Canonical Returned | Cache Hit |
|--------------|------------|-------------------|-----------|
| "Krabil, Baj Chaiye." | "krabil baj chaiye" | "कृपया बैठ जाइए।" | ✅ |
| "krupaya bait jaiye" | "krupaya bait jaiye" | "कृपया बैठ जाइए।" | ✅ |
| "kripaya baith jaiye" | "kripaya baith jaiye" | "कृपया बैठ जाइए।" | ✅ |
| "krupaya baith jaiye" | "krupaya baith jaiye" | "कृपया बैठ जाइए।" | ✅ |
| "dhyan se suniye" | "dhyan se suniye" | "ध्यान से सुनिए।" | ✅ |
| "aaj hum kuch naya seekhenge" | "aaj hum kuch naya seekhenge" | "आज हम कुछ नया सीखेंगे।" | ✅ |

---

## E. Cached Audio Behavior

**Verified Working**: When canonical phrase matches:
- `text_result["cached"] = True`
- Backend returns `"source": "cache"` in audio_result
- Cached Santali WAV served immediately
- NO live Parler-TTS invoked
- NO "Generating audio live..." message shown

---

## F. Root Cause of Hindi Demo Mode Showing English Phrases

**Root Cause**: The Uvicorn server was running an old version of the code (Python module caching). The `/api/phrasebook` endpoint was returning only English phrases without `source_lang` field until `/api/phrasebook/reload` was called.

**Evidence**: 
- Before reload: API returned 53 English phrases, no `source_lang` field
- After reload: API returns 85 phrases (53 en + 32 hi) with correct `source_lang` field

---

## G. Demo Mode Filtering Fix

**Frontend Logic (app.js)** - Already correct:
```javascript
function filterPhrasebook() {
    const lang = getSelectedDemoLang();  // "en" or "hi"
    const filtered = allPhrases.filter(p => p.source_lang === lang);
    renderPhrasebook(filtered);
}
```

**Backend API (/api/phrasebook)** - Returns `source_lang` field:
```json
{
  "category": "CLASSROOM MANAGEMENT",
  "source_text": "कृपया बैठ जाइए।",
  "source_lang": "hi",
  "santali_text": "ᱫᱟᱭᱟ ᱠᱟᱛᱮ ᱥᱮᱱ ᱢᱮ ᱾",
  "audio_url": "/phrasebook_audio/phrase_d95472099706.wav"
}
```

---

## H. Hindi Phrases Visible in Demo Mode

**Verified**: 32 Hindi phrases across 7 categories:

| Category | Count | Examples |
|----------|-------|----------|
| GREETING | 4 | सुप्रभात बच्चों।, नमस्ते बच्चों।, आज आप कैसे हैं?, क्या आप सीखने के लिए तैयार हैं? |
| CLASSROOM MANAGEMENT | 5 | कृपया बैठ जाइए।, खड़े हो जाइए।, ध्यान से सुनिए।, शांत रहिए।, मेरी बात ध्यान से सुनिए। |
| LEARNING MATERIALS | 5 | अपनी किताबें निकालिए।, अपनी किताब बंद कीजिए।, अपनी कॉपी निकालिए।, अपना पेन निकालिए।, बोर्ड की ओर देखिए। |
| TEACHING INSTRUCTIONS | 7 | आज हम कुछ नया सीखेंगे।, आज का पाठ शुरू करते हैं।, बोर्ड पर देखिए।, मेरे बाद दोहराइए।, इसे पढ़िए।, इसे लिखिए।, इसका उत्तर दीजिए। |
| QUESTIONS | 4 | क्या आपको समझ आया?, क्या आप समझ गए?, क्या किसी को कोई सवाल है?, क्या आप इसका उत्तर दे सकते हैं? |
| ENCOURAGEMENT | 4 | बहुत अच्छा।, अच्छा प्रयास।, फिर से कोशिश कीजिए।, शाबाश। |
| CLASS CLOSING | 3 | आज के लिए इतना ही।, धन्यवाद बच्चों।, कल मिलते हैं। |

---

## I. Search/Filter Behavior

**Verified Working**:
- Hindi selected + search "बैठ" → returns "कृपया बैठ जाइए।" only
- English selected + search → searches English phrases only
- Language switching: English → Hindi → English → Hindi works correctly with no stale phrases

---

## J. Language Switching Test

**Tested Sequence**: English → Hindi → English → Hindi

| Step | Language | Phrases Shown | Status |
|------|----------|---------------|--------|
| 1 | English | 53 English phrases | ✅ |
| 2 | Hindi | 32 Hindi phrases | ✅ |
| 3 | English | 53 English phrases | ✅ |
| 4 | Hindi | 32 Hindi phrases | ✅ |

No stale phrases, correct Santali translations, correct cached audio URLs.

---

## K. Exact Automated Tests Performed

### Test 1: Alias Matching (test_matching_full.py)
```
=== Phrasebook Matching Tests ===
Test: 'Krabil, Baj Chaiye.' (lang=hi) → cache_hit: True, canonical: 'कृपया बैठ जाइए।' PASS
Test: 'krupaya bait jaiye' (lang=hi) → cache_hit: True, canonical: 'कृपया बैठ जाइए।' PASS
Test: 'kripaya baith jaiye' (lang=hi) → cache_hit: True, canonical: 'कृपया बैठ जाइए।' PASS
Test: 'krupaya baith jaiye' (lang=hi) → cache_hit: True, canonical: 'कृपया बैठ जाइए।' PASS
Test: 'dhyan se suniye' (lang=hi) → cache_hit: True, canonical: 'ध्यान से सुनिए।' PASS
Test: 'aaj hum kuch naya seekhenge' (lang=hi) → cache_hit: True, canonical: 'आज हम कुछ नया सीखेंगे।' PASS
Test: 'Sit down' (lang=en) → cache_hit: True PASS
Test: 'Listen carefully' (lang=en) → cache_hit: True PASS
Test: 'Random hindi speech' (lang=hi) → cache_hit: False PASS
Test: 'Random english speech' (lang=en) → cache_hit: False PASS

=== All tests PASSED ===
```

### Test 2: Punctuation Normalization (test_punctuation.py)
```
Input: "Krabil, Baj Chaiye." → normalized: "krabil baj chaiye" → Canonical: "कृपया बैठ जाइए।" PASS
Input: "Krabil, Baj Chaiye" → normalized: "krabil baj chaiye" → Canonical: "कृपया बैठ जाइए।" PASS
Input: "krabil baj chaiye" → normalized: "krabil baj chaiye" → Canonical: "कृपया बैठ जाइए।" PASS
Input: "KRABIL, BAJ CHAIYE." → normalized: "krabil baj chaiye" → Canonical: "कृपया बैठ जाइए।" PASS
Input: "  krabil  baj  chaiye  " → normalized: "krabil baj chaiye" → Canonical: "कृपया बैठ जाइए।" PASS
```

### Test 3: WebSocket Error Handling
```
Invalid JSON test: {'type': 'error', 'message': 'Invalid message format.', 'error_code': 'INVALID_JSON'} PASS
End without audio: {'type': 'error', 'message': 'No audio received.', 'error_code': 'NO_AUDIO'} PASS
```

### Test 4: Health & Phrasebook API
```
GET /health → {"status":"ok","models_loaded":{"stt":true,"translate":true,"tts":true},"phrasebook_phrases":85} PASS
GET /api/phrasebook → 85 phrases with source_lang field PASS
POST /api/phrasebook/reload → {"status":"ok","phrases_loaded":85} PASS
```

---

## L. Test Results Summary

| Test | Result |
|------|--------|
| Hindi alias "krabil baj chaiye" added | ✅ PASS |
| Normalization handles commas | ✅ PASS |
| Canonical Hindi display | ✅ PASS |
| Cached audio for matched phrases | ✅ PASS |
| Free-form Hindi not forced to phrasebook | ✅ PASS |
| Demo Mode Hindi filtering | ✅ PASS |
| Demo Mode language switching | ✅ PASS |
| Demo Mode search within language | ✅ PASS |
| English phrases unchanged | ✅ PASS |
| Phrasebook cache key includes source_lang | ✅ PASS |
| WebSocket error handling | ✅ PASS |
| Health endpoint | ✅ PASS |

---

## M. Remaining Limitations

1. **CPU Parler-TTS Latency**: Uncached live TTS still 30-90s on CPU (unchanged, hardware limitation)
2. **Alias Coverage**: Only 32 Hindi phrases have aliases; free-form Romanized Hindi won't match
3. **No Fuzzy Matching**: Conservative approach - exact alias match required (by design)
4. **Model Versions**: Still using Whisper base, distilled IndicTrans2, Parler-TTS (no upgrades)
5. **Server Module Caching**: Requires `/api/phrasebook/reload` after code changes (Python behavior)

---

## Verification Checklist

- [x] Existing English phrasebook still works
- [x] Hindi phrasebook works
- [x] Hindi cached audio works
- [x] Hindi Demo Mode works
- [x] English Demo Mode still works
- [x] Romanized Hindi aliases work (including "Krabil, Baj Chaiye.")
- [x] Canonical Hindi display works
- [x] Conservative phrase correction works
- [x] Free-form Hindi not incorrectly rewritten
- [x] English recognition still works
- [x] Hindi recognition still works
- [x] Back-to-back recordings work (Phase 1 preserved)
- [x] No cross-request contamination (Phase 1 preserved)
- [x] WebSocket remains stable
- [x] /health remains functional
- [x] Phase 1 fixes remain intact
- [x] No persistent server left running

---

**Phase 1.5 Hindi Bug Fix: COMPLETE**