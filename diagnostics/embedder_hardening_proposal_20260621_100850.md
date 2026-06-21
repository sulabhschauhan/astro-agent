# Embedder Hardening Proposal — chunk_id-only → chunk_id + text-hash

**Generated:** 2026-06-21 10:08:50 UTC
**Read-only proposal** — no code, data, or ChromaDB changes made or implied by writing this file.

Source diagnostics this proposal builds on: `diagnostics/chromadb_dup_report_20260621_080119.md` (3,930 duplicate-text groups / 7,896 chunks, 100% matching an `X` / `X_c<N>` chunk_id pair) and `diagnostics/chunking_code_audit_20260621_092249.md` §5(c), which already named the embedder's id-only check as the proximate gap.

## 1. Current shape of embedder.py

- **File path:** `ingestion/embedder.py`
- **Total line count:** 165

**Idempotency-check block — verbatim, lines 103–109:**

```python
    # Idempotency: skip chunks already present in ChromaDB
    existing_ids = set(collection.get(include=[])["ids"])
    to_embed = [c for c in embeddable if c["chunk_id"] not in existing_ids]
    skipped_existing = len(embeddable) - len(to_embed)
    if skipped_existing:
        logger.info(f"Skipping {skipped_existing} chunks already in ChromaDB — {len(to_embed)} to embed")
    total_batches = (len(to_embed) + BATCH_SIZE - 1) // BATCH_SIZE
```

This is a string-set membership check on `chunk_id` only. It cannot see that two different ids hold byte-identical `text`.

**Chunk metadata construction before insert — verbatim, lines 55–65:**

```python
def _to_metadata(chunk: dict) -> dict:
    """ChromaDB-safe metadata — no None values, embedding_status excluded."""
    return {
        "topic":      chunk.get("topic") or "",
        "language":   chunk.get("language") or "eng",
        "page_ref":   chunk.get("page_ref") or 0,
        "image_path": chunk.get("image_path") or "",
        "book_name":  chunk.get("book_name") or "",
        "page_type":  chunk.get("page_type") or "",
        "word_count": chunk.get("word_count") or 0,
    }
```

**The actual `collection.upsert()` call — verbatim, lines 112–121 (loop header + call):**

```python
    for batch_num, i in enumerate(range(0, len(to_embed), BATCH_SIZE), start=1):
        batch = to_embed[i: i + BATCH_SIZE]
        try:
            embeddings = _embed_batch([c["text"] for c in batch], openai_client)
            collection.upsert(
                ids=[c["chunk_id"] for c in batch],
                embeddings=embeddings,
                documents=[c["text"] for c in batch],
                metadatas=[_to_metadata(c) for c in batch],
            )
```

No `.add()` call exists in this file — only `.upsert()`, here and nowhere else.

## 2. Where text-hash should live

- **Recommended field name:** `text_sha256`
- **Algorithm:** SHA-256, computed over the raw UTF-8-encoded `text` field, unmodified.
  - Rationale is precedent-matching, not cryptographic. `diagnostics/chromadb_dup_diagnostic.py:109` — the script that originally sized this bug class (3,930 groups) — already hashes with `hashlib.sha256((text or "").encode("utf-8")).hexdigest()`. Using the same algorithm and the same "no normalization" convention means the embedder's notion of "duplicate" matches the audit's notion of "duplicate" bit-for-bit; a different choice (e.g. MD5, or a normalized variant) would make post-fix dedup counts incomparable to the established baseline for no benefit.
  - MD5 is already used elsewhere in this codebase (`agent/palm_processor.py:64`, `frontend/app.py:238/365/512`) but for a different purpose — fingerprinting uploaded image *bytes* to detect re-uploads of the same file. That is a different invariant (file-identity, not text-content-identity) and reusing MD5 here would blur the distinction. No reason to deviate from SHA-256.

- **When the hash should be computed — chunker time vs. embedder time:**

  **Chunker time (`ingestion/chunker.py`):**
  - \+ Single source of truth; `chunked_chunks.json` becomes self-describing for any future tool, not just `embedder.py`.
  - \+ Arguably the more "correct" layer per CLAUDE.md's LAYER FIRST rule — the duplicate-text bug originates at the chunking layer (confirmed by the chunking-code audit: `chunk_all()` re-chunking already-chunked progress files).
  - − Requires editing a second file, which conflicts with this task's explicit single-file scope.
  - − Doesn't help the data already on disk: the existing `chunked_chunks.json` / `data/progress/*.json` were written before any such change and would still need the hash computed retroactively somewhere downstream anyway.

  **Embedder time (`ingestion/embedder.py`):**
  - \+ Matches the task's explicit single-file constraint.
  - \+ `chunker.py` has zero ChromaDB awareness today (confirmed by grep — no `chromadb` import in that file); the ChromaDB-uniqueness invariant structurally belongs in the layer that already owns ChromaDB state.
  - \+ Self-healing across the transition window: computed fresh on every embed call, so it never depends on when/how an upstream JSON record was produced.
  - − The hash never gets written back into `chunked_chunks.json` itself — but per the chunking-code audit's exhaustive grep, no tool other than `embedder.py` and `chunker.py` currently reads that file's chunk dicts, so this is a theoretical cost, not an active one.

  **Pick: embedder time.** It satisfies the task's single-file scope, it's the layer that already holds ChromaDB state, and computing at chunker time wouldn't retroactively fix anything already on disk — that data would need the same embedder-time fallback regardless.

- **Compatibility check performed (not just asserted):** `ingestion/query_engine.py:96-114` builds its search-result dicts by explicitly whitelisting metadata keys (`meta.get("book_name", "")`, `meta.get("topic", "")`, etc. — six named `.get()` calls, no `for k, v in meta.items()` anywhere). Adding `text_sha256` to `_to_metadata()`'s output will **not** leak into user-facing query results; confirmed by reading the consumer, not assumed.

- **Schema-lock flag (see §6 / Recommended next step):** CLAUDE.md's "Chunk Metadata Schema (locked — do not alter)" lists exactly the 7 fields `_to_metadata()` currently returns (plus `chunk_id`/`text`, which become Chroma's `id`/`document`, not metadata). Adding `text_sha256` is an **additive** change to that schema, not a rename/removal — but the schema is explicitly marked locked, and this proposal does not have standing to silently extend it. Flagging as an open question, not resolving it here.

## 3. The minimal diff to embedder.py (prose only — no code written)

(a) **Hash computation, if not already present in metadata:**
- Add `import hashlib` to the top-of-file import block (near line 8).
- Add one line inside `_to_metadata()` (lines 55–65): a new dict key, `"text_sha256": hashlib.sha256((chunk.get("text") or "").encode("utf-8")).hexdigest()`. No separate helper function needed — one line is enough at this size.

(b) **Pre-insert check querying for existing `text_sha256` matches:**
- Immediately after the existing id-based filter (lines 103–109), add a second filtering pass:
  - One bulk read: `existing_meta = collection.get(include=["metadatas"])["metadatas"]` — same "pull everything once" idiom already used one line above for `existing_ids` (line 104), not a new query pattern.
  - Build `existing_hashes = {m.get("text_sha256") for m in existing_meta if m.get("text_sha256")}` — falsy/missing values drop out naturally, which is exactly the desired behavior for chunks that pre-date this field (see §4).
  - Re-filter `to_embed`: for each candidate, compute its hash (reusing the line-(a) expression), reject if it's in `existing_hashes` **or** already seen earlier in this same run (a local `seen_hashes` set, to also catch intra-batch dupes — two new chunks in one run with identical text).

(c) **Skip + log + counter on collision:**
- One counter, initialized alongside `skipped_existing` (line 106 area): `skipped_duplicate_text = 0`.
- One `logger.warning(...)` per rejected chunk inside the hash-filter loop, naming the chunk_id and noting it matched existing/in-batch text.
- Increment the counter per rejection.

(d) **End-of-run summary:**
- One new key in the `report` dict (lines 136–144): `"total_skipped_duplicate_text": skipped_duplicate_text`.
- One new `print()` line in the `__main__` block (after line 160), mirroring the existing `Pending:` / `Failed batches:` lines already there.

**Line-equivalent count:** import (1) + hash expression reused twice (1 definition + inline reuse) + metadata key (1) + hash-filter block (~8–10: bulk read, set-builder, loop, seen-set check) + counter init (1) + warning line (1) + report key (1) + print line (1) ≈ **16–19 line-equivalents.** Within the ~30 budget — no scope flag needed on size grounds. (The schema-lock question in §2/§6 is the actual open item, not size.)

## 4. Backward compatibility

**Mixed-state correctness (old chunks have no `text_sha256`, new ones will):**
Confirmed safe. `existing_meta`'s old records simply have no `text_sha256` key; `m.get("text_sha256")` returns `None`; the set-comprehension's `if m.get("text_sha256")` guard excludes `None`/missing values from `existing_hashes` with no exception path needed. Old chunks contribute nothing to the collision check but also never crash it — this mirrors the existing `.get(...) or default` defensive style already used throughout `_to_metadata()` (lines 58–64).

**What this does *not* retroactively fix:** an old duplicate pair already sitting in ChromaDB (e.g. `Deva-keralam_p8_c0` / `Deva-keralam_p8_c0_c0`, both pre-existing, neither "incoming") is invisible to a pre-insert check by construction — neither record is ever the "new" side of the comparison. That cleanup is the separate targeted-delete pass named in the task context, correctly out of scope here.

**Does `text_sha256` need a one-time backfill onto existing chunks?**
- *For:* would let a future audit query `text_sha256` directly via Chroma's `where` filter instead of re-hashing `documents` at read time (as `chromadb_dup_diagnostic.py:106-112` currently does).
- *Against:* it's a write against the live collection (`collection.update()` across ~11,688 records) — directly conflicts with this task's read-only / no-ChromaDB-writes constraint and with "don't bundle with the targeted delete." It's also likely moot: once the targeted-delete pass removes the duplicate-text records (already planned per task context), the only chunks left needing backfill are *non*-duplicates, which were never at risk of a missed collision in the first place.
- **Recommend: new-only, no backfill.** Revisit only if a future audit specifically needs `text_sha256` queryable on 100% of the live collection — it doesn't today.

## 5. Failure modes this proposal does not cover

- **Byte-for-byte only.** SHA-256 over the literal `text` field catches exact duplicates and nothing softer — near-identical text (one extra space, a stray OCR artifact like the lone `|` character that was the entire "text" in the dup report's largest group, a truncated copy) hashes completely differently and passes through undetected.
- **Normalization (strip/lowercase) before hashing — argued both ways:**
  - *For:* would catch a marginally wider class of accidental near-dupes (trailing-whitespace variance, case drift from re-OCR).
  - *Against:* (1) the diagnostic that established this problem's actual size (`chromadb_dup_diagnostic.py:109`) hashes raw text — normalizing differently in the fix makes its dupe counts incomparable to that baseline; (2) this corpus mixes Devanagari and Latin script, and `chunker.py`'s own `detect_language()`/`detect_topic()` are case-sensitive over that mixed text — a normalized hash input becomes a second, divergent mental model of "what does this hash represent" versus the literal stored document; (3) the actual observed failure mode (per the dup report) is full-body byte-identical duplication, not whitespace-edge variance, so `strip()` buys close to zero additional catch rate against the real bug.
  - **Recommend: no normalization.** Hash `text` exactly as stored.

## 6. Test plan

**Smallest unit test:** call the metadata-construction path with a known string and assert the exact digest — e.g. `_to_metadata({"text": "hello world"})["text_sha256"] == hashlib.sha256(b"hello world").hexdigest()`. Pure function, no ChromaDB client, no OpenAI client, no I/O.

**Smallest integration test simulating the X / X_c0 failure mode:**
1. Seed a fresh test collection (temp-dir `PersistentClient`, per `get_collection()`'s own pattern) with one record: `chunk_id="X"`, `text="identical body"`, upserted through the same code path the pipeline uses.
2. Run the pipeline against a one-item input list: `chunk_id="X_c0"`, `text="identical body"` — different id, byte-identical text (this is exactly the documented `Deva-keralam_p8_c0` / `_p8_c0_c0` pattern from `chromadb_dup_report_20260621_080119.md`).
3. Assert: `collection.count()` is still 1 (no second record inserted), the run's report shows `total_skipped_duplicate_text == 1`, and `"X_c0"` is absent from `collection.get()["ids"]`.

Note for context: `ingestion/embedder.py` currently has **zero** test coverage — no file under `tests/` references it (confirmed by glob across `tests/**/*.py`). This would be the first test file for this module; there's no existing fixture/harness to extend.

## Compatibility risks identified (none blocking, one flagged as a design question)

- **No breakage found** in `query_engine.py`'s metadata consumption (explicit whitelist, verified by reading the code — see §2).
- **No breakage found** in the mixed-state transition window (see §4 — `.get()` defaults handle it cleanly, same idiom already in use).
- **Open, not resolved here:** CLAUDE.md's chunk metadata schema is explicitly marked "locked — do not alter." This proposal's only schema change is additive (`+text_sha256`, nothing renamed or removed), but a proposal-only pass doesn't have standing to decide whether "locked" permits additive fields or not. Flagging rather than assuming.

## Recommended next step

The diff itself is ready to implement (16–19 line-equivalents, single file, no breakage found in either consumer checked) — but one design question needs an explicit answer first: whether adding `text_sha256` to embedder.py's `_to_metadata()` output counts as altering the CLAUDE.md-locked chunk metadata schema, and if so, whether that lock should be amended (one line, additive) in the same change or requires separate sign-off.
