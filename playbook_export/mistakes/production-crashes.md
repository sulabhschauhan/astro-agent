# Production Crashes — Root Causes and Fixes

Every crash recorded during development of this project. Organised by component.
Each entry has: symptom, root cause, fix, and how to prevent recurrence.

---

## Ingestion Pipeline

### CRASH-01: FileNotFoundError on input JSON

**Symptom:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/all_chunks_v2.json'
```

**Root cause:** The constant `ALL_CHUNKS_PATH` in `embedder.py` had a hardcoded
filename (`all_chunks_v2.json`) left over from an earlier naming iteration. The
actual file was `all_chunks.json`. The error message was correct but the constant
was never updated.

**Fix:** Changed `ALL_CHUNKS_PATH = "data/all_chunks_v2.json"` to `"data/all_chunks.json"`.

**Prevention:** Constants that reference file paths should be verified against
the actual filesystem before the first full run. Run a `Path(path).exists()` check
at module load time and raise a clear error immediately, not at the point of open.

---

### CRASH-02: UnicodeDecodeError on JSON load (Windows)

**Symptom:**
```
UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position N
```

**Root cause:** Python's `open()` on Windows defaults to the system locale encoding
(cp1252). JSON files written with `ensure_ascii=False` contain UTF-8 multibyte
characters (Hindi/Sanskrit Devanagari, special punctuation). The cp1252 codec
cannot decode these.

**Fix:** Add `encoding="utf-8"` to every `open()` call that reads or writes JSON.

**Prevention:** Never use bare `open(path)` in a project that handles multilingual
text. Always specify `encoding="utf-8"`. Add this to the coding standards.

---

### CRASH-03: Embedding report stat_key bug (silent wrong counts)

**Symptom:** Embedding report showed `embedded: 0` for all books even when chunks
were successfully written to ChromaDB.

**Root cause:** The report loop mapped `embedding_status == "complete"` → key
`"embedded"`, but the assignment used `stat_key = "embedded" if status == "complete"`.
An earlier version of the code used `status == "embedded"` as the check, so the
mapping was `"complete" → never matches → always wrote to "pending"`.

**Fix:**
```python
# Before (wrong):
stat_key = "embedded" if chunk["embedding_status"] == "embedded" else "pending"

# After (correct):
stat_key = "embedded" if chunk["embedding_status"] == "complete" else "pending"
```

**Prevention:** When mapping a string value to a key, verify the source values
against the actual values set earlier in the same pipeline. This was AI-generated
code that was accepted without checking whether `"complete"` or `"embedded"` was
the actual status string in use.

---

### CRASH-04: Windows PermissionError on ChromaDB temp directory cleanup

**Symptom:**
```
PermissionError: [WinError 32] The process cannot access the file because
it is being used by another process: '...\\chroma_db\\chroma.sqlite3'
```

**Root cause:** ChromaDB's `PersistentClient` holds a SQLite file lock for the
duration of the process. Attempting to delete or move the `chroma_db` directory
in the same Python process (e.g., to test an empty-collection edge case) fails
because the lock is still held.

**Fix:** Run tests that require an empty collection as a separate Python process
invocation, not in the same script:
```bash
python -c "from tests.test_empty import run; run()"
```

**Prevention:** Never try to delete ChromaDB directories from within code that
also creates a ChromaDB client. Always use a different directory path for test
collections (e.g., `data/chroma_db_test/`).

---

### CRASH-05: Devanagari fraction filter misfires on English books

**Symptom:** `_should_translate()` returned `True` for 508 chunks from `BPHS - 1
RSanthanam` — an English book. Those pages would have been sent to the translation
API unnecessarily.

**Root cause:** BPHS is an English translation of a Sanskrit text. The book
includes the original Sanskrit verses in Devanagari script alongside the English
commentary. Some pages are 44%+ Devanagari characters. The content-based
Devanagari fraction check correctly detected the script but had no way to know
the book was "English with Sanskrit quotes" vs. "a Hindi book."

**Fix:** Added a source filter as the primary guard before any content filter:
```python
def _should_translate(chunk):
    if not _is_hindi_book(chunk.get("book_name", "")):
        return False        # source filter first — no content check needed
    return _devanagari_fraction(chunk["text"]) >= 0.25
```

**Prevention:** Content-based signals (character sets, keyword density, topic
patterns) are always ambiguous across a mixed-source corpus. Apply a source-level
filter (book name, file type, domain tag) before any content filter. Validate
the filter on the full dataset before committing to any threshold.

---

## Query Engine / Vector Store

### CRASH-06: ChromaDB silent crash on n_results > collection size

**Symptom:** Query with `n_results=5` on a collection with 3 documents raises
an opaque internal error from ChromaDB with no clear message about the cause.

**Root cause:** ChromaDB does not validate that `n_results <= collection.count()`.
When the request exceeds the collection size it crashes internally rather than
returning fewer results or a clear error.

**Fix:**
```python
safe_n = min(n_results, collection.count())
if safe_n == 0:
    raise RuntimeError("Collection is empty — run embedder.py first.")
results = collection.query(query_embeddings=[embedding], n_results=safe_n)
```

**Prevention:** Always clamp `n_results` before querying. This is a known
ChromaDB limitation — treat it as a guard that must always be present.

---

### CRASH-07: Empty collection returns no error, causes silent failures downstream

**Symptom:** On a fresh clone before running the embedder, `search()` returned
an empty list with no error. The agent then returned a generic "no passages found"
response — which looked like a real answer rather than a configuration error.

**Root cause:** ChromaDB returns empty results (not an error) when the collection
exists but has no documents. From the API perspective this is valid. From the
application perspective a fresh collection is always a configuration error.

**Fix:** Explicit check before querying:
```python
if collection.count() == 0:
    raise RuntimeError(
        "ChromaDB collection 'astro_chunks' is empty. "
        "Run embedder.py first to populate the collection."
    )
```

**Prevention:** At application startup (or at least at query time), verify the
collection is non-empty and raise a clear error with remediation instructions.

---

## Agent / LLM Layer

### CRASH-08: _call_gpt signature mismatch after refactor

**Symptom:** `TypeError: _call_gpt() takes 3 positional arguments but 2 were given`

**Root cause:** `_call_gpt` was originally designed as `(client, system_prompt,
user_message)` for single-turn use. When session history was added, it needed to
accept a full messages list `(client, messages)`. The function signature was
updated but one call site was not updated atomically.

**Fix:** Changed both the function signature and all call sites in the same edit.
Verified with a 7/7 regression test before committing.

**Prevention:** When changing a function signature, search for all call sites
before making the edit. Change signature and all call sites atomically in one
diff. Never change the signature first and call sites second across separate edits.

---

### CRASH-09: Parashara re-introduces himself mid-conversation

**Symptom:** After several turns of conversation, asking a follow-up question
triggers the agent to say "I am Parashara, the ancient sage..." again.

**Root cause:** The `introduce=True` flag was passed to `ask()` on every call
from the CLI test harness. The flag was not gated on whether the session already
had prior history.

**Fix:**
```python
effective_introduce = introduce and not (session and session.get_history())
```

**Prevention:** Any flag that is intended to fire only on the first interaction
must be gated on session state, not just on the caller's intent. Callers don't
always know the session state.

---

### CRASH-10: Response time failure — 6–11s exceeds acceptable threshold

**Symptom:** astrologer QA showed response times of 6.29s and 11.09s. Original
target was 5s.

**Root cause:** GPT-4o-mini inference with 5 retrieval chunks + kundali context
+ session history takes 6–11s depending on response length. This is a model
latency floor, not a code issue.

**Fix:** Two-part:
1. Raised dev baseline threshold to 10s (documents that 6-11s is expected for
   synchronous calls)
2. Documented that streaming via SSE in the FastAPI layer is the production fix
   — do not attempt to stream from inside `astrologer.py`

**Prevention:** Set response time expectations based on observed model latency,
not target UX latency. Model latency and UX latency are separate concerns:
- Model latency: 6–11s (irreducible)
- UX latency: first token in <1s via SSE streaming (FastAPI concern)

---

### CRASH-11: Session history token bloat

**Symptom:** Not a crash but a cost/latency risk. Storing full retrieval context
(5 chunks × ~400 words each = ~2,000 words) in session history per turn would
result in 12,000 words of retrieval context in history after 6 turns.

**Root cause:** Initial design stored the full `user_message` (which includes
retrieval context) in history, not just the bare question.

**Fix:**
```python
session.add_message("user", question)    # bare question, not user_message with retrieval
session.add_message("assistant", answer)
```

The current turn's `user_message` (with retrieval context) goes directly to GPT.
It is NOT stored in history. History stores only the conversational record.

**Prevention:** Explicitly document what gets stored in history vs. what is
ephemeral to the current turn. The retrieval context changes every turn and is
the most expensive part of the prompt — never accumulate it.

---

## File I/O

### CRASH-12: Partial write corrupts output file on crash

**Symptom:** After a process crash mid-write, the output JSON file was truncated
at the point of crash — containing valid JSON up to a point, then a fragment.
The next run raised `json.JSONDecodeError` and lost all progress.

**Root cause:** `file.write(json.dumps(data))` writes incrementally. A crash
mid-write leaves a partial file. The original file is already truncated before
the new content is fully written.

**Fix:** Atomic write via `.tmp` then `os.replace()`:
```python
tmp = path.with_suffix(".tmp")
tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
tmp.replace(path)  # atomic: either old file or new file, never partial
```

**Prevention:** Use atomic writes on every file that represents expensive
pipeline output. The rule is: if re-generating this file costs API money or
significant compute, protect it with atomic writes.

---

## Development Environment

### CRASH-13: Bash curly braces break in f-strings passed via -c flag

**Symptom:**
```
/usr/bin/bash: eval: line N: bad substitution
```

**Root cause:** When passing Python code with f-strings via `python -c "..."` in
bash, the curly braces in f-strings (`{variable}`) are interpreted by bash as
variable substitutions before Python sees them.

**Fix:** Write multi-line Python test code to a `.py` file, run the file, then
delete it:
```python
# Write test_script.py → run it → delete it
```

Alternatively use single quotes for the outer shell string (prevents bash variable
expansion) but this breaks on Windows.

**Prevention:** Never put f-strings or dict literals in `python -c "..."` bash
commands. Use temporary files for any test script longer than 2 lines or
containing curly braces.

---

### CRASH-14: Missing API key produces unclear error

**Symptom:** OpenAI client raises an `AuthenticationError` with a message about
invalid API key format — not a clear "API key not found" message.

**Root cause:** `OpenAI()` with no key argument reads from the `OPENAI_API_KEY`
environment variable. If it is not set, the client initialises with `None` and
raises on first API call.

**Fix:** Add `load_dotenv()` at the top of every module that creates an
`OpenAI()` client:
```python
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
```

Add a startup check in the embedder and agent entry points:
```python
import os
if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError(
        "OPENAI_API_KEY not set. Create a .env file with your key."
    )
```

**Prevention:** Always call `load_dotenv()` before instantiating any API client.
Validate that the key is present at startup, not at first use.

---

### CRASH-15: Background process killed when Claude Code exits

**Symptom:** Process starts fine in the background, dies silently when Claude Code
`/exit` is called. No error, no log entry — the process simply stops.

**Root cause:** Claude Code's `Bash()` tool spawns child processes attached to
the Claude Code process tree. When Claude Code exits, the OS sends SIGTERM/kills
the entire process group, taking any background child processes with it.

**Fix:** On Windows, use `start` to detach the process from the Claude Code tree:
```bat
start python run_overnight.py
```
This launches Python as an independent process that survives Claude Code exit.

**Prevention:** Never use `Bash(run_in_background=True)` for overnight or
long-running pipeline runs. Always detach with `start python script.py` on
Windows before exiting Claude Code.

---

## Summary Table

| ID | Component | Symptom | Root cause category |
|---|---|---|---|
| CRASH-01 | embedder | FileNotFoundError | Wrong constant value |
| CRASH-02 | all JSON | UnicodeDecodeError | Windows encoding default |
| CRASH-03 | embedder | Wrong report counts | String comparison mismatch |
| CRASH-04 | query_engine | PermissionError on cleanup | SQLite file lock (Windows) |
| CRASH-05 | translator | False-positive translation | Content filter without source guard |
| CRASH-06 | query_engine | ChromaDB opaque crash | n_results > collection size |
| CRASH-07 | query_engine | Silent empty results | Empty collection not checked |
| CRASH-08 | astrologer | TypeError signature | Signature change without atomic call-site update |
| CRASH-09 | astrologer | Mid-convo re-introduction | Flag not gated on session state |
| CRASH-10 | astrologer | Response time 6–11s | Model latency floor, not code |
| CRASH-11 | session | Token bloat risk | Full retrieval context stored in history |
| CRASH-12 | all pipeline | Truncated JSON on crash | Non-atomic file writes |
| CRASH-13 | dev | Bash substitution error | F-strings in shell -c argument |
| CRASH-14 | all LLM | Unclear auth error | load_dotenv() missing |
| CRASH-15 | dev | Background process dies on /exit | Child process attached to Claude Code process tree |
