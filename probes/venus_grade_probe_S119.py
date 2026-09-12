"""
probes/venus_grade_probe_S119.py

Venus-only grade-discrimination probe (S119): can gpt-4o vision produce a
DIFFERENT Venus grade across two hands, and separate "merely small" from
"sunken/depressed" (different classical consequents in Cheiro -- health
vs. crime -- so conflating them is a correctness risk)? NOT imported by
the pipeline, NOT wired anywhere. Reuses S117's image-encoding helper
only (mount_development_probe_S117._encode_image); vocabulary/prompt are
new.

CORPUS VERIFICATION (done before writing this file -- see
diagnostics/latest_run.md for the grep evidence this session). All 8
proposed grades ARE genuinely Cheiro's own words, applied specifically
to the Mount of Venus, in data/cheiro/cheiro_clean_v1.json -- no drops
needed this time (contrast with S118, where 2 of 6 proposed mount-wide
grades had to be dropped as unattested):
  - "well developed"        -- p112 ("Venus be well developed, it
                                indicates strong and robust health")
  - "small"                 -- p112 ("A small Mount of Venus betrays
                                poor health")
  - "abnormally large"      -- p112 ("The Mount of Venus, abnormally
                                large, indicates a violent passion")
  - "full and large"        -- p183 ("the person with the mount full
                                and large")
  - "very poor development" -- p183 ("a very poor development of the
                                Mount of Venus")
  - "not well developed"    -- p222 ("the Mount of Venus is not well
                                developed")
  - "depressed"              -- p221 ("The Mount of Venus may be either
                                depressed on the hand, or very high.
                                When depressed, such a subject will
                                commit crime simply for the sake of
                                crime")
  - "very high"              -- p221 (same sentence -- "or very high...
                                when high, the crime will be committed
                                more for the sake of satisfying the
                                animal desires")

Two-layer response per call, per hand: (1) a raw VISUAL OBSERVATION on a
closed scale (fullness/size, elevation, distinctly-sunken-or-not) BEFORE
any Cheiro-grade label is applied -- lets the report distinguish "vision
saw something different but mapped it the same" from "vision genuinely
saw the same thing"; (2) the MAPPED Cheiro grade from the 8-term set
above (or "cannot-tell", first-class, never forced); (3) a one-clause
reason.

Run N=3 PER HAND (6 calls total), temp=0. No enhancement, no cropping.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent))
from mount_development_probe_S117 import _encode_image  # noqa: E402 -- reuse, not reinvent

_N_RUNS = 3
_MODEL = "gpt-4o"

_FULLNESS_VALUES = frozenset({"flat", "small", "moderate", "full", "very-full-or-large"})
_ELEVATION_VALUES = frozenset({"sunken/concave", "low", "moderate", "high", "very-high"})
_SUNKEN_VALUES = frozenset({"yes", "no", "cannot-tell"})

# Corpus-verified closed set -- see module docstring for the grep
# evidence behind every value (all 8 attested, no drops this time).
_GRADE_VALUES = frozenset({
    "well developed",
    "small",
    "abnormally large",
    "full and large",
    "very poor development",
    "not well developed",
    "depressed",
    "very high",
    "cannot-tell",
})

_SYSTEM_PROMPT = """You are analysing a photograph of a human palm, looking ONLY at the Mount of Venus -- the large fleshy pad at the base of the thumb, encircled by the Life line.

Report exactly this JSON shape, no markdown:
{
  "visual_observation": {
    "fullness_size": "flat|small|moderate|full|very-full-or-large",
    "elevation": "sunken/concave|low|moderate|high|very-high",
    "distinctly_sunken_or_concave": "yes|no|cannot-tell"
  },
  "mapped_cheiro_grade": "well developed|small|abnormally large|full and large|very poor development|not well developed|depressed|very high|cannot-tell",
  "reason": "one short clause, under 15 words"
}

Field guidance:
- "visual_observation" is your RAW read of the mount's physical shape, BEFORE applying any classical label -- report exactly what you see.
- "fullness_size": how much area/volume the pad occupies relative to the rest of the palm.
- "elevation": how raised the pad is above the surrounding palm surface.
- "distinctly_sunken_or_concave": answer "yes" ONLY if the mount looks genuinely concave/hollowed-in, not merely small or flat-but-level with the palm. This is a DIFFERENT judgment from size -- a mount can be small but level (not sunken), or it can be actively concave. Answer "no" if it is small/flat but not concave. Answer "cannot-tell" if you cannot make this distinction confidently from the image.
- "mapped_cheiro_grade": your best mapping of the visual observation onto EXACTLY one of the 9 listed grade strings (8 real grades + "cannot-tell"). Use "cannot-tell" whenever you are not confident enough to choose a specific grade -- this is a fully legitimate, expected answer, never a failure. Do NOT invent a grade outside this list.
- "reason": what you actually observed in THIS image that led to your judgment.
"""


def _run_once(client: OpenAI, mime: str, b64: str) -> dict:
    """One vision call. Returns a result dict with either 'parsed' (the
    JSON dict) or 'error' (a string) -- never raises, so one bad run
    doesn't kill the other runs."""
    try:
        response = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ],
                },
            ],
            max_tokens=400,
            temperature=0,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
    except Exception as exc:  # noqa: BLE001 -- a probe run failing must not kill the other runs
        return {"raw": None, "parsed": None, "error": f"{type(exc).__name__}: {exc}"}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {"raw": raw, "parsed": None, "error": f"JSONDecodeError: {exc}"}

    return {"raw": raw, "parsed": parsed, "error": None}


def _validate_closed_vocab(parsed: dict) -> dict:
    """Reports, never coerces: off-vocab values in any of the 4 closed-
    vocab fields. Purely diagnostic -- no silent fallback."""
    off_vocab: list[str] = []
    vis = parsed.get("visual_observation")
    if not isinstance(vis, dict):
        off_vocab.append("visual_observation missing or not an object")
    else:
        if vis.get("fullness_size") not in _FULLNESS_VALUES:
            off_vocab.append(f"fullness_size={vis.get('fullness_size')!r}")
        if vis.get("elevation") not in _ELEVATION_VALUES:
            off_vocab.append(f"elevation={vis.get('elevation')!r}")
        if vis.get("distinctly_sunken_or_concave") not in _SUNKEN_VALUES:
            off_vocab.append(f"distinctly_sunken_or_concave={vis.get('distinctly_sunken_or_concave')!r}")
    if parsed.get("mapped_cheiro_grade") not in _GRADE_VALUES:
        off_vocab.append(f"mapped_cheiro_grade={parsed.get('mapped_cheiro_grade')!r}")
    return {"off_vocab": off_vocab}


def run_probe_for_hand(image_path: Path, n_runs: int = _N_RUNS) -> list[dict]:
    mime, b64 = _encode_image(image_path)
    client = OpenAI()
    results = []
    for _ in range(n_runs):
        result = _run_once(client, mime, b64)
        result["vocab_check"] = _validate_closed_vocab(result["parsed"]) if result["parsed"] is not None else None
        results.append(result)
    return results


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python probes/venus_grade_probe_S119.py <hand_a_image_path> <hand_b_image_path>")
        sys.exit(1)
    hand_a_path = Path(sys.argv[1])
    hand_b_path = Path(sys.argv[2])
    for p in (hand_a_path, hand_b_path):
        if not p.exists():
            print(f"Image not found: {p}")
            sys.exit(1)

    hand_a_results = run_probe_for_hand(hand_a_path)
    hand_b_results = run_probe_for_hand(hand_b_path)

    out_path = Path(__file__).parent.parent / "diagnostics" / "venus_grade_probe_S119_raw.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({
            "hand_a": {"image": str(hand_a_path), "runs": hand_a_results},
            "hand_b": {"image": str(hand_b_path), "runs": hand_b_results},
        }, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote hand_a ({len(hand_a_results)} runs) + hand_b ({len(hand_b_results)} runs) to {out_path}")


if __name__ == "__main__":
    main()
