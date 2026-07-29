## E2G PREFLIGHT — S79 — 2026-07-29T09:21:36Z — 212d9c6

Model: Sonnet 4.6. Read-only investigation, no design decisions, no source edits (except the one throwaway probe permitted for Q3/Q4, deleted at the end — named in PROBE SCRIPTS section below). No re-ingestion, no corpus writes, no embedding calls beyond the two read-only probes (a live `collection.get()` — metadata-only, no embedding API call — and one `pdfplumber` local text-layer read).

---

### Q1 — VISION OUTPUT SCHEMA

There are THREE vision calls in `agent/palm_processor.py`. Only two of them (`describe_palm_image`, `describe_hand_detail_image`) produce the text that flows into Stage 1 (`palm_reading.py` / `claim_extraction.py`); `validate_palm_image` is a pre-filter quality gate whose output never reaches Stage 1.

**a. Exact vision prompt text, verbatim:**

`describe_palm_image` (`agent/palm_processor.py:191-211`), the per-hand (LEFT/RIGHT) description call — this is the primary source parsed by `_parse_fields` into Stage 1:
```
f"You are a trained observer preparing hand notes for a "
f"Cheiro-tradition palmist. You are NOT the palmist: record only "
"what is physically visible in this {hand} hand image. No "
"meanings, no character traits, no predictions — never write "
"'indicating', 'suggesting', or any interpretation. Output "
"EXACTLY these labeled lines, in this order:\n"
"HAND SHAPE: palm proportions (square vs elongated), overall build\n"
"FINGERS: length relative to palm, straightness, fingertip shape, spacing\n"
"THUMB: relative size, how low or high it is set, angle from the palm\n"
"LIFE LINE: presence, depth, length, course, origin and end, breaks/\n"
"chains/forks/islands if visible\n"
"HEAD LINE: same attributes\n"
"HEART LINE: same attributes\n"
"FATE LINE: same attributes (state plainly if absent or barely visible)\n"
"OTHER LINES: sun/health/marriage lines only if clearly visible\n"
"MOUNTS: which pads appear developed, flat, or unremarkable\n"
"MARKS: crosses, stars, grilles, squares, moles — only if clearly visible\n"
"For any attribute not clearly visible, write 'not clearly visible' — "
"never guess or fill in what a typical hand would show."
```
(This is a system-role message; `{hand}` is Python-interpolated to "left"/"right".)

`describe_hand_detail_image` (`agent/palm_processor.py:271-280`), the optional whole-hand-photo call, sent as a user-role text block alongside the image:
```
"You are a Cheiro-tradition palmist. Examine this hand photograph carefully. "
"Describe only what you can physically observe: hand shape, finger lengths "
"relative to each other, thumb angle and flexibility, visible lines (life, "
"head, heart, fate, sun), any notable mounts, markings, or unusual features. "
"Be precise and observational. Do not interpret or predict — only describe."
```

`validate_palm_image`'s system prompt (`agent/palm_processor.py:19-30`), for completeness (NOT part of the Stage-1-feeding path):
```
"You are a palm image validator. Analyse the image and report objective "
"observations only — do not identify which hand (left or right) this is.\n"
"Return ONLY valid JSON, no markdown:\n"
"{\n"
"  \"quality\": \"good|poor_readable|unusable\",\n"
"  \"issues\": [\"blurry\",\"partial\",\"dark\",\"not_a_hand\"],\n"
"  \"palm_facing\": \"camera|away|unclear\",\n"
"  \"finger_direction\": \"up|down|sideways|unclear\"\n"
"}\n"
"issues is an empty list if none."
```

**b. Output schema as it actually exists:**

`describe_palm_image` (`agent/palm_processor.py:167-238`) returns `response.choices[0].message.content` — a **plain `str`**, not a dataclass or structured object. `describe_hand_detail_image` (`agent/palm_processor.py:241-295`) likewise returns a plain `str` (raises `ValueError` on empty content, `agent/palm_processor.py:293-294`).

That raw string is later parsed, downstream, by `agent/interpretive/palm_reading.py`:
- `_parse_fields(block: str) -> dict[str, str]` (`palm_reading.py:230-247`) — parses the `describe_palm_image` output's flat `"LABEL: text"` lines (regex `_FIELD_LINE = re.compile(r"^([A-Z][A-Z ]{2,}):\s*(.*)$")`, `palm_reading.py:226`) into a `dict[str, str]` keyed by field label (`"THUMB"`, `"LIFE LINE"`, etc.).
- `_parse_bullet_fields(block: str) -> dict[str, str]` (`palm_reading.py:250-267`) — parses `describe_hand_detail_image`'s markdown `"- **Label**: text"` bullet lines (regex `_BULLET_FIELD = re.compile(r"^-\s*\*\*([^*]+)\*\*:\s*(.*)$")`, `palm_reading.py:227`) into a `dict[str, str]`.

Carried into Stage 1 as `PalmReadingPrep` (`palm_reading.py:1581-1605`, `@dataclass(frozen=True)`):
```python
gated_results: dict[str, list[dict]]
supported_features: tuple[str, ...]
unsupported_features: tuple[str, ...]
claims: tuple[Claim, ...]
texts_by_feature: dict[str, str]
diagnostics: dict = field(default_factory=dict)
```
`prepare_palm_reading(palm_left, palm_right, hand_detail=None, client=None)` (`palm_reading.py:1608` onward) is the entry point: `palm_left`/`palm_right`/`hand_detail` are each `str | None` — the raw vision-call output strings themselves, parsed via `_parse_fields`/`_parse_bullet_fields` at `palm_reading.py:1634-1636`.

**c. Per-feature confidence / visibility / uncertainty field — does one exist?**

**No.** Grepped `agent/` for `confidence|visibility|uncertainty|bounding_box|bbox|region` (case-insensitive) — every hit belongs to unrelated subsystems: `agent/astrologer.py`'s `LOW_CONFIDENCE_THRESHOLD`/`low_confidence` (the quarantined Q&A `ask()` path, not palm), `agent/infra/chart_profile.py`'s `uncertainty_virupa`/`uncertainty_days` (Shadbala/dasha calculation-engine tiers, not palm), and `agent/infra/calc_router.py`'s Stage-2 classification `confidence` (question routing, not vision). None of these attach to a per-feature vision-output field. The ONLY structured confidence-like field anywhere in the vision path is `validate_palm_image`'s `quality`/`issues` (image-level, not per-feature, and not carried into Stage 1 — see (a)/(b) above).

**d. Free prose or constrained vocabulary?**

Two different schemas coexist:
- `validate_palm_image` (image-level gate, NOT Stage-1-feeding): fully constrained. `_VALID_PALM_FACING = frozenset({"camera", "away", "unclear"})` (`palm_processor.py:32`), `_VALID_FINGER_DIRECTION = frozenset({"up", "down", "sideways", "unclear"})` (`palm_processor.py:33`), `quality` constrained to `"good"|"poor_readable"|"unusable"` and `issues` to a subset of `["blurry","partial","dark","not_a_hand"]` (both enforced only by the prompt's own JSON schema text, `palm_processor.py:24-25` — no Python-side enum validation on `quality`/`issues` themselves, only on `palm_facing`/`finger_direction`, `palm_processor.py:113-116`).
- `describe_palm_image`/`describe_hand_detail_image` (the Stage-1-feeding calls): **free prose per feature**, not a constrained vocabulary. The only constrained element is the single fallback phrase `"not clearly visible"` the prompt instructs the model to write when an attribute isn't visible (`palm_processor.py:209`) — and this is prompt-level guidance only, not Python-enforced; real production output shows variant phrasings of this same idea (e.g. `"Barely visible"`, `"not clearly visible"`, `"No marks clearly visible"` — confirmed in `diagnostics/dogfood_capture.md`, which is exactly why `palm_reading.py`'s `_ABSENCE_PHRASES`/`_ABSENCE_PATTERNS_BY_FEATURE` two-tier system exists at all, see Q7).

**e. Bounding box / region reference per feature?**

**No.** No `bbox`/`bounding_box`/region-coordinate field exists anywhere in `agent/palm_processor.py`'s vision calls or in the downstream parsed schema. Confirmed by the same grep as (c) — zero hits for any bounding-box/region concept in `agent/`.

---

### Q2 — EMBEDDING + RETRIEVAL STACK

**a. ChromaDB embedding function — local or remote?**

**Remote API** (OpenAI), not a local model. `ingestion/query_engine.py:18`: `EMBEDDING_MODEL = "text-embedding-3-small"`; used at `ingestion/query_engine.py:82-84`:
```python
openai_client = OpenAI()
response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=question)
query_embedding = response.data[0].embedding
```
Same model string set independently at `ingestion/embedder.py:25` (ingestion-side), used at `ingestion/embedder.py:46`. `get_collection()` (`ingestion/query_engine.py:23-28`) calls `client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})` with **no `embedding_function` argument** — ChromaDB's own default embedding function is never invoked, because the query embedding is computed externally (OpenAI) and passed directly as `query_embeddings=[query_embedding]` (`ingestion/query_engine.py:86-94`), never as `query_texts=`.

**b. Cross-encoder / reranker anywhere in the retrieval path?**

**No.** Grepped the entire repo (case-insensitive) for `rerank|cross_encoder|CrossEncoder|re-rank` — the only hit is a prose mention in `diagnostics/path_c_validation_20260621_173724.md:179` ("no amount of re-ranking the existing chunks would have surfaced Moon-in-Aries-specific content"), a hypothetical discussed in an old validation report, not actual code. No reranking/cross-encoder module, import, or call site exists anywhere in `ingestion/` or `agent/`.

**c. `_retrieve_per_feature` and `_build_feature_query` in full:**

`_build_feature_query` (`agent/interpretive/palm_reading.py:438-444`):
```python
def _build_feature_query(feature: str, quality: str) -> str:
    """Ratified variant (iii), verbatim shape from the S67 probe."""
    noun = feature.split("/")[0]
    return (
        f"what does a {quality} {noun} signify — meaning and indications "
        f"of a {quality} {noun}"
    )
```

`_retrieve_per_feature` (`agent/interpretive/palm_reading.py:447-497`):
```python
def _retrieve_per_feature(
    left_fields: dict[str, str],
    right_fields: dict[str, str],
    hd_fields: dict[str, str],
) -> tuple[dict[str, list[dict]], list[str]]:
    """Returns (per_feature_results, failed_features).
    per_feature_results is in _FEATURE_REGISTRY order, every feature
    present as a key (empty list if skipped or the search call failed) --
    this map, not just what's displayed, is the future R3 evidence
    structure, so every assignment is kept even when a chunk_id repeats
    across features.

    ACCEPTED GAP (S68 F-C close-out, CLAUDE.md "Known Source Divergences
    / Accepted Gaps (V1)" register, item (c)): "heart line" queries this
    corpus's p.156-162 chapter, but a deterministic metadata lookup
    (`diagnostics/fc_heartline_corpus_S68.md`) found p.157-158 have ZERO
    chunks (a chunking-pipeline gap, not a retrieval-tuning one), and
    positive-configuration doctrine that DOES exist (`p159_c2`, `p160_c1`
    -- e.g. "a happy, tranquil nature, good fortune, and happiness in
    affection") never ranked in this feature's embedding retrieval
    across the S68 probe's runs; `p159_c2`'s "...reaching the base of
    the first\\nfinger" line-wrap also defeats a literal substring check
    for that doctrine, independent of ranking. Non-harmful under A1: a
    chunk that never gets retrieved can never be cited, so the model
    falls back to `[OBS]`-tagged observation for this feature rather
    than fabricating a citation -- this gap is a coverage LOSS (thinner
    heart-line interpretation), not a grounding-safety risk. V1.1
    candidate fix: corpus re-ingestion/chunk-repair (see CLAUDE.md's
    V1.1 register) -- not attempted here (diagnostics-only probe, no
    production code touched)."""
    texts_by_feature = _gather_feature_texts(left_fields, right_fields, hd_fields)
    results: dict[str, list[dict]] = {}
    failed: list[str] = []
    for feature in _FEATURE_REGISTRY:
        quality = _resolve_feature_quality(feature, texts_by_feature[feature])
        if quality is None:
            results[feature] = []
            continue
        query = _build_feature_query(feature, quality)
        try:
            results[feature] = search(
                query, n_results=_N_RESULTS_PER_FEATURE, book_name=_CHEIRO_BOOK
            )
        except Exception as exc:  # noqa: BLE001 -- one bad query must not kill the reading
            logger.warning(
                "palm_reading._retrieve_per_feature: search failed for "
                "feature=%r: %s", feature, exc,
            )
            failed.append(feature)
            results[feature] = []
    return results, failed
```
Constants referenced: `_N_RESULTS_PER_FEATURE = 3` (`palm_reading.py:176`), `_CHEIRO_BOOK = "cheiroslanguageo00chei_1"` (`palm_reading.py:166`).

**d. Live chunk_id schema vs. `CHUNK_ANCHOR_TAG_PATTERN`:**

`CHUNK_ANCHOR_TAG_PATTERN = re.compile(r"\[(?:OBS|[A-Za-z0-9_]+_p\d+_c\d+)\]")` (`agent/interpretive/palm_reading.py:883`).

Live schema, confirmed two ways: (1) construction-site tracing — `ingestion/pdf_processor.py:145`: `chunk_id = f"{book_name}_p{page_num}{side}"` (`side` is `"L"`/`"R"`/`""`, only non-empty when `process_pdf(..., split_spreads=True)`; grepped every call site — `ingestion/run_single_book.py:87`, `ingestion/chunker.py:218`, `ingestion/pdf_processor.py:226,247`, `ingestion/image_extractor.py:178` — none passes `split_spreads=True`, so `side` is always `""` in practice), then `ingestion/chunker.py:145`: `"chunk_id": f"{parent['chunk_id']}_c{i}"` — final shape `{book_name}_p{page_num}_c{i}`. (2) live verification — a read-only `collection.get()` probe (see PROBE SCRIPTS section) pulled all 463 live `cheiroslanguageo00chei_1` chunk_ids and checked each against the exact pattern: **0 of 463 fail to match** (sample: `'cheiroslanguageo00chei_1_p100_c0'`, `'cheiroslanguageo00chei_1_p105_c2'`, etc.). The pattern's `[A-Za-z0-9_]+_p\d+_c\d+` shape would NOT match an id containing an `L`/`R` side-letter between page number and `_c` (e.g. `..._p87L_c0` breaks the regex, verified by hand-tracing the greedy-backtrack behavior) — but since `split_spreads` is never `True` in this codebase, that edge case is theoretical, not live.

---

### Q3 — CHEIRO SOURCE + CORPUS CENSUS

**a. Source PDF present?**

Yes. `data/pdfs/cheiroslanguageo00chei_1.pdf`, size **16,183,952 bytes** (~16.18 MB), confirmed via `ls -la` (`-rw-r--r-- 1 Sulabh Chauhan 197121 16183952 May 24 10:18 data/pdfs/cheiroslanguageo00chei_1.pdf`).

**b. pdfplumber per-page char count (whole PDF):**

310 pages total (pdfplumber's own page count). Full page→char_count table is large (310 rows) — captured via the throwaway probe (see PROBE SCRIPTS section) and not reproduced in full here to keep this report navigable; the complete captured output was reviewed line-by-line during this investigation. Summary: **123 of 310 pages have char_count < 100** (candidate scanned/OCR-needed pages), including 0-char pages. Representative sample of the < 100 list: pages 1, 4, 5, 6, 10, 18, 22, 46, 49, 50(16), 53(37), 54, 59(41), 60, 63(42), 64, 67, 68(37), 73, 74, 77, 78(26), 79(1), 80, 83, 84(64), 91, 92(82), 101(17), 102, 103, 104(21), 109, 110(33), 121(34), 122, 126, 131, 132(10), 142, 143, 144(11), **157(12), 158(0)**, 167(48), 168(2), 175(9), 176, 185, 186(47), 195, 196(10), 211(38), 212, and then a long, near-alternating run from 233-298 (illustration-plate pages, mostly 0 or under 100 chars each), plus 301, 302, 307, 308, 309, 310.

**c. Live ChromaDB census — page → chunk_count:**

Total chunks for `book_name='cheiroslanguageo00chei_1'`: **463**, across **181 distinct pages** (of 310 total PDF pages). **129 pages have ZERO live chunks**: `2, 3, 4, 5, 6, 8, 9, 10, 18, 19, 22, 46, 49, 50, 53, 54, 59, 60, 63, 64, 67, 68, 73, 74, 77, 78, 79, 80, 83, 84, 91, 92, 102, 103, 104, 109, 110, 122, 126, 131, 132, 142, 143, 144, 157, 158, 167, 168, 175, 176, 185, 186, 191, 195, 196, 211, 212, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 301, 302, 307, 308, 309, 310`. (Computed as the set difference between all 310 pages and the 181 that appear in the live per-page chunk-count table — every page not listed in the table has exactly zero chunks.)

**d. p.157-158 cross-tab — text layer empty, or chunker/filter problem?**

**Text layer is empty at the PDF level — this is an ingest INPUT problem, not a chunker/filter bug.** Evidence, both from pdfplumber (the PDF's own embedded/native text layer, independent of this project's Tesseract OCR pipeline) and from the live collection:
- pdfplumber: p.157 = **12 chars**, p.158 = **0 chars**.
- Live ChromaDB: p.157 = **0 chunks**, p.158 = **0 chunks**.
- Full ingestion-pipeline trace (read directly from the persisted pipeline artifacts, no probe needed): `data/progress/cheiroslanguageo00chei_1.json` shows both pages entered `pdf_processor.py`'s OCR stage already empty — `page_type: "diagram"`, `text` = `""` for both (this is `classify_page`'s `MIN_TEXT_WORDS = 50` threshold firing, `ingestion/pdf_processor.py:27,54-55` — Tesseract OCR itself returned fewer than 50 words for both pages, consistent with pdfplumber's own near-zero native-text-layer reading). `data/all_chunks.json` (post `image_extractor.extract_diagram_text`, the GPT-4o-vision diagram-fill stage) shows text is STILL `""` for both pages after that stage ran — meaning GPT-4o vision either was never actually invoked for these two images or returned nothing usable, and this is NOT an isolated p.157/158 issue: `data/processed_chunks.json` (the `image_extractor` idempotency log) contains **zero entries for `cheiroslanguageo00chei_1`** at all (0 of 62 total logged ids belong to this book), and a full per-book scan of `data/all_chunks.json` shows **all 127 `page_type="diagram"` pages AND all 5 `page_type="mixed"` pages for this book have `nonempty_text == 0`** — i.e., GPT-4o vision fill never succeeded for a single diagram/mixed page in this entire book's ingestion run, not just p.157/158. `data/chunked_chunks.json` confirms both pages' sub-chunks (`..._p157_c0`, `..._p158_c0`) still carry empty text after `chunker.py`'s pass-through (`ingestion/chunker.py:169-170`, the "diagram + no text → pass through unchanged" branch). `data/pending_chunks.json` confirms both chunk_ids landed in the "pending" (never-embedded) bucket — `ingestion/embedder.py:88-92`: `embedding_status = "complete" if chunk.get("text","").strip() else "pending"`, and only `embeddable` (complete) chunks are ever sent to OpenAI/ChromaDB (`ingestion/embedder.py:91-92`).
- A separate, book-wide finding surfaced by this same trace, outside p.157/158 specifically: `ingestion/image_extractor.py:131-134`'s `diagram_chunks` filter selects ONLY `page_type == "diagram"`, never `"mixed"` — so the 5 `"mixed"`-classified pages for this book can never receive a GPT-4o vision fill at all, by construction, regardless of whether `image_extractor` ran successfully otherwise; combined with `ingestion/pdf_processor.py:158-169`'s else-branch setting `text=""` for both `"diagram"` AND `"mixed"` types (discarding the raw OCR text pdf_processor itself already read for a "mixed" page), `"mixed"` pages are structurally guaranteed to reach the chunker with empty text.

**e. Ingestion script — chunking parameters, filters, whitespace normalization:**

Script: `ingestion/run_single_book.py` (stages: `pdf_processor` (OCR) → `image_extractor` (GPT-4o vision on diagram pages) → `chunker` → `embedder`; `ingestion/chunker.py` and `ingestion/pdf_processor.py` hold the actual parameters).

Chunking parameters (`ingestion/chunker.py:17-23`):
```python
MERGE_MIN_WORDS = 100
SPLIT_THRESHOLD = 500
WINDOW_SIZE = 400
WINDOW_OVERLAP = 50
LANGDETECT_MIN_WORDS = 30
DEVANAGARI_HIN_THRESHOLD = 0.25
```
Page classification threshold (`ingestion/pdf_processor.py:27`): `MIN_TEXT_WORDS = 50` — pages with fewer OCR'd words are classified `"diagram"` outright (`ingestion/pdf_processor.py:54-55`), before any of the numeric-density/planetary-keyword/structural/illustration heuristics run.

Filter/drop conditions: `ingestion/chunker.py:185-186` — `if not paragraphs: return []` (a page whose OCR text, after Devanagari-stripping and paragraph-splitting, yields zero paragraphs produces **zero output chunks** — this is the only hard "drop" condition in the chunker itself). Separately, `ingestion/embedder.py:88-92` is a POST-chunking filter: any chunk whose `text` is empty/whitespace-only is marked `"pending"` and excluded from embedding entirely (never reaches ChromaDB) — this is the filter that actually determines p.157/158's zero-chunk outcome, not `chunker.py`'s own paragraph-split logic (which does still emit one pass-through chunk for a "diagram, no text" page, per Q3d above — it's `embedder.py` that then drops it).

Whitespace normalization: **`strip_devanagari()`** (`ingestion/chunker.py:60-76`) does line-level stripping/joining (`"\n".join(cleaned_lines).strip()`) as a side effect of removing Devanagari lines, but there is **no general-purpose whitespace-collapse step** (no `re.sub(r"\s+", " ", ...)` or equivalent) anywhere in `ingestion/chunker.py` or `ingestion/pdf_processor.py` — confirmed by grep (`whitespace|normalize|re\.sub|\.strip\(\)` in `pdf_processor.py` returns only the single `text.strip()` at `pdf_processor.py:107`, inside `ocr_image()`, which only trims leading/trailing whitespace from the whole OCR'd page, not internal whitespace). This absence is directly relevant to the already-documented `p159_c2` line-wrap defeating literal substring matching (CLAUDE.md's accepted-gap register, item (c)) — the module's own docstring already flags this at `palm_reading.py:467-468`.

---

### Q4 — IMAGE FIXTURES + PREPROCESSING

**a. Palm images retained anywhere in the tree?**

**Yes — three real palm/hand photo files, tracked in git, not gitignored:**
```
data/test_images/palm_left_test.jpg   (127,074 bytes)
data/test_images/palm_right_test.jpg  (104,223 bytes)
data/test_images/Back Hand.jpeg       (107,428 bytes)
```
`git ls-files data/test_images/` confirms all three are tracked (not ignored — grepped `.gitignore` for `test_images|\.jpg|\.jpeg|\.png`, zero matches, so nothing in `.gitignore` excludes this directory). Referenced directly by `tests/test_palm_endtoend.py:20-23`:
```python
_LEFT_PATH   = _ROOT / "data" / "test_images" / "palm_left_test.jpg"
_RIGHT_PATH  = _ROOT / "data" / "test_images" / "palm_right_test.jpg"
_LEFT_BYTES  = _LEFT_PATH.read_bytes()
_RIGHT_BYTES = _RIGHT_PATH.read_bytes()
```
(Module-level reads — `test_duplicate_detection`, `test_prompt_assembly` use the deterministic parts; a 4th, real-GPT-call test in the same file uses the bytes for an actual vision call, per the file's own docstring "Test 4 makes real GPT-4o vision calls".) `"Back Hand.jpeg"` is referenced by five diagnostic probe scripts (`scripts/probe_pass3_preflight.py`, `probe_pass4_preflight.py`, `probe_pass5_preflight.py`, `probe_r1_retrieval.py`) and `SESSION_LOG.md`, as the HAND_DETAIL fixture image for Ring 3 preflight probes — not referenced by any `tests/` pytest file directly. Every other palm-related test file (`test_palm_quality.py`, `test_context_classifier_fallback.py`, `test_context_integration.py`, `test_prompt_builder.py`, `test_nudge_endtoend.py`, `tests/interpretive/test_palm_reading.py`) uses synthetic TEXT fixtures (plain strings describing a palm), never real image bytes — confirmed by grep for `image_bytes|\.jpg|\.jpeg|\.png|Image\.new|Image\.open|BytesIO` across `tests/`, which returned matches only in `test_palm_endtoend.py`.

**b. Image preprocessing today?**

**None.** Grepped `agent/` (case-insensitive) for `ImageEnhance|CLAHE|cv2|\.resize\(|\.rotate\(|contrast|autocontrast` — zero hits for actual image-processing code (the only "contrast" hits are unrelated prose comments in `golden_harness.py`/`chart_profile.py`/`muhurta_scorer.py` using the English word "contrast", not `ImageEnhance.Contrast`). This matches CLAUDE.md's own V1.1 register entry: "contrast preprocessing before vision-model description" is listed as a NOT-YET-DONE V1.1 candidate (Ring 3 pass-2 finding), confirming this gap is already known, not newly discovered.

**c. Upload path formats/size limits; raw bytes to disk?**

Formats accepted: `st.file_uploader(..., type=["jpg", "jpeg", "png"])` — three call sites in `frontend/app.py:611-613` (left palm), `:786-787` (right palm), `:981-983` (hand_detail). No `.streamlit/config.toml` exists in the repo (confirmed — `find .streamlit` returns nothing), so Streamlit's unconfigured default `maxUploadSize` (200 MB) applies; no project-specific size limit is enforced.

Raw bytes never touch disk. Traced the left-palm path (`frontend/app.py:614-644`, representative of all three uploaders): `_lb = uploaded_left.read()` (`:616`) reads into an in-memory `bytes` object; `hashlib.md5(_lb)` computes a hash for dedup; `validate_palm_image(_lb, "left")` (`:621`) is called directly on the in-memory bytes; on success, `st.session_state.palm_left_bytes = _lb` (`:643`) stores the bytes in Streamlit's in-memory session state. Grepped `frontend/app.py` for `getvalue\(\)|\.save\(|open\(.*['"]wb|tempfile|NamedTemporaryFile` — zero hits (the one `.save(` mention in the whole file is `st.session_state.session_mgr.save()` at `:1268`, unrelated session-data persistence, not image bytes). Confirms the no-storage lock (CLAUDE.md's S66 F5 dogfood-capture note: "derived text ONLY... image bytes, image hashes... deliberately EXCLUDED") holds for the live upload path as currently written.

---

### Q5 — LABELED-PAIR INVENTORY (counts only, not judged)

**a. `diagnostics/dogfood_capture.md`:** **6 `## RUN` blocks** (timestamps `2026-07-27T14:57:44`, `2026-07-27T15:04:44`, `2026-07-27T15:07:04`, `2026-07-28T14:25:11`, `2026-07-29T10:21:07`, `2026-07-29T11:02:48`), **35 `claims_inventory` rows total** (counted via `grep -cE "^C[0-9]+ \| "`).

**b. Ring 3 rubric artifacts, passes 3/4/5, U/C/D row counts per artifact:**

These three files use two visibly different table conventions (pass 3 uses a 4-column `# | Clause | Verdict | Evidence` layout with some SPLIT-verdict and non-ledger "no claim"/decline-block rows; pass 4/5 use a cleaner `# | Clause | Anchor | Verified?` layout). Counts below are exact per the format each file actually uses — reported as measured, with the ambiguous rows flagged rather than silently forced into one bucket (per this task's "count, do not judge" instruction).

- **`diagnostics/ring3_palm_rubric_S67_pass3.md`** (Run A/B/C, 3 runs):
  - Run A (14 rows): D=5, U=3, C=4, **1 SPLIT row** (row 13: C+U in one row), **1 non-U/C/D row** (row 14, "Jupiter decline block" — scored "P4-clean", a coverage-accuracy check, not a claim verdict).
  - Run B (14 rows): D=4, U=2, C=4 (+1 unlabeled continuation row, row 8, sharing row 7's citation with no independent verdict marker), **1 SPLIT row** (row 12: D-frame+C), **2 non-U/C/D rows** (row 3 "no claim"/silent-clause-drop, row 14 decline-block "P4-clean").
  - Run C (16 rows): D=6, U=4, C=2 (+1 unlabeled continuation row, row 8), **1 SPLIT row** (row 14: D-frame+C), **2 non-U/C/D rows** (row 5 "no claim", row 16 decline-block — this one scored "P4 FAIL", the file's primary pre-registered finding).

- **`diagnostics/ring3_palm_rubric_S68_pass4.md`** (Run A/B/C, 3 runs, cleaner single-letter-verdict format including a `1a`/`1b` split for the hand-shape row):
  - Run A (17 rows, incl. 1a/1b): D=1, U=11, C=5.
  - Run B (18 rows, incl. 1a/1b): D=2, D-frame=2, U=10, C=4.
  - Run C (18 rows, incl. 1a/1b): D=2, U=10, C=6.
  - Pass-4 grand total: D=5, D-frame=2, U=31, C=15 (53 rows).

- **`diagnostics/ring3_palm_rubric_S70_pass5.md`** (Run A ONLY — Run B/C explicitly not scored, per the file's own "Run plan" section): 10 rows — D=2, D-frame=2, **U=3** (rows 3, 5, 10), **C=3** (rows 2, 6, 8). Matches CLAUDE.md's own Locked-Decisions prose exactly ("3 U-rows total... 3 C-rows, 4 D/D-frame rows").

**c. `scripts/probe_neutral_chunk_valence.py`'s 25-candidate-chunk output — persisted anywhere?**

The **script** exists (`scripts/probe_neutral_chunk_valence.py`). Its **output** (the actual 25 candidate chunk_ids) is **NOT persisted as a durable artifact anywhere** — grepped the whole repo for `25 candidate|probe_neutral_chunk_valence`, only 3 files matched: the script itself, `CLAUDE.md`, and `SESSION_LOG.md` — and `SESSION_LOG.md:4424-4428` explicitly states the scan was run as `"Phase 1, no commit"`, only its SUMMARY (the count "25" and the separate `p139_c0` finding) survives in prose; no `diagnostics/*.md` file holds the actual chunk_id list.

---

### Q6 — GROUNDING GATE SOURCE

Full dump of `agent/interpretive/claim_extraction.py` (578 lines) — E-1 through E-4, the stopword set, and `_PARAPHRASE_OVERLAP_FLOOR` with its surrounding comment, all included, verbatim, unabridged:

```python
"""
agent/interpretive/claim_extraction.py
S69 F-H Stage 1 -- per-feature claim extraction directly from gated chunks.

CITATION: CLAUDE.md S69 queue's F-H entry (two-stage extract-then-voice
redesign, PRIMARY fix-forward for Ring 3 pass 4's architectural grounding
ruling -- single-call generation composes from the model's pretraining
prior first, retrieved doctrine second, making citations decorative).
`diagnostics/fh_stage1_probe_S69.md` is the pre-implementation probe this
module now productionizes: 12-cell matrix (3 frozen pass-4 runs x 2 models
x 2 temperatures) measured against the SAME frozen inputs pass 4 already
scored. Result LOCKED from that probe: model=gpt-4o-mini, temperature=0
(SC-1/2/3/5 PASS in all 12 cells at every model/temp combination tried,
so the cheaper/faster model was not a quality tradeoff here). The probe's
SC-4 finding -- 12/12 cells FAILED to extract a fate-line claim
referencing the rises-from-life-line precondition, because "barely
visible" never confirms where the line rises from -- is NOT treated as a
defect to force past: this module's extractor may legitimately decline a
conditional claim upstream (empty claims list, or E-4 marking a claim
excluded_from_voice), and E-4 below is this module's own deterministic,
Python-owned analog of that same conservatism, not a workaround for it.
ACCEPTED DEVIATION, 3-place registration (CLAUDE.md's own convention):
this module docstring + the E-4 code comment are places 2 and 3; place 1
(the CLAUDE.md Known-Source-Divergences entry itself) is NOT added here --
that is the F-H close-out prompt's job, flagged in this prompt's own
report to diagnostics/latest_run.md, not done silently in this file.

RETIRES accepted gaps (a) (V-2 anchor legality was union-only across all
gated features) and (f) (a chunk gated under two features could get
credit for either) from `palm_reading.py`'s own accepted-gap register --
E-1 below checks legality per-feature, against ONLY the chunk_id set this
module itself offered that feature's extraction call, never a
whole-reading union. This is the module-contract-level fix those two gaps
were deferred pending; the close-out prompt still owns updating
palm_reading.py's own docstring/CLAUDE.md text once wiring lands.

SCOPE: this module knows nothing about palm_reading.py's retrieval,
support-gate, or Ring 1/voice-generation machinery -- it is a pure
extraction stage, callable independently, wired in a LATER prompt. It
does not import palm_reading (avoids a circular import once that wiring
lands: palm_reading.py will need to import THIS module, so the reverse
import must never exist) and does not import agent.infra.calc_router,
agent.infra.orchestrator, or agent.infra.chart_profile, matching the
project's existing upload-triggered-artifact scope lock.
"""

from __future__ import annotations

import itertools
import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI

# ─── LLM call configuration ─────────────────────────────────────────────

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: fh_stage1_probe_S69.md's locked result -- gpt-4o-mini at
# temperature=0 passed SC-1/2/3/5 in every one of the probe's 12 cells,
# identically to gpt-4o's results at the same criteria; no quality
# tradeoff was observed for the cheaper/faster model on this extraction
# task. Scope guard: this module's extraction call site only. Revisit
# trigger: pass-5 evidence that gpt-4o-mini underperforms gpt-4o on a
# metric the probe didn't measure.
_EXTRACTION_MODEL = "gpt-4o-mini"
_EXTRACTION_TEMPERATURE = 0

# Same value as palm_reading._READING_TIMEOUT_SECONDS -- duplicated, NOT
# imported, to avoid a circular import (palm_reading.py will import THIS
# module once wired; this module must never import palm_reading back).
# Re-sync by hand if palm_reading.py's own timeout is ever revisited.
_EXTRACTION_TIMEOUT_SECONDS = 30.0

# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: fh_stage1_probe_S69.md's pooled overlap distribution
# across all 12 cells / 73 extracted claims -- min=0.50, p25=median=p75=
# max=1.00: the overwhelming majority of genuine extractions restate
# their cited chunk almost word-for-word, with the single pooled minimum
# observed at 0.50. UNLIKE the 0.30 support-score floor in palm_reading.py
# (which sits between a measured negative-control ceiling of 0.2192 and a
# measured minimum genuine score of 0.3954), this probe never measured a
# genuinely-fabricated claim's overlap score -- there is no noise ceiling
# to sit above here, only a pooled minimum-observed-GENUINE value to sit
# below. 0.40 sits with a conservative 0.10 margin below that pooled
# minimum -- narrower certainty than the support-gate precedent, and
# explicitly flagged as such, not silently presented as equally proven.
# Scope guard: applies ONLY to a claim_text vs. its own cited chunk's
# text, never cross-chunk. Revisit trigger: pass-5 evidence, or a future
# probe that actually measures fabricated-claim overlap (would let this
# floor graduate to the same two-sided justification the 0.30 floor has).
_PARAPHRASE_OVERLAP_FLOOR = 0.40

_VALID_VALENCE = frozenset({"supports", "corrective", "conditional"})


# ─── Content-word overlap -- transplanted verbatim from ──────────────────
# scripts/probe_fh_stage1_extraction.py's _STOPWORDS / _WORD_PATTERN /
# _content_words / _overlap_ratio (the same probe that measured the
# pooled distribution _PARAPHRASE_OVERLAP_FLOOR is set from) -- same
# method, not re-derived, so the floor and the measurement it was set
# from stay comparable.
_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "of", "in", "on", "at", "to", "for",
    "with", "by", "is", "are", "was", "were", "be", "been", "being", "this",
    "that", "these", "those", "it", "its", "as", "from", "into", "which",
    "who", "whom", "your", "you", "their", "his", "her", "he", "she", "they",
    "not", "no", "than", "then", "so", "such", "if", "when", "while",
    "suggests", "suggest", "indicates", "indicate", "may", "might", "also",
})
_WORD_PATTERN = re.compile(r"[a-z]+")


def _content_words(text: str) -> set[str]:
    return {w for w in _WORD_PATTERN.findall(text.lower()) if w not in _STOPWORDS}


def _overlap_ratio(a: str, b: str) -> float:
    wa, wb = _content_words(a), _content_words(b)
    if not wa or not wb:
        return 0.0
    shared = len(wa & wb)
    return shared / min(len(wa), len(wb))


# ─── Extraction system prompt -- transplanted verbatim from ──────────────
# scripts/probe_fh_stage1_extraction.py's _EXTRACTION_SYSTEM_PROMPT. This
# EXACT text is what fh_stage1_probe_S69.md validated (SC-1/2/3/5 PASS in
# all 12 cells) -- redrafting it here, even lightly, would mean shipping
# an untested prompt under a tested one's name. Do not edit without a new
# probe run.
_EXTRACTION_SYSTEM_PROMPT = """You are a claim-extraction engine for a palmistry RAG pipeline. You are given ONE observed hand feature, its confirmed physical observation(s) from a photographed hand, and a small set of retrieved reference passages ("chunks"), each labeled with a chunk_id.

Your ONLY job: for each provided chunk, decide whether it states doctrine (a meaning or interpretation) that applies to this feature, and if so extract it as a claim.

STRICT RULES:
1. Paraphrase-or-nothing: every claim must restate doctrine LITERALLY PRESENT in exactly ONE of the provided chunks. Never invent doctrine, even if you recall real palmistry teaching from training -- if no provided chunk states it, it does not go in a claim.
2. If a chunk's stated doctrine actually REJECTS or CONTRADICTS the natural inference the confirmed observation would suggest, extract it anyway, with valence="corrective".
3. If a chunk's doctrine only holds under a precondition (e.g. "if the line rises from X..."), use valence="conditional" and populate condition_text with that precondition (verbatim or lightly paraphrased). condition_text must be null for any other valence.
4. Otherwise, if a chunk directly and positively supports the observation, use valence="supports".
5. Never merge two chunks into one claim -- one claim cites exactly one chunk_id.
6. If NONE of the provided chunks state doctrine for this feature, return an empty claims list. Do not force a claim.
7. Discuss only the given feature -- do not reference any other palm feature.

Respond with a single JSON object, no prose outside it, matching exactly:
{"feature": "<given feature name, copied exactly>", "claims": [{"claim_id": "C1", "chunk_id": "<must exactly match a provided chunk_id>", "claim_text": "<paraphrase>", "valence": "supports|corrective|conditional", "condition_text": "<precondition or null>", "observation_basis": "<the confirmed observation clause this claim applies to>"}]}"""


def _build_user_prompt(feature: str, observation_text: str, chunks: list[dict]) -> str:
    obs_block = observation_text.strip() if observation_text and observation_text.strip() else "(none recorded)"
    chunk_block = "\n\n".join(f"[{c['chunk_id']}]\n{c['text']}" for c in chunks)
    return (
        f"FEATURE: {feature}\n\n"
        f"CONFIRMED OBSERVATIONS (from the user's photographed hand(s)):\n- {obs_block}\n\n"
        f"RETRIEVED CHUNKS (use ONLY these -- do not draw on outside knowledge):\n{chunk_block}\n\n"
        f"Extract claims per your instructions."
    )


# E2F step 1: extracts the chunk_id an E-3 (paraphrase-overlap-floor)
# failure names, from the exact message shape _validate_response builds
# at lines 250-252 below (f"...for chunk {chunk_id!r}"). repr() of a str
# quotes with '...' unless the string itself contains a single quote, so
# this pattern assumes the former -- matching every chunk_id this corpus
# actually produces (ingestion-generated, no apostrophes). A failure
# string that doesn't match (E-1/E-2 failures, malformed-JSON, etc.)
# simply contributes no chunk_id to the retry's excluded set.
_E3_CHUNK_ID_PATTERN = re.compile(r"for chunk '([^']+)'$")


# F2c retry correction-instruction pattern, same shape as
# palm_reading.py's own S66 F2c retry ("Your draft failed these checks:
# ...; Rewrite the reading correcting ONLY these issues. Same facts, same
# structure.") -- deterministic-reviewer-only (Python's own E-1/E-2/E-3
# checks below observe the response independently, then hand that
# observation to the model as a correction instruction; this is NOT
# AI-reviewing-AI, CLAUDE.md Working Style #5/#9), same single-retry
# shape, adapted to per-feature extraction instead of whole-reading voice.
#
# E2F step 3a (supersedes step 1's original approach here, which is what
# caused the 2026-07-29 dogfood empty_retry regression): turn 1 (the
# first user message) ALWAYS presents the full, unfiltered `chunks` list
# -- this must match what attempt 1 actually saw, because turn 2 (the
# prior assistant response, echoed back verbatim as `prior_raw`) may
# cite a chunk that would otherwise vanish from turn 1's own presented
# list, producing an incoherent conversation history (turn 2 references
# a chunk turn 1 never showed) that reliably drove the model to decline
# rather than resolve the contradiction. Retry-pool discipline is
# instead enforced ONLY via turn 3's correction instruction, which names
# any E-3-excluded chunk_ids explicitly and tells the model not to cite
# them -- discipline by instruction, not by rewriting history. When
# excluded_chunk_ids is empty (a non-E-3 failure -- E-1/E-2/malformed-
# JSON -- triggered the retry), the OLD "Same chunks, same feature"
# wording stays accurate, since nothing is actually excluded.
def _build_retry_messages(
    feature: str, observation_text: str, chunks: list[dict],
    prior_raw: str, failures: list[str], excluded_chunk_ids: set[str],
) -> list[dict]:
    if excluded_chunk_ids:
        quoted_ids = ", ".join(f"'{cid}'" for cid in sorted(excluded_chunk_ids))
        instruction = (
            "The following chunk(s) failed the overlap check on attempt 1 "
            "and must NOT be cited on this retry: " + quoted_ids + ". "
            "Cite only from the remaining chunks in the list above."
        )
    else:
        instruction = "Same chunks, same feature."
    return [
        {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(feature, observation_text, chunks)},
        {"role": "assistant", "content": prior_raw},
        {
            "role": "user",
            "content": (
                "Your extraction failed these checks: " + "; ".join(failures) + ". "
                "Re-extract claims for this feature, correcting ONLY these issues. "
                + instruction
            ),
        },
    ]


def _call_llm(client, messages: list[dict]) -> str:
    """Single try/except boundary around one API call. Raises the
    underlying exception to the caller, which owns retry/fail-closed
    decisions -- this function never swallows errors itself."""
    response = client.chat.completions.create(
        model=_EXTRACTION_MODEL,
        messages=messages,
        temperature=_EXTRACTION_TEMPERATURE,
        timeout=_EXTRACTION_TIMEOUT_SECONDS,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


# ─── Deterministic validators (E-1/E-2/E-3) ──────────────────────────────

_REQUIRED_CLAIM_KEYS = frozenset({"chunk_id", "claim_text", "valence", "condition_text", "observation_basis"})


def _validate_response(raw: str, chunk_map: dict[str, str]) -> tuple[list[dict] | None, list[str]]:
    """Returns (accepted_raw_claims, failures). accepted_raw_claims is None
    iff failures is non-empty -- an ALL-OR-NOTHING result per feature call
    (any single claim's E-1/E-2/E-3 violation rejects the whole response,
    matching palm_reading.py's own F2c precedent of retrying the whole
    draft, never patching individual sentences)."""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, [f"malformed JSON response: {exc}"]

    if not isinstance(parsed, dict) or "claims" not in parsed or not isinstance(parsed["claims"], list):
        return None, ["response missing a top-level 'claims' list"]

    failures: list[str] = []
    accepted: list[dict] = []
    for i, raw_claim in enumerate(parsed["claims"]):
        if not isinstance(raw_claim, dict):
            failures.append(f"claims[{i}] is not an object")
            continue
        # E-2 schema: required fields present, valence in the allowed set.
        # claim_id is deliberately NOT required here -- this module always
        # re-keys with its own counter (see extract_claims), never trusting
        # a model-emitted id for uniqueness, so an absent/duplicate
        # model-side claim_id can never itself be a validation failure.
        missing = _REQUIRED_CLAIM_KEYS - set(raw_claim)
        if missing:
            failures.append(f"claims[{i}] missing keys: {sorted(missing)}")
            continue
        if raw_claim["valence"] not in _VALID_VALENCE:
            failures.append(f"claims[{i}] invalid valence: {raw_claim['valence']!r}")
            continue
        # E-1 legality: chunk_id must belong to THIS feature's OWN gated
        # set (never a whole-reading union) -- retires accepted gaps (a)
        # and (f) from palm_reading.py's V-2 anchor-legality register.
        chunk_id = raw_claim["chunk_id"]
        if chunk_id not in chunk_map:
            failures.append(f"claims[{i}] cites chunk_id {chunk_id!r}, not in this feature's own gated set")
            continue
        # E-3 paraphrase floor.
        overlap = _overlap_ratio(raw_claim["claim_text"], chunk_map[chunk_id])
        if overlap < _PARAPHRASE_OVERLAP_FLOOR:
            failures.append(
                f"claims[{i}] claim_text overlap {overlap:.2f} below floor "
                f"{_PARAPHRASE_OVERLAP_FLOOR} for chunk {chunk_id!r}"
            )
            continue
        accepted.append({**raw_claim, "_overlap": overlap})

    if failures:
        return None, failures
    return accepted, []


# ─── Dataclasses ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class Claim:
    claim_id: str
    feature: str
    chunk_id: str
    claim_text: str
    valence: str
    condition_text: str | None
    observation_basis: str
    excluded_from_voice: bool
    exclusion_reason: str | None


@dataclass(frozen=True)
class ExtractionResult:
    claims: tuple[Claim, ...]
    failed_features: tuple[str, ...]
    diagnostics: dict = field(default_factory=dict)


# ─── E-4: conditional fail-closed ────────────────────────────────────────

_UNVERIFIED_PRECONDITION_REASON = "precondition unverified"


def _apply_e4(
    accepted_raw_claims: list[dict], feature: str, observation_text: str, counter: itertools.count,
) -> tuple[list[Claim], list[dict]]:
    """E-4: valence=conditional OR a populated condition_text (checked
    together, regardless of valence label -- a "supports"/"corrective"
    claim that nonetheless carries a non-null condition_text is treated
    with the SAME suspicion as an explicitly conditional one, since rule 3
    of the system prompt already asks the model to keep condition_text
    null for any other valence; a populated one there is either a real
    unstated precondition or a prompt-compliance slip, and this module
    fails closed on either) -> excluded_from_voice=True,
    exclusion_reason="precondition unverified", UNLESS condition_text is a
    case-insensitive substring of this feature's own confirmed observation
    text. Exact-substring only, no fuzzy matching -- coarse by design;
    direction of error is omission (a real match phrased differently is
    missed and the claim stays excluded), never a false verification."""
    claims: list[Claim] = []
    exclusion_ledger: list[dict] = []
    obs_lower = (observation_text or "").lower()

    for raw_claim in accepted_raw_claims:
        claim_id = f"C{next(counter)}"
        condition_text = raw_claim.get("condition_text")
        valence = raw_claim["valence"]

        excluded = False
        reason = None
        if valence == "conditional" or condition_text is not None:
            if condition_text and condition_text.lower() in obs_lower:
                excluded = False
            else:
                excluded = True
                reason = _UNVERIFIED_PRECONDITION_REASON

        claim = Claim(
            claim_id=claim_id,
            feature=feature,
            chunk_id=raw_claim["chunk_id"],
            claim_text=raw_claim["claim_text"],
            valence=valence,
            condition_text=condition_text,
            observation_basis=raw_claim.get("observation_basis", ""),
            excluded_from_voice=excluded,
            exclusion_reason=reason,
        )
        claims.append(claim)
        if excluded:
            exclusion_ledger.append({
                "claim_id": claim_id, "feature": feature, "chunk_id": claim.chunk_id,
                "reason": reason, "condition_text": condition_text,
            })

    return claims, exclusion_ledger


# ─── Public API ─────────────────────────────────────────────────────────


def extract_claims(
    gated_results: dict[str, list[dict]],
    texts_by_feature: dict[str, str],
    client=None,
) -> ExtractionResult:
    """One extraction call per feature present in `gated_results` with a
    non-empty chunk list (a feature with zero gated chunks is skipped
    entirely -- nothing to extract from, not a failure). Same
    `gated_results` shape palm_reading._apply_support_gate emits: dict
    mapping feature name -> list of chunk dicts (each with at least
    chunk_id/text keys; extra keys like score/page_ref are ignored here).

    F2c semantics, per feature (not per stage): an E-1/E-2/E-3 validation
    failure on a feature's response triggers exactly ONE retry for THAT
    feature only, with the failure list fed back as a correction
    instruction (same pattern as palm_reading.py's own S66 F2c retry).
    Hard cap: 2 LLM calls per feature, no exceptions. A feature whose
    retry ALSO fails validation lands in `failed_features` -- fail-closed:
    zero claims from it survive, and it is the caller's job (a later
    wiring prompt) to treat it as unsupported downstream.

    client: injection seam for tests -- if None, a real OpenAI() client is
    constructed lazily INSIDE this function (never at module import time;
    palm_reading.py's own S65 flag (b) documents the conftest-stubbing
    breakage a module-level import causes, not repeated here).

    Raises:
        RuntimeError: every feature that had gated chunks failed
                      extraction (both calls each) -- nothing extractable
                      at all, matching the Stage-1 fail-closed ruling (no
                      reading is possible from zero surviving claims). A
                      `gated_results` with NO feature having any gated
                      chunks (e.g. every feature declined) is NOT this
                      case -- that returns an empty, non-raising
                      ExtractionResult, since there was nothing to attempt
                      in the first place.
    """
    if client is None:
        from openai import OpenAI  # lazy import -- see docstring
        client = OpenAI()

    counter = itertools.count(1)
    all_claims: list[Claim] = []
    failed_features: list[str] = []
    exclusion_ledger: list[dict] = []
    feature_diagnostics: dict[str, dict] = {}

    # If this is empty (every feature's gated chunk list is empty), the
    # loop below never runs and this function returns an empty, non-
    # raising ExtractionResult -- no LLM call at all. Downstream, this is
    # the root of palm_reading.py's own NOTED BEHAVIOR CHANGE (S69 F-H
    # close-out, CLAUDE.md): the old single-call architecture still made
    # one low-confidence LLM call here; this one makes zero.
    attempted_features = [f for f, chunks in gated_results.items() if chunks]

    for feature in attempted_features:
        chunks = gated_results[feature]
        chunk_map = {c["chunk_id"]: c["text"] for c in chunks}
        observation_text = texts_by_feature.get(feature, "") or ""
        # diag enum reference (no prior enum listing existed in this module
        # before E2F step 1 -- added here as the closest diag-initialization
        # anchor point):
        #   attempt_1_status / attempt_2_status: "not_attempted", "error",
        #     "validation_failed", "validated", "validated_empty",
        #     "skipped_no_viable_chunks" (E2F step 1, new).
        #   final_outcome: "failed_first_no_retry", "failed_both",
        #     "success_first", "success_retry", "empty_first", "empty_retry",
        #     "failed_first_no_viable_retry" (E2F step 1, new).
        # No runtime validation enforces these as a closed set.
        diag: dict = {
            "call_count": 0, "retry_used": False,
            "attempt_2_status": "not_attempted", "attempt_2_claim_count": None,
        }

        diag["call_count"] += 1
        try:
            raw = _call_llm(client, [
                {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(feature, observation_text, chunks)},
            ])
        except Exception as exc:  # noqa: BLE001 -- one bad call must not crash extract_claims
            failed_features.append(feature)
            diag["status"] = "failed"
            diag["error"] = f"claim_extraction: API call failed for feature {feature!r}: {exc}"
            diag["attempt_1_status"] = "error"
            diag["attempt_1_claim_count"] = 0
            diag["final_outcome"] = "failed_first_no_retry"
            feature_diagnostics[feature] = diag
            continue

        accepted, failures = _validate_response(raw, chunk_map)

        if failures:
            diag["attempt_1_status"] = "validation_failed"
            diag["attempt_1_claim_count"] = 0
        elif accepted:
            diag["attempt_1_status"] = "validated"
            diag["attempt_1_claim_count"] = len(accepted)
        else:
            diag["attempt_1_status"] = "validated_empty"
            diag["attempt_1_claim_count"] = 0

        if failures:
            diag["first_attempt_failures"] = tuple(failures)
            # E2F step 1: drop any chunk an E-3 failure already named from
            # the retry's own pool -- the root cause this step fixes is the
            # retry being told "same chunks" and re-attempting a claim
            # against the SAME chunk it just failed the overlap floor on
            # (Run 2 evidence: p.88_c0 attempt 1 overlap 0.08, attempt 2
            # still against p.88_c0, overlap 0.20, still below floor, while
            # a validatable chunk sat unused at rank 2). Non-E-3 failures
            # (E-1/E-2/malformed-JSON) contribute no chunk_id here, so the
            # pool is unchanged for those -- matches _E3_CHUNK_ID_PATTERN's
            # own module comment.
            excluded_chunk_ids = {
                match.group(1)
                for f in failures
                if (match := _E3_CHUNK_ID_PATTERN.search(f))
            }
            remaining_chunks = [c for c in chunks if c["chunk_id"] not in excluded_chunk_ids]
            if not remaining_chunks:
                # Every attempt-1 chunk failed E-3 -- no viable chunk left
                # to retry against. Retrying here would only repeat Run 2's
                # exact failure mode (re-attempting against a chunk already
                # known to fail the overlap floor), so the retry call is
                # skipped entirely rather than burning a second LLM call on
                # a pool that cannot pass.
                diag["retry_used"] = False
                diag["attempt_2_status"] = "skipped_no_viable_chunks"
                diag["attempt_2_claim_count"] = None
                diag["final_outcome"] = "failed_first_no_viable_retry"
                diag["status"] = "failed"
                failed_features.append(feature)
                feature_diagnostics[feature] = diag
                continue
            diag["retry_used"] = True
            diag["call_count"] += 1
            try:
                raw = _call_llm(client, _build_retry_messages(
                    feature, observation_text, chunks, raw, failures, excluded_chunk_ids
                ))
            except Exception as exc:  # noqa: BLE001
                failed_features.append(feature)
                diag["status"] = "failed"
                diag["error"] = f"claim_extraction: API retry failed for feature {feature!r}: {exc}"
                diag["first_attempt_failures"] = failures
                diag["attempt_2_status"] = "error"
                diag["attempt_2_claim_count"] = None
                diag["final_outcome"] = "failed_both"
                feature_diagnostics[feature] = diag
                continue
            accepted, failures = _validate_response(raw, chunk_map)

        if failures:
            failed_features.append(feature)
            diag["status"] = "failed"
            diag["failures"] = failures
            diag["attempt_2_status"] = "validation_failed"
            diag["attempt_2_claim_count"] = 0
            diag["final_outcome"] = "failed_both"
            feature_diagnostics[feature] = diag
            continue

        if diag["retry_used"]:
            diag["attempt_2_status"] = "validated" if accepted else "validated_empty"
            diag["attempt_2_claim_count"] = len(accepted)
            diag["final_outcome"] = "success_retry" if accepted else "empty_retry"
        else:
            diag["final_outcome"] = "success_first" if accepted else "empty_first"

        claims, this_exclusion_ledger = _apply_e4(accepted, feature, observation_text, counter)
        all_claims.extend(claims)
        exclusion_ledger.extend(this_exclusion_ledger)
        diag["status"] = "ok"
        diag["claim_count"] = len(claims)
        diag["overlap_scores"] = [
            {"claim_id": c.claim_id, "chunk_id": c.chunk_id, "overlap": round(a["_overlap"], 3)}
            for c, a in zip(claims, accepted)
        ]
        feature_diagnostics[feature] = diag

    if attempted_features and len(failed_features) == len(attempted_features):
        raise RuntimeError(
            "claim_extraction.extract_claims: all "
            f"{len(attempted_features)} attempted feature(s) failed extraction "
            f"({sorted(failed_features)}) -- nothing extractable, no reading possible."
        )

    diagnostics = {"features": feature_diagnostics, "exclusion_ledger": exclusion_ledger}

    return ExtractionResult(
        claims=tuple(all_claims),
        failed_features=tuple(failed_features),
        diagnostics=diagnostics,
    )
```

---

### Q7 — ABSENCE / LOW-VISIBILITY HANDLING TODAY

`_ABSENCE_PHRASES` (TIER 1, `agent/interpretive/palm_reading.py:218-224`), verbatim:
```python
_ABSENCE_PHRASES: tuple[re.Pattern, ...] = tuple(
    re.compile(re.escape(phrase), re.IGNORECASE)
    for phrase in (
        "not clearly visible", "no clear marks", "unremarkable",
        "not observed", "not visible", "none",
    )
)
```

`_ABSENCE_PATTERNS_BY_FEATURE` (TIER 2, `agent/interpretive/palm_reading.py:596-619`), verbatim, including its noun-source dict and pattern builder:
```python
_SUPPORT_NEEDLES: dict[str, tuple[str, ...]] = {
    "life line": ("life",),
    "head line": ("head",),
    "heart line": ("heart",),
    "fate line": ("fate",),
    "sun line": ("sun",),
    "thumb": ("thumb",),
    "fingers": ("finger",),
    "mount of venus": ("venus",),
    "mount of jupiter": ("jupiter",),
    "markings/other features": (
        "mark", "star", "cross", "island", "square", "circle", "hair",
    ),
}

_ABSENCE_NOUN_EXTRAS: dict[str, tuple[str, ...]] = {
    "markings/other features": ("marking",),
}


def _build_absence_noun_pattern(needles: tuple[str, ...]) -> re.Pattern:
    noun_alt = "|".join(re.escape(n) for n in needles)
    return re.compile(
        rf"\bno\b(?:[,;]?\s+\w+){{0,3}}[,;]?\s+(?:{noun_alt})s?\b[,;]?"
        rf"(?:[,;]?\s+\w+){{0,6}}\s+visible\b",
        re.IGNORECASE,
    )


_ABSENCE_PATTERNS_BY_FEATURE: dict[str, re.Pattern] = {
    feature: _build_absence_noun_pattern(needles + _ABSENCE_NOUN_EXTRAS.get(feature, ()))
    for feature, needles in _SUPPORT_NEEDLES.items()
}
```

**Every call site consuming them:**
- `_is_absence(text: str, feature: str | None = None) -> bool` (`palm_reading.py:298-311`) — the sole function that reads either constant:
```python
def _is_absence(text: str, feature: str | None = None) -> bool:
    if any(p.search(text) for p in _ABSENCE_PHRASES):
        return True
    if feature is not None:
        pattern = _ABSENCE_PATTERNS_BY_FEATURE.get(feature)
        if pattern is not None and pattern.search(text):
            return True
    return False
```
- Call site 1: `_resolve_feature_quality` (`palm_reading.py:414`): `non_absent = [t for t in raw_texts if not _is_absence(t, feature)]` — filters which raw per-hand/HAND_DETAIL texts are treated as "genuinely observed" vs. absence-phrased, before quality-string extraction and query-building.
- Call site 2: `_is_genuine_negative_absence` (`palm_reading.py:664-678`): `return all(_is_absence(t, feature) for t in raw_texts)` — used by `_apply_support_gate` to distinguish "every source confirms this feature is genuinely absent" (no decline needed) from "feature was never mentioned at all" (goes to the decline block).

**What happens end-to-end today when a feature's observation is "Barely visible":**

`"Barely visible"` is caught by **neither** tier. TIER 1 is a fixed substring list (`"not clearly visible"`, `"no clear marks"`, `"unremarkable"`, `"not observed"`, `"not visible"`, `"none"`) — `"barely visible"` shares the word "visible" but not any of these full substrings. TIER 2 requires the shape `"no" + ... + <feature-noun> + ... + "visible"` — `"Barely visible"` has neither a leading `"no"` nor the feature's own noun (e.g. `"fate"`) anywhere in the clause, so `_build_absence_noun_pattern`'s regex cannot match it either. This is confirmed directly by the module's OWN code comment at `palm_reading.py:671-674` (inside `_is_genuine_negative_absence`'s docstring): *"Also False whenever a real, non-absent quality was observed (e.g. "Barely visible" is not caught by `_ABSENCE_PHRASES` or `_ABSENCE_PATTERNS_BY_FEATURE`) even if no chunk ends up supporting it — that is a doctrine-coverage gap, not a negative finding."*

Consequently, the full live path for e.g. `"FATE LINE: Barely visible."` (a real, repeated production observation — confirmed present in multiple `diagnostics/dogfood_capture.md` RUN blocks):
1. `_gather_feature_texts` collects the raw text under `"fate line"`.
2. `_resolve_feature_quality("fate line", ["Barely visible."])`: `_is_absence` returns `False` → treated as a real, non-absent observation. `_extract_quality` → `"barely visible"`. `_clean_quality_prefix` leaves it unchanged (doesn't start with `"fate line"` or a linking verb).
3. `_build_feature_query("fate line", "barely visible")` builds a REAL retrieval query: `"what does a barely visible fate line signify — meaning and indications of a barely visible fate line"`.
4. `_retrieve_per_feature`/`search()` runs this query against the live ChromaDB collection and returns up to 3 gated chunks (in the Ring 3 rubric evidence, this repeatedly retrieves `p163_c1`, a chunk about the wrist/Rascettes, not fate-line doctrine proper).
5. `_apply_support_gate` checks score ≥ `_SUPPORT_SCORE_FLOOR` (0.30) and a needle match (`"fate"` in chunk text) — if it passes, `"fate line"` is marked `supported`, NOT declined.
6. Stage 1 (`claim_extraction.extract_claims`) may extract a claim citing that chunk.
7. Stage 2 (`claim_voicing`) voices it into the final reading prose with a `[C-n]` citation tag.
8. **What the user ultimately sees**: a confident, specific-sounding interpretive sentence about their "barely visible" fate line, carrying a citation that LOOKS grounded (a real `[chunk_id]` anchor) — but per the Ring 3 human-rubric evidence gathered independently in Q5(b) above, this exact `p163_c1` citation for a "barely visible fate line" claim has been scored **U → FAIL ("anchor-fidelity FAIL, adjudication #2")** in BOTH pass 3 and pass 4, across multiple runs — the cited chunk does not actually license the specific claim being voiced. This is precisely the defect class underlying CLAUDE.md's "V1 PALM DROPPED" decision (S71): "Barely visible" and other soft/hedged vision-output phrasings slip past both absence tiers, generate a real query, retrieve a real (but insufficiently specific) chunk, pass the support gate, and produce a citation that reads as grounded but repeatedly fails human anchor-fidelity review.

---

### Q8 — REPO STATE

**a. HEAD short hash + `git log origin/main..HEAD --oneline`:**
```
HEAD: 212d9c6
$ git log origin/main..HEAD --oneline
(empty)
```
HEAD is fully in sync with `origin/main` — nothing ahead, nothing to push.

**b. `git status --short`:**
```
(empty — clean working tree)
```

**c. Current test count from the last recorded run (SESSION_LOG.md / CLAUDE.md — suite NOT re-run this task):**

Last count actually recorded in `SESSION_LOG.md` (line 4845): **3302 pass / 0 fail / 7 skip / 1 xpassed**. Flagging precisely, per this task's "from SESSION_LOG/CLAUDE.md" instruction: this is the last figure WRITTEN INTO those two docs — it does NOT yet reflect the two new tests added by this session's own earlier E2F step 2 work (commit `16f6439`) and the step-3 rewrite (commit `be35a1a`), whose commit messages state **3304 pass / 0 fail / 7 skip / 1 xpassed** as the actually-observed count at commit time. Neither `SESSION_LOG.md` nor `CLAUDE.md` has had this newer 3304 figure written into their own prose yet (that close-out bookkeeping step hasn't run) — reporting both numbers rather than picking one, since the task specifically asked for the docs' own recorded value, not this session's live knowledge.

---

### UNKNOWNS

- None of Q1-Q8's sub-items required an "UNKNOWN" answer — every item was answerable from the existing codebase, tracked data files (`data/progress/*.json`, `data/all_chunks.json`, `data/chunked_chunks.json`, `data/pending_chunks.json`, `data/processed_chunks.json`), the live ChromaDB collection, or the two documentation files (`SESSION_LOG.md`/`CLAUDE.md`).
- Partial-precision caveat (not a hard UNKNOWN, flagged for transparency): Q5(b)'s pass-3 rubric file uses a table convention with SPLIT-verdict rows (one row carries two verdicts, e.g. "C + U") and non-ledger rows ("no claim"/decline-block accuracy checks scored "P4-clean"/"P4 FAIL" rather than U/C/D) — these were reported as separate categories rather than forced into a single U/C/D bucket, since doing so would require a judgment call this task's "count, do not judge" instruction didn't authorize.
- Q3(e)'s exact reconciliation between the "127 diagram + 5 mixed = 132 zero-text pages" (derived from `data/all_chunks.json`'s own `page_type` field) and the "129 pages with zero live chunks" (derived from the live ChromaDB census) was not fully reconciled line-by-line — both numbers are independently measured and reported as-is; the 3-page gap likely reflects a small number of diagram/mixed pages where partial OCR text did clear the embedder's non-empty-text filter despite the page's own classification, but this was not traced further as it wasn't required to answer Q3(d)'s specific p.157/158 question.

### PROBE SCRIPTS CREATED AND DELETED

- `scripts/e2g_preflight_probe_S79.py` — created to answer Q3(b) (pdfplumber per-page char-count census), Q3(c) (live ChromaDB page→chunk_count census via a metadata-only `collection.get()`, no embedding calls), Q3(d)'s cross-tab, and Q2(d)'s live chunk_id-schema verification. Run once, output captured verbatim into this report, then deleted immediately after (confirmed via `ls` returning "No such file or directory" post-deletion). Not wired into pytest, not shipped as a module, made zero writes to the PDF/ChromaDB/any production file.
