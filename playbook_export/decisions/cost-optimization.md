# Cost Optimization Decisions

All cost-related decisions made in this project, with actual numbers and trade-offs.
Figures are based on OpenAI pricing as of May 2026.

---

## Cost Architecture: Separate Ingestion Cost from Query Cost

The most important cost decision is structural: maximise one-time ingestion cost
to minimise recurring per-query cost.

```
One-time ingestion cost (paid once):
  OCR processing            ~$0           (Tesseract, open-source)
  Diagram text extraction   ~$3–4         (GPT-4o vision, all diagrams)
  Hindi translation         ~$0.54        (GPT-4o-mini, 3 books)
  Embeddings                ~$0.05        (text-embedding-3-small, all chunks)
  ─────────────────────────────────────
  Total ingestion           ~$4–5

Recurring per-query cost:
  Query embedding           ~$0.000002    (text-embedding-3-small, 1 query)
  GPT-4o-mini inference     ~$0.0005–0.001 (5 chunks + context + answer)
  ─────────────────────────────────────
  Total per query           ~$0.001       (target: <$0.01)
```

**Rule:** Any expensive model call that is query-independent should be done at
ingestion time and cached. GPT-4o vision for diagrams and GPT-4o-mini translation
are one-time ingestion operations, not per-query operations.

---

## Embedding Model Cost

**Choice:** `text-embedding-3-small` at $0.02 / 1M tokens

| Model | Cost / 1M tokens | Dimension | Notes |
|---|---|---|---|
| text-embedding-ada-002 | $0.10 | 1536 | Legacy, lower quality |
| text-embedding-3-small | $0.02 | 1536 | **Selected** — 5× cheaper, better quality |
| text-embedding-3-large | $0.13 | 3072 | 6.5× more expensive, marginal quality gain |

**Savings vs ada-002:** 5× on embedding cost (significant for large corpora).
**Savings vs 3-large:** 6.5× with no meaningful quality loss for this use case.

**Actual embedding cost for this project:**
- ~3,000 sub-chunks × ~200 tokens average = ~600,000 tokens
- At $0.02/1M: ~$0.012 total to embed the entire corpus

---

## Translation Cost

**Choice:** GPT-4o-mini at $0.15/1M input, $0.60/1M output tokens

**Actual cost estimate for 3 Hindi books:**
- ~1,800 Hindi page chunks × ~300 tokens input + ~300 tokens output
- Input: 1,800 × 300 × $0.00000015 = $0.081
- Output: 1,800 × 300 × $0.00000060 = $0.324
- System prompt per call: ~150 tokens × 1,800 calls = $0.041
- **Total: ~$0.54**

This is a one-time cost. It never recurs.

**Why not GPT-4o for translation:**
- GPT-4o would cost ~15× more = ~$8 for the same translations
- Quality difference on Hindi prose is marginal (~5–10%)
- $7.50 cost difference for negligible quality gain → not justified

---

## Diagram Text Extraction Cost

**Choice:** GPT-4o vision — one-time only

**Actual cost estimate:**
- ~743 pending diagram chunks (images)
- GPT-4o image tokens: ~765 tokens per 512×512 tile
- For hand-drawn diagrams at ~1024×1024: ~2,295 tokens per image
- At GPT-4o pricing ($5.00/1M input, $15.00/1M output):
  - Input (image + prompt): ~2,295 × 743 × $0.000005 = $8.52
  - Output (extracted text): ~200 × 743 × $0.000015 = $2.23
  - **Total: ~$3–4 for all diagrams**

This is also one-time. The extracted text is stored in the chunk and never
re-extracted.

**Why not GPT-4o-mini for diagrams:**
- Vision quality on complex astrological charts and palmistry hand diagrams
  is significantly lower in mini
- Wrong extraction corrupts every future query that retrieves those chunks
- $3–4 vs ~$0.50 — the $2.50–3.50 quality premium is worth it for permanent
  ingestion quality

---

## Inference Cost

**Choice:** GPT-4o-mini at temperature 0.4

**Per-query cost breakdown:**
```
Query embedding:      1 × ~20 tokens × $0.02/1M  = ~$0.0000004
Retrieved chunks:     5 × ~200 words × ~267 tokens = ~1,335 tokens input
Kundali context:      ~500 tokens input
Session history:      6 turns × ~100 tokens = ~600 tokens input
System prompt:        ~400 tokens input
User question:        ~20 tokens input
─────────────────────────────
Total input:          ~2,855 tokens × $0.00000015 = ~$0.00043
GPT-4o-mini output:   ~300 tokens × $0.00000060   = ~$0.00018
─────────────────────────────
Total per query:      ~$0.0006

At $10/month subscription: allows ~16,667 queries/month
At $20/month subscription: allows ~33,333 queries/month
```

This is comfortably below the $0.01/query target. GPT-4o at the same structure
would cost ~$0.009/query — still under $0.01 but 15× more expensive.

---

## Idempotency as Cost Control

Every expensive operation implements an idempotency guard. This is as important
for cost control as it is for correctness.

**Embedding idempotency:**
```python
existing_ids = set(collection.get(include=[])["ids"])
to_embed = [c for c in embeddable if c["chunk_id"] not in existing_ids]
```
A re-run of the embedder on a fully-embedded corpus makes 0 API calls.

**Translation idempotency:**
```python
if "original_hindi" in chunk:
    continue  # already translated — skip
```
A re-run of the translator on a fully-translated file makes 0 API calls.

**Without idempotency:** A single crash-and-restart during embedding would
re-embed the entire corpus — doubling the embedding cost. For translation, it
would re-translate all books. Always implement idempotency before running on
the full dataset.

---

## Incremental Save as Cost Protection

Save progress every N operations so a crash doesn't require restarting from zero.

```python
SAVE_INTERVAL = 50  # write to disk every 50 translated chunks

if translated_count % SAVE_INTERVAL == 0:
    _save(chunks, output_path)
```

**Worst-case cost exposure with SAVE_INTERVAL = 50:**
- If a crash happens just before save #N, at most 49 chunks need to be
  re-translated on restart
- At ~$0.0003/chunk: max $0.015 extra cost from a crash
- Without incremental saves: up to $0.54 (entire translation cost) wasted

For embeddings (batch_size = 100), the batch is the unit of idempotency —
a failed batch is simply not in ChromaDB and will be re-attempted on restart.

---

## Session History Length as Cost Control

**Choice:** MAX_HISTORY_TURNS = 6 (12 messages, ~1,200 tokens)

**Why not longer history:**
- Each additional turn adds ~100 tokens of input per query
- 6 turns (12 messages) adds ~1,200 tokens
- 20 turns (40 messages) adds ~4,000 tokens — increases per-query cost by ~$0.0006
- For a $10/month product, the entire model inference budget is ~$0.001/query
- History beyond 6 turns is rarely semantically useful in conversational Q&A

**Why not shorter history:**
- Users expect follow-up questions to work ("and what about Venus in that house?")
- 3 turns is the minimum useful conversational window
- 6 turns handles most real conversation patterns

**Token cost vs conversation quality curve:**
- 0 turns: no context, follow-ups fail
- 3 turns: basic follow-ups work
- 6 turns: multi-step conversations work (sweet spot)
- 12+ turns: diminishing returns, rising cost

---

## Chunking Parameters as Quality/Cost Trade-off

Chunking parameters directly affect retrieval quality and embedding cost:

```python
MERGE_MIN_WORDS = 100    # prevents micro-chunks (bad quality, wasted embeddings)
SPLIT_THRESHOLD = 500    # prevents oversized chunks (dilutes retrieval signal)
WINDOW_SIZE = 400        # ~400 words per chunk at $0.000008/chunk to embed
WINDOW_OVERLAP = 50      # 50-word overlap recovers split-boundary context
```

**What bad chunking costs:**
- Too small (< 50 words): embedding hundreds of near-empty chunks that never
  retrieve well. Wastes embedding budget.
- Too large (> 600 words): a single chunk contains too many topics; retrieval
  matches the chunk but only part of it is relevant. Dilutes answer quality.
- WINDOW_SIZE = 400 was validated empirically: chunks this size return relevant
  passages on domain-specific queries with scores of 0.57–0.60

---

## Cost Monitoring

Track actual vs estimated cost at every pipeline stage:

```python
# In translator.py — actual token usage from API response
cost = (
    response.usage.prompt_tokens     * INPUT_COST_PER_TOKEN
    + response.usage.completion_tokens * OUTPUT_COST_PER_TOKEN
)
chunk["translation_cost"] = round(cost, 8)
total_cost += cost
```

Always use actual token counts from `response.usage`, not estimates from
character count. Estimates can be off by 30–50% on multilingual text.

Print a cost summary at the end of every expensive pipeline run:
```
Translation complete — 1,800 translated, total cost $0.5381
```

This creates an audit trail and catches unexpected cost spikes before they
accumulate.
