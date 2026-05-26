# RAG Pipeline Patterns

Patterns discovered building a production PDF → embeddings → LLM Q&A pipeline.
All patterns are validated on real data, not theoretical.

---

## 1. Pipeline Stage Design

### The canonical stage order

```
source_processor   → raw page chunks + extracted image paths
image_extractor    → fills text field on diagram chunks via vision LLM (one-time)
chunker            → splits/refines chunks, sets language + topic + word_count
translator         → translates non-English chunks (one-time ingestion cost)
embedder           → writes final chunks to vector store
────────────────────────────────────────────────────
query_engine       → query → vector search → ranked chunks
prompt_builder     → chunks + user context → system + user prompt strings
agent              → prompt_builder + LLM call → structured response
session_manager    → stores Q&A history, persists to disk
```

**Rule:** Each stage owns exactly one transformation. No stage does two things.
Stages communicate through files (JSON) or well-defined function interfaces, never
through shared mutable state.

### File handoff pattern

Each stage reads one file, writes one file. This enables crash recovery and
independent re-runs.

```
all_chunks.json          ← pdf_processor output (raw pages)
processed_chunks.json    ← image_extractor output (diagrams filled)
translated_chunks.json   ← translator output (non-English → English)
embedding_report.json    ← embedder output (stats, not chunks)
data/chroma_db/          ← embedder writes here; query_engine reads here
data/sessions/{id}.json  ← session_manager persists here
```

**Crash recovery rule:** If a stage's output file already exists, resume from it.
The translator does this: if `translated_chunks.json` exists, load it as the base
and only translate the untranslated chunks. Never restart from zero.

---

## 2. Chunk ID Schema

### Design the ID for the post-split state

The chunker splits page-level chunks into sub-chunks. The ID schema must
accommodate this from the start.

```python
# Page-level chunk from pdf_processor:
chunk_id = f"{book_name}_p{page_num}"         # e.g. "BPHS Vol1_p42"

# Sub-chunks from chunker (always append _c{index}):
chunk_id = f"{book_name}_p{page_num}_c{i}"   # e.g. "BPHS Vol1_p42_c0", "_c1", "_c2"

# Diagram pages with no split still get _c0:
chunk_id = f"{book_name}_p{page_num}_c0"
```

**Why _c0 on unsplit chunks:** ChromaDB uses chunk_id as the primary key for
upsert. If page-level and sub-chunk IDs coexist in the collection, upserts will
silently overwrite the wrong document. Always use one canonical ID format.

---

## 3. Chunking Strategy

### The three-step text chunking pipeline

```python
text → split_on_paragraphs() → merge_paragraphs() → sliding_window() if > threshold
```

**Validated parameters (tuned on mixed OCR'd text):**
- `MERGE_MIN_WORDS = 100` — merge adjacent paragraphs until buffer hits 100 words
- `SPLIT_THRESHOLD = 500` — pages over 500 words get sliding window
- `WINDOW_SIZE = 400` — 400-word window
- `WINDOW_OVERLAP = 50` — 50-word overlap between windows

**Why merge before split:** OCR'd text from old books has many 1–2 sentence
paragraphs (line breaks treated as paragraphs). Without merging, you get hundreds
of near-empty chunks that retrieve poorly.

### Language detection order matters

```python
def detect_language(text):
    # 1. Devanagari check FIRST — more reliable than langdetect for short text
    devanagari_fraction = count_devanagari(text) / len(non_whitespace(text))
    if devanagari_fraction >= 0.25:
        return "hin"
    if devanagari_fraction > 0:
        return "mixed"

    # 2. Length guard — langdetect unreliable under 30 words
    if word_count(text) < 30:
        return "eng"

    # 3. langdetect fallback
    try:
        return "hin" if detect(text) == "hi" else "eng"
    except LangDetectException:
        return "eng"
```

**Critical:** Do character-level script detection before library-based language
detection. Libraries fail on short text and on classical script mixed with roman.

### Strip non-target script before chunking, not before embedding

```python
# chunker.py — for text/mixed pages only
text = strip_devanagari(text)
paragraphs = split_on_paragraphs(text)
```

Strip happens inside `chunk_page()`, after the language has already been detected
from the original text. Do not strip before language detection or you lose the
signal needed to route the chunk to translator.py.

---

## 4. Embedding Pipeline

### Idempotency via existing ID check

```python
existing_ids = set(collection.get(include=[])["ids"])
to_embed = [c for c in embeddable if c["chunk_id"] not in existing_ids]
```

Always check what is already in the collection before embedding. Upsert is
idempotent at the document level, but calling the embedding API for documents
that are already stored wastes money.

### Batch size and rate limit handling

```python
BATCH_SIZE = 100          # balance: large enough for efficiency, small enough to retry cheaply
RATE_LIMIT_RETRIES = 4
RATE_LIMIT_BASE_DELAY = 10  # seconds; doubles: 10, 20, 40, 80
```

Batch at 100 for embeddings (text-embedding-3-small handles this well). For
translation and LLM calls where each item is a separate request, use per-request
retries instead of batch retries.

### ChromaDB metadata: no None values

```python
def _to_metadata(chunk):
    return {
        "topic":      chunk.get("topic") or "",       # None → ""
        "language":   chunk.get("language") or "eng",
        "page_ref":   chunk.get("page_ref") or 0,     # None → 0
        "image_path": chunk.get("image_path") or "",
        "book_name":  chunk.get("book_name") or "",
        "page_type":  chunk.get("page_type") or "",
        "word_count": chunk.get("word_count") or 0,
    }
```

ChromaDB rejects None in metadata. Always coerce: strings to `""`, ints to `0`.
Never store the `embedding_status` or translation fields in ChromaDB metadata —
those are pipeline-internal fields, not retrieval fields.

---

## 5. Vector Search

### Distance to similarity conversion

ChromaDB cosine distance returns 0 for identical vectors and up to 2 for opposite.
Always convert to similarity before returning to callers:

```python
score = 1 - distance   # 1.0 = identical, 0.0 = orthogonal, negative = opposite
```

Callers should never see raw distance values. The score field in returned chunks
should always be in [0, 1] range with 1 = best match.

### Guard n_results > collection size

```python
safe_n = min(n_results, collection.count())
if safe_n == 0:
    raise RuntimeError("ChromaDB collection is empty — run embedder.py first.")
results = collection.query(query_embeddings=[embedding], n_results=safe_n, ...)
```

ChromaDB raises an opaque error (not a clear ValueError) when `n_results` exceeds
the collection size. Always clamp. Also check for empty collection explicitly —
an empty collection returns no error but returns empty results, which downstream
code may misinterpret.

### Metadata filter building for multi-field queries

```python
def _build_where(filters: dict) -> dict | None:
    if not filters:
        return None
    if len(filters) == 1:
        k, v = next(iter(filters.items()))
        return {k: {"$eq": v}}
    return {"$and": [{k: {"$eq": v}} for k, v in filters.items()]}
```

ChromaDB's where syntax differs between single and multi-field filters. Single
field uses `{field: {"$eq": value}}`. Multi-field requires `{"$and": [...]}`.
Centralise this in one helper so callers just pass a plain dict.

---

## 6. Prompt Architecture

### System prompt owns all policy; user message owns all context

```
system: persona + rules + tone + disclaimer + low-confidence caveat
user:   retrieved passages + kundali context + palm description + question
```

Never put policy in the user message (it can be overridden by injected content).
Never put retrieval context in the system prompt (it changes every turn and bloats
the cached prompt).

### Source citations belong in context, not in response

Pass sources to the LLM as context blocks in the user message so it can ground
its answer. Instruct the system prompt explicitly not to cite book names or page
numbers in the response text. Users want the wisdom, not the bibliography.

```python
# In user message:
"[1] Book Name, p.42 (topic: planets, score: 0.61)\n{chunk_text}\n"

# In system prompt:
"Do not cite book names, page numbers, or passage numbers in your response."
```

### Low-confidence path

Define a score threshold below which the system warns the LLM:

```python
LOW_CONFIDENCE_THRESHOLD = 0.45
# Observed good-query range: 0.57–0.60
# Set conservatively (low) — too many false low-confidence warnings are annoying
# Tune down if flagging good queries; tune up if hallucination increases
```

When `top_score < threshold`, append a caveat to the system prompt:
```
NOTE: The available passages have a weak match to this question.
Answer carefully and explicitly acknowledge this before responding.
```

Do not refuse to answer — let the LLM decide what it can say honestly.

---

## 7. Session History

### Store bare Q&A in history, not retrieval context

```python
# On successful answer:
session.add_message("user", question)        # bare question only
session.add_message("assistant", answer)     # bare answer only

# When building messages for next turn:
messages = [{"role": "system", "content": system_prompt}]
         + session.get_recent_history(n=6)   # last 6 turns = 12 messages
         + [{"role": "user", "content": user_msg_with_retrieval}]
```

Storing full retrieval context in history causes token bloat proportional to
history length × number of chunks × chunk size. Only the current turn needs
retrieved passages. History needs only the conversational record.

### Sliding window, not truncation

```python
def get_recent_history(self, n=6):
    recent = list(self._history[-(n * 2):])
    # Guard: drop leading assistant message if history is odd-length
    if recent and recent[0]["role"] != "user":
        recent = recent[1:]
    return recent
```

Use a sliding window (last N turns) rather than hard truncation. The guard on
the leading message handles the edge case where slicing mid-history lands on an
assistant message.

### Session file is write-once per turn, not per message

Save the session file after the full turn completes (user + assistant both added),
not after each individual `add_message` call. And only save on success — never
in a `finally` block or after a failed LLM call.

```python
answer = _call_gpt(client, messages)   # raises on failure
session.add_message("user", question)  # only reached on success
session.add_message("assistant", answer)
# caller saves session after this returns
```

### Suppress re-introduction after first turn

```python
effective_introduce = introduce and not (session and session.get_history())
```

The `introduce` flag should only fire on the very first interaction. If a session
is resumed or the session already has history, re-introduction mid-conversation
is jarring and confusing to users.

---

## 8. Atomic File Writes

Use everywhere a pipeline stage writes a file that cost money to produce:

```python
def _save(data, path):
    p = Path(path)
    tmp = p.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(p)          # atomic on POSIX; near-atomic on Windows
    except Exception as e:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"Failed to save {path}: {e}") from e
```

A crash mid-write leaves a `.tmp` file, not a partial JSON. The target file is
either the previous good version or the new complete version. Never corrupt.

---

## 9. Content-Based vs Source-Based Filtering

**Never use content-based filters alone when sources are mixed.**

Example failure: A Devanagari character fraction check was designed to identify
Hindi book pages. It correctly identified Hindi prose. But it also flagged 508
pages from an English translation of a Sanskrit text — because that book
included the original Sanskrit verses alongside the English translation.

**Pattern:**
```python
# WRONG — content filter alone
def should_translate(chunk):
    return devanagari_fraction(chunk["text"]) >= 0.25

# RIGHT — source filter first, then content filter
def should_translate(chunk):
    if not is_hindi_book(chunk["book_name"]):   # source filter
        return False
    return devanagari_fraction(chunk["text"]) >= 0.25  # content filter
```

Use partial case-insensitive match for source filtering so minor filename
variations don't cause silent miss:
```python
HINDI_BOOKS = {"hasta samudrika", "jataka parijata", "lal kitab"}
any(stem in book_name.lower() for stem in HINDI_BOOKS)
```

---

## 10. Topic Tagging

### First-match ordered keyword map

```python
TOPIC_KEYWORDS = {
    "mahadasha": "dasha",    # more specific terms first
    "antardasha": "dasha",
    "dasha": "dasha",
    "nakshatra": "nakshatra",
    "lagna": "lagna",
    "ascendant": "lagna",
    # ... less specific terms later
    "planet": "planets",
    "sun": "planets",
    # ...
}

def detect_topic(text):
    text_lower = text.lower()
    for keyword, topic in TOPIC_KEYWORDS.items():
        if keyword in text_lower:
            return topic
    return "general"
```

**Order matters.** Put more specific terms before general terms. "mahadasha"
before "dasha" before "planet". The first match wins; later terms are never
evaluated. Test on your hardest cases (pages with multiple topic signals) to
verify the order is correct.
