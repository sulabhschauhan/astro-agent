"""
scripts/census_feature_page_ranges_S82.py

Diagnostics-only census of the live Cheiro corpus per palm-feature page
range. Uses coll.get() (metadata lookup, no embedding, no OpenAI call) and
the PRODUCTION _build_where clause builder against the real ChromaDB --
not a hand-written where clause. Writes diagnostics/census_feature_page_ranges_S82.md.

DECISION THIS SERVES (S82 prompt 4): if page_ref is int in live metadata AND
every non-null range holds >= _N_RESULTS_PER_FEATURE chunks, the flag flip is
viable; if any range holds 0, that feature's layer is DATA, not retrieval;
1-2 is viable-but-thin. This script only reports; it does not decide or fix.

Does not modify any production file, does not flip _FEATURE_PAGE_FILTER_ENABLED,
does not run a full palm reading, makes no OpenAI calls.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.query_engine import get_collection, _build_where
from agent.interpretive.palm_reading import (
    _FEATURE_PAGE_RANGES,
    _CHEIRO_BOOK,
    _N_RESULTS_PER_FEATURE,
)

_NAMED_CHUNK_IDS = [
    "cheiroslanguageo00chei_1_p165_c2",
    "cheiroslanguageo00chei_1_p163_c1",
    "cheiroslanguageo00chei_1_p145_c0",
    "cheiroslanguageo00chei_1_p160_c3",
    "cheiroslanguageo00chei_1_p159_c2",
    "cheiroslanguageo00chei_1_p160_c1",
]

REPORT_PATH = Path(__file__).resolve().parent.parent / "diagnostics" / "census_feature_page_ranges_S82.md"


def main() -> None:
    failures = 0
    lines: list[str] = []
    lines.append("# S82 Prompt 4 — Live Cheiro Feature Page-Range Census\n")
    lines.append(
        "Diagnostics only. Reports numbers; makes no range-change "
        "recommendation. Threshold cited: `_N_RESULTS_PER_FEATURE` "
        f"(imported, currently {_N_RESULTS_PER_FEATURE}) -- the production "
        "per-feature retrieval gate. Scope: palm-feature retrieval, Cheiro "
        "book only.\n"
    )

    try:
        coll = get_collection()
    except Exception as exc:  # noqa: BLE001 -- report, don't crash the census
        lines.append(f"\n**FATAL: could not open ChromaDB collection: {exc}**\n")
        failures += 1
        REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
        print(f"FATAL opening collection: {exc}")
        return

    # ── STEP 1: metadata type check ─────────────────────────────────────
    lines.append("## Step 1 — page_ref metadata type check\n")
    step1_type = None
    step1_example = None
    try:
        sample = coll.get(
            where={"book_name": {"$eq": _CHEIRO_BOOK}},
            limit=5,
            include=["metadatas"],
        )
        metas = sample.get("metadatas", [])
        types_seen = []
        for m in metas[:5]:
            v = m.get("page_ref")
            types_seen.append((type(v).__name__, v))
        if types_seen:
            step1_type = types_seen[0][0]
            step1_example = types_seen[0][1]
        lines.append(f"- First 5 page_ref values (type, value): {types_seen}")
        if step1_type != "int":
            lines.append(
                f"\n**STOP CONDITION HIT: page_ref type is `{step1_type}`, "
                f"not int (example value: {step1_example!r}). $gte/$lte would "
                "silently match nothing. This is a DATA-layer finding.**\n"
            )
            REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
            print(f"STOP: page_ref type is {step1_type}, not int. See report.")
            return
        lines.append(f"- Result: page_ref is `int` (example: {step1_example!r}). Proceeding.\n")
    except Exception as exc:  # noqa: BLE001
        failures += 1
        lines.append(f"- **FAILED: Step 1 sample fetch raised: {exc}**\n")

    # ── STEP 2: per-feature census via production _build_where ─────────
    lines.append("## Step 2 — per-feature census (production `_build_where` clause)\n")
    lines.append(
        "| feature | range | chunk count | distinct page_refs present | "
        "pages in range with zero chunks |"
    )
    lines.append("|---|---|---|---|---|")

    counts_by_feature: dict[str, int] = {}

    for feature, page_range in _FEATURE_PAGE_RANGES.items():
        if page_range is None:
            continue
        start, end = page_range
        where = None
        try:
            where = _build_where({"book_name": _CHEIRO_BOOK, "page_ref": (start, end)})
            result = coll.get(where=where, include=["metadatas"])
        except Exception as exc:  # noqa: BLE001 -- one bad range must not kill the census
            failures += 1
            lines.append(
                f"| {feature} | {start}-{end} | **FAILED** | "
                f"clause={where} error={exc} | — |"
            )
            continue

        metas = result.get("metadatas", [])
        page_refs = sorted({m.get("page_ref") for m in metas if m.get("page_ref") is not None})
        chunk_count = len(metas)
        counts_by_feature[feature] = chunk_count
        pages_in_range = set(range(start, end + 1))
        zero_chunk_pages = sorted(pages_in_range - set(page_refs))
        lines.append(
            f"| {feature} | {start}-{end} | {chunk_count} | {page_refs} | {zero_chunk_pages} |"
        )

    lines.append("")

    # ── STEP 3: direct id lookup for the six named chunks ───────────────
    lines.append("## Step 3 — direct id lookup for the six named chunks\n")
    lines.append(
        "Note: these six were reconciled against the PRE-correction "
        "85-94/95-97 thumb/fingers split. A mismatch on thumb/fingers "
        "range containment is expected and is not a defect.\n"
    )
    lines.append("| chunk_id | found | page_ref | containing feature range(s) |")
    lines.append("|---|---|---|---|")

    for chunk_id in _NAMED_CHUNK_IDS:
        try:
            got = coll.get(ids=[chunk_id], include=["metadatas"])
        except Exception as exc:  # noqa: BLE001
            failures += 1
            lines.append(f"| {chunk_id} | **FAILED** | error={exc} | — |")
            continue

        ids_found = got.get("ids", [])
        if not ids_found:
            lines.append(f"| {chunk_id} | no | — | — |")
            continue

        page_ref = got["metadatas"][0].get("page_ref")
        containing = [
            f"{feat} ({rng[0]}-{rng[1]})"
            for feat, rng in _FEATURE_PAGE_RANGES.items()
            if rng is not None and rng[0] <= page_ref <= rng[1]
        ]
        containing_str = ", ".join(containing) if containing else "none"
        lines.append(f"| {chunk_id} | yes | {page_ref} | {containing_str} |")

    lines.append("")

    # ── STEP 4: flag blocking / thin features (no fix proposed) ─────────
    lines.append("## Step 4 — blocking / thin features (report only, no fix proposed)\n")
    blocking = sorted(f for f, c in counts_by_feature.items() if c == 0)
    thin = sorted(f for f, c in counts_by_feature.items() if 1 <= c <= 2)
    lines.append(f"- Blocking (0 chunks): {blocking if blocking else 'none'}")
    lines.append(f"- Thin (1-2 chunks, < _N_RESULTS_PER_FEATURE={_N_RESULTS_PER_FEATURE}): {thin if thin else 'none'}")

    lines.append("\n## Decision-branch placement\n")
    if blocking:
        lines.append(
            f"**Branch: DATA-layer block.** {len(blocking)} feature(s) hold 0 chunks "
            f"in their verified range: {blocking}. The flag stays OFF for these "
            "regardless of retrieval tuning."
        )
    elif thin:
        lines.append(
            f"**Branch: viable but thin.** All non-null ranges hold >=1 chunk; "
            f"{len(thin)} feature(s) hold fewer than {_N_RESULTS_PER_FEATURE}: {thin}. "
            "The flip is viable; those features ship thin."
        )
    else:
        lines.append(
            f"**Branch: viable, full width.** Every non-null range holds "
            f">= {_N_RESULTS_PER_FEATURE} chunks. The flag flip is viable."
        )

    lines.append(f"\n## Failures\n\nTotal failures during this census: **{failures}**")
    if failures:
        lines.append(
            "\nA nonzero failure count means this census is PARTIAL -- do not "
            "treat it as complete."
        )

    try:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED writing report to {REPORT_PATH}: {exc}")
        raise

    print(f"Report written to {REPORT_PATH}")
    print(f"Total failures: {failures}")
    print(f"Blocking (0 chunks): {blocking}")
    print(f"Thin (1-2 chunks): {thin}")


if __name__ == "__main__":
    main()
