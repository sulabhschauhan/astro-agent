"""
path_c_validation.py
Path (c) Q&A validation: four follow-up questions against Sheridan's
Saturn-11th-from-Lagna AstroSage paragraph, answered via RAG+GPT-4o-mini
under the locked Q&A prompt. This is the test that locks or breaks
architecture path (c) (AstroSage paragraph terminal, RAG+LLM reserved for
follow-up Q&A only) -- see SESSION_LOG.md Session 22's three candidate
paths and the failed layered-generation spike (spikes/
interpretive_text_saturn_11th.py), which path (c) was scoped to avoid by
never asking the LLM to layer over/extend the parent paragraph, only to
answer separate follow-up questions without contradicting it.

READ-ONLY ON CHROMADB: only ingestion.query_engine.search() is called
(one OpenAI embedding call + one collection.query() per question). No
ChromaDB writes. Exactly one GPT-4o-mini chat completion per question --
no retries, no chained calls, no judge call. Rubric scoring against the
output is a human/Claude judgment step performed after this script runs,
not automated here (scoring requires reading the output against the
parent paragraph side by side, per the task's own instruction -- an LLM
judge call would also violate CLAUDE.md's NO ANCHORED JUDGMENT rule).

No production code is imported for mutation, only for retrieval
(ingestion.query_engine.search, unmodified, same call shape the Session 22
spike used).
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # project root, for `ingestion` import

from openai import OpenAI

from ingestion.query_engine import search, CHROMA_DIR, COLLECTION_NAME

MODEL = "gpt-4o-mini"
TEMPERATURE = 0  # matches spikes/interpretive_text_saturn_11th.py step3_generate_standalone/step4_generate_layered
RAG_TOP_K = 5

# Verbatim from spikes/interpretive_text_saturn_11th.py's ASTROSAGE_PARA
# constant -- confirmed byte-identical to Section A of the saved spike
# artifact (spikes/saturn_11th_comparison.md), which is what the task
# calls "the exact paragraph that Output A in the Session 22 spike used."
# NOTE: no Sheridan_Kundli.pdf exists anywhere in this repository (checked
# via glob across the whole tree and via the data/pdfs/ directory listing,
# which holds only Sulabh's and Surbhi's AstroSage exports, not Sheridan's)
# -- so no PDF page reference can be cited for this paragraph. Flagged
# explicitly in the report rather than inventing a page number.
ASTROSAGE_PARA = (
    "SATURN is in Pisces in your 11th House. Physically as well as "
    "mentally you will be very courageous during this period. This is "
    "a good phase for your relatives. Go for attempts in your career "
    "life as the success is assured. Gain of material things is also "
    "indicated. You will purchase land and machinery during this period. "
    "Substantial gains in your business and trades are assured. Your "
    "enemies will not be able to plunk before you. You will come into "
    "contact with people from far off places. This period is also very "
    "good as far as love life is concerned. You will receive full "
    "support from your family members."
)

QUESTIONS = {
    "Q1": ("definitional", "What does the 11th house from ascendant classically signify?"),
    "Q2": ("mechanism", "Why does Saturn in the 11th house tend to give gains rather than restrictions?"),
    "Q3": ("cross-placement", "How does Saturn in the 11th differ in effect from Saturn in the 12th?"),
    "Q4": ("edge-case, documented corpus gap",
           "What do classical texts say specifically about Saturn's transit through the "
           "11th from ascendant when natal Moon is in Aries?"),
}

SYSTEM_PROMPT = (
    "You are a classical Vedic astrologer in the voice of Parashara, grounded strictly "
    "in BPHS, Phaladeepika, Saravali, and the supplied retrieved passages. The user has "
    "already received an AstroSage paragraph (provided as the parent context). Your job "
    "is to answer the user's follow-up question in <= 4 sentences. Cite at least one "
    "classical source by name and page if any retrieved chunk supports your answer. Do "
    "not contradict the parent paragraph. If the retrieved passages do not directly "
    "address the question, say so explicitly -- do not invent a classical claim."
)


def _build_user_prompt(question: str, chunks: list[dict]) -> str:
    passages_block = "\n".join(
        f"[{c['book_name']} p{c['page_ref']}] {c['text']}" for c in chunks
    )
    return (
        f"Parent paragraph: {ASTROSAGE_PARA}\n"
        f"Follow-up question: {question}\n"
        f"Retrieved classical passages:\n{passages_block}"
    )


def run_query(qid: str, kind: str, question: str, openai_client: OpenAI) -> dict:
    try:
        chunks = search(question, n_results=RAG_TOP_K)
    except Exception as exc:
        raise RuntimeError(f"{qid}: ingestion.query_engine.search() failed: {exc}") from exc

    user_prompt = _build_user_prompt(question, chunks)

    try:
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
        )
        output = response.choices[0].message.content
        usage = response.usage
    except Exception as exc:
        raise RuntimeError(f"{qid}: GPT-4o-mini call failed: {exc}") from exc

    return {
        "qid": qid,
        "kind": kind,
        "question": question,
        "chunks": chunks,
        "user_prompt": user_prompt,
        "output": output,
        "usage": usage,
    }


def build_report(results: list[dict]) -> str:
    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append("# Path (c) Q&A Validation\n")
    lines.append(f"**Generated:** {now}  ")
    lines.append(f"**Collection:** `{COLLECTION_NAME}` @ `{CHROMA_DIR}` (post-dedup, 7,743 chunks)  ")
    lines.append(f"**Model:** `{MODEL}`, temperature={TEMPERATURE} (matches spikes/interpretive_text_saturn_11th.py step3/step4)  ")
    lines.append("**Read-only on ChromaDB** -- one `search()` call (embed + `.query()`) and one chat completion per question, no retries, no chained calls.\n")

    lines.append("## 1. Parent paragraph\n")
    lines.append(
        "**PDF page reference: NOT AVAILABLE.** No `Sheridan_Kundli.pdf` (or any file with "
        "\"Sheridan\" in its name) exists anywhere in this repository -- confirmed via a full-tree "
        "glob. `data/pdfs/` holds only two personal AstroSage exports, and both belong to other "
        "reference-chart subjects (`VedicReport5-24-202610-01-26PM.pdf` is Sulabh's, "
        "`Wife_VedicReport.pdf` is Surbhi's), not Sheridan's. The paragraph below is therefore "
        "sourced from `spikes/interpretive_text_saturn_11th.py`'s `ASTROSAGE_PARA` constant, "
        "confirmed byte-identical (diffed) against Section A of the saved Session 22 artifact "
        "`spikes/saturn_11th_comparison.md` -- i.e. it IS verified to be \"the exact paragraph "
        "that Output A in the Session 22 spike used,\" but its original PDF page cannot be cited "
        "because the source PDF is not in this repository. Not fabricated.\n"
    )
    lines.append(f"> {ASTROSAGE_PARA}\n")

    lines.append("## 2. Per-query results\n")
    for r in results:
        lines.append(f"### {r['qid']} ({r['kind']})\n")
        lines.append(f"**Question:** {r['question']}\n")
        lines.append("**Top-5 retrieved chunks:**\n")
        lines.append("| # | chunk_id | source | page | score |")
        lines.append("|---|---|---|---|---|")
        for i, c in enumerate(r["chunks"], 1):
            lines.append(f"| {i} | `{c['chunk_id']}` | {c['book_name']} | {c['page_ref']} | {c['score']} |")
        lines.append("")
        lines.append("**Q&A output (verbatim):**\n")
        lines.append("> " + (r["output"] or "[empty response]").replace("\n", "\n> "))
        lines.append("")
        lines.append("**Rubric scores:**\n")
        lines.append("__RUBRIC_PLACEHOLDER__\n")

    lines.append("## 3. Aggregate scoring\n")
    lines.append("__AGGREGATE_PLACEHOLDER__\n")

    lines.append("## 4. Honest verdict\n")
    lines.append("__VERDICT_PLACEHOLDER__\n")

    return "\n".join(lines) + "\n"


def main():
    openai_client = OpenAI()
    results = []
    for qid, (kind, question) in QUESTIONS.items():
        print(f"Running {qid} ({kind})...")
        result = run_query(qid, kind, question, openai_client)
        results.append(result)
        print(f"  retrieved {len(result['chunks'])} chunks, output length {len(result['output'] or '')} chars")

    report = build_report(results)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = Path(__file__).parent / f"path_c_validation_{timestamp}.md"
    out_path.write_text(report, encoding="utf-8")

    print(report)
    print(f"[written to {out_path}]")


if __name__ == "__main__":
    main()
