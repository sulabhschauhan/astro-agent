# S66 Task 1 — Review-debt settlement: 4b/4d verification + fix-forwards

Self-gated, run in order, STOP-on-red, commit-on-green per step. Only
source file edited: `frontend/app.py`.

## Step 1 — Exhume overwritten S65 4b report

`git show ad5809b:diagnostics/latest_run.md` succeeded on the first try —
commit `ad5809b` contains the S65 4b report ("frontend/app.py — AstroSage
terminal-bare display + Pratyantar/Lal-Kitab withholding (Session 65, 4b)").
No log-walk needed. Archived to
`diagnostics/archive/s65_4b_report_ad5809b.md`.

Commit: `1e0ce5f` — "S66: archive S65 4b diagnostics report (review-debt audit trail)"

## Step 2 — Repo-wide verification greps (full results)

### `grep -rn "pending_question" .`
```
SESSION_LOG.md:161:[Omitted long matching line]
SESSION_LOG.md:2977:   deletion): `pending_question` session key, the "Generate My Reading"
```
Both hits are in `SESSION_LOG.md` (docs, historical record of the S65 4d
removal). Zero live code references. **Matches expectation.**

### `grep -rn "Generate My Reading" .`
```
SESSION_LOG.md:161:[Omitted long matching line]
SESSION_LOG.md:2977:   deletion): `pending_question` session key, the "Generate My Reading"
```
Same two `SESSION_LOG.md` hits (one line contains both search terms).
Zero live code references. **Matches expectation.**

### `grep -rn "introduce" frontend/ agent/`
```
agent\astrologer.py:90:    introduce: bool = False,
agent\astrologer.py:113:        introduce: If True, Parashara introduces himself — suppressed if session
agent\astrologer.py:197:    effective_introduce = introduce and not (session and session.get_history())
agent\astrologer.py:209:        introduce=effective_introduce,
agent\astrologer.py:248:    result = ask(question, introduce=True)
agent\prompt_builder.py:104:    introduce: bool = False,
agent\prompt_builder.py:120:        introduce: If True, Parashara introduces himself.
agent\prompt_builder.py:134:    if introduce:
agent\interpretive\palm_reading.py:14:    language/strict-context rules; no CQ/introduce/history).
agent\interpretive\palm_reading.py:103:- This is a ONE-SHOT reading: do not ask clarifying questions, do not introduce yourself, and do not reference any prior conversation -- there is none.
agent\infra\orchestrator.py:203:    of the three, confirmed by reading (not assumed): none introduces a
agent\calculations\transits\muhurta_scorer.py:38:- No new deferrals introduced here. Vedha-sthana, aspect overrides,
```
Classification:
- `agent/astrologer.py` (5 hits), `agent/prompt_builder.py` (3 hits) —
  **quarantined-module-internal**, expected and fine per task framing
  (ask()'s own `introduce` kwarg machinery; module retained for V1.1
  research only, not frontend-reachable).
- `agent/interpretive/palm_reading.py` (2 hits) — docstring/prompt-text
  use of the plain English word "introduce" describing the one-shot
  palm reading's own no-introduction contract; not a call into the
  quarantined `ask()`/`introduce=` flow. **Fine.**
- `agent/infra/orchestrator.py:203`, `agent/calculations/transits/muhurta_scorer.py:38`
  — unrelated plain-English uses ("introduces", "introduced"), not the
  `introduce` kwarg. **Fine.**
- **Zero hits in `frontend/`** (grep returned no matches for that path).

**Matches expectation** — zero live frontend references; all `agent/`
hits fall into the expected quarantined-internal or unrelated-word
buckets.

### `grep -rn "nudges" frontend/`
```
frontend\app.py:715:            for _nudge in msg.get("nudges", []):
```
Exactly the one known residue, in the history-render loop, as expected
(pre-edit line number; removed in Step 3 below).
**Matches expectation** — sole live reference, and it's the known one.

**Conclusion: no STOP triggered — all greps matched the expected
pattern exactly.**

## Step 3 — Fix-forward A: nudges residue removal

`frontend/app.py`, history-render loop (was lines 711-716): removed

```python
        if msg["role"] == "assistant":
            for _nudge in msg.get("nudges", []):
                st.info(_nudge)
```

leaving only `st.markdown(msg["content"])` inside the `with
st.chat_message(msg["role"]):` block. Nothing else in that loop changed.

## Step 4 — Fix-forward B: name-anchored AstroSage splitter

`frontend/app.py`:
- Import changed: `from agent.astrosage_parser import parse_astrosage_pdf`
  → `from agent.astrosage_parser import parse_astrosage_pdf, _PRIORITY_ORDER`.
- Added module-level `_SECTION_HEADER_RE = re.compile(r"^\[(" +
  "|".join(re.escape(n) for n in _PRIORITY_ORDER) + r")\]$", re.MULTILINE)`
  directly after `_WITHHELD_SECTIONS`.
- `_split_astrosage_sections()` now splits on `_SECTION_HEADER_RE` instead
  of the generic `re.split(r"^\[([^\]]+)\]$", ...)` — only lines matching
  a known `_PRIORITY_ORDER` name are treated as section headers, so a
  spurious bracketed line inside a section's own body (e.g. `[something]`
  appearing in AstroSage's own text) is no longer misparsed as a new
  section boundary. `len(parts) < 3` fail-soft behavior preserved
  unchanged in shape.
- Docstring updated: names now documented as auto-tracking the parser via
  `_PRIORITY_ORDER`; only the join format (`"[Name]\n content"`, `"\n\n"`
  separator) remains a manual coupling.
- Ride-along: fail-soft branch now returns
  `pdf_context.removeprefix("ASTROSAGE PDF DATA:\n")` instead of the raw
  `pdf_context`, stripping the leading parser-prefix line before display
  (plain `removeprefix`, no regex).

Verified: `ast.parse()` on the edited file passes; `_PRIORITY_ORDER` import
resolves live (`['Varshaphal', 'Pratyantar', 'Muntha', 'Sade Sati',
'Favourable Points', 'Transit Today', 'Lal Kitab']`).

## Step 5 — Full suite

```
3166 passed, 3 skipped, 1 warning in 83.59s
```

Expected 3166 passed / 3 skipped — **exact match, zero delta** (frontend/
is outside testpaths as anticipated). Green → committed.

Commit: `d88d026` — "S66: review-debt fix-forwards — nudges residue
removal + name-anchored AstroSage splitter"

## Commit hashes (this task, in order)

1. `1e0ce5f` — S66: archive S65 4b diagnostics report (review-debt audit trail)
2. `d88d026` — S66: review-debt fix-forwards — nudges residue removal + name-anchored AstroSage splitter
