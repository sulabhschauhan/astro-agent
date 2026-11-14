"""Parameter-compatibility probe (~$0.001; 2-6 tiny calls, 5 output tokens each).

DECISION THIS SERVES: do the palm-call model swaps need param-hardening, or can the
existing call shape stand? The palm code calls chat.completions.create with
`max_tokens=` + `temperature=0` + response_format=json (the gpt-4o shape). GPT-6-gen
models may reject a non-default `temperature` AND/OR require `max_completion_tokens`
instead of `max_tokens`. This checks the EXACT shape, per model. It is a PARAMETER
check, not a quality test -- 5 output tokens, trivial prompt.

    python scripts/param_compat_probe.py
"""
from __future__ import annotations

import datetime
import os
import shutil
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = ["gpt-6-luna", "gpt-6.1-terra"]
MSG = [{"role": "user", "content": "Reply with the JSON {\"ok\": true}"}]


def _try(client, **kw):
    """Return (ok, detail). detail is the error type:message on failure."""
    try:
        r = client.chat.completions.create(messages=MSG,
                                           response_format={"type": "json_object"}, **kw)
        return True, (r.choices[0].message.content or "").strip()[:40]
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {str(e)[:160]}"


def main() -> int:
    from openai import OpenAI
    client = OpenAI()
    out = ["# Param-compat probe (per model; palm call shape)", ""]
    for m in MODELS:
        out.append(f"## {m}")
        # 1. EXACT palm shape: max_tokens + temperature=0
        ok1, d1 = _try(client, model=m, max_tokens=5, temperature=0)
        out.append(f"- max_tokens + temperature=0  -> {'OK' if ok1 else 'FAIL'}  {d1}")
        if ok1:
            out.append("  => palm calls work AS-IS on this model; no hardening needed.")
            out.append("")
            continue
        # 2. isolate which param: drop temperature, keep max_tokens
        ok2, d2 = _try(client, model=m, max_tokens=5)
        out.append(f"- max_tokens (no temperature)  -> {'OK' if ok2 else 'FAIL'}  {d2}")
        # 3. swap max_tokens -> max_completion_tokens, keep temperature=0
        ok3, d3 = _try(client, model=m, max_completion_tokens=5, temperature=0)
        out.append(f"- max_completion_tokens + temp=0 -> {'OK' if ok3 else 'FAIL'}  {d3}")
        # 4. both fixes: max_completion_tokens, no temperature
        ok4, d4 = _try(client, model=m, max_completion_tokens=5)
        out.append(f"- max_completion_tokens (no temp)-> {'OK' if ok4 else 'FAIL'}  {d4}")
        # verdict
        need = []
        if ok2 and not ok1:
            need.append("drop/omit temperature")
        if ok3 and not ok2:
            need.append("use max_completion_tokens not max_tokens")
        if not any([ok1, ok2, ok3, ok4]):
            need.append("NONE WORKED -- inspect errors above before swapping")
        out.append(f"  => FIX NEEDED: {', '.join(need) or 'see errors'}")
        out.append("")

    text = "\n".join(out)
    print(text)
    runs = os.path.join(_ROOT, "diagnostics", "runs")
    os.makedirs(runs, exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(runs, f"{ts}_param_compat_probe.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    shutil.copyfile(path, os.path.join(_ROOT, "diagnostics", "latest_run.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
