# Ensuring Retrieval Completeness for Dispersed Facts in Correctness-Critical RAG

## TL;DR
- For a correctness-critical Q&A system over a structured reference book where operative conditions are scattered across sections, practitioners converge on a **hybrid architecture**: do **offline, schema-constrained structured extraction of a conditions→meanings rules table (a knowledge base), grounded and human-verified**, and complement it at query time with **metadata/topic-tagged exhaustive retrieval plus hierarchical (parent/section) fallback and a reranker**. Naive top-k semantic retrieval over prose chunks is the wrong default because it optimizes top-1 relevance, not coverage.
- The reason to prefer the offline rules-KB is determinism and auditability: the LLM's non-determinism and hallucination are acceptable during an offline, human-supervised build phase but unacceptable at runtime; separating the two phases yields certified, auditable behavior. Schema-constrained extraction plus entity grounding dramatically reduces the "mass hallucination" of naive LLM output (SPIRES: 97–98/100 correct ontology identifiers with the method vs. just 3/100 native), but forced-schema extraction can itself fabricate values when evidence is absent, so a validation step is mandatory.
- "Pass everything into a long-context LLM" is the weakest option for correctness: it is subject to "lost in the middle" (Liu et al., TACL 2024: GPT-3.5-Turbo multi-document QA "can drop by more than 20%," in the worst case falling below closed-book performance of 56.1%), context-stuffing/distraction, higher cost/latency, and non-determinism — which is why teams in law, medicine, and finance avoid it as a primary mechanism and prefer retrieve-lean-then-structure.

## Key Findings
1. **The problem is a recognized retrieval-completeness failure, not a generation failure.** Legal-RAG literature names exactly your pattern: answering often "requires synthesizing information scattered across multiple sections," and "interpreting an exception clause… may depend on definitions or stipulations introduced much earlier in the document." Standard RAG "return[s] a limited number of passages (e.g., the top 5 or 10), potentially omitting essential information."

2. **Offline structured extraction into a rules KB is the highest-accuracy/highest-determinism approach — with a mandatory verification step.** Schema-constrained extraction (Pydantic/JSON-schema-guided LLM output, e.g., LlamaExtract, `llm --schema`, Anthropic tool-use) turns prose into a deterministic, queryable table of conditions→meanings. The SPIRES method (Caufield et al., *Bioinformatics* 40(3):btae104, 2024) shows ontology-grounded schema extraction returns correct identifiers for 98/100 Gene Ontology terms with GPT-3.5-turbo (97/100 with GPT-4-turbo), versus "just 3" correct for native LLM prompting — which the authors call "mass hallucination." But schema enforcement alone does not eliminate fabrication — forced required-fields can push fabrication toward 100% when the evidence is absent — so human-in-the-loop validation before KB insertion is documented best practice (SCICERO: validation modules raised precision from 54% at the extraction step to a final 75%, F1 from 69% to 77%, on 3.6K triples — an over-20% precision increase).

3. **Metadata/topic-tagged exhaustive retrieval is the most directly relevant query-time mechanism for your problem.** If every chunk is tagged `topic="head line"`, you can force-retrieve ALL chunks for that topic regardless of vector similarity, guaranteeing coverage. This is the pattern behind Coheso's legal "two-step" approach: exhaustive retrieval + structured (SQL-like) processing for queries that "demand exhaustive coverage of relevant documents."

4. **Parent-document / auto-merging retrieval solves the dispersed-detail problem when conditions live in one chapter.** LangChain's `ParentDocumentRetriever` and LlamaIndex's `AutoMergingRetriever`/`HierarchicalNodeParser` retrieve small precise chunks but pass the larger parent section to the LLM.

5. **Reranking + higher k improves recall of dispersed facts only if the fact was in the candidate pool.** The standard two-stage pattern (retrieve 50–100, rerank to 3–10 with a cross-encoder like Cohere Rerank or bge-reranker-v2-m3) yields meaningful precision gains, but "no reranker rescues a chunk that never made the candidate list."

6. **Hybrid dense+sparse (BM25) and Anthropic's Contextual Retrieval materially cut retrieval failures.** Anthropic (Sept 2024) reports Contextual Embeddings + Contextual BM25 cut the top-20-chunk retrieval failure rate by 49% (5.7% → 2.9%), and "reranked Contextual Embedding and Contextual BM25 reduced the top-20-chunk retrieval failure rate by 67% (5.7% → 1.9%)."

7. **Query decomposition / multi-query / HyDE help gather dispersed aspects of one topic.** Decomposing "give a full head-line reading" into sub-queries (long line? short line? chained? island?) and retrieving each independently is the largest recall lever among query transforms.

8. **Big-context "pass everything" is the weakest for correctness.** Lost-in-the-middle, distraction, cost, and non-determinism dominate.

## Details

### The problem, precisely stated
Your failure is structural: an INTRODUCTION/DEFINITION paragraph has high semantic similarity to a topic query ("tell me about the head line"), so top-k retrieval surfaces it, while the dispersed operative conditions ("a long straight line = strong logical mind," "an island = mental weakness") are lower-similarity and get missed. This is documented in legal RAG as "fragmented information" and "distributed factual dependencies," and Anthropic's SEC-filing example ("The company's revenue grew by 3% over the previous quarter") is the same context-loss pathology. The core insight from the literature: standard RAG optimizes for getting the single most relevant chunk into top-k, not for exhaustive coverage of everything said about one entity.

### (A) Offline full-document structured extraction into a rules KB
**What it is.** Rather than relying on live semantic retrieval over prose, you process the whole book offline and extract a structured, exhaustive table: `{topic: "head line", condition: "long straight line", meaning: "strong logical mind"}`, etc. At query time you query this table directly (or retrieve over it), optionally still surfacing the source prose for grounding.

**How it's done.**
- **Schema-constrained extraction.** Attach a Pydantic/JSON schema to the LLM so decoding is steered to valid fields/types (LlamaIndex structured outputs / LlamaExtract; Simon Willison's `llm --schema`; Anthropic's "Extracting Structured JSON using Claude and Tool Use" cookbook). KnowCoder represents schemas as Python classes; PARSE adds reflection-based guardrails to address hallucination and schema-compliance failures.
- **Knowledge-graph / GraphRAG construction.** Microsoft GraphRAG extracts entities+relations, builds communities, and pre-generates summaries. SPIRES (Caufield et al., *Bioinformatics* 2024) recursively interrogates an LLM against a user-defined schema and grounds entities to ontology IDs.
- **Two-phase (offline neural, online symbolic) discipline.** The key architectural principle: "the LLM's non-determinism and vulnerability to adversarial input are acceptable costs during knowledge base construction (an offline, human-supervised process) but unacceptable costs during production operation." Building the KB offline and then querying it symbolically at runtime gives "certified, auditable agent behavior."

**Tradeoffs.**
- *Accuracy/completeness:* Highest, because you read the WHOLE section once during extraction, so no operative condition is silently dropped by similarity ranking. SPIRES demonstrates the grounding win: 98/100 correct identifiers with the method (GPT-3.5-turbo) vs. 3/100 native.
- *Hallucination during extraction:* Real and must be managed. Forced required-fields cause fabrication when evidence is absent; schema-driven few-shot prompting can "generate structured field values that are not present in the original input." Mitigations: evidence-rule constraints ("extract a value only if clearly supported by text," with a supporting quote per cell), confidence scores, and human-in-the-loop review. HITL is a documented best practice with measurable gains (SCICERO precision 54%→75%; Tsaneva et al., *Information Processing & Management* 2025, report human-verification workflows add +4% precision / +3% recall "without any trade-offs in other performance metrics").
- *Determinism/auditability:* Best of all options — a fixed table gives the same answer every time and every meaning traces to a source span.
- *Cost/maintenance:* Higher upfront extraction cost; full GraphRAG indexing is famously expensive (Microsoft reported a $33,000 indexing cost for a large 5-GB legal dataset in early 2024, since driven down to ~0.1% of that by LazyGraphRAG). For a single book, extraction cost is modest (one practitioner cites ~$7 to index a 32,000-word book). Maintenance = re-extract when the source changes.

### (B) Metadata-filtered exhaustive topic retrieval
Tag every chunk during ingestion with structured metadata (`topic`, `feature`, `section`). At query time, detect the topic and use a metadata filter (e.g., ChromaDB `where`, or a graph/SQL predicate) to retrieve ALL chunks for that topic — bypassing vector-similarity ranking so the dispersed condition chunks cannot be dropped. Metadata filtering "narrows the search space… improving retrieval speed and accuracy," and is explicitly recommended where "accuracy is paramount." Coheso's legal system combines "exhaustive retrieval with structured data processing through SQL" precisely because aggregate/coverage queries "demand exhaustive coverage of relevant documents." Tradeoffs: requires clean, consistent tagging (the main engineering cost); can pull too much if a topic is large (mitigate with a downstream reranker or structured filtering). This is the single most directly applicable query-time technique for your "gather everything about the head line" need.

### (C) Parent-section / auto-merging retrieval
`ParentDocumentRetriever` (LangChain) indexes small child chunks for precise matching but returns the larger parent document/section to the LLM. LlamaIndex's `HierarchicalNodeParser` + `AutoMergingRetriever` chunk at multiple sizes (default 2048/512/128) and, when a majority of a parent's children are retrieved, "merge up" to pass the parent for "more complete context for response synthesis." This is a strong fit if all head-line conditions live in one head-line chapter: any hit on a head-line child pulls the whole chapter. Tradeoffs: if operative conditions are dispersed across DIFFERENT chapters/pages (your stated case), a single parent may not contain them all — so parent retrieval helps but does not by itself guarantee coverage. It also reintroduces context-window/lost-in-the-middle and distraction risks as parents grow.

### (D) Big-context "pass everything and let the LLM interpret"
Feeding many/all topically-matching paragraphs into a long-context model and letting it synthesize is tempting but the weakest for correctness-critical use:
- **Lost in the middle** (Liu et al., TACL 2024): accuracy is highest when evidence is at the very start or end; GPT-3.5-Turbo multi-document QA "can drop by more than 20%," and "in the worst case, performance in 20- and 30-document settings is lower than performance without any input documents (i.e., closed-book performance; 56.1%)." Extended-context model variants do not fix this.
- **Diminishing returns / distraction:** Using 50 documents instead of 20 improved GPT-3.5 performance only ~1.5%; more chunks eventually "backfire," bringing "irrelevant or distracting information that can confuse the model" and even induce hallucination on near-misses. Production practitioners report top-3 often beating top-10.
- **Cost/latency/non-determinism:** In one Elasticsearch/LlamaIndex comparison, long-context single-pass ran ~45s vs ~1s for targeted RAG, and full-context "occasionally failed to pinpoint the exact information required, especially when multiple similar documents were present."
- **Auditability:** Hard to trace which sentence drove the answer — a dealbreaker where "decisions require a clear audit trail."

Anthropic's own nuance: "If your knowledge base is smaller than 200,000 tokens (about 500 pages of material), you can just include the entire knowledge base in the prompt… with no need for RAG." A single palmistry book may fit — but even so, lost-in-the-middle and non-determinism argue against relying on raw stuffing for a completeness-critical reading; use it, if at all, as a fallback with structured guidance.

### Supporting techniques
- **Reranking:** Two-stage retrieve-broadly-then-rerank (retrieve 50–100, cross-encoder rerank to 3–10) is "the cheapest, highest-leverage RAG fix when first-stage retrieval has good recall but poor top-k precision." Cohere Rerank and bge-reranker-v2-m3 are strong defaults; typical NDCG@10 lift is in the 5–15 range, and legal/regulatory corpora commonly see NDCG@5 uplift of 0.10–0.15. Caveat: measure recall@50 first — "if recall@50 is below 0.85 on your golden set, fix the retriever… before paying for a reranker," because a reranker cannot rescue a chunk that never made the candidate list.
- **Hybrid dense+BM25 + Contextual Retrieval:** BM25 catches exact terms embeddings miss ("error code TS-999"); Anthropic's Contextual Retrieval prepends a 50–100-token chunk-specific context before embedding/indexing, cutting top-20 retrieval failures 49% (embeddings+BM25) and 67% with reranking added.
- **Query decomposition / multi-query / HyDE:** Decomposition gives the largest recall gains (one eval reports context_recall +0.250) by breaking a topic into sub-questions and retrieving each; HyDE improves ranking/semantic alignment (context_precision +0.143, faithfulness up to 0.946 in that eval); multi-query helps mainly at scale where different phrasings reach different regions of the vector space. Directly applicable to "assemble every condition for one feature."
- **RAPTOR / hierarchical summarization** (Sarthi et al., ICLR 2024): recursive cluster-and-summarize tree; improves multi-step QA (e.g., +20% absolute on QuALITY with GPT-4) but recursive summarization can amplify hallucination (the paper's annotation study found ~4% of summaries contained minor hallucinations).

## Recommendations

**Recommended architecture (staged):**

**Stage 1 — Build the offline rules KB (do this first; it is the backbone).**
- Chunk the book **structure-aware** (by topic/section, not fixed-size), tagging each chunk with `topic`, `feature`, `section`, `page`.
- Run **schema-constrained extraction** per section to produce a table `{feature, condition, meaning, source_span}`. Use an evidence rule ("only extract what is explicitly supported; attach the verbatim source quote per row") and emit a per-row confidence score.
- **Human-verify** the extracted table once (this is cheap for one book and eliminates the dominant hallucination risk). This gives you a deterministic, auditable answer key.
- At query time, for "give a full reading of feature X," **query the table for all rows where feature=X** — guaranteeing completeness — and have the LLM narrate strictly from those rows, citing source spans.

**Stage 2 — Add a retrieval safety net (for open-ended questions and to surface prose grounding).**
- Index chunks with **hybrid dense+BM25** (optionally Anthropic Contextual Retrieval) and **metadata**; when a topic is identified, apply a **metadata filter to exhaustively pull all chunks tagged to that topic**, then **rerank**.
- Keep **parent/section retrieval** as the fallback when a query hits prose not yet in the KB.

**Stage 3 — Reserve long-context synthesis as a last-resort fallback**, never the primary path; if used, order evidence with strongest items first/last and instruct the model to answer only from provided passages and to abstain when unsupported.

**Benchmarks/thresholds that change the recommendation:**
- Build a golden set of ~50–100 (feature → complete list of conditions/meanings) pairs. Measure **coverage/recall of conditions**, not just answer relevance.
- If **recall@50 < ~0.85** on dispersed conditions, the retriever (not the reranker/LLM) is the problem — invest in metadata-exhaustive retrieval or the rules KB.
- If extraction verification shows **>~5% fabricated/unsupported rows**, tighten the evidence rule, lower temperature, add schema guardrails (PARSE-style), and keep HITL.
- If the whole book is **<200K tokens** and answers are not correctness-critical, prompt-caching the whole book is an acceptable simple baseline — but still validate against the golden set for lost-in-the-middle.

**Bottom line:** For a domain where an incomplete reading is a product failure, converge on **(A) offline verified rules-KB as the source of truth + (B) metadata-exhaustive topic retrieval + (C) parent-section fallback**, with hybrid+rerank underneath. Avoid (D) as a primary mechanism.

## Caveats
- Much of the strongest quantitative practitioner data (Anthropic's 49%/67%, reranker NDCG lifts, decomposition recall gains) comes from vendor blogs and single-dataset evals; treat exact numbers as indicative, not universal, and validate on your own golden set.
- Several cited items are arXiv preprints (not peer-reviewed) and some carry 2026 dates; the "PhantomFill" forced-schema fabrication result uses synthetic-by-construction inputs. SPIRES (*Bioinformatics* 2024), the Lost-in-the-Middle paper (TACL 2024), RAPTOR (ICLR 2024), and Tsaneva et al. (*Information Processing & Management* 2025) are peer-reviewed anchors.
- GraphRAG's full entity/community pipeline is likely overkill for a single book; its value is multi-hop/global-sensemaking across large corpora. A simple schema-extracted rules table captures your conditions→meanings structure at far lower cost.
- "Lost in the middle" severity varies by model and is being actively mitigated (evidence reordering, Ms-PoE, IN2 training); test your specific model rather than assuming.