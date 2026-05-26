# Project Setup Checklist

Use this checklist when starting a new AI/RAG project with Claude Code.
Completing this in Session 0 prevents the most common early-project failures.

---

## Repository

- [ ] `git init` and initial commit done
- [ ] `.gitignore` created — verify these are excluded before first commit:
  ```
  .env
  *.env
  data/chroma_db/
  data/extracted_images/
  data/sessions/
  data/*.json        # generated pipeline files — not source files
  __pycache__/
  *.pyc
  .DS_Store
  ```
- [ ] No large binary files committed (PDFs, images, model weights)
- [ ] Sensitive files (API keys, credentials) confirmed not tracked:
  `git ls-files | grep -E "\.env|key|secret|credential"`

---

## Context Files

- [ ] `CLAUDE.md` created from template — all `[PLACEHOLDERS]` replaced
- [ ] `.cursorrules` created from template — all `[PLACEHOLDERS]` replaced
- [ ] `.claude/` directory created with all 4 agent files:
  - `architect.md`
  - `business.md`
  - `critic.md`
  - `qa.md`
- [ ] Session 0 logged in CLAUDE.md with today's date
- [ ] Schema section in CLAUDE.md is locked and matches actual output schema

**Verify Claude Code loads the files correctly:**
Open a new conversation and ask: "What is the output schema for this project?"
If it can answer from CLAUDE.md, the context is loading.

---

## Environment

- [ ] `.env` file created (not committed) with all required keys:
  ```
  OPENAI_API_KEY=sk-...
  # Add other keys as needed
  ```
- [ ] `python-dotenv` in dependencies — every module that calls an API loads it:
  ```python
  from dotenv import load_dotenv
  load_dotenv(Path(__file__).parent.parent / ".env")
  ```
- [ ] API key validated at startup — not at first use:
  ```python
  if not os.getenv("OPENAI_API_KEY"):
      raise EnvironmentError("OPENAI_API_KEY not set. Add it to .env")
  ```
- [ ] Python version pinned in `.python-version` or `pyproject.toml`

---

## Dependencies

- [ ] `requirements.txt` or `pyproject.toml` created
- [ ] All dependencies installed and import-verified:
  ```bash
  python -c "import chromadb, openai, langdetect, dotenv; print('OK')"
  ```
- [ ] Platform-specific binary dependencies documented in CLAUDE.md:
  - Tesseract path (Windows: `C:\Program Files\Tesseract-OCR\tesseract.exe`)
  - Poppler path (Windows: `C:\Program Files\poppler-X.X.X\Library\bin`)
  - Any CUDA/GPU paths for local models

---

## Data Directory Structure

- [ ] Create all data directories before running any pipeline stage:
  ```
  data/
  ├── sources/           ← input files (PDFs, etc.)
  ├── extracted_images/  ← diagram images from processor
  ├── sessions/          ← per-session JSON files
  └── chroma_db/         ← vector store (auto-created by ChromaDB)
  ```
- [ ] Source files in `data/sources/` (or `data/pdfs/`) — verify with:
  ```python
  from pathlib import Path
  print(list(Path("data/pdfs").glob("*.pdf")))
  ```
- [ ] Source file registry in CLAUDE.md matches actual files on disk

---

## Schema Lock

The output schema must be locked before any pipeline component is written.
Changes after components are written require updating all components atomically.

- [ ] Define the primary data schema in CLAUDE.md under "Output Schema"
- [ ] Mark it "locked — do not alter"
- [ ] Include:
  - All field names and types
  - Which component sets each field
  - Valid values for enum fields (e.g., `language: "eng|hin|mixed"`)
  - Which fields are nullable
- [ ] Chunk ID convention documented:
  - Page-level ID: `{source_name}_p{page_num}`
  - Sub-chunk ID: `{source_name}_p{page_num}_c{index}`
  - Diagram (no-split) ID: `{source_name}_p{page_num}_c0`

---

## Pipeline Planning

Before writing any code, map the full pipeline in CLAUDE.md:

- [ ] Module Dependency Order section filled in with actual file names
- [ ] File handoff documented: which file each stage reads and writes
- [ ] One-time vs recurring stages identified:
  - One-time ingestion (OCR, diagram extraction, translation, embedding)
  - Recurring per-query (embedding the query, LLM call)
- [ ] Total estimated one-time ingestion cost calculated
- [ ] Estimated per-query cost calculated and confirmed < budget threshold

---

## Session 0 Completion Criteria

Session 0 is complete when:

- [ ] All items above are checked
- [ ] `CLAUDE.md` and `.cursorrules` are committed
- [ ] `.claude/` agent files are committed
- [ ] `.gitignore` is committed and verified (run `git status` — no `.env` shown)
- [ ] Python environment is working (imports succeed)
- [ ] Source data files are in place and accessible
- [ ] Schema is locked and documented
- [ ] Session 0 log entry is updated in CLAUDE.md with today's date

**Session 0 log entry format:**
```markdown
- Session 0 (YYYY-MM-DD): Repo created, folder structure, CLAUDE.md, .cursorrules,
  .claude/ agents, schema locked, [N] source files verified — COMPLETE
```

---

## Common Session 0 Mistakes

**Not verifying .gitignore before first commit**
If `.env` or `data/*.json` are tracked once, removing them from git history is
painful. Check `git status` carefully before the first commit.

**Placeholder left in CLAUDE.md**
If `[STACK_TABLE]` or `[OUTPUT_SCHEMA]` is still in CLAUDE.md, Claude Code will
not have the context it needs. Search for `[` in both files before committing.

**Schema defined too loosely**
"The chunk has text and metadata" is not a locked schema. Lock means: exact field
names, exact types, exact valid values, and which component sets each field.
This decision is hardest to change later.

**Skipping the 4-agent review for Session 0 setup**
Session 0 components (folder structure, schema, pipeline design) are the most
expensive to change later. Even a brief architect + critic review of the schema
before locking it catches issues that would require refactoring multiple files
in later sessions.

**Storing API keys in code instead of .env**
Even in private repos. Keys in code end up in commit history, logs, and
shared conversations. Use `.env` from the first line of code that needs a key.
