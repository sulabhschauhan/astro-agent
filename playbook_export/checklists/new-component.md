# New Component Checklist

Use this checklist every time a new file is being added to the project.
Do not start writing code until all pre-write steps are complete.

---

## Pre-Write: 4-Agent Review

Run all four agents before writing a single line. Present findings as a numbered
list of design decisions. Get explicit confirmation before proceeding.

```
@.claude/architect.md  — interface contracts, failure modes, dependencies
@.claude/business.md   — user value, cost, shipping impact
@.claude/critic.md     — what will break, unvalidated assumptions
@.claude/qa.md         — minimum tests, idempotency, edge cases
```

**Gate:** Do not start writing until at least 3 design decisions are confirmed.
At least one Critic finding must be explicitly addressed in the design.

---

## Pre-Write: Design Decisions to Confirm

Confirm these before writing any component that fits the categories:

**For any component with external API calls:**
- [ ] Rate limit retry logic designed (retries, base delay, backoff factor)
- [ ] What happens when API is down for the full retry window?
- [ ] Cost per call estimated and acceptable

**For any component with file I/O:**
- [ ] Input file path constant defined, verified to exist (or clear error if not)
- [ ] Output file path constant defined
- [ ] Atomic write strategy decided (`.tmp` → `os.replace`)
- [ ] Encoding explicitly `utf-8` on all `open()` calls

**For any ingestion component (processes expensive input):**
- [ ] Idempotency strategy defined (what field/ID signals "already processed"?)
- [ ] Incremental save strategy defined (save every N items)
- [ ] Resume-from-partial strategy tested

**For any schema-touching component:**
- [ ] Locked schema reviewed — confirm no new required fields are being added
- [ ] If schema addition is necessary: all downstream readers updated atomically
- [ ] New fields are additive only (no removals, no renames)

**For any filtering/classification component:**
- [ ] Filter validated on the FULL dataset before committing to threshold
- [ ] Source filter applied before content filter for mixed-source corpora
- [ ] Edge case: does this filter trigger on data it was not intended for?

---

## Writing Phase

### Structural requirements (every component)

- [ ] Single responsibility — does exactly one thing
- [ ] Public interface is minimal: one or two public functions, rest private (`_`)
- [ ] All constants at module top with inline comment explaining the value
- [ ] `try/except` on every external call with meaningful error message
- [ ] `logger` used throughout — not `print()` in production code
- [ ] `load_dotenv()` at top if component uses OpenAI or any external API key
- [ ] `encoding="utf-8"` on every file open

### Threshold values (if any)

Every numeric threshold in the component must have:
- [ ] Explicit justification in a comment (empirical or reasoned)
- [ ] A scope guard that prevents noise from triggering it
  (e.g., `word_count >= MIN_WORDS` before applying a density threshold)
- [ ] A tuning note: "increase if X, decrease if Y"

### Idempotency (if component touches expensive operations)

- [ ] Skip logic: check before calling API / embedding / translating
- [ ] The skip condition is based on a field that only exists after processing
  (`"original_hindi" in chunk`, `chunk_id in existing_ids`, etc.)
- [ ] Incremental save every N operations if the run takes > 1 minute

---

## Post-Write: QA Checklist

Run the following tests before marking the component complete.
Start with the hardest case, not the easiest.

```
[ ] Happy path test passed with REAL data (not synthetic)
[ ] Empty input handled gracefully (no crash, clear message)
[ ] Missing input file raises clear error with remediation instructions
[ ] Idempotency verified: run twice = same result, no duplicate API calls
[ ] Hardest case tested (most complex input, highest risk of misclassification)
[ ] Output schema matches locked contract (spot-check 5 output items)
[ ] Logs are meaningful: can you debug a failure from logs alone?
[ ] All constants validated against actual data (no stale values)
```

**For components with external API calls, additionally:**
```
[ ] Rate limit retry tested (mock or real)
[ ] Behaviour when API returns empty response tested
[ ] Cost for a sample run logged and matches estimate
```

**For retrieval components, additionally:**
```
[ ] n_results clamped to min(n_results, collection.count())
[ ] Empty collection raises explicit RuntimeError (not silent empty results)
[ ] Similarity scores are in [0, 1] range (not raw distances)
[ ] Metadata filters tested with at least 2 combinations
```

**For agent/LLM components, additionally:**
```
[ ] Persona/tone consistent across 3+ different question types
[ ] Low-confidence path tested (weak retrieval scores)
[ ] Session history: bare Q&A stored, not full retrieval context
[ ] Introduction suppressed when session has prior history
[ ] Response time measured — document the baseline
```

---

## Post-Write: Session Log Update

Update CLAUDE.md session log immediately after QA passes:

```markdown
- Session N (YYYY-MM-DD): component_name.py complete + validated on [hardest test case];
  [key design decision locked]; [N/N QA tests passed] — COMPLETE
```

Include:
- The hardest test case used for validation (not the easiest)
- Any design decision that was locked during this session
- QA pass rate (if applicable)
- Any known limitations or deferred improvements

---

## Anti-Patterns to Avoid

These were observed causing problems in this project:

- **Accepting AI diff without identifying at least one issue** — summarising
  is not reviewing
- **Testing on the easiest example first** — builds false confidence
- **Running full dataset before sample validation** — wastes compute and money
- **Changing a function signature without updating all call sites atomically** —
  causes TypeError crashes discovered at runtime, not at edit time
- **Content filter without source filter** — misfires on mixed-content sources
- **Storing retrieval context in session history** — token bloat compounds per turn
- **Non-atomic file writes on expensive pipeline output** — crash = corrupted data
- **Missing `encoding="utf-8"`** — silent failures on Windows with multilingual text
- **No `load_dotenv()` before first API call** — unclear auth errors
