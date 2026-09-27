"""
scripts/build_kp_units.py  (S145 Task 3 -- KP corpus ingest into the EXISTING
chapter_index + domain_tags architecture; NO new pipeline).

Adds KP books as MORE UNITS in data/chapter_index_bphs.json and their tags in
data/domain_tags_bphs.json, so agent.astro.planner.select_units + payload_builder
pick them up UNCHANGED. (The _bphs filenames are now a slight misnomer -- they are
the single corpus index the loaders hardcode; appending KP into them is the
no-code-change seam that keeps "one pipeline".)

Per book it emits:
  - a chapter_index unit whose `text` carries NUMBERED PARAGRAPHS ("\n1. "...) so
    the EXISTING payload_builder.VERSE_SPLIT_RE segments it into paragraph-level
    segments with the SAME segment_id scheme as BPHS (verified: ids produced by
    payload_builder over the merged index == ids written here).
  - domain_tags segments + a per-unit roll-up via a RECALL-FIRST deterministic
    tagger (generous: over-tag is fine, never miss -- matches the planner's
    "widen when unsure, never narrow" doctrine). Auto first-pass, for spot-check;
    confidence is "high" for a keyword/house hit, and unfittable (kept, fail-safe)
    when nothing matched. NOT human-verified -- disclosed in diagnostics/latest_run.md.

Reuses payload_builder's OWN pure functions so segmentation/ids are byte-identical
to the live path. Pure: no LLM, no network, no swisseph. Idempotent: re-running
REPLACES existing kp_ entries, never duplicates.

Run:  python scripts/build_kp_units.py
"""
from __future__ import annotations
import re, json, sys
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from agent.astro.payload_builder import (  # noqa: E402
    strip_devanagari, split_unit_segments, approx_tokens, _short_tag_map,
)

DATA = REPO_ROOT / "data"
PDF_DIR = DATA / "pdfs" / "krishnamurti-padhdhati-vol-3-english"
CI_PATH = DATA / "chapter_index_bphs.json"
DT_PATH = DATA / "domain_tags_bphs.json"

DOMAINS_16 = ["career","marriage","wealth","children","health","education","longevity",
              "travel","property","parents","siblings","spirituality","enemies_conflict",
              "timing_dasha","technique_method","planetary_nature"]

# ---- CURATED 9 (confirmed 2026-09-27): KP's distinctive-strength books only.
# Dropped from the 21 built: Astro-Secrets 1-6 (general), True-Astrology x2 (dupes),
# KP-Astrology-Basics + KP-Simple-Rules (beginner/redundant), 6-KP-Readers (compilation),
# Vol-3 (166k general sink). Re-add any by appending here and re-running (idempotent). ----
BOOKS = [
    ("kp_reader_2", "KP", "KP Reader II (Fundamentals)", "K-P-Reader-2_djvu.txt"),
    ("kp_nakshatra_padhathi", "KP", "KP Basics of Nakshatra Padhathi", "K-P-basics-of-Nakshatra-Padhathi_djvu.txt"),
    ("kp_house_grouping", "KP", "House Grouping - KP Astrology", "House Grouping - KP Astrology_djvu.txt"),
    ("kp_longevity_hariharan", "KP", "How to Judge Longevity (K. Hariharan)", "K-P-how-to-Judge-Longevity-K-HARIHARAN_djvu.txt"),
    ("kp_longevity_judge", "KP", "How to Judge Longevity", "How to judge longevity_djvu.txt"),
    ("kp_progeny_romance", "KP", "KP Progeny & Romance", "K-P-Progeny-Romance_djvu.txt"),
    ("kp_friendship_love_marriage", "KP", "Astrological Secrets of Friendship, Love and Marriage", "Astrological Secrets of Friendship  Love and Marriage_djvu.txt"),
    ("kp_horary_times", "KP", "Jyotish KP: The Times Horary Astrology", "Jyotish-KP-the-Times-Horary-Astrology_djvu.txt"),
    ("kp_dynamics", "KP", "KP Dynamics", "K-P-Dynamics_djvu.txt"),
]

# ================================ cleaning ======================================
_JUNK = [re.compile(p, re.I) for p in [
    r"^\s*$", r"^\s*\d{1,4}\s*$", r"Sampath[_ ]?eBooks", r"^\s*Pag[e?]?\s*$",
    r"jzaZpi|Jcumaz|Le2<|Z\^xid",
]]
def clean_djvu(raw: str) -> str:
    raw = strip_devanagari(raw)
    kept = [ln.strip() for ln in raw.splitlines() if not any(p.search(ln) for p in _JUNK)]
    stream = re.sub(r"\s{2,}", " ", " ".join(kept))
    return re.sub(r"[¬-]\s+", "", stream).strip()      # rejoin hyphen-split words
def cut_front_matter(raw: str, marker="PREFACE") -> str:
    i = raw.find(marker); return raw[i:] if i != -1 else raw

# ============================== paragraphing ====================================
TARGET_WORDS = 90
def paragraph_stream(stream: str):
    sents = re.split(r"(?<=[.?!])\s+(?=[A-Z(])", stream)
    paras, buf, wc = [], [], 0
    for s in sents:
        buf.append(s); wc += len(s.split())
        if wc >= TARGET_WORDS:
            paras.append(" ".join(buf)); buf, wc = [], 0
    if buf: paras.append(" ".join(buf))
    return [p.strip() for p in paras if p.strip()]
def numbered_text(paras): return "".join(f"\n{i}. {p}\n" for i, p in enumerate(paras, 1))

# ========================= RECALL-FIRST tagger ==================================
STEMS = {
    "longevity": ["longev","ayush","ayus","maraka","marak","badhaka","badhak","bhadhak",
                  "deergha","alpay","madhyay","poornay","mrityu","marana","balarish"],
    "health":   ["disease","illness","ailment","infirm","roga","surger","operation"],
    "timing_dasha": ["dasa","dasha","bhukti","antardas","antara ","sookshma","pratyantar"],
    "technique_method": ["sub lord","sub-lord","sublord","cuspal","cusp sub","significator",
                        "star lord","constellation","nakshatra","horary","stellar","ruling planet"],
    "children": ["child","progeny","putra","daughter"],
    "marriage": ["marriage","marital","spouse","wedding"],
    "career":   ["career","profession","occupation"],
    "wealth":   ["wealth","riches","prosperity","finance"],
    "education":["education","learning"],
    "travel":   ["foreign","abroad","migration"],
    "spirituality":["spiritual","moksha","pilgrim"],
    "enemies_conflict":["litigation","lawsuit"],
    "parents":  ["mother","father","parent"],
    "siblings": ["brother","sister","co-born","coborn"],
}
WORDS = {
    "longevity": ["death","dead","die","dies","died","dying","demise","fatal","killer",
                  "unexpected end","end of life","span of life","meets his end","passes away","passed away"],
    "health":   ["sick","health","patient","hospital"],
    "children": ["son","children"],
    "marriage": ["wife","husband","married","couple"],
    "career":   ["officer","service","business"],
    "wealth":   ["money","income"],
    "education":["study","studies","exam","degree"],
    "travel":   ["travel","journey"],
    "property": ["land","vehicle","estate"],   # NOT "house" (=bhava in astrology; degenerate)
    "siblings": ["sibling"],
    "spirituality":["guru","temple","dharma","religious"],
    "enemies_conflict":["enemy","enemies","court","dispute","opponent"],
}
def _mk_stem(d): return {k:[re.compile(r"(?<![a-z])"+re.escape(x),re.I) for x in v] for k,v in d.items()}
def _mk_word(d): return {k:[re.compile(r"(?<![a-z])"+re.escape(x)+r"(?![a-z])",re.I) for x in v] for k,v in d.items()}
_STEM_RE, _WORD_RE = _mk_stem(STEMS), _mk_word(WORDS)
HOUSE_TO_DOMAIN = {8:"longevity",12:"longevity",2:"longevity",7:"longevity",3:"longevity",6:"health"}
HOUSE_RE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+house|\bhouse[s]?\s+((?:\d{1,2}[, ]*)+)", re.I)

def tag_segment(text: str):
    doms = set()
    for dom in DOMAINS_16:
        if any(rx.search(text) for rx in _STEM_RE.get(dom, [])) or \
           any(rx.search(text) for rx in _WORD_RE.get(dom, [])):
            doms.add(dom)
    for m in HOUSE_RE.finditer(text.lower()):
        for n in re.findall(r"\d{1,2}", m.group(0)):
            if int(n) in HOUSE_TO_DOMAIN: doms.add(HOUSE_TO_DOMAIN[int(n)])
    doms = [d for d in DOMAINS_16 if d in doms]
    return (doms, "high", False) if doms else ([], "low", True)  # unfittable -> fail-safe KEPT

# ============================== build one book ==================================
def build_book(uid, book, title, djvu_name, all_ids):
    raw = (PDF_DIR / djvu_name).read_text(encoding="utf-8", errors="replace")
    text = numbered_text(paragraph_stream(clean_djvu(cut_front_matter(raw))))
    unit = {"unit_id": uid, "book": book, "kind": "chapter", "chapter_number": None,
            "title_raw": title, "title_clean": title, "start_page_ref": None,
            "end_page_ref": None, "page_count": None, "char_count": len(text),
            "token_estimate": approx_tokens(text), "text": text, "needs_split": False}
    short = _short_tag_map([{"unit_id": u} for u in all_ids])[uid]
    tags = []
    for ordinal, seg_text, _ in split_unit_segments(text):
        d, conf, unfit = tag_segment(seg_text)
        tags.append({"segment_id": f"{short}_s{ordinal:03d}", "unit_id": uid,
                     "ordinal": ordinal, "domains": d, "confidence": conf,
                     "unfittable": unfit, "tokens": approx_tokens(seg_text)})
    return unit, tags

def unit_rollup(uid, tags):
    per = {}
    for t in tags:
        for d in t["domains"]:
            per.setdefault(d, {"segment_count": 0, "tokens": 0})
            per[d]["segment_count"] += 1; per[d]["tokens"] += t["tokens"]
    return {"unit_id": uid, "domains": [d for d in DOMAINS_16 if d in per],
            "segment_count": len(tags), "tokens": sum(t["tokens"] for t in tags),
            "per_domain": per}

def main():
    ci = json.loads(CI_PATH.read_text(encoding="utf-8"))
    dt = json.loads(DT_PATH.read_text(encoding="utf-8"))
    ci["units"]     = [u for u in ci["units"]     if not u["unit_id"].startswith("kp_")]
    dt["units"]     = [u for u in dt["units"]     if not u["unit_id"].startswith("kp_")]
    dt["segments"]  = [s for s in dt["segments"]  if not s["unit_id"].startswith("kp_")]

    all_ids = [u["unit_id"] for u in ci["units"]] + [b[0] for b in BOOKS]
    for uid, book, title, fn in BOOKS:
        unit, tags = build_book(uid, book, title, fn, all_ids)
        # invariant: segmentation reproduces text exactly
        assert "".join(t for _, t, _ in split_unit_segments(unit["text"])) == unit["text"]
        ci["units"].append(unit)
        dt["units"].append(unit_rollup(uid, tags))
        dt["segments"].extend(tags)
        dc = Counter(d for t in tags for d in t["domains"])
        print(f"{uid}: {len(tags)} segs, {unit['token_estimate']} tok -> {dict(dc.most_common(5))}")

    dt["segment_count"] = len(dt["segments"])
    dt["generated_at"] = datetime.now(timezone.utc).isoformat()
    dt["generated_by"] = "scripts/build_domain_tags.py + scripts/build_kp_units.py (KP append)"
    CI_PATH.write_text(json.dumps(ci, ensure_ascii=False, indent=2), encoding="utf-8")
    DT_PATH.write_text(json.dumps(dt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"merged: {len(ci['units'])} units, {dt['segment_count']} segments")

if __name__ == "__main__":
    main()
