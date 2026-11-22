"""Ingest the Tajaka aspect-yoga corpus (Ithasala/Ishrafa) as a corpus domain (S169).

Adds data/tajika_aspects_corpus.txt to the live corpus as ONE whole-chapter unit
("tajaka_yogas") in data/chapter_index_bphs.json, and tags it by life-area in
data/domain_tags_bphs.json so the planner's domain selection pulls it in (the
"whole-chapter pass-through" path -- needs_split=False, selected via the
domain_tags UNITS list). Mirrors scripts/ingest_sahams_corpus.py.

SOURCE FIDELITY: the corpus is verbatim-English B.V. Raman Varshaphal Ch.VII
(§57-63) -- no translation step, so (unlike the Devanagari saham doctrine) there
is NO Sulabh verification gate. Each segment quotes the OCR beside its gloss.

PRETTY-PRINT (S166 lock): writes with indent=2. The sahams ingest script wrote
indent=None (minified) -- a latent regression against the S166 "keep the JSONs
pretty-printed" lock; this script does NOT repeat it. Because the live files are
already pretty-printed, re-writing them with indent=2 preserves their format
(no spurious whole-file reformat diff).

SAFETY: idempotent (re-running replaces the tajaka_yogas entries, never
duplicates), DRY-RUN by default (prints the diff), writes only with --apply, and
self-checks every new record's field set against an existing record so a schema
drift aborts rather than corrupting the file. Backs up each file to
<file>.bak_S169 before writing.

    python scripts/ingest_tajaka_yogas_corpus.py            # dry run
    python scripts/ingest_tajaka_yogas_corpus.py --apply     # write

Python 3.11.
"""
from __future__ import annotations

import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(REPO, "data", "tajika_aspects_corpus.txt")
CHAPTER_INDEX = os.path.join(REPO, "data", "chapter_index_bphs.json")
DOMAIN_TAGS = os.path.join(REPO, "data", "domain_tags_bphs.json")

UNIT_ID = "tajaka_yogas"
BOOK = "B.V. Raman Varshaphal"
BACKUP_SUFFIX = ".bak_S169"

# "*" in the corpus expands to every LIFE-AREA domain (not the technique/nature
# tags, which are not subject areas).
_LIFE_AREAS = ("career", "marriage", "wealth", "children", "health", "education",
               "longevity", "travel", "property", "parents", "siblings",
               "spirituality", "enemies_conflict")

_SEG_RE = re.compile(r"\[\[seg:\s*([^|\]]+?)\s*\|\s*domains:\s*([^\]]*?)\s*\]\]")


def _approx_tokens(text: str) -> int:
    return len(text.split())


def parse_corpus(vocab: set[str]) -> tuple[str, list[dict]]:
    """Return (full_text, segments). Each segment: {segment_id, domains, text}.
    Text between one [[seg]] tag and the next belongs to that segment."""
    raw = open(CORPUS, encoding="utf-8").read()
    marks = list(_SEG_RE.finditer(raw))
    if not marks:
        sys.exit("no [[seg: ...]] tags found in corpus -- aborting")
    segs = []
    for i, m in enumerate(marks):
        sid = m.group(1).strip()
        toks = [t.strip() for t in m.group(2).split(",") if t.strip()]
        domains: list[str] = []
        for t in toks:
            if t == "*":
                domains.extend(_LIFE_AREAS)
            else:
                domains.append(t)
        domains = sorted(set(domains))
        bad = [d for d in domains if d not in vocab]
        if bad:
            sys.exit(f"segment {sid}: domains not in vocabulary: {bad}")
        end = marks[i + 1].start() if i + 1 < len(marks) else len(raw)
        body = raw[m.end():end].strip()
        segs.append({"segment_id": sid, "domains": domains, "text": body})
    return raw, segs


def main() -> None:
    apply = "--apply" in sys.argv
    ci = json.load(open(CHAPTER_INDEX, encoding="utf-8"))
    dt = json.load(open(DOMAIN_TAGS, encoding="utf-8"))
    vocab = set(dt["domain_vocabulary"])

    full_text, segs = parse_corpus(vocab)
    union = sorted({d for s in segs for d in s["domains"]})

    # --- schema templates from an existing record (self-check against drift) ---
    ci_fields = set(ci["units"][0].keys())
    dt_unit_fields = set(dt["units"][0].keys())
    dt_seg_fields = set(dt["segments"][0].keys())

    new_unit = {
        "unit_id": UNIT_ID, "book": BOOK, "kind": "chapter",
        "chapter_number": None,
        "title_raw": "B.V. Raman Varshaphal Ch.VII -- Yogas (Ithasala/Ishrafa)",
        "title_clean": "Tajaka aspect yogas (interpretive corpus)",
        "start_page_ref": None, "end_page_ref": None, "page_count": None,
        "char_count": len(full_text), "token_estimate": _approx_tokens(full_text),
        "text": full_text, "needs_split": False,
    }
    assert set(new_unit) == ci_fields, (
        f"chapter_index unit schema drift: {set(new_unit) ^ ci_fields}")

    seg_tokens = sum(_approx_tokens(s["text"]) for s in segs)
    per_domain: dict[str, dict] = {}
    for d in union:
        d_segs = [s for s in segs if d in s["domains"]]
        per_domain[d] = {"segment_count": len(d_segs),
                         "tokens": sum(_approx_tokens(s["text"]) for s in d_segs)}
    new_dt_unit = {"unit_id": UNIT_ID, "domains": union,
                   "segment_count": len(segs), "tokens": seg_tokens,
                   "per_domain": per_domain}
    assert set(new_dt_unit) == dt_unit_fields, (
        f"domain_tags unit schema drift: {set(new_dt_unit) ^ dt_unit_fields}")

    new_dt_segs = []
    for i, s in enumerate(segs, start=1):
        rec = {"segment_id": s["segment_id"], "unit_id": UNIT_ID, "ordinal": i,
               "domains": s["domains"], "confidence": "high",
               "unfittable": not s["domains"], "tokens": _approx_tokens(s["text"])}
        assert set(rec) == dt_seg_fields, (
            f"domain_tags segment schema drift: {set(rec) ^ dt_seg_fields}")
        new_dt_segs.append(rec)

    # --- idempotent: drop any prior tajaka_yogas records ---
    ci["units"] = [u for u in ci["units"] if u.get("unit_id") != UNIT_ID]
    dt["units"] = [u for u in dt["units"] if u.get("unit_id") != UNIT_ID]
    dt["segments"] = [s for s in dt["segments"] if s.get("unit_id") != UNIT_ID]

    ci["units"].append(new_unit)
    dt["units"].append(new_dt_unit)
    dt["segments"].extend(new_dt_segs)
    dt["segment_count"] = len(dt["segments"])

    print(f"corpus: {len(segs)} segments, {seg_tokens} approx-tokens, "
          f"{len(full_text)} chars")
    print(f"unit 'tajaka_yogas' tagged with life-area domains: {union}")
    print(f"per_domain segment counts: "
          f"{ {d: per_domain[d]['segment_count'] for d in union} }")
    print(f"domain_tags.segment_count -> {dt['segment_count']}")

    if not apply:
        print("\nDRY RUN -- nothing written. Re-run with --apply to write "
              f"(backs up to *{BACKUP_SUFFIX} first).")
        return

    import shutil
    for path, obj in ((CHAPTER_INDEX, ci), (DOMAIN_TAGS, dt)):
        shutil.copy2(path, path + BACKUP_SUFFIX)   # back up the original first
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)   # S166: pretty-print
    print("\nAPPLIED. Re-run pytest + a live varshaphal question to confirm the "
          "Tajika aspect corpus is retrieved.")


if __name__ == "__main__":
    main()
