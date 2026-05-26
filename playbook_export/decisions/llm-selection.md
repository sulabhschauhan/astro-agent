# LLM Selection Decisions

Every model and configuration choice made in this project, with the reasoning
that was evaluated and the alternatives that were rejected.

---

## Inference Model: GPT-4o-mini

**Used for:** Main question-answering agent (every user query)

**Decision:** GPT-4o-mini at temperature 0.4

**Why GPT-4o-mini over GPT-4o:**
- Cost: GPT-4o-mini is ~15× cheaper per token than GPT-4o
- Quality gap on Q&A tasks: small (~5–10% on reasoning benchmarks)
- For factual Q&A grounded in retrieved passages, the retrieval quality dominates
  the answer quality more than the model's reasoning ability
- GPT-4o is reserved for tasks where vision or complex reasoning is required

**Why not GPT-3.5-turbo:**
- GPT-4o-mini has better instruction following, particularly for:
  - Maintaining persona voice consistently
  - Respecting "do not cite sources" instructions
  - Handling multi-turn context coherently
- Cost difference vs GPT-4o-mini is minimal; quality difference is meaningful

**Temperature: 0.4**
- Not 0: Factual Q&A benefits from some interpretive flexibility when passages
  conflict or are ambiguous. Pure determinism produces robotic responses.
- Not 0.7+: High temperature introduces hallucination risk when the model is
  expected to stay grounded in retrieved passages.
- 0.4 is empirically the balance point for grounded but natural-sounding answers.

---

## Diagram Interpretation: GPT-4o (vision)

**Used for:** Extracting text from chart images, palmistry diagrams, and
illustrated plates — one-time ingestion only

**Decision:** GPT-4o vision at one-time ingestion cost

**Why GPT-4o over GPT-4o-mini for vision:**
- GPT-4o-mini's vision capability is significantly weaker on:
  - Dense astrological wheel charts with overlapping symbols
  - Hand-drawn palmistry diagrams with annotations
  - Tables with mixed Hindi/Sanskrit headers
- This is a one-time ingestion cost (~$3–4 for all diagrams) — the model
  quality choice doesn't affect per-query cost
- Wrong extraction at ingestion time corrupts every query that touches those
  chunks forever; the extra cost is worth the quality guarantee

**Why not open-source vision models (LLaVA, etc.):**
- Quality on dense symbolic diagrams significantly below GPT-4o
- Would require local GPU inference setup that breaks the serverless deployment model
- One-time ingestion cost is low enough that cost advantage of open-source
  does not justify the quality risk

---

## Translation Model: GPT-4o-mini

**Used for:** Hindi prose → English translation of 3 Hindi books (one-time)

**Decision:** GPT-4o-mini at temperature 0.1, ~$0.54 total

**Why GPT-4o-mini over GPT-4o for translation:**
- GPT-4o-mini is 85–90% of GPT-4o quality on Hindi prose translation tasks
- The 5–10% quality gap does not justify 15× cost difference for bulk ingestion
- Classical Hindi prose (Lal Kitab, Hasta Samudrika) translates well at mini
  quality — it is straightforward prose, not dense philosophical argument

**Temperature: 0.1**
- Translation requires high consistency and minimal creativity
- Low temperature ensures the same Sanskrit technical term is always translated
  the same way across all chunks (critical for retrieval coherence)
- Not 0: preserves slight flexibility for context-dependent word choices in
  classical texts

**Why NOT IndicTrans2 (open-source Hindi translation model):**
- Evaluated and rejected. On classical Hindi texts from 1941–1976:
  - Produced broken English with incorrect Sanskrit term handling
  - Failed on archaic Hindi vocabulary not in modern training data
  - Could not preserve technical terminology (Graha, Bhava, Nakshatra) —
    translated them to generic English words, losing domain specificity
- GPT-4o-mini correctly identifies and preserves Vedic technical terms
- Open-source models optimised for modern Hindi cannot be trusted on classical
  texts without extensive validation

**Why not Sanskrit-specific models:**
- Books are primarily Hindi prose with Sanskrit technical terms embedded
- Sanskrit-only models would mishandle the surrounding Hindi commentary
- GPT-4o-mini handles the Hindi/Sanskrit mix correctly in a single pass

---

## Embedding Model: text-embedding-3-small

**Used for:** All chunk embeddings (1536-dimensional)

**Decision:** text-embedding-3-small at dim=1536

**Why text-embedding-3-small over text-embedding-ada-002:**
- Better semantic quality on benchmark retrieval tasks
- Lower cost ($0.02/1M tokens vs $0.10/1M tokens for ada-002)
- ada-002 is the legacy model — OpenAI's own benchmarks show 3-small is superior

**Why text-embedding-3-small over text-embedding-3-large:**
- text-embedding-3-large: dim=3072, higher cost, marginal quality improvement
  on practical retrieval tasks
- For a corpus of classical texts with domain-specific vocabulary, the quality
  difference is not empirically significant enough to justify 2× cost
- If retrieval quality becomes a bottleneck, upgrade to 3-large; don't pre-optimise

**Dimension: 1536 (default)**
- text-embedding-3-small supports dimension reduction (Matryoshka embeddings)
- Smaller dimensions (e.g., 256) reduce storage cost but degrade retrieval quality
- 1536 is the full dimension and the safe default until retrieval quality is measured

**Why OpenAI embeddings over open-source (sentence-transformers, etc.):**
- Multilingual quality on Hindi/Sanskrit text is significantly better
- No local inference setup required — consistent with serverless deployment
- text-embedding-3-small specifically has strong multilingual coverage

---

## Similarity Threshold: 0.45 (low-confidence flag)

**Decision:** Flag queries with top chunk score below 0.45 as low-confidence

**Calibration basis:**
- Observed good queries (clear, specific astrological questions) consistently
  returned top scores in the 0.57–0.60 range
- Vague or off-topic queries returned scores in the 0.40–0.50 range
- Threshold set at 0.45: below observed good-query floor, above observed
  noise floor

**Tuning guidance:**
- If too many legitimate queries are flagged: lower the threshold (try 0.40)
- If hallucination increases on weak queries: raise the threshold (try 0.50)
- Recalibrate after adding new books — corpus expansion changes score distribution

**Important:** This threshold flags the response, it does not block it. The LLM
is told the match is weak and instructed to be careful and acknowledge uncertainty.
Refusing to answer when confidence is low trains users to ask better questions
but also blocks legitimate edge-case queries.

---

## Persona Configuration

**Decision:** Named persona (Parashara) at temperature 0.4 with direct prediction style

**Why a named persona over "AI assistant":**
- Vedic astrology is a traditional lineage-based knowledge system
- Users expect wisdom delivered with authority, not hedged AI disclaimers
- Named personas have better instruction-following on style consistency
  (empirically observed in this domain)

**Why "direct predictions" not "academic citations":**
- Target users are people seeking guidance, not researchers
- Citing chapter and verse mid-answer breaks the conversational register
- Sources are provided as grounding context to the LLM but never appear in output

**Disclaimer strategy:** End every reading with a fixed disclaimer, exact wording
controlled by a constant in `prompt_builder.py`, not by the LLM. LLM-generated
disclaimers are inconsistent in wording and sometimes missing. Fixed-string
disclaimers are always present and always identical.

---

## Rate Limit Backoff: 3 retries, 10/20/40 second delays

**Decision:** Exponential backoff: base 10s, doubles per retry, max 3 retries

**Why 10s base (not 1s or 60s):**
- OpenAI rate limit windows are typically 60s for RPM limits, 1 minute for TPM
- A 10s base with 3 retries covers up to 70s of wait time — sufficient for
  most transient rate limits to clear
- A 1s base retries too fast (doesn't let the window reset)
- A 60s base makes a 3-retry sequence take 210s (3.5 minutes) — too slow for
  interactive use

**Why 3 retries (not 5):**
- If 3 retries at 10/20/40s haven't succeeded, the issue is likely not transient
- 4th retry would wait 80s — at that point, raise and let the human decide

**Applied to:** embedder batch calls, astrologer GPT calls, translator GPT calls.
Each component has its own retry logic — do not share a single global retry
mechanism, as different components have different cost/latency trade-offs.
