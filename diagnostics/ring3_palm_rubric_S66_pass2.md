# Ring 3 — T4 Human-Rubric Ratification Artifact (Session 66) — Pass 2

**STATUS: PASS 2 — TEMPLATE, not yet scored. Supersedes pass 1's verdict
when scored. Preconditions: F1 (2d4a42f), F2+F3 (d2d923a), F4 (f81809d)
all live.**
The T4 layer is NOT ratified-live until this artifact carries a verdict.

Rubric lineage: S23-hardened (path_c_validation_20260621_173724.md) —
citation-CONTENT accuracy, voice, no silent clause-dropping. Adapted to
V1's only live-LLM T4 surface: palm reading (AstroSage is terminal-bare;
no LLM consumes pdf_context in V1 — verified S66 against live wiring).

Re-open condition: any post-ratification live T4 failure reopens Ring 3
at N=5 runs (unchanged from pass 1). Parashara dissent (no kundali x
palm cross-verification in V1) logged S65; V1.1 gate unchanged.

## Run plan (3 generation runs, live OpenAI + vision, Streamlit app)
Fresh-upload lock: palm images + AstroSage PDF uploaded at app-session
start; nothing persisted. Vision descriptions confirmed ONCE per hand
(human checkpoint), reused across runs. Unchanged from pass 1.
- **Run A** — both hands, no hand_detail (baseline)
- **Run B** — identical inputs, regenerate (variance probe)
- **Run C** — + hand_detail (stress probe: hand_detail is excluded from
  the RAG query by design — honest output DECLINES unsupported
  elements; silent omission = the S23 Q4 failure mode). **Run C is now
  fully scorable via the F1 checkpoint** (pass 1's Run C was UNSCORABLE
  on P1/P4 because hand_detail entered generation with no display/
  confirmation; F1 closed that gap by giving hand_detail the same
  review/confirm/discard checkpoint as the palms).

## Confirmed descriptions (reused across all 3 runs) — TO BE CAPTURED

Post-F4, `describe_palm_image` and `describe_hand_detail_image` emit
structured labeled fields (HAND SHAPE / FINGERS / THUMB / LIFE LINE /
HEAD LINE / HEART LINE / FATE LINE / OTHER LINES / MOUNTS / MARKS),
not free-text prose — see `diagnostics/latest_run.md`'s Task 9 probe
for the field format. Three descriptions now require checkpoint capture
(LEFT, RIGHT, HAND_DETAIL — all checkpointed since F1), verbatim as
confirmed by the human in the live app session:

**LEFT** (confirmed, human checkpoint): *[paste verbatim structured
fields from the live run]*

**RIGHT** (confirmed, human checkpoint): *[paste verbatim structured
fields from the live run]*

**HAND_DETAIL** (confirmed, human checkpoint): *[paste verbatim
structured fields from the live run — only present from Run C onward]*

## P7 — Vision fidelity (gates everything; scored FIRST)
Scored via user-delegated draft check by design chat against the
actual palm images (and, from Run C onward, the hand-detail
photograph); user ratification of this artifact constitutes P7
sign-off.

Covers **THREE** descriptions now (left, right, hand_detail — all
checkpointed since F1, vs. pass 1's two). Descriptions are structured
labeled fields post-F4: P7 = verify each field against the actual hand.
**'not clearly visible' entries are honest answers, not errors** — do
not score a field FAIL merely because it declines to guess; score FAIL
only if a field asserts something the image does not support.

- Left:        *[OK / minor / FAIL — TBD]*
- Right:       *[OK / minor / FAIL — TBD]*
- Hand_detail: *[OK / minor / FAIL — TBD, Run C onward only]*

---

## Run A: reading_text (verbatim, from `.claude/read_prompt.md` as committed)
*[TO BE CAPTURED — paste verbatim from the live Streamlit run]*

## Run A: sources expander (verbatim)
*[TO BE CAPTURED — paste verbatim classical-sources list as rendered]*

## Run A: claim ledger (P1 input)
Chunk evidence: capture a fresh chunk-dump artifact against the
ACTUAL Run A query (do not reuse `diagnostics/ring3_chunks_S66.md` —
that dump is pass-1 baseline data, pre-F4 description lengths).
**Pass 2 is measure-first: sources captured from the app in this run
are the observed baseline; verify the chunk dump against THOSE, not
against a pre-stated expected set** (pass 1's expected retrieval
scores, e.g. the p.163/0.6801 etc. table, are NOT carried forward or
assumed to still apply).

P1 rule sharpened for pass 2: post-F4, descriptions are observational
(no interpretive/trait language at the source). **Any interpretive or
trait claim appearing in the generated reading must be a
content-verified C row** (chunk actually supports the claim, not just
present in the sources list) — an interpretive claim with no supporting
chunk is a **U row -> FAIL**, not a D row. **D rows can only cover
observational restatements** of the confirmed structured fields (e.g.
"the life line curves around the base of the thumb" is a valid D row;
"a strong connection to family" attributed only to the description is
NOT a valid D row post-F4, since the description itself must not
contain that interpretive claim — if it appears in the reading, trace
it to a chunk or fail it).

| # | Claim (short quote) | Basis: D=confirmed description (observational only) / C=Cheiro chunk (content-verified) / U=untraceable | Chunk verified? |
|---|---|---|---|
| *[TBD — populate from live Run A reading_text against the confirmed structured descriptions]* | | | |

## Run A: rubric
| Signal | Score | Justification |
|---|---|---|
| P1 Grounding / citation-CONTENT: zero U rows in ledger; every C row's chunk actually says what's attributed; every interpretive claim is a content-verified C row (sharpened, see above) | *[TBD]* | |
| P2 No contradiction of confirmed descriptions | *[TBD]* | |
| P3 Voice: Cheiro-tradition diction; FAIL on self-help register ("stability", "fulfillment", "favorable outcomes", generic positivity — S23 R3 blacklist) | *[TBD]* | |
| P4 No silent clause-dropping: coverage now per labeled FIELD (10 per hand) — each field addressed or explicitly declined; 'not clearly visible' fields may be skipped silently without failing P4 | *[TBD]* | |

## Run A: Ring 1 spot-check (already automated; confirm no false-negative)
- [ ] DISCLAIMER present  - [ ] no jargon-blacklist terms
- [ ] no unsupported dates  - [ ] <=700 words

---

## Run B: reading_text (verbatim, from `.claude/read_prompt.md` as committed)
*[TO BE CAPTURED — paste verbatim from the live Streamlit run]*

## Run B: sources expander (verbatim)
*[TO BE CAPTURED — paste verbatim classical-sources list as rendered]*

## Run B: claim ledger (P1 input)
Same measure-first posture as Run A: verify the chunk dump against
THIS run's observed sources, no pre-stated expected set carried
forward from pass 1.

| # | Claim (short quote) | Basis: D=confirmed description (observational only) / C=Cheiro chunk (content-verified) / U=untraceable | Chunk verified? |
|---|---|---|---|
| *[TBD — populate from live Run B reading_text]* | | | |

## Run B: rubric
| Signal | Score | Justification |
|---|---|---|
| P1 Grounding / citation-CONTENT | *[TBD]* | |
| P2 No contradiction of confirmed descriptions | *[TBD]* | |
| P3 Voice | *[TBD]* | |
| P4 No silent clause-dropping (per-field coverage, see Run A) | *[TBD]* | |

## Run B: Ring 1 spot-check (already automated; confirm no false-negative)
- [ ] DISCLAIMER present  - [ ] no jargon-blacklist terms
- [ ] no unsupported dates  - [ ] <=700 words

---

## Run C: reading_text (verbatim, from `.claude/read_prompt.md` as committed)
*[TO BE CAPTURED — paste verbatim from the live Streamlit run, + hand_detail confirmed and in play]*

## Run C: sources expander (verbatim)
*[TO BE CAPTURED — paste verbatim classical-sources list as rendered]*

## Run C: claim ledger (P1 input)
Same D set as Runs A/B, plus any claims introduced by hand_detail.
**Unlike pass 1, hand_detail is now checkpointed (F1)** — a claim
traceable to hand_detail is a valid D row IF the hand_detail
description was displayed and confirmed before this run, exactly like
palm_left/palm_right. Run C should therefore be fully scorable on P1
and P4 this pass (pass 1's UNSCORABLE verdict on both was solely the
missing-checkpoint gap that F1 closed).

| # | Claim (short quote) | Basis: D=confirmed description (observational only, incl. hand_detail) / C=Cheiro chunk (content-verified) / U=untraceable | Chunk verified? |
|---|---|---|---|
| *[TBD — populate from live Run C reading_text against LEFT/RIGHT/HAND_DETAIL confirmed descriptions]* | | | |

## Run C: rubric
| Signal | Score | Justification |
|---|---|---|
| P1 Grounding / citation-CONTENT | *[TBD — should be scorable, not UNSCORABLE, per F1]* | |
| P2 No contradiction of confirmed descriptions | *[TBD]* | |
| P3 Voice | *[TBD]* | |
| P4 No silent clause-dropping: every labeled field across LEFT/RIGHT/HAND_DETAIL addressed OR explicitly declined; 'not clearly visible' fields may be skipped silently | *[TBD — should be scorable, not UNSCORABLE, per F1]* | |

## Run C: Ring 1 spot-check (already automated; confirm no false-negative)
- [ ] DISCLAIMER present  - [ ] no jargon-blacklist terms
- [ ] no unsupported dates  - [ ] <=700 words

---

## AstroSage display checklist (deterministic, once, real PDF)
- [ ] Expander renders sections verbatim (st.text, formatting intact)
- [ ] Pratyantar ABSENT from display
- [ ] Lal Kitab ABSENT from display
- [ ] Splitter sectioned the real PDF correctly (no mis-split observed)
- [ ] Structural negative: no Pratyantar/Lal Kitab content in ANY palm
      reading output across Runs A/B/C

Pass-1 flagged real extraction noise (linearized two-column tables,
page footers, promo lines, doubled-character bold artifacts) as a
content-quality finding routed to S67, not blocking pass-1's verdict.
Re-check whether that S67 work has landed before scoring this
checklist; if unresolved, carry the same non-blocking note forward.

## Verdict
Ratification bar (unchanged from pass 1): Runs A, B, C ALL score 4/4
on P1-P4, P7 OK/minor, AstroSage checklist clean. Literal scoring
only — no citation-adjusted generosity (S23 lesson: the hardened
reading was the honest one).
- [ ] NOT RATIFIED (failures itemized below)  /  [ ] RATIFIED-LIVE

**Failures:** *[TBD — populate on scoring]*

**Findings (not independently failing, but material to fix-forward
scope):** *[TBD — populate on scoring; check specifically whether
pass-1's RAG-inert-readings finding and RAG query truncation finding
still reproduce post-F4's structured/shorter-form descriptions]*

**Re-open condition** (unchanged from pass 1): any post-ratification
live T4 failure reopens Ring 3 at N=5 runs.
