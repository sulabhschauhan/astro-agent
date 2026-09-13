"""
End-to-end composer wiring check (S131). ZERO API cost -- every model is stubbed.

DECISION THIS SERVES: if composer-OFF is byte-identical to pre-S131, composer-ON
renders through answer_view, and a composer failure falls back to the OFF view,
the wiring is safe to enable; else it is not.
TOKEN CEILING: none -- no model call is made.

The planner is replaced with the captured plan (Stage 1 is not what S131
changed, and its own live parsing is not under test here); the interpreter is
fed the capture's stored raw response, which is the same seam
scripts/replay_capture.py uses.

    python -m scripts.probe_composer_e2e_S131

Python 3.11.
"""
import json, re, sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1]))
from agent.astro import pipeline, answer_view

CAP = str(__import__('pathlib').Path(__file__).resolve().parents[1]
           / 'diagnostics' / 'qa_capture' / '20260913T065603Z.md')
body = open(CAP, encoding='utf-8').read()
turn = body.split('## TURN ')[1]

question = re.search(r'### question\n```\n(.*?)\n```', turn, re.S).group(1).strip()
chart_facts = json.loads(re.search(r'### chart_facts\n```json\n(.*?)\n```', turn, re.S).group(1))
plan_json = re.search(r'### plan \(Stage 1, as the PLANNER produced it\)\n```json\n(.*?)\n```', turn, re.S).group(1)
raw = re.search(r'### interpreter raw response\n```json\n(.*?)\n```', turn, re.S)
if raw is None:
    raw = re.search(r'### interpreter raw response\n```\n(.*?)\n```', turn, re.S)
interp_raw = raw.group(1)

print("plan keys:", sorted(json.loads(plan_json).keys()))


_pd = json.loads(plan_json)
_real_plan = pipeline.planner.Plan(question=question, reasoning="from capture", **{k: _pd[k] for k in
    ("domains", "houses", "time_scope", "whose_chart", "in_scope", "source")})
pipeline.planner.plan_question = lambda q, llm=None, **kw: _real_plan


def planner_llm(system, user, **kw):
    return plan_json, {"stub": True}


def interpreter_llm(system, user, **kw):
    return interp_raw, {"stub": True}


def composer_llm(system, user, **kw):
    claims = json.loads(user)["claims"]
    blocks = [{"type": "lead",
               "text": "Short version: a few supportive patterns show up, "
                       "but only some of them could be confirmed against your chart."}]
    for c in claims:
        blocks.append({"type": "claim", "claim_id": c["claim_id"],
                       "text": f"[plain rewrite {c['claim_id']}, verified={c['checked']}]"})
    return json.dumps({"blocks": blocks, "demoted": []}), {"stub": True}


print("\n=== A. composer OFF (default) -- must be unchanged from pre-S131")
off = pipeline.answer_question(question, chart_facts, llm=planner_llm,
                               interpreter_llm=interpreter_llm)
print("composed key:", off.get("composed"))
print("timings has composer?", "composer" in off["trace"]["timings"])
print("kept:", len(off["kept_claims"]), "ghosts:", off["ghost_citations"])
view_off = answer_view.render_user_answer(off)
print("view starts:", view_off[:90].replace("\n", " "))

print("\n=== B. composer ON")
on = pipeline.answer_question(question, chart_facts, llm=planner_llm,
                              interpreter_llm=interpreter_llm,
                              composer_llm=composer_llm, compose=True)
c = on["composed"]
print("composed:", c["composed"], "in:", c["claims_in"], "rendered:", c["claims_rendered"],
      "violations:", len(c["violations"]), "advisory:", len(c["condition_advisory"]))
print("timings has composer?", "composer" in on["trace"]["timings"])
print("pipeline 'answer' unchanged vs A?", on["answer"] == off["answer"])
view_on = answer_view.render_user_answer(on)
print("\n--- what the user would see ---")
print(view_on)

print("\n=== C. composer ON but the model fails -- must fall back, not crash")
bad = pipeline.answer_question(question, chart_facts, llm=planner_llm,
                               interpreter_llm=interpreter_llm,
                               composer_llm=lambda s, u, **k: ("garbage", {}),
                               compose=True)
print("composed:", bad["composed"]["composed"], "|", bad["composed"]["reason"][:50])
print("view == composer-OFF view?", answer_view.render_user_answer(bad) == view_off)
