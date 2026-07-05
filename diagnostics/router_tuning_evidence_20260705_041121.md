# Router Tuning Evidence Dump (Session 49, P7.0f)

READ-ONLY diagnostic. No files modified, no parameters tuned. Evidence for
design chat only.

## 1. Verbatim constants from `agent/infra/calc_router.py`

### `_DOMAIN_KEYWORDS` (full lists per domain)

```python
_MARRIAGE_KEYWORDS: tuple[str, ...] = (
    "marriage", "compatibility", "partner", "kundli milan", "ashtakoot",
    "mangal dosha", "7th house", "spouse", "wedding", "relationship",
)

_CAREER_KEYWORDS: tuple[str, ...] = (
    "career", "job", "profession", "work", "business", "10th house",
    "shadbala", "strength", "saturn", "promotion", "success",
)

_DASHA_KEYWORDS: tuple[str, ...] = (
    "dasha", "period", "mahadasha", "antardasha", "current period",
    "running period", "timing", "when", "phase",
)

_DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "marriage_compatibility": _MARRIAGE_KEYWORDS,
    "career_strength": _CAREER_KEYWORDS,
    "current_dasha": _DASHA_KEYWORDS,
}
```

### `_STEM_MAP` (all entries)

```python
_STEM_MAP: dict[str, str] = {
    "married": "marriage",
    "marry": "marriage",
    "compatible": "compatibility",
    "compat": "compatibility",
    "job": "career",
    "jobs": "career",
    "working": "career",
}
```

### `_UNBUILT_MODULE_KEYWORDS` (all entries)

```python
_UNBUILT_MODULE_KEYWORDS: dict[str, str] = {
    "yoga": "yoga detection",
    "transit": "transit engine (gochara/sade sati)",
    "gochara": "gochara transit engine",
    "sade sati": "Sade Sati transit engine",
    "ashtakavarga": "Ashtakavarga (BAV/SAV)",
    "navamsa": "D9 (Navamsa) divisional chart",
    "divisional": "divisional charts (vargas)",
    "d10": "D10 divisional chart",
    "d9": "D9 (Navamsa) divisional chart",
    "varga": "divisional charts (vargas)",
    "jaimini": "Jaimini karakas/arudha/padas",
    "chara": "Chara dasha",
    "yogini": "Yogini dasha",
    "ashtottari": "Ashtottari dasha",
    "varshaphal": "Varshaphal annual chart",
    "muhurta": "Muhurta scorer (module exists but is not wired to Q&A in V1)",
}
```
Checked (as of P7.0b) via word-boundary regex `\b{re.escape(keyword)}s?\b`
against `question.lower()`, in dict-insertion order, BEFORE domain
classification -- first match wins and short-circuits.

### `_CONFIDENCE_FLOOR` / `_CONFIDENCE_MARGIN`

```python
_CONFIDENCE_FLOOR = 0.4
_CONFIDENCE_MARGIN = 0.15
```

### Exact scoring formula (`_score_domain` / `_keyword_hits`, verbatim logic)

```python
def _normalize_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    expanded = list(tokens)
    for tok in tokens:
        mapped = _STEM_MAP.get(tok)
        if mapped is not None:
            expanded.append(mapped)
    return expanded


def _keyword_hits(keyword: str, question_tokens: list[str]) -> bool:
    keyword_tokens = _normalize_tokens(keyword)
    if len(keyword_tokens) > 1:
        return " ".join(keyword_tokens) in " ".join(question_tokens)
    kw = keyword_tokens[0]
    if len(kw) < 3:
        return False
    return any(len(tok) >= 3 and (kw in tok or tok in kw) for tok in question_tokens)


def _score_domain(question_tokens: list[str], keywords: tuple[str, ...]) -> float:
    matched = sum(1 for kw in keywords if _keyword_hits(kw, question_tokens))
    return min(matched, 3) / 3
```

Route decision: `best_score < 0.4` (floor) OR `(best_score - second_score) < 0.15`
(margin) -> REFUSAL ("question not classifiable with confidence"). Multi-word
keywords match as an exact adjacent phrase substring; single-word keywords
match via bidirectional substring containment (both sides >=3 chars) against
each token, additively expanded by `_STEM_MAP`.

---

## 2. Per-row breakdown -- 10 currently-refused golden rows

For each row: question text, per-domain matched keywords (after
normalization/stemming) + score, and the refusal branch actually taken.
Computed by direct inspection via `_normalize_tokens` / `_keyword_hits` /
`_score_domain` imported read-only from `calc_router.py` -- no code changed.

### sulabh_career_q1 -- "How strong is my career potential?"
- normalized tokens: `how, strong, is, my, career, potential`
- marriage_compatibility: matched=[] score=0.000
- career_strength: matched=`['career']` score=0.333
- current_dasha: matched=[] score=0.000
- best=career_strength (0.333), second=marriage_compatibility (0.000), margin=0.333
- **Branch: confidence-floor refusal** (0.333 < 0.4)

### sulabh_career_q2 -- "Which planet most supports my profession?"
- normalized tokens: `which, planet, most, supports, my, profession`
- marriage_compatibility: matched=[] score=0.000
- career_strength: matched=`['profession']` score=0.333
- current_dasha: matched=[] score=0.000
- best=career_strength (0.333), second=marriage_compatibility (0.000), margin=0.333
- **Branch: confidence-floor refusal** (0.333 < 0.4)

### sulabh_career_q3 -- "Is my 10th house strong enough for leadership roles?"
- normalized tokens: `is, my, 10th, house, strong, enough, for, leadership, roles`
- marriage_compatibility: matched=[] score=0.000
- career_strength: matched=`['10th house']` score=0.333
- current_dasha: matched=[] score=0.000
- best=career_strength (0.333), second=marriage_compatibility (0.000), margin=0.333
- **Branch: confidence-floor refusal** (0.333 < 0.4)
- Note: "strong" does NOT match keyword "strength" -- bidirectional substring
  containment requires one to literally contain the other ("strong" vs
  "strength" share only the "str" prefix, neither contains the other).

### sulabh_career_q4 -- "Will a job change in the next 12 months favor me?"
- normalized tokens: `will, a, job, change, in, the, next, 12, months, favor, me, career`
  (note: "career" appended via `_STEM_MAP["job"] -> "career"` additive expansion)
- marriage_compatibility: matched=[] score=0.000
- career_strength: matched=`['career']` score=0.333
- current_dasha: matched=[] score=0.000
- best=career_strength (0.333), second=marriage_compatibility (0.000), margin=0.333
- **Branch: confidence-floor refusal** (0.333 < 0.4)
- **Latent bug found on inspection**: the literal keyword "job" does NOT
  match here even though the token "job" is plainly present in the
  question. `_keyword_hits(keyword, ...)` calls `_normalize_tokens(keyword)`
  on the keyword string itself, not just the question -- and because "job"
  is itself a `_STEM_MAP` key, `_normalize_tokens("job")` returns
  `['job', 'career']` (length 2), which routes "job" into the **multi-word
  phrase-match branch** (`len(keyword_tokens) > 1`) instead of the
  single-word substring-containment branch. That branch requires the
  literal adjacent phrase `"job career"` to appear in the question -- which
  it never will in natural text. Verified directly:
  `_keyword_hits("job", toks)` -> `False`; `_keyword_hits("career", toks)`
  -> `True`. Net effect: "job" only "counts" via its stem-mapped alias
  "career", never via itself -- for this question that happens not to
  change the final score (1 hit either way), but it means the literal "job"
  keyword-list entry is effectively **dead**.

  Checked all 7 `_STEM_MAP` keys against all 3 `_DOMAIN_KEYWORDS` lists for
  exact membership: **only "job" is both a `_STEM_MAP` key and a literal
  `_DOMAIN_KEYWORDS` entry** (in `_CAREER_KEYWORDS`). "jobs", "married",
  "marry", "compatible", "compat", "working" are `_STEM_MAP` keys too, but
  are NOT themselves literal keyword-list entries -- their aliases
  ("career", "marriage", "compatibility") are the literal entries, and none
  of those aliases are themselves `_STEM_MAP` keys, so they don't trigger
  this same self-referential expansion. This bug is therefore narrow: it
  only ever affects the literal "job" keyword, and only in questions
  containing "job" without an adjacent literal "career" -- it happened to
  be score-neutral for q4 specifically (1 matched keyword either way via
  the "career" alias), so it is not, by itself, the reason q4 was refused.

### sulabh_marriage_q7 -- "Does either of us have Mangal Dosha (Kuja Dosha)?"
- normalized tokens: `does, either, of, us, have, mangal, dosha, kuja, dosha`
- marriage_compatibility: matched=`['mangal dosha']` score=0.333
- career_strength: matched=[] score=0.000
- current_dasha: matched=[] score=0.000
- best=marriage_compatibility (0.333), second=career_strength (0.000), margin=0.333
- **Branch: confidence-floor refusal** (0.333 < 0.4)

### sulabh_marriage_q8 -- "Is there a Nadi dosha between us?"
- normalized tokens: `is, there, a, nadi, dosha, between, us`
- marriage_compatibility: matched=[] score=0.000
- career_strength: matched=[] score=0.000
- current_dasha: matched=[] score=0.000
- best=marriage_compatibility (0.000), second=career_strength (0.000), margin=0.000
- **Branch: confidence-floor refusal** (0.000 < 0.4) -- zero keyword hits in
  any domain; "nadi dosha" is not in `_MARRIAGE_KEYWORDS` at all (only
  "mangal dosha" is).

### sulabh_marriage_q9 -- "Where is the weakest link in our compatibility?"
- normalized tokens: `where, is, the, weakest, link, in, our, compatibility`
- marriage_compatibility: matched=`['compatibility']` score=0.333
- career_strength: matched=[] score=0.000
- current_dasha: matched=[] score=0.000
- best=marriage_compatibility (0.333), second=career_strength (0.000), margin=0.333
- **Branch: confidence-floor refusal** (0.333 < 0.4)

### sulabh_marriage_q10 -- "What does our overall compatibility mean for us as a couple?"
- normalized tokens: `what, does, our, overall, compatibility, mean, for, us, as, a, couple`
- marriage_compatibility: matched=`['compatibility']` score=0.333
- career_strength: matched=[] score=0.000
- current_dasha: matched=[] score=0.000
- best=marriage_compatibility (0.333), second=career_strength (0.000), margin=0.333
- **Branch: confidence-floor refusal** (0.333 < 0.4)

### sulabh_dasha_q14 -- "Am I currently in Sade Sati, and when does the next cycle begin?"
- **Branch: unbuilt-module keyword match** -- keyword=`'sade sati'`,
  module=`'Sade Sati transit engine'`. Short-circuits BEFORE domain scoring
  is ever computed (see section 3 for the hypothetical score if this entry
  were absent).

### sulabh_dasha_q15 -- "Which month this year is astrologically best for me to make a major move?"
- normalized tokens: `which, month, this, year, is, astrologically, best, for, me, to, make, a, major, move`
- marriage_compatibility: matched=[] score=0.000
- career_strength: matched=[] score=0.000
- current_dasha: matched=[] score=0.000
- best=marriage_compatibility (0.000), second=career_strength (0.000), margin=0.000
- **Branch: confidence-floor refusal** (0.000 < 0.4) -- zero keyword hits in
  any of the 3 whitelisted domains; "month"/"year"/"move" are not in
  `_DASHA_KEYWORDS` (which has "period", "phase", "timing", "when", etc.,
  but not "month" or "year").

### Branch summary across all 10 rows
- **9/10** refused via the **confidence-floor path** (`best_score < 0.4`,
  either a single keyword hit at 0.333 or zero hits at 0.000).
- **1/10** (q14) refused via the **unbuilt-module-keyword path**
  (`_UNBUILT_MODULE_KEYWORDS["sade sati"]`), which never reaches domain
  scoring at all.
- **0/10** refused via the **margin-tie path** specifically (every row here
  has a second-place score of 0.000, so margin always equals best_score
  itself -- no row in this set exhibits a genuine two-domain near-tie).

---

## 3. q14 -- Sade Sati domain-keyword gap + hypothetical

**Does any sade-sati-related term exist in `_DOMAIN_KEYWORDS`?** No. Grepping
all three domain keyword tuples (`_MARRIAGE_KEYWORDS`, `_CAREER_KEYWORDS`,
`_DASHA_KEYWORDS`) for "sade" or "sati" returns zero matches in all three.
There is no domain-classification keyword for Sade Sati anywhere -- it only
exists as an `_UNBUILT_MODULE_KEYWORDS` refusal trigger.

**Hypothetical: if the `_UNBUILT_MODULE_KEYWORDS["sade sati"]` entry were
absent** (computed by inspection, no code changed): the question would fall
through to domain scoring. Normalized tokens:
`am, i, currently, in, sade, sati, and, when, does, the, next, cycle, begin`.

- marriage_compatibility: matched=[] score=0.000
- career_strength: matched=[] score=0.000
- current_dasha: matched=`['when']` score=0.333 (single hit -- "when" is a
  literal `_DASHA_KEYWORDS` entry)

Best score 0.333 < floor 0.4 -> **still REFUSED**, just via the
confidence-floor path instead of the unbuilt-module path. Removing the
"sade sati" entry alone would not make this row route or MATCH; the
question still only clears one dasha keyword ("when"), one short of the
2-hit requirement.

---

## 4. Status

Read-only. No parameters tuned, no code fixed, no changes suggested for
implementation. All findings above return to design chat.
