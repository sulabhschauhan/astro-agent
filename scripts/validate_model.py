#!/usr/bin/env python3
"""
Model validation pass for the Astro Agent interpreter stage.

RUN THIS ON YOUR LOCAL MACHINE (the cloud sandbox is firewalled from OpenAI).
    python scripts/validate_model.py                 # auto-picks best gpt-5* on your account
    python scripts/validate_model.py gpt-5           # force a model id
    python scripts/validate_model.py gpt-5.6-terra   # fallback candidate

What it checks (the only things a paid call can prove):
  1. Does the model cite REAL verse ids that exist in the payload (0 ghost citations)?
  2. Does it hold citation recall at 80k-115k-token payloads (big + revived-timing)?
  3. Actual tokens incl. hidden reasoning tokens -> real cost at reasoning_effort=minimal.
  4. Honest refusal on an out-of-scope prompt.
Writes diagnostics/latest_run.md. Makes ~4-5 calls, a few cents.
"""
import os, re, sys, json
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
for ln in open(os.path.join(ROOT, ".env"), encoding="utf-8"):
    m = re.match(r'\s*([A-Za-z_]+)\s*=\s*"?([^"\n]+?)"?\s*$', ln)
    if m: os.environ.setdefault(m.group(1), m.group(2))

from openai import OpenAI
from agent.astro import planner as P
from agent.astro import payload_builder as pb

# ---- Fix 1 applied in-memory (drop timing_dasha from dasha-computation + suppressed sub-dashas) ----
FIX_UNITS = {"bphs2_ch46", "bphs2_ch61", "bphs2_ch62", "bphs2_ch63"}
_orig_load = P._load_domain_tags
def _patched_load(path=P.DOMAIN_TAGS_PATH):
    d = _orig_load(path)
    if not d.get("_fix1_applied"):
        for s in d["segments"]:
            if s["unit_id"] in FIX_UNITS and "timing_dasha" in s["domains"]:
                s["domains"] = [x for x in s["domains"] if x != "timing_dasha"]
        per = defaultdict(lambda: defaultdict(lambda: {"segment_count": 0, "tokens": 0}))
        for s in d["segments"]:
            for dom in s["domains"]:
                per[s["unit_id"]][dom]["segment_count"] += 1
                per[s["unit_id"]][dom]["tokens"] += s.get("tokens", 0)
        for u in d["units"]:
            u["per_domain"] = {k: dict(v) for k, v in per[u["unit_id"]].items()}
        d["_fix1_applied"] = True
    return d
P._load_domain_tags = _patched_load
P._TAGS_CACHE.clear()

# ---- real chart from the committed career payload header (one chart, one source) ----
cp = json.load(open(os.path.join(ROOT, "data", "career_payload_bphs.json"), encoding="utf-8"))
CHART = {"lord_house_map": cp["header"]["lord_house_map"], "ascendant_sign": cp["header"].get("ascendant_sign")}
FACT_BLOCK = "CHART FACTS (the only chart facts you may use):\n" + \
    f"Ascendant sign: {CHART['ascendant_sign']}\n" + \
    "\n".join(f"House {h}: its lord sits in house {CHART['lord_house_map'][str(h)]}" for h in range(1, 13))

SYSTEM = (
    "You are a Vedic astrologer grounded ONLY in the numbered verses provided below, from "
    "Brihat Parashara Hora Shastra. Rules:\n"
    "- Use ONLY the verses given. Never use outside knowledge or invent doctrine.\n"
    "- Cite every claim with the verse id in square brackets exactly as given, e.g. [ch24_s013].\n"
    "- Never quote verse text; cite the id only.\n"
    "- A claim is valid only if the cited verse's condition matches the CHART FACTS.\n"
    "- If the provided verses cannot answer the question, say so plainly and refuse. Honest silence beats a guess.\n"
)

QUESTIONS = [  # (name, question, domains, time_scope, in_scope)
    ("career",          "What does my chart say about my career and profession?", ["career"], "present", True),
    ("wealth",          "Will I become wealthy, and how?",                        ["wealth"], "present", True),
    ("marriage_timing", "When will I get married?",                ["marriage", "timing_dasha"], "future", True),
    ("property",        "Will I own my own house?",                               ["property"], "present", True),
    ("out_of_scope",    "What medicine should I take for my fever?",              [],          "none",   False),
]

def pick_model(client, forced):
    if forced: return forced
    ids = [m.id for m in client.models.list().data]
    for pref in ("gpt-5.6-terra", "gpt-5.6", "gpt-5", "gpt-5-mini"):
        got = sorted([i for i in ids if i.startswith(pref)])
        if got: return got[0]
    raise SystemExit(f"No gpt-5* model on this account. Available: {sorted(i for i in ids if i.startswith('gpt'))}")

def build_prompt(doms, ts, insc):
    plan = P.Plan(question="", domains=[d for d in P.DOMAINS if d in set(doms)], houses=[1],
                  whose_chart="self", time_scope=ts, in_scope=insc, reasoning="frozen")
    if not plan.domains:
        return None, []
    sel = P.select_units(plan)
    payload = P.filter_segments_by_domain(pb.build_payload(CHART, unit_ids=sel.unit_ids), plan)
    kept = [s for s in payload["segments"] if s["kept"]]
    kept += [{"segment_id": u["unit_id"], "text": u["text"]} for u in payload.get("units", [])]  # whole-chapter units
    verse_block = "\n\n".join(f"[{s['segment_id']}] {s['text'].strip()}" for s in kept)
    ids = {s["segment_id"] for s in kept}
    return verse_block, ids

def call(client, model, system_plus_verses, user):
    kwargs = dict(model=model,
                  messages=[{"role": "system", "content": system_plus_verses},
                            {"role": "user", "content": user}])
    try:
        return client.chat.completions.create(reasoning_effort="minimal", **kwargs)
    except TypeError:
        return client.chat.completions.create(**kwargs)
    except Exception as e:
        if "reasoning_effort" in str(e):
            return client.chat.completions.create(**kwargs)
        raise

def main():
    forced = sys.argv[1] if len(sys.argv) > 1 else None
    client = OpenAI()
    model = pick_model(client, forced)
    IN, OUT, CIN = 1.25/1e6, 10/1e6, 0.125/1e6  # adjust per model if not gpt-5
    lines = [f"# Model validation — {model} — {datetime.now(timezone.utc).isoformat()}", ""]
    print(f"Validating model: {model}\n")
    for name, q, doms, ts, insc in QUESTIONS:
        verses, ids = build_prompt(doms, ts, insc)
        if verses is None:  # pipeline refuses out-of-scope with NO call
            lines += [f"## {name}: PIPELINE-REFUSED before any call (in_scope=False) — correct, $0", ""]
            print(f"{name:16} pipeline-refused (no call)"); continue
        sysmsg = SYSTEM + "\n\nVERSES:\n" + verses
        user = FACT_BLOCK + f"\n\nQUESTION: {q}\n\nAnswer using only the verses, citing ids."
        resp = call(client, model, sysmsg, user)
        ans = resp.choices[0].message.content or ""
        u = resp.usage
        rt = getattr(getattr(u, "completion_tokens_details", None), "reasoning_tokens", 0) or 0
        cited = set(re.findall(r"\[([a-zA-Z0-9_]+)\]", ans))
        real_c = sorted(cited & ids); ghost = sorted(cited - ids)
        cost = u.prompt_tokens*IN + u.completion_tokens*OUT
        refused = any(w in ans.lower() for w in ("cannot answer", "cannot be answered", "insufficient", "do not address", "refuse", "not addressed"))
        lines += [f"## {name}", f"- question: {q}",
                  f"- prompt_tokens: {u.prompt_tokens:,} | completion: {u.completion_tokens:,} | reasoning: {rt:,}",
                  f"- est cost this call: ${cost:.4f}",
                  f"- real citations ({len(real_c)}): {real_c}",
                  f"- GHOST citations ({len(ghost)}): {ghost}   <-- MUST be 0",
                  f"- looks-refused: {refused}", "", "### answer", ans, "", "---", ""]
        print(f"{name:16} in={u.prompt_tokens:>7,} out={u.completion_tokens:>5,} reasoning={rt:>5,} "
              f"real_cite={len(real_c)} ghost={len(ghost)} ${cost:.3f}")
    out = os.path.join(ROOT, "diagnostics", "latest_run.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write("\n".join(lines))
    print(f"\nwrote {out}")

if __name__ == "__main__":
    main()
