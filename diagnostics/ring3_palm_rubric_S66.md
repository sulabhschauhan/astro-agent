# Ring 3 — T4 Human-Rubric Ratification Artifact (Session 66)

**STATUS: TEMPLATE — not yet scored. Becomes the Ring 3 FROZEN BASELINE
once scored and committed (keep-forever per S62 retention convention).**
The T4 layer is NOT ratified-live until this artifact carries a verdict.

Rubric lineage: S23-hardened (path_c_validation_20260621_173724.md) —
citation-CONTENT accuracy, voice, no silent clause-dropping. Adapted to
V1's only live-LLM T4 surface: palm reading (AstroSage is terminal-bare;
no LLM consumes pdf_context in V1 — verified S66 against live wiring).

Re-open condition: any post-ratification live T4 failure reopens Ring 3
at N=5 runs. Parashara dissent (no kundali x palm cross-verification in
V1) logged S65; V1.1 gate unchanged.

## Run plan (3 generation runs, live OpenAI + vision, Streamlit app)
Fresh-upload lock: palm images + AstroSage PDF uploaded at app-session
start; nothing persisted. Vision descriptions confirmed ONCE per hand
(human checkpoint), reused across runs.
- **Run A** — both hands, no hand_detail (baseline)
- **Run B** — identical inputs, regenerate (variance probe)
- **Run C** — + hand_detail (stress probe: hand_detail is excluded from
  the RAG query by design — honest output DECLINES unsupported
  elements; silent omission = the S23 Q4 failure mode)

## P7 — Vision fidelity (gates everything; score FIRST)
Confirmed describe_palm_image output vs. your actual palms. Gross
misdescription -> STOP, do not score P1-P4 (they'd be scoring a reading
of hands that aren't yours). Record verdict per hand:
- Left:  [ OK / MINOR ERRORS (list) / GROSS ERROR — STOP ]
- Right: [ OK / MINOR ERRORS (list) / GROSS ERROR — STOP ]

## Per-run scoring (repeat block for Runs A, B, C)

### Run _: reading_text (paste verbatim)
> [paste]

### Run _: sources expander (book / page / score rows, verbatim)
> [paste]

### Run _: claim ledger (P1 input)
Every substantive palmistry claim in the reading, one row each:
| # | Claim (short quote) | Basis: D=confirmed description / C=Cheiro chunk / U=untraceable | Chunk verified? |
To verify chunk CONTENT (not just book/page existence), dump retrieved
chunk text:
  python -c "from ingestion.query_engine import search; \
  [print(c['book_name'], c['page_ref'], '\n', c['text'][:600], '\n---') \
  for c in search('<paste the run's RAG query: concatenated confirmed \
  hand descriptions>', n_results=6, book_name='cheiroslanguageo00chei_1')]"

### Run _: rubric
| Signal | Score | Justification |
|---|---|---|
| P1 Grounding / citation-CONTENT: zero U rows in ledger; every C row's chunk actually says what's attributed (S23 Q3 rule: plausible-but-wrong attribution = FAIL) | Y/N | |
| P2 No contradiction of confirmed descriptions | Y/N | |
| P3 Voice: Cheiro-tradition diction; FAIL on self-help register ("stability", "fulfillment", "favorable outcomes", generic positivity — S23 R3 blacklist) | Y/N | |
| P4 No silent clause-dropping: every major feature in confirmed descriptions (+ hand_detail in Run C) addressed OR explicitly declined; silent omission = FAIL (S23 Q4 rule) | Y/N | |

### Run _: Ring 1 spot-check (already automated; confirm no false-negative)
- [ ] DISCLAIMER present  - [ ] no jargon-blacklist terms
- [ ] no unsupported dates  - [ ] <=700 words

## AstroSage display checklist (deterministic, once, real PDF)
- [ ] Expander renders sections verbatim (st.text, formatting intact)
- [ ] Pratyantar ABSENT from display
- [ ] Lal Kitab ABSENT from display
- [ ] Splitter sectioned the real PDF correctly (d88d026 name-anchored
      regex, first real-data exercise) — note any mis-split
- [ ] Structural negative: no Pratyantar/Lal Kitab content in ANY palm
      reading output (should be impossible — no LLM sees pdf_context)

## Verdict
Ratification bar: Runs A, B, C ALL score 4/4 on P1-P4, P7 OK/minor,
AstroSage checklist clean. Literal scoring only — no
citation-adjusted generosity (S23 lesson: the hardened reading was
the honest one).
- [ ] RATIFIED-LIVE  /  [ ] NOT RATIFIED (failures itemized below)
Failures + fix-forward design notes:
> [fill]
