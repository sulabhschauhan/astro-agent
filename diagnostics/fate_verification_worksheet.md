# Line of Fate — Verification Worksheet (13 rules)

> **VERIFICATION IS SULABH'S.** This file is a review aid only — a
> deterministic fidelity pre-check plus a formatted review row per rule.
> **No rule's `verified` flag was changed by producing this worksheet.**
> Every rule in `data/palm_rules/palm_rules_fate_line_v1.json` still reads
> `"verified": false, "verifier": null, "verified_date": null` exactly as
> authored. The two empty columns at the right of each row
> (`Sulabh_verdict`, `source_fidelity to record`) are for Sulabh to fill in
> by hand; nothing here pre-fills or infers them.

## What the FIDELITY PRE-CHECK does and does not do
Deterministic, character-level only — locates each rule's `source_quote`
in `data/cheiro/cheiro_pdf_fulltext.md` and classifies the match:

- **EXACT** — the quote appears verbatim (char-for-char) in the fulltext.
- **OCR_DRIFT** — matches only after normalizing known OCR corruption
  (the `¬ ` soft-hyphen line-break artifact, `V hen`→`When`,
  `failm*e`→`failure`, curly-vs-straight quote/dash normalization,
  whitespace collapse) — i.e. the rule's quote is a *cleaned* version of a
  garbled fulltext span. Would show both spans side by side for Sulabh to
  judge; not needed this run (see below).
- **MISMATCH** — cannot be reconciled even after OCR normalization
  (possible paraphrase-creep). Hard-flagged.
- **NOT_FOUND** — not locatable in the fulltext at all. Hard-flagged.

This checks **fidelity to the source text only** — it says nothing about
whether the antecedent modeling, claim wording, or vocabulary reachability
is *correct*. That judgment, and the `verified` flag itself, stay entirely
Sulabh's.

## Summary — fidelity class counts

| class | count | rule_ids |
|---|---|---|
| **EXACT** | **13** | FT_001, FT_002, FT_003, FT_004, FT_005, FT_006, FT_007, FT_008, FT_009, FT_010, FT_011, FT_012, FT_013 |
| OCR_DRIFT | 0 | — |
| MISMATCH (hard-flag) | 0 | — |
| NOT_FOUND (hard-flag) | 0 | — |

**All 13 rules' `source_quote` fields are byte-exact substrings of their
cited fulltext lines.** Zero hard flags. This includes `FT_011`, whose
quote deliberately preserves the source's own OCR garble (`"V hen"`,
`"failm*e"`) verbatim — that garble is *in the source itself* at line 1112,
so the rule's quote matching it exactly is the correct outcome, not a
defect; see FT_011's row below.

**Display note (not a data issue):** printing these quotes through this
session's terminal renders the curly apostrophe (`’`, U+2019) as a `�`
mojibake glyph in a few rows (FT_002, FT_005, FT_009, FT_012) — a Windows
console/codepage rendering artifact only. Verified directly at the
Unicode-codepoint level (bypassing display): both the rule JSON and the
fulltext file contain the identical `U+2019` character at every one of
those positions, with no `U+FFFD` (replacement character) anywhere in
either file. No corruption exists; this note exists only so a reviewer
who re-runs a similar check on this terminal isn't misled by the same
rendering glitch.

---

## Review rows

### FT_001 — doctrine F014a — p103, fulltext line 1093
| field | value |
|---|---|
| antecedents | `Line of Fate/Starting_Point → relation_target:Line of Life` AND `Line of Fate/Depth=well_marked` |
| claim | A fate line rising from the line of life and strong from that point on brings success and riches won by personal merit. |
| source_quote | "If the fate-line rise from the line of life and from that point on is strong, success and riches will be won by personal merit;" |
| **fidelity** | **EXACT** (line 1093) |
| NOTES (schema_flags) | NAMING-MISMATCH: source says "is strong" (no literal 'strong' token in any value pool) — mapped to `Depth=well_marked` as the nearest closed-vocab match. Verify live-phrasing before treating as fireable; raise for Sulabh if a dedicated 'strong' token is preferred instead. |
| Sulabh_verdict [verify / hold / fix] | |
| source_fidelity to record | |

### FT_002 — doctrine F014b — p103, fulltext line 1093
| field | value |
|---|---|
| antecedents | `Line of Fate/Starting_Point → relation_target:Wrist` AND `Line of Fate/Proximity=touching → relation_target:Line of Life` |
| claim | A fate line starting low near the wrist and held close by the side of the life line means the subject's early life is sacrificed to the wishes of parents or relatives. |
| source_quote | "but if the line be marked low down near the wrist and tied down, as it were, by the side of the life-line, it tells that the early portion of the subject's life will be sacrificed to the wishes of parents or relatives (g-g, Plate XX.)." |
| **fidelity** | **EXACT** (line 1093) |
| NOTES (schema_flags) | NAMING-MISMATCH: source says "tied down ... by the side of the life-line" (no literal degree word) — mapped to `Proximity=touching` (closest of the 3 closed degree values: touching/medium/distant) as an interpretive choice, not a literal match. |
| Sulabh_verdict [verify / hold / fix] | |
| source_fidelity to record | |

### FT_003 — doctrine F015 — p103, fulltext line 1094
| field | value |
|---|---|
| antecedents | `Line of Fate/Starting_Point → relation_target:Wrist` AND `Line of Fate/Slope=straight` AND `Line of Fate/Ending_Point → relation_target:Mount of Saturn` |
| claim | A fate line rising from the wrist and running straight to the Mount of Saturn is a sign of extreme good fortune and success. |
| source_quote | "When the line of fate rises from the wrist and proceeds straight up the hand to its destination on the Mount of Saturn, it is a sign of extreme good fortune and success." |
| **fidelity** | **EXACT** (line 1094) |
| NOTES (schema_flags) | none |
| Sulabh_verdict [verify / hold / fix] | |
| source_fidelity to record | |

### FT_004 — doctrine F016a, F016b — p103, fulltext line 1095
| field | value |
|---|---|
| antecedents | `Line of Fate/Starting_Point → relation_target:Mount of Luna` |
| claim | A fate line rising from the Mount of Luna makes fate and success more or less dependent on the fancy and caprice of other people — often seen in public favorites. |
| source_quote | "Rising from the Mount of Luna, fate and success will be more or less dependent on the fancy and caprice of other people." |
| **fidelity** | **EXACT** (line 1095) |
| NOTES (schema_flags) | MODIFIER-FOLD: doctrine F016b ("This is very often found in the case of public favorites.") is a consequence-elaboration of this same antecedent, not authored as a separate rule — folded into claim prose only. |
| Sulabh_verdict [verify / hold / fix] | |
| source_fidelity to record | |

### FT_005 — doctrine F021a, F021c — p104, fulltext line 1100
| field | value |
|---|---|
| antecedents | `Line of Fate/Ending_Point → relation_target:Mount of Jupiter` |
| claim | A fate line ascending to the center of the Mount of Jupiter brings unusual distinction and power into the subject's life — such people are born to climb higher than their fellows through enormous energy, ambition, and determination. |
| source_quote | "If the line of fate ascend to the center of the Mount of Jupiter, unusual distinction and power will come into the subject's life." |
| **fidelity** | **EXACT** (line 1100) |
| NOTES (schema_flags) | MODIFIER-FOLD: F021c ("Such people are born to climb up higher...") folded into claim prose, not a separate rule. DUPLICATE-RECONCILED: doctrine F023 (p104, "crossing its own mount and reaching Jupiter...") keys the same `Ending_Point=Mount of Jupiter` primitive and was flagged a near-duplicate — reconciled here, not separately authored; F023's "crossing its own mount" precondition is not represented. |
| Sulabh_verdict [verify / hold / fix] | |
| source_fidelity to record | |

### FT_006 — doctrine F024a — p104, fulltext line 1103
| field | value |
|---|---|
| antecedents | `Line of Fate/Length=cutting_into_finger_of_Saturn` |
| claim | A fate line that runs beyond the palm, cutting into the finger of Saturn, is not a good sign — everything in the subject's life will go too far. |
| source_quote | "When the line runs beyond the palm, cutting into the finger of Saturn, it is not a good sign, as everything will go too far." |
| **fidelity** | **EXACT** (line 1103) |
| NOTES (schema_flags) | LOWER-CONFIDENCE: `cutting_into_finger_of_Saturn` is registry-legal and Length is attribute-legal for Line of Fate, but the FATE LINE vision-prompt block only solicits generic "same attributes" free text — this exact extreme-length phrasing is never explicitly prompted for. Recommend confirming live-phrasing reachability before treating as fireable. |
| Sulabh_verdict [verify / hold / fix] | |
| source_fidelity to record | |

### FT_007 — doctrine F025a — p104, fulltext line 1104
| field | value |
|---|---|
| antecedents | `Line of Fate/Ending_Point → relation_target:Line of Heart` |
| claim | A fate line abruptly stopped by the line of heart means success will be ruined through the affections. |
| source_quote | "When the line of fate is abruptly stopped by the line of heart, success will be ruined through the affections;" |
| **fidelity** | **EXACT** (line 1104) |
| NOTES (schema_flags) | none |
| Sulabh_verdict [verify / hold / fix] | |
| source_fidelity to record | |

### FT_008 — doctrine F026 — p104, fulltext line 1105
| field | value |
|---|---|
| antecedents | `Line of Fate/Ending_Point → relation_target:Line of Head` |
| claim | A fate line stopped by the line of head means success will be thwarted by some stupidity or blunder of the head. |
| source_quote | "When stopped by the line of head, it foretells that success will be thwarted by some stupidity or blunder of the head." |
| **fidelity** | **EXACT** (line 1105) |
| NOTES (schema_flags) | none |
| Sulabh_verdict [verify / hold / fix] | |
| source_fidelity to record | |

### FT_009 — doctrine F028 — p104, fulltext line 1107
| field | value |
|---|---|
| antecedents | `Line of Fate/Starting_Point → relation_target:Line of Head` AND `Line of Head/Depth=well_marked` *(cross-feature)* |
| claim | A fate line rising from a well-marked line of head means success will be won late in life, after a hard struggle and through the subject's own talents. |
| source_quote | "If the line of fate rise from the line of head, and that line be well marked, then success will be won late in life, after a hard struggle and through the subject's talents." |
| **fidelity** | **EXACT** (line 1107) |
| NOTES (schema_flags) | CROSS-FEATURE ANTECEDENT: second antecedent keys on Line of Head's own Depth, not Line of Fate — literal match to "well marked", confirmed structurally supported by `palm_rules_table._antecedent_fires()` (feature read per-antecedent). CROSS-LINE INDEX: per README.md this cross-line rule is NOT YET logged in `_doctrine/cross_line_index.md` — open debt. |
| Sulabh_verdict [verify / hold / fix] | |
| source_fidelity to record | |

### FT_010 — doctrine F029 — p104, fulltext line 1108
| field | value |
|---|---|
| antecedents | `Line of Fate/Starting_Point → relation_target:Line of Heart` |
| claim | A fate line rising from the line of heart extremely late in life means success will be won only after a difficult struggle. |
| source_quote | "When it rises from the line of heart extremely late in life, after a difficult struggle success will be won." |
| **fidelity** | **EXACT** (line 1108) |
| NOTES (schema_flags) | none |
| Sulabh_verdict [verify / hold / fix] | |
| source_fidelity to record | |

### FT_011 — doctrine F031 — p105, fulltext line 1112
| field | value |
|---|---|
| antecedents | `Line of Fate/Continuity=broken` |
| claim | A broken and irregular fate line means an uncertain career — the ups and downs of success and failure, full of light and shadow. |
| source_quote | "V hen broken and irregular, the career will be uncertain; the ups and downs of success and failm*e full of light and shadow." |
| **fidelity** | **EXACT** (line 1112) — quote matches the fulltext's own OCR garble ("V hen", "failm*e") verbatim, by design |
| NOTES (schema_flags) | OCR ARTIFACT: preserved verbatim per chunk_exact convention, not corrected. ANTECEDENT SIMPLIFICATION: source names "broken and irregular"; only `Continuity=broken` authored — a second ANDed `Continuity=irregular` antecedent on the same attribute would be permanently unfireable (self-contradictory equality check); "irregular" folded into claim prose instead. NEAR-DUPLICATE: shares its antecedent with FT_012's *pre-Step-3* form — see FT_012 below, now resolved (different value). |
| Sulabh_verdict [verify / hold / fix] | |
| source_fidelity to record | |

### FT_012 — doctrine F032a — p105, fulltext line 1113
| field | value |
|---|---|
| antecedents | `Line of Fate/Continuity=broken_overlapping` |
| claim | A fate-line break where the second portion begins before the first one ends is not simple misfortune and loss but denotes a complete change in life — one more in accordance with the subject's own wishes, in position and success, if the overlap is very pronounced. |
| source_quote | "When there is a break in the line, it is a sure sign of misfortune and loss; but if the second portion of the line begin before the other leaves off, it de¬ notes a complete change in life, and if very decided it will mean a change more in accordance with the subject's own wishes in the way of position and success (a-a, Plate XXI.)." |
| **fidelity** | **EXACT** (line 1113) — including the source's own `de¬ notes` OCR line-break artifact, preserved verbatim |
| NOTES (schema_flags) | RE-POINTED (Step 3 of 3): was `Continuity=broken` (misfortune/loss claim, duplicating FT_011); now `Continuity=broken_overlapping`. source_quote deliberately widened to the FULL sentence (both clauses) since the overlap claim only makes sense as a contrast against the general-break clause it overrides. RESOLVED DESIGN POINT: FT_011/FT_012 are mutually exclusive values of one single-valued attribute — no precedence rule needed. **UNPROVEN (2 unknowns)**: (1) whether GPT-4o vision can distinguish an overlapping break from a clean one in a real photo — untested; (2) whether the extractor correctly routes the FATE LINE `BREAK TYPE` field into `Continuity` without collision against the inherited free-text break signal — traced only for one synthetic n=1 trial (safe), not proven in general. |
| Sulabh_verdict [verify / hold / fix] | |
| source_fidelity to record | |

### FT_013 — doctrine F033, F033b — p105, fulltext line 1114
| field | value |
|---|---|
| antecedents | `Line of Fate/Continuity=double` |
| claim | A double or sister fate line is an excellent sign, denoting two distinct careers which the subject will follow. |
| source_quote | "A double or sister fate-line is an excellent sign." |
| **fidelity** | **EXACT** (line 1114) |
| NOTES (schema_flags) | MODIFIER-FOLD: F033b ("It denotes two distinct careers...") folded into claim prose, not a separate rule. F033c ("This is much more important if they go to different mounts.") is PARKED_RELATION per doctrine_fate.md (compound dual-termination) and is NOT authored here. |
| Sulabh_verdict [verify / hold / fix] | |
| source_fidelity to record | |

---

## Reminder
Fidelity PASS on all 13 rows means the **quotes are faithful to the
source text** — it says nothing about whether an antecedent's modeling
choice, a NAMING-MISMATCH soft-token substitution (FT_001, FT_002), a
lower-confidence phrasing guess (FT_006), an unproven vision capability
(FT_012), or a still-open cross-line-index gap (FT_009) should pass
Sulabh's own review. Those judgments, and every `verified` flag, remain
entirely Sulabh's non-delegable call — nothing in this worksheet infers
or pre-fills them.
