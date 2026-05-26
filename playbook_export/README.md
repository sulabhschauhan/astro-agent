# AI Project Playbook

A reusable setup for production AI/RAG projects built with Claude Code.
Extracted from a working production project after 4 validated sessions of development.

---

## What This Is

This playbook packages the collaboration system that keeps AI-assisted development
from shipping untested code. It contains:

- **4-agent review system** — four specialist agents that review every new component
  from different angles before a single line is written
- **6 working style standards** — non-negotiable principles that force human checkpoints
  between AI output and production
- **CLAUDE.md + .cursorrules templates** — production-grade context files with locked
  schema tracking, session logging, and pipeline documentation
- **Session log pattern** — tracks what is complete, what is not started, and why
  key decisions were made

The system was built because AI moves fast and skips validation steps. These files
slow it down at exactly the right moments.

---

## File Inventory

| File | Purpose |
|---|---|
| `templates/CLAUDE.md.template` | Main Claude Code context — stack, pipeline, schemas, session log |
| `templates/.cursorrules.template` | Cursor IDE context — mirrors CLAUDE.md, adds working style rules |
| `templates/.claude/architect.md` | Reviews interface contracts, data flow, failure modes |
| `templates/.claude/business.md` | Reviews user value, cost per query, shipping speed |
| `templates/.claude/critic.md` | Challenges assumptions, flags what will break in production |
| `templates/.claude/qa.md` | Defines minimum tests, acceptance criteria, known edge cases |

---

## Quick Start

### 1. Copy templates into your new project

```bash
cp templates/CLAUDE.md.template  /path/to/project/CLAUDE.md
cp templates/.cursorrules.template  /path/to/project/.cursorrules
cp -r templates/.claude/  /path/to/project/.claude/
```

### 2. Replace all placeholders

Search for `[` in both template files. Required replacements:

| Placeholder | Replace with |
|---|---|
| `[PROJECT_NAME]` | Short slug, e.g. `my-rag-agent` |
| `[DESCRIPTION]` | One-sentence project summary |
| `[STACK_TABLE]` | Your tech stack in the provided table format |
| `[FOLDER_STRUCTURE]` | Your module layout (`module/ → file.py, file.py`) |
| `[PIPELINE_STEPS]` | Ordered component list with `→` arrows |
| `[OUTPUT_SCHEMA]` | Your primary data contract (lock it before writing any component) |
| `[VECTOR_DB_CONFIG]` | If using a vector store: collection name, dimension, persist path |
| `[PYTHON_VERSION]` | e.g. `3.11` |
| `[PLATFORM_DEPENDENCIES]` | OS-specific binary paths (Tesseract, Poppler, CUDA, etc.) |
| `[DATA_REGISTRY]` | Your data sources with status (ready / needs processing) |
| `[DOMAIN_AGENT_BEHAVIOR]` | Domain-specific LLM rules (photo handling, calculation guardrails, etc.) |
| `[INGESTION_COMMANDS]` | Step-by-step shell commands for pipeline stages |
| `[SESSION_LOG]` | Delete example rows; add your own Session 0 entry |
| `[COMPONENT_DESIGN_SECTION]` | Delete placeholder; add real sections as you plan each component |

### 3. Customize the QA agent for your stack

In `.claude/qa.md`, replace the "Known Edge Cases" section with edge cases
relevant to your project. Add to it as you discover new failure modes.

### 4. Start Session 0

Log it in CLAUDE.md the moment the repo is created:
```
- Session 0 (YYYY-MM-DD): Repo created, folder structure, CLAUDE.md, .cursorrules — COMPLETE
```

---

## The 4-Agent Review System

Before writing any new file or component, load all four agents and run through
their questions. Reconcile all findings before writing code.

### When it is mandatory
- Any new file
- Schema changes
- Threshold values
- Pipeline changes
- API integrations

### The four agents

**Architect** (`.claude/architect.md`)
Asks: Are interfaces explicit? Is data flow one-directional? What is the failure
mode at each external call? Can this component be swapped without changing
dependent files?

**Business** (`.claude/business.md`)
Asks: What does the user actually experience? Is cost per query acceptable?
Is this the 20% of work that delivers 80% of value? Does this delay shipping?

**Critic** (`.claude/critic.md`)
Asks: What will break in production? What assumption has not been validated?
Has the hardest case been tested? Is this threshold empirically justified?

**QA** (`.claude/qa.md`)
Asks: What are the minimum tests before this is accepted? What does failure
look like — silent or loud? Has idempotency been verified on every expensive
operation?

### How to run the review in Claude Code

```
Before writing [ComponentName], run the 4-agent review:
@.claude/architect.md @.claude/business.md @.claude/critic.md @.claude/qa.md
```

Present findings as a numbered list of decisions. User confirms before any
code is written.

---

## The 6 Working Style Standards

These are non-negotiable. They belong in every project's CLAUDE.md verbatim.

| # | Standard | Why it matters |
|---|---|---|
| 1 | **REVIEW before PROCEED** | Summarizing a diff is not the same as validating it |
| 2 | **SAMPLE before SCALE** | Never run full dataset without a cheap sanity check first |
| 3 | **HARDEST CASE first** | Easy tests build false confidence |
| 4 | **OVERRIDE auto-suggestions** | Auto-suggestions skip validation by default |
| 5 | **THRESHOLD DISCIPLINE** | Every numeric threshold needs justification + scope guard |
| 6 | **AI reviewing AI** | Flag every chain of AI decisions without a human checkpoint |

---

## Key Production Lessons Learned

These were discovered building the source project. Most are universal.

### Data contracts
- **Lock the schema before writing any component that touches it.** Schema drift
  between pipeline stages is the hardest class of bug to debug.
- **Sub-chunks need a suffix convention** (`_c{index}`) so IDs are unique after
  splitting. Design chunk IDs for the post-split state, not the pre-split state.

### Idempotency
- **Every expensive operation needs an idempotency guard.** Check: does re-running
  this waste money or corrupt state? OpenAI embeddings, translations, and LLM
  calls all need skip logic on re-run.
- **Atomic file writes** (`.tmp` then `os.replace`) prevent partial writes on crash.
  Use them on every file that an expensive pipeline writes.

### Filtering
- **Content-based filters can misfire on mixed-content sources.** A Devanagari
  fraction check flagged 508 English-book pages as Hindi because the English
  book included Sanskrit verses alongside its translation. Always combine content
  filters with source filters.

### LLM context
- **Store bare Q&A in session history, not full retrieval context.** Putting
  retrieval passages in history causes token bloat. Only the current turn needs
  the retrieved chunks; history only needs the question and answer text.
- **Suppress re-introduction when session has prior history.** Check
  `session.get_history()` before passing `introduce=True`.

### Vector DB (ChromaDB)
- **Guard `n_results > collection.count()`.** ChromaDB crashes silently when
  `n_results` exceeds the number of stored documents. Always clamp:
  `min(n_results, collection.count())`.
- **Distance to similarity**: ChromaDB cosine returns distance (0 = identical,
  2 = opposite). Convert to similarity with `score = 1 - distance`.
- **Empty collection raises no error** — it returns empty results. Add an
  explicit `RuntimeError` if `collection.count() == 0`.

### Rate limits
- **Exponential backoff on all OpenAI calls.** Base delay 10s, doubles each
  retry (10 / 20 / 40s), max 3 retries. Apply to embeddings, completions,
  and translation calls separately.

### Response quality
- **Low-confidence threshold needs calibration from real queries**, not intuition.
  Run 20+ test queries and check the score distribution before setting a cutoff.
- **Persona re-introduction is jarring mid-conversation.** Gate `introduce=True`
  on the session having no prior history, not just on a boolean parameter.

---

## Session Log Pattern

Track every session in CLAUDE.md. The format keeps both human and AI oriented
on what is done, what is in-flight, and what design decisions were locked.

```markdown
## Session Log

- Session 0 (YYYY-MM-DD): Repo created, folder structure, CLAUDE.md, .cursorrules — COMPLETE
- Session 1 (YYYY-MM-DD): [component] complete + validated on [test case]; [key fix] — COMPLETE
- Session 2: [component] — NOT STARTED
- Session 3: [component] — NOT STARTED
```

**Rules:**
- Log the date when completing, not when planning
- Include at least one validation result (test count, edge case caught)
- Include any key decisions made that are not obvious from the code
- Mark NOT STARTED until work begins; update inline when done

---

## Coding Standards (defaults — override per project)

- Python [PYTHON_VERSION]
- Surgical edits only — no full file rewrites
- Always `try/except` with meaningful error messages
- Preserve all interfaces and the locked output schema
- No comments explaining what — only why (non-obvious constraints, workarounds)
