# E2F step 0 — thumb query retrieval top-k measurement

Model: Sonnet 4.6. Read-only measurement via throwaway script
`scripts/e2f_probe_thumb_retrieval.py` (imports the real
`_gather_feature_texts` / `_resolve_feature_quality` /
`_build_feature_query` from `agent/interpretive/palm_reading.py` and
the real `search()` from `ingestion/query_engine.py` — no
reimplementation, no stubbing; live ChromaDB + live OpenAI embedding
call, `text-embedding-3-small`). No source/test edits. No commit.

## Inputs (verbatim from `diagnostics/dogfood_capture.md`)

**Run 2 (`## RUN 2026-07-27T15:04:44.168390`), Confirmed descriptions,
THUMB field, both hands** (dogfood_capture.md:145, :165):

- LEFT: `THUMB: Medium size, set moderately low, wide angle from the palm.`
- RIGHT: `THUMB: Medium size, set moderately low, wide angle from the palm.`
- hand_detail: none in this run (Run 2 has no `#### HAND_DETAIL` section).

`_PLAIN_FEATURE_FIELDS` thumb entry (`palm_reading.py:334`):
`"thumb": ("THUMB", "Thumb")`.

**Run 3 (`## RUN 2026-07-27T15:07:04.792115`), HAND_DETAIL block,
Thumb bullet** (dogfood_capture.md:272), used for the controlled
with-hand_detail comparison:

`- **Thumb**: The thumb is of average length with a moderate angle of separation from the hand, indicating some flexibility.`

This matches `_parse_bullet_fields`'s `- **Label**: text` shape
(`_BULLET_FIELD` regex, `palm_reading.py:227`) exactly — no
reconstruction-shape mismatch, so the step-2 STOP condition did not
fire.

## Exact query strings used (both variants, verbatim from script output)

WITHOUT hand_detail:
```
what does a medium size thumb signify — meaning and indications of a medium size thumb
```

WITH hand_detail (Run 3 Thumb bullet):
```
what does a medium size / the thumb is of average length with a moderate angle of separation from the hand thumb signify — meaning and indications of a medium size / the thumb is of average length with a moderate angle of separation from the hand thumb
```

Note: LEFT and RIGHT thumb text is byte-identical in Run 2, so
`_resolve_feature_quality`'s dedup (`seen` list, `palm_reading.py:431-434`)
collapses both to a single `"medium size"` clause in the no-hand_detail
variant — this isn't a bug in the probe, it's what the real merge
function does on this input.

## Top-20 WITHOUT hand_detail

| rank | chunk_id | score | text (first 100 chars) |
|---|---|---|---|
| 1 | cheiroslanguageo00chei_1_p88_c0 | 0.5569 | 45 Cheiro's Language of the Hand.  formed thumb denotes strength of intellectual will; the short, th |
| 2 | cheiroslanguageo00chei_1_p87_c0 | 0.5513 | The Thumb. 47  reason goes, the thumb loses all power and drops in on the hand, but that if the reas |
| 3 | cheiroslanguageo00chei_1_p88_c1 | 0.5327 | When the second phalange is much longer than the first, the subject, though having all the calmness |
| 4 | cheiroslanguageo00chei_1_p89_c2 | 0.5322 | THE SECOND PHALANGE.  The next important characteristic of the thumb is the shape and make of the se |
| 5 | cheiroslanguageo00chei_1_p89_c0 | 0.5226 | The Thumb. 49  THE SUPPLE-JOINTED THUMB.  For example, the supple-jointed thumb, bending from the ha |
| 6 | cheiroslanguageo00chei_1_p85_c0 | 0.5033 | CHAPTER IX. THE THUMB.  THE thumb is in every sense so important that it calls for special atten- ti |
| 7 | cheiroslanguageo00chei_1_p86_c0 | 0.4837 | 46 Cheiro's Language of the Hand.  Trinity; the ordinary priest has to use the whole hand. And, agai |
| 8 | cheiroslanguageo00chei_1_p97_c0 | 0.4731 | The Fingers. Dd  of balance in the hand to the thumb, and indicates the power of the subject to infl |
| 9 | cheiroslanguageo00chei_1_p96_c2 | 0.4652 | When pointed, the reverse—callousness and frivolity.  When the third finger (the finger of the Sun) |
| 10 | cheiroslanguageo00chei_1_p99_c0 | 0.4482 | The Palm, and Large and Small Hands.  en =)  LARGE AND SMALL HANDS.  It is a thing well worth remark |
| 11 | cheiroslanguageo00chei_1_p90_c2 | 0.4443 | When the hand is hard the natural tendeney toward energy and firm- ness indicated by the thumb is in |
| 12 | cheiroslanguageo00chei_1_p96_c3 | 0.4438 | When the fourth, or little finger, is well-shaped and long, it acts as a kind |
| 13 | cheiroslanguageo00chei_1_p96_c1 | 0.4225 | When the first, or index finger, is excessively long, it denotes great pride, and a tendeney to rule |
| 14 | cheiroslanguageo00chei_1_p95_c1 | 0.4106 | Fingers thick and clumsy, as well as short, are more or less cruel and selfish.  When the fingers ar |
| 15 | cheiroslanguageo00chei_1_p98_c0 | 0.4083 | CHAPTER NIL THE PALM, AND LARGE AND SMALL HANDS.  A rut, hard, dry palm indicates timidity, and a ne |
| 16 | cheiroslanguageo00chei_1_p225_c1 | 0.4074 | On all iniportant points, such as Ulness, death, loss of fortune, marriage, and so forth, see what t |
| 17 | cheiroslanguageo00chei_1_p85_c1 | 0.4043 | gives the blessing hy the thumb and first and second fingers, representing the 45 |
| 18 | cheiroslanguageo00chei_1_p96_c0 | 0.4035 | ot Cheivo's Language of the Hand.  his own comfort before that of others; he will desire luxury in e |
| 19 | cheiroslanguageo00chei_1_p190_c0 | 0.4031 | 124 Cheiro's Language of the Hand.  THE STAR ON THE FINGERS.  The star on the tips or outer phalange |
| 20 | cheiroslanguageo00chei_1_p220_c1 | 0.4019 | The first class is very ordinary. The man or woman becomes a mur- derer by civeumstances. Such an in |

Production `_N_RESULTS_PER_FEATURE = 3` (`palm_reading.py:176`) means
the REAL Run-2 gated set was ranks 1-3 only: `p88_c0`, `p87_c0`,
`p88_c1` — all three are genuinely thumb-topic chunks (Ch. IX, "The
Thumb"), not off-topic noise.

## Top-20 WITH hand_detail (Run 3 Thumb bullet)

| rank | chunk_id | score | text (first 100 chars) |
|---|---|---|---|
| 1 | cheiroslanguageo00chei_1_p87_c0 | 0.5395 | The Thumb. 47  reason goes, the thumb loses all power and drops in on the hand, but that if the reas |
| 2 | cheiroslanguageo00chei_1_p88_c1 | 0.5126 | When the second phalange is much longer than the first, the subject, though having all the calmness |
| 3 | cheiroslanguageo00chei_1_p89_c2 | 0.5071 | THE SECOND PHALANGE.  The next important characteristic of the thumb is the shape and make of the se |
| 4 | cheiroslanguageo00chei_1_p88_c0 | 0.5063 | 45 Cheiro's Language of the Hand.  formed thumb denotes strength of intellectual will; the short, th |
| 5 | cheiroslanguageo00chei_1_p89_c0 | 0.4808 | The Thumb. 49  THE SUPPLE-JOINTED THUMB.  For example, the supple-jointed thumb, bending from the ha |
| 6 | cheiroslanguageo00chei_1_p86_c0 | 0.4469 | 46 Cheiro's Language of the Hand.  Trinity; the ordinary priest has to use the whole hand. And, agai |
| 7 | cheiroslanguageo00chei_1_p96_c2 | 0.4392 | When pointed, the reverse—callousness and frivolity.  When the third finger (the finger of the Sun) |
| 8 | cheiroslanguageo00chei_1_p85_c0 | 0.4389 | CHAPTER IX. THE THUMB.  THE thumb is in every sense so important that it calls for special atten- ti |
| 9 | cheiroslanguageo00chei_1_p90_c2 | 0.4382 | When the hand is hard the natural tendeney toward energy and firm- ness indicated by the thumb is in |
| 10 | cheiroslanguageo00chei_1_p96_c3 | 0.4367 | When the fourth, or little finger, is well-shaped and long, it acts as a kind |
| 11 | cheiroslanguageo00chei_1_p97_c0 | 0.4342 | The Fingers. Dd  of balance in the hand to the thumb, and indicates the power of the subject to infl |
| 12 | cheiroslanguageo00chei_1_p99_c0 | 0.4263 | The Palm, and Large and Small Hands.  en =)  LARGE AND SMALL HANDS.  It is a thing well worth remark |
| 13 | cheiroslanguageo00chei_1_p96_c0 | 0.4263 | ot Cheivo's Language of the Hand.  his own comfort before that of others; he will desire luxury in e |
| 14 | cheiroslanguageo00chei_1_p57_c1 | 0.4220 | THE SQUARE HAND AND MIXED FINGERS.  This is a type that is very often seen, and more so among men th |
| 15 | cheiroslanguageo00chei_1_p221_c1 | 0.4137 | It is the hand of the subtlest nature in regard to crime. There will be nothing abnormal in connecti |
| 16 | cheiroslanguageo00chei_1_p220_c1 | 0.4071 | The first class is very ordinary. The man or woman becomes a mur- derer by civeumstances. Such an in |
| 17 | cheiroslanguageo00chei_1_p98_c1 | 0.4053 | If it inclines to the line of life, it promises disappointment and trouble in domestic affairs, and |
| 18 | cheiroslanguageo00chei_1_p95_c1 | 0.3923 | Fingers thick and clumsy, as well as short, are more or less cruel and selfish.  When the fingers ar |
| 19 | cheiroslanguageo00chei_1_p65_c1 | 0.3917 | With these hands, therefore, it must be borne im mind that the developed joints are the peculiar cha |
| 20 | cheiroslanguageo00chei_1_p95_c2 | 0.3902 | When the fingers are thick and pnffy at the base, the subject considers  53 |

With hand_detail, production top-3 shifts to: `p87_c0`, `p88_c1`,
`p89_c2` — `p88_c0` (rank 1 without hand_detail) drops to rank 4,
outside the production `n_results=3` cutoff.

## Rank of `cheiroslanguageo00chei_1_p87_c0`

- WITHOUT hand_detail: **rank 2**, score 0.5513
- WITH hand_detail: **rank 1**, score 0.5395

## Rank of `cheiroslanguageo00chei_1_p88_c0`

- WITHOUT hand_detail: **rank 1**, score 0.5569
- WITH hand_detail: **rank 4**, score 0.5063

## Score delta, p87_c0 minus p88_c0

- WITHOUT hand_detail: 0.5513 − 0.5569 = **−0.0056** (p87_c0 scores
  slightly lower, sits one rank below p88_c0)
- WITH hand_detail: 0.5395 − 0.5063 = **+0.0332** (p87_c0 scores
  higher, sits three ranks above p88_c0)

## Observation (measurement only, no fix hypothesized)

Both `p87_c0` and `p88_c0` rank inside the top-4 in BOTH variants, and
production's actual `n_results=3` gate already includes `p87_c0` in
Run 2's real (no-hand_detail) retrieval — the chunk C3 in Run 3's
`claims_inventory` cites (`cheiroslanguageo00chei_1_p87_c0`) was
already present, ranked 2nd, in Run 2's gated 3-chunk set. Run 2's
Stage-1 `stage1_feature_diagnostics` (dogfood_capture.md:237) records
`thumb: outcome=failed_both attempt_1=validation_failed/0
attempt_2=validation_failed/0` — zero validated claims despite the
genuinely on-topic chunk being retrieved and gated. This measurement
does not determine why extraction failed on an already-present
chunk; that is outside this turn's read-only-retrieval scope. Design
chat has both top-20 lists and both score deltas to weigh (a)
top-k widening vs (c) template enrichment against.

## Script + dependency notes

- Live dependencies used: ChromaDB persist dir `data/chroma_db`
  (present, non-empty) and `OPENAI_API_KEY` (set) for the
  `text-embedding-3-small` embedding call — no stubbing, per the
  no-live-dependency-STOP constraint (dependency was available, so no
  STOP triggered).
- Console encoding note: an initial run without `PYTHONIOENCODING=utf-8`
  mangled the book's curly-quote/em-dash characters in terminal
  output (cp1252 default); re-run with `PYTHONIOENCODING=utf-8` for
  the tables above. Scores from the two runs matched to 4 decimals
  except one ±0.0001 floating-point wobble on `p88_c0` (0.5570 vs
  0.5569) — embedding-API-call noise, not a code difference.
