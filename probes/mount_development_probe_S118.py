"""
probes/mount_development_probe_S118.py

Re-run of S117's mount-development probe, swapping the invented 5-point
scale for CHEIRO'S OWN grade vocabulary, corpus-verified against
data/cheiro/cheiro_clean_v1.json (not assumed). NOT imported by the
pipeline, NOT wired anywhere -- reuses S117's image-encoding helper only
(mount_development_probe_S117._encode_image); everything vocabulary- and
prompt-related is new.

CORPUS VERIFICATION (done before writing this file, not assumed -- see
diagnostics/latest_run.md for the full grep evidence this session):
  KEPT (genuinely Cheiro's own words, applied to a MOUNT's development,
  found in cheiro_clean_v1.json):
    - "well developed"   -- cheiroslanguageo00chei_1_p112 (Venus, Sun mounts)
    - "abnormally large" -- cheiroslanguageo00chei_1_p111, _p112 (Venus)
    - "small"             -- cheiroslanguageo00chei_1_p112 (Venus: "A small
                              Mount of Venus betrays poor health")
    - "not well developed" -- cheiroslanguageo00chei_1_p222 (Venus) --
                              OUTSIDE p111-113, but genuinely Cheiro's own
                              mount-development phrase elsewhere in the
                              same book (Part on insanity/crime hand-types).
    - "depressed"          -- cheiroslanguageo00chei_1_p217 (Jupiter),
                              _p221 (Venus) -- same caveat as above.
  DROPPED (searched corpus-wide, never found applied to a MOUNT):
    - "normal": 17 corpus-wide hits, every one either "abnormal"/
      "abnormally" (a different word) or a generic usage ("normal hand",
      "normal position of the line of head") -- NEVER "normal Mount of
      X" or "Mount of X is normal" anywhere in the corpus.
    - "absent": 1 corpus-wide hit (cheiroslanguageo00chei_1_p204),
      describing the LINE OF HEALTH being absent -- never a mount.

CONSEQUENCE (flagged, not silently patched around): with "normal" and
"absent" dropped, this probe's closed vocabulary has NO baseline/
"typical" grade and NO "cannot-locate" grade -- only excess (well
developed / abnormally large), deficient (small / not well developed /
depressed, one bucket, three corpus-attested synonym phrasings bundled
as a single enum value per the instructing prompt's own framing), and
the methodological refusal "cannot-tell" (not corpus vocabulary --
ours, so the model is never forced to guess). A mount Cheiro's own text
says nothing distinctive about literally has no exact-match grade in
this vocabulary; see diagnostics/latest_run.md Q4 for how this is
handled in scoring.
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

_MOUNTS = (
    "jupiter", "saturn", "apollo", "mercury",
    "mars_positive", "mars_negative", "venus", "luna",
)

_LOCATED_VALUES = frozenset({"yes", "no"})

# Corpus-verified closed set only -- see module docstring for the
# grep evidence behind each surviving value and the two dropped ones.
_DEVELOPMENT_VALUES = frozenset({
    "well developed",
    "abnormally large",
    "small / not well developed / depressed",
    "cannot-tell",
})

_SYSTEM_PROMPT = """You are analysing a photograph of a human palm for the fleshy mounts used in traditional Western (Cheiro-system) palmistry.

The 8 mounts and where each sits on the palm:
- jupiter: base of the index finger
- saturn: base of the middle finger
- apollo: base of the ring finger (also called the Sun mount)
- mercury: base of the little finger
- mars_positive: the pad between the thumb and the Life line, upper thumb-side edge of the palm (also called Mars Active/Positive)
- mars_negative: the pad on the percussion (outer) edge of the palm, opposite the thumb, above Luna (also called Mars Passive/Negative)
- venus: the large fleshy pad at the base of the thumb, encircled by the Life line
- luna: the pad on the lower percussion edge of the palm, opposite the thumb, below mars_negative (also called the Moon mount)

For EACH of the 8 mounts, report exactly these three fields:
- "located": "yes" if you can identify where this mount is in the image, "no" if you cannot (e.g. cropped out of frame, occluded).
- "development": your judgment of how raised/fleshy/prominent this mount appears, relative to the rest of the palm. Must be EXACTLY one of these four strings:
  "well developed", "abnormally large", "small / not well developed / depressed", "cannot-tell".
  Use "cannot-tell" whenever the image does not give you enough information to judge confidently -- do NOT guess. This is a fully legitimate, expected answer, not a failure.
- "reason": one short clause (under 15 words) stating what you observed.

Return ONLY valid JSON, no markdown, in exactly this shape:
{
  "jupiter": {"located": "yes|no", "development": "...", "reason": "..."},
  "saturn": {"located": "yes|no", "development": "...", "reason": "..."},
  "apollo": {"located": "yes|no", "development": "...", "reason": "..."},
  "mercury": {"located": "yes|no", "development": "...", "reason": "..."},
  "mars_positive": {"located": "yes|no", "development": "...", "reason": "..."},
  "mars_negative": {"located": "yes|no", "development": "...", "reason": "..."},
  "venus": {"located": "yes|no", "development": "...", "reason": "..."},
  "luna": {"located": "yes|no", "development": "...", "reason": "..."}
}
"""


def _run_once(client: OpenAI, mime: str, b64: str) -> dict:
    """One vision call. Returns a result dict with either 'parsed' (the
    JSON dict) or 'error' (a string) -- never raises, so one bad run
    doesn't kill the other N-1 runs."""
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
            max_tokens=1200,
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
    """Reports, never coerces: which mounts are missing from the response
    entirely, and any located/development value outside the corpus-
    verified closed set. Purely diagnostic -- no silent fallback."""
    missing_mounts = [m for m in _MOUNTS if m not in parsed]
    off_vocab: list[str] = []
    for mount in _MOUNTS:
        entry = parsed.get(mount)
        if not isinstance(entry, dict):
            continue
        located = entry.get("located")
        development = entry.get("development")
        if located not in _LOCATED_VALUES:
            off_vocab.append(f"{mount}.located={located!r}")
        if development not in _DEVELOPMENT_VALUES:
            off_vocab.append(f"{mount}.development={development!r}")
    return {"missing_mounts": missing_mounts, "off_vocab": off_vocab}


def run_probe(image_path: Path, n_runs: int = _N_RUNS) -> list[dict]:
    mime, b64 = _encode_image(image_path)
    client = OpenAI()
    results = []
    for _ in range(n_runs):
        result = _run_once(client, mime, b64)
        result["vocab_check"] = _validate_closed_vocab(result["parsed"]) if result["parsed"] is not None else None
        results.append(result)
    return results


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python probes/mount_development_probe_S118.py <image_path>")
        sys.exit(1)
    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        sys.exit(1)

    results = run_probe(image_path)

    out_path = Path(__file__).parent.parent / "diagnostics" / "mount_development_probe_S118_raw.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps({"image": str(image_path), "n_runs": len(results), "runs": results}, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {len(results)} run(s) to {out_path}")


if __name__ == "__main__":
    main()
