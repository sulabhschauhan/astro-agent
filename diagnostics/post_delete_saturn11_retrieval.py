"""
post_delete_saturn11_retrieval.py
Read-only re-run of the exact retrieval call from the Session 22
interpretive-text spike (spikes/interpretive_text_saturn_11th.py
step2_retrieve_chunks(): ingestion.query_engine.search(RAG_QUERY,
n_results=8), no book filter), now that targeted_delete_execute.py has
removed the 3,945 X/X_c<N> duplicate-text children from the collection.

Uses the production `search()` function unmodified -- no custom query
construction -- so this is an apples-to-apples comparison against the
pre-delete top-8 baseline, which is hardcoded below verbatim from the
spike's saved artifact (spikes/saturn_11th_comparison.md), since that
artifact recorded book_name/page_ref/score/text for each of the 8 slots
but not chunk_id (the spike script never printed chunk_id).

READ-ONLY CONTRACT: only ingestion.query_engine.search() (an OpenAI
embedding call for the query text + a single collection.query()) is
called. No ChromaDB writes.
"""

import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # project root, for `ingestion` import
sys.path.insert(0, str(Path(__file__).parent))  # diagnostics dir, for sibling-script imports

from ingestion.query_engine import search, CHROMA_DIR, COLLECTION_NAME
from targeted_delete_dryrun import CLEAN_BOOKS

RAG_QUERY = "Saturn transit eleventh house effects classical"
RAG_TOP_K = 8

# Verbatim from spikes/saturn_11th_comparison.md "## RAG chunks retrieved" --
# the actual pre-delete top-8 this spike's step2_retrieve_chunks() returned.
# No chunk_id was recorded there; (book_name, page_ref, text prefix) is used
# as the passage-identity key for the new-vs-old comparison below.
PRE_DELETE_TOP8 = [
    {"book_name": "Deva-keralam", "page_ref": 147, "score": 0.6686,
     "text_prefix": "(b) Saturn’s Transit in 12th House: If Saturn"},
    {"book_name": "Deva-keralam", "page_ref": 147, "score": 0.6686,
     "text_prefix": "(b) Saturn’s Transit in 12th House: If Saturn"},
    {"book_name": "Phaladeepika 2nd Ed. 1950 by V Subrahmanya Sastri", "page_ref": 33, "score": 0.6543,
     "text_prefix": "other planets. Effects of the transit of the"},
    {"book_name": "Deva-keralam", "page_ref": 59, "score": 0.6449,
     "text_prefix": "to the native. Loss of quadrupeds, lands, calling"},
    {"book_name": "Deva-keralam", "page_ref": 59, "score": 0.6449,
     "text_prefix": "to the native. Loss of quadrupeds, lands, calling"},
    {"book_name": "Deva-keralam", "page_ref": 59, "score": 0.6403,
     "text_prefix": "42 Chandra Kala Nadi 3085. Saturn’s Transit in"},
    {"book_name": "Deva-keralam", "page_ref": 59, "score": 0.6403,
     "text_prefix": "42 Chandra Kala Nadi 3085. Saturn’s Transit in"},
    {"book_name": "Deva-keralam", "page_ref": 59, "score": 0.6326,
     "text_prefix": "Notes: The concerned lines dealing with Saturn’s transit"},
]
# 5 distinct underlying passages across those 8 slots (3 duplicated pairs +
# 2 singletons): p147 "12th-house" (off-topic), p33 TOC heading (off-topic,
# not content), p59 "5th-10th list" (off-topic, cuts off before 11th), p59
# "12-houses-from-ascendant list" (on-topic -- explicitly lists "11th -
# gains"), p59 "notes: lines on 11th/12th missing" (meta -- documents the
# corpus gap, mentions 11th by name).


def _passage_key(book_name: str, page_ref, text: str) -> tuple:
    """Whitespace-normalized first-8-words key. Raw stored text has embedded
    newlines from OCR line breaks; a raw character slice would split
    differently than a hand-typed prefix written with single spaces, so
    both sides of the comparison normalize through the same split()/join()
    before keying -- avoids a false 'new passage' from formatting noise
    rather than an actual content difference."""
    normalized = " ".join((text or "").split())
    words = normalized.split(" ")[:8]
    return (book_name, page_ref, " ".join(words))


def build_report(results: list[dict]) -> str:
    lines = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append("# Post-Delete Saturn-11th Retrieval Re-run\n")
    lines.append(f"**Generated:** {now}  ")
    lines.append(f"**Collection:** `{COLLECTION_NAME}` @ `{CHROMA_DIR}`  ")
    lines.append(f"**Query:** `{RAG_QUERY!r}`, k={RAG_TOP_K}, via `ingestion.query_engine.search()` (production path, unmodified)  ")
    lines.append("**Read-only run** -- no ChromaDB writes. One OpenAI embedding call for the query text, one `collection.query()` call.\n")

    lines.append("## Post-delete top-8\n")
    lines.append("| # | chunk_id | book_name | page_ref | score | text (first 250 chars) |")
    lines.append("|---|---|---|---|---|---|")
    for i, r in enumerate(results, 1):
        snippet = (r["text"] or "")[:250].replace("\n", " ").replace("|", "\\|")
        lines.append(f"| {i} | `{r['chunk_id']}` | {r['book_name']} | {r['page_ref']} | {r['score']} | {snippet} |")
    lines.append("")

    # Distinct-passage check
    post_keys = [_passage_key(r["book_name"], r["page_ref"], r["text"]) for r in results]
    distinct_post = len(set(post_keys))
    dup_within = len(post_keys) - distinct_post
    lines.append("## Distinct-passage check\n")
    lines.append(f"- Distinct passages in post-delete top-8: {distinct_post}/{len(results)}")
    lines.append(f"- Within-result duplicates: {dup_within} -- {'PASS (0 expected)' if dup_within == 0 else 'ANOMALY'}\n")

    # New-vs-old comparison
    pre_keys = {_passage_key(p["book_name"], p["page_ref"], p["text_prefix"]) for p in PRE_DELETE_TOP8}
    new_passages = [r for r, k in zip(results, post_keys) if k not in pre_keys]
    held_over = [r for r, k in zip(results, post_keys) if k in pre_keys]
    lines.append("## New vs. pre-delete top-8\n")
    lines.append(f"- Pre-delete distinct passages (from spikes/saturn_11th_comparison.md): {len(pre_keys)}")
    lines.append(f"- Post-delete results that match a pre-delete passage (held over): {len(held_over)}")
    lines.append(f"- **Post-delete results that are NEW (not in the pre-delete top-8): {len(new_passages)}**\n")
    if new_passages:
        lines.append("New passages:\n")
        for r in new_passages:
            snippet = (r["text"] or "")[:200].replace("\n", " ")
            lines.append(f"- `{r['chunk_id']}` ({r['book_name']} p.{r['page_ref']}, score={r['score']}): {snippet}")
        lines.append("")
    if held_over:
        lines.append("Held-over passages (also in pre-delete top-8):\n")
        for r in held_over:
            lines.append(f"- `{r['chunk_id']}` ({r['book_name']} p.{r['page_ref']}, score={r['score']})")
        lines.append("")

    # Clean-book appearance check -- distinguish NEW appearances from ones
    # that were already in the pre-delete top-8 too (e.g. Phaladeepika p33
    # ranked pre-delete already; its continued presence isn't a new effect
    # of the delete, just an unrelated, already-present result holding its rank).
    clean_hits = [r for r in results if r["book_name"] in CLEAN_BOOKS]
    new_keys = {k for k in post_keys if k not in pre_keys}
    clean_hits_new = [r for r, k in zip(results, post_keys) if r["book_name"] in CLEAN_BOOKS and k in new_keys]
    clean_hits_held = [r for r in clean_hits if r not in clean_hits_new]
    lines.append("## Clean-book appearance check\n")
    if clean_hits:
        lines.append(f"- {len(clean_hits)} result(s) from the 6 clean books appear in the post-delete top-8.")
        if clean_hits_new:
            lines.append(f"  - **{len(clean_hits_new)} NEW** (did not appear pre-delete):")
            for r in clean_hits_new:
                lines.append(f"    - `{r['chunk_id']}` ({r['book_name']} p.{r['page_ref']}, score={r['score']})")
        if clean_hits_held:
            lines.append(f"  - {len(clean_hits_held)} held over (already ranked in the pre-delete top-8 too, not a new effect of this delete):")
            for r in clean_hits_held:
                lines.append(f"    - `{r['chunk_id']}` ({r['book_name']} p.{r['page_ref']}, score={r['score']})")
    else:
        lines.append("- None. No clean-book (BPHS-1/2, Phaladeepika, Saravali, Cheiro, Lal Kitab) result appears in the post-delete top-8.")
    lines.append("")

    lines.append("## Subjective on-topic assessment (manual review, full text read -- not keyword-scored)\n")
    lines.append(
        "Honest count: **2 of 8** results directly and specifically address Saturn's "
        "transit effect in the 11th house. The other 6 break down as follows:\n\n"
        "| # | chunk_id | verdict | why |\n"
        "|---|---|---|---|\n"
        "| 1 | `Deva-keralam_p147_c2` | adjacent, not on-topic | Saturn transit, but explicitly the **12th** house, not 11th. |\n"
        "| 2 | `Phaladeepika_p33_c1` | off-topic | Table-of-contents heading -- lists chapter topics, has no actual content. |\n"
        "| 3 | `Deva-keralam_p59_c1` | adjacent, not on-topic | Saturn-transit-by-house list, but this fragment only covers 5th-10th; text ends \"...ascendant etc.\" right before reaching 11th. |\n"
        "| 4 | `Deva-keralam_p59_c0` | **on-topic** | Explicit 12-house Saturn-transit list that states \"11th - gains\" by name. |\n"
        "| 5 | `Deva-keralam_p59_c2` | **on-topic** | Explicitly names \"Saturn's transit in 11th and 12th from ascendant\" (flagging the source's own missing lines) and supplies a fallback: \"11th - pleasures and wealth.\" Meta/caveated, but genuinely about the asked question. |\n"
        "| 6 | `Deva-keralam_p153_c0` | adjacent, not on-topic | Another Saturn-transit-by-house list, but this chunk's text is truncated at the 4th house -- never reaches 11th. |\n"
        "| 7 | `Deva-keralam_p147_c1` | off-topic | Saturn transiting Nakshatras (lunar mansions counted from Janma Nakshatra) -- a different classification system from houses-from-ascendant entirely. |\n"
        "| 8 | `Deva-keralam_p202_c2` | off-topic | Worked example about Jupiter substituting for Saturn on a 2nd-house illustration; no mention of the 11th house. |\n\n"
        "**Not an improvement in relevance, only in bloat.** The 2 on-topic results are the exact "
        "same 2 (Deva-keralam p59, c0/c2) that were already the \"legitimate signal\" pre-delete -- "
        "this delete didn't change which passages are genuinely on-topic, it just removed their "
        "duplicate copies. The TOC heading and the 12th-house passage are *still* in the top-8 "
        "(held over, never duplicates, so untouched by this delete). The 3 newly-surfaced slots "
        "freed up by dedup were filled with comparably off-topic content (a nakshatra-based passage, "
        "a Jupiter/2nd-house example, a truncated house-list), not better content. This confirms the "
        "Session 22 finding stands: the delete fixed the **data layer** (duplicate pollution -- see "
        "Check 1, fully resolved), but the **retrieval layer**'s relevance problem (embedding "
        "similarity surfacing TOC headings and wrong-house passages above the two genuinely on-topic "
        "ones) is untouched and remains exactly as broken as the spike found it.\n"
    )

    book_dist = Counter(r["book_name"] for r in results)
    lines.append("## Book distribution of post-delete top-8\n")
    for book, n in book_dist.most_common():
        lines.append(f"- {book}: {n}")
    lines.append("")

    return "\n".join(lines) + "\n"


def main():
    try:
        results = search(RAG_QUERY, n_results=RAG_TOP_K)
    except Exception as exc:
        raise RuntimeError(f"ingestion.query_engine.search() failed: {exc}") from exc

    report = build_report(results)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = Path(__file__).parent / f"post_delete_saturn11_retrieval_{timestamp}.md"
    out_path.write_text(report, encoding="utf-8")

    print(report)
    print(f"[written to {out_path}]")


if __name__ == "__main__":
    main()
