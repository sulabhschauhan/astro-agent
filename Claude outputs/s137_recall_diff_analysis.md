# S137 capture diff — recall question, and what it actually found

Design-chat analysis, 2026-09-19. Read-only, $0, no model call.
Sources: `diagnostics/qa_capture/20260919T072700Z.md` (Phase 1),
`diagnostics/qa_capture/20260919T080136Z.md` (after the prompt fix).
Controlled: identical question, identical `unit_ids` selection, same chart.

**Headline: the recall drop is real but secondary. The precision gain is not
what it appears to be — 4 of the 8 shipped claims in the fixed run carry a
chart assertion the fact block refutes, each shielded by a precondition that
is true and does not test the assertion.**

---

## 1. The two runs, side by side

| | `072700Z` (Phase 1) | `080136Z` (after fix) |
|---|---|---|
| claims_in | 14 | 8 |
| kept / dropped | 11 / 3 | 8 / 0 |
| applicable / undetermined / not_applicable | 2 / 9 / 3 | 8 / 0 / 0 |
| predicate verdicts | 3 SAT · 3 CON · 9 UNEVAL | 18 SAT · 0 · 0 |
| typed_coverage | 0.40 | 1.00 |

## 2. Where Run A's 14 claims went

**Correctly resolved (8).**
- A2 `ch39_s009`, A7 `ch39_s006`, A11 `ch21_s012` — declared in Run B's `silent_on`.
- A3, A8, A10 (`ch39_s008`) — upgraded into typed B2 / B3 / B8.
- A5 `ch24_s033` (4th lord in 10th) and A6 `ch24_s008` (asc lord in 10th) — both
  genuinely false, CONTRADICTED in Run A, correctly absent from Run B.
- A1 → re-expressed as B1 / B6.
- A14 `ch21_s008` — correctly gone.

**Lost without declaration (3).**

| claim | segment | precondition | fact block | verdict |
|---|---|---|---|---|
| A13 | `ch24_s103` | `lord_in_house(11, 6)` | `lord_house_map["11"] = 6` | **SATISFIED — true** |
| A12 | `ch21_s005` | was `unfittable` | expressible now (`planet_in_house(Mercury,4)`) | unknown |
| A9 | `ch39_s007`, `ch39_s020` | was `unfittable` | expressible now — `vipareeta_6_8_link` **FIRED**; `sarala_yoga`, `vimala_yoga` ruled out | unknown |

**A13 is the significant one.** It is verifiably true, it was typed, it was kept
in Run A, it is absent from Run B, and `ch24_s103` appears nowhere in Run B's
`silent_on`. It is also **the only non-flattering claim either run produced**
("troubles from enemies and diseases… gains coming with service conditions and
conflicts"). The missing counterweight recorded at SESSION_LOG S136 §12 item 6
was in hand and was dropped silently.

## 3. The larger finding — precondition under-coverage

Four of Run B's eight shipped claims assert something the fact block refutes.
In each case the declared precondition is SATISFIED and does not cover the
assertion.

**B2 — `ch39_s008`, `ch39_s010`.** Statement: *"the 10th lord in the 4th and
**aspecting the ascendant** … the Sun–Mercury pair **aspects the ascendant** via
Yogada GL"*. Fact: `aspects_by_planet.Mercury = [10]`, `.Sun = [10]`. Neither
aspects house 1. Declared: `aspects_house(Mercury, house=10)` → SATISFIED.
The predicate names house 10; the sentence says ascendant.
**This is Phase 0's own claim-9 confident-wrong, verbatim, now wearing a green
badge** (ANSWER_VERIFICATION_ARCHITECTURE §4).

**B5 — `ch24_s106`.** Statement: *"With the **11th lord in the 10th** … honoured
by authority"*. Fact: `lord_house_map["11"] = 6`. Declared:
`house_lord_is(11, Venus)` → SATISFIED. The predicate tests **who** lords the
11th, never **where** it sits. Run A typed the same segment as
`lord_in_house(11, 10)`, got CONTRADICTED, and **correctly dropped it**.
Run B re-typed it weaker and shipped it. A claim the system correctly rejected
yesterday ships today with a verified badge.

**B8 — `ch39_s008`.** Statement: *"the 10th from the ascendant **occupied by its
lord or benefics**"*. Fact: house 10 is empty; Mercury is in 4. Declared:
`planet_in_house(Mercury, 4)` → SATISFIED, and tests nothing in the statement.

**B4 — `ch41_s015`, `ch39_s012`.** Parenthetical: *"Jupiter and Mars **mutually
aspect**"*. Fact: Mars aspects [5, 8, 9] (Jupiter is in 5, so Mars→Jupiter
holds); Jupiter aspects [1, 9, 11]; Mars is in house 2 — `aspected_by.Jupiter =
["Ketu", "Mars"]`, one-way. Not mutual. Declared: `yoga_fired(kendra_trikona_1_5)`
+ `yoga_fired(kendra_trikona_4_5)`, both genuinely FIRED — so the false
parenthetical rides in unchallenged.

### The defect class

`ANSWER_VERIFICATION_ARCHITECTURE §7.1` names *"a fabricated precondition that
happens to be SATISFIED"*. This is the neighbouring and far more frequent class:
**a true precondition that is not the statement's condition.**

Nothing binds the declared precondition to the sentence it is supposed to
license. The S137 prompt rule *"judge expressibility against the VOCABULARY,
never the facts"* removed `unfittable` — and with it the honest UNEVALUABLE
signal — without supplying anything that checks the precondition actually covers
the claim.

Net, on the same question: Run A shipped 3 false claims and dropped 3;
Run B ships 4 false claims and drops 0.

## 4. Consequences

1. **The recall caution is partly confirmed** (A13 lost, verifiably true,
   undeclared) but is not the main event.
2. **Phase 3 must be blocked.** Retiring `_CONDITION_RE` and the advisory planet
   reader removes the only remaining machinery that reads a claim's own prose —
   which is exactly what is now going unchecked. Under-coverage is invisible to
   a predicate evaluator by construction.
3. **Phase 2's WHAT DOESN'T APPLY gains value**, not loses it: 20 ruled_out
   verdicts computed (all five Pancha Mahapurusha, gajakesari, sarala, vimala,
   mangal_dosha, kalsarpa, six kendra-trikona pairs) and none reach the user.
4. **`silent_on` is confirmed unreliable as the recall instrument.** Run A lists
   `ch24_s008`, `ch24_s033`, `ch24_s106` in `silent_on` *while simultaneously
   emitting all three as claims*. It records intent, not behaviour.
5. The S137 metrics table stands as measured and its *interpretation* needs the
   amendment: `typed_coverage 1.00` and `18/18 SATISFIED` measure predicate
   evaluability, not claim truth.

## 5. Proposed direction (design only — not implemented)

**The missing invariant:** every chart-fact token in a claim's statement must be
covered by one of its declared preconditions.

This is structurally the mechanism S131 already built — `composer._verify`'s
ENFORCING no-new-chart-facts check: closed vocabulary, set containment, no prose
parsing, failing block degrades rather than drops. There it compares a rewrite's
chart tokens against the claim it rests on. Here it compares the *statement's*
chart tokens against the *preconditions'* declared tokens. Same machinery, one
layer up. No new mechanism, no regex judge, no threshold — set containment, with
the uncovered-token rate as the health metric, the same shape as `unfittable`'s.

**Self-flagged objection (REVIEW before PROCEED).** Extracting chart tokens from
a statement *is* prose parsing, the thing S137 abolished. The defence is that it
is a **coverage counter, not a judge**: its errors point toward hedging, which is
the safe direction S125 permits for a permissive matcher. It must therefore ship
**advisory-first with no drop authority** and be promoted on a measured rate —
exactly the disposition the S129b planet reader was given — never switched on
enforcing in one step.
