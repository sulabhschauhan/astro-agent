# P7 Muhurta wiring, step 1 of 5: chart_profile.py builder

Session 64. Adds `build_muhurta_profile(chart_data, evaluated_at_jd=None)`
to `agent/infra/chart_profile.py`. ONE FILE, as scoped. NOT committed --
design chat ratification pending per the prompt's own constraint.

## Step 0 gate: find_muhurta_windows() signature check

Read `agent/calculations/transits/muhurta_scorer.py` before writing any
code. Confirmed signature matches the assumed shape exactly -- did not
stop:

```python
def find_muhurta_windows(
    natal_moon_sign: int,   # 0=Aries..11=Pisces
    janma_nakshatra: int,   # 0=Ashwini..26=Revati
    start_jd: float,
    end_jd: float,
) -> list[MuhurtaWindow]:
```

`MuhurtaWindow` fields: `start_jd, end_jd, tier (MuhurtaTier), chandrabala,
tarabala, panchaka, is_janma_rashi, is_janma_tara, favorable_count,
warnings`. Contiguous tiling of `[start_jd, end_jd]`, no gaps, raises
`ValueError` on out-of-range natal identifiers or `start_jd > end_jd`.

## Blocking conflict surfaced before editing, resolved via AskUserQuestion

The prompt asked `build_muhurta_profile()` to **return a `DomainAnswer`**.
`chart_profile.py`'s own module docstring locks that construction to the
not-yet-built Result Formatter: *"this module intentionally contains no
Result Formatter (DomainChartProfile -> DomainAnswer rendering)"*; the
`DomainAnswer` dataclass docstring itself: *"this module does not
construct DomainAnswer instances itself."* Verified via grep that every
sibling domain (`_format_arudha_lagna`, `_format_upapada`, and 5 other
`DomainAnswer(...)` call sites) constructs `DomainAnswer` exclusively in
`result_formatter.py`, never in `chart_profile.py`. Complying literally
would have been a first-of-its-kind break of a stated locked boundary, in
a step explicitly scoped to chart_profile.py only ("no formatter edits
this prompt").

Surfaced via `AskUserQuestion` rather than guessing either direction.
**User selected: return a plain payload dict**, matching
`build_arudha_lagna_profile()`/`build_upapada_profile()`'s existing
precedent exactly. `DomainAnswer` assembly for `domain="muhurta_window"`
is deferred to the formatter step (step 2 of 5).

## Design decisions made while implementing

- **natal_moon_sign / janma_nakshatra extraction**: prompt said "from
  chart_data's Moon longitude." Verified against code instead of
  complying literally (per the standing "verify task prompts against
  code" convention) -- no sibling builder derives Moon sign/nakshatra via
  an ephemeris longitude call for this purpose. The sade_sati branch of
  `build_domain_profile()` and `_koota_natal_info_from_chart()` both read
  the pre-computed strings directly: `SIGNS.index(chart_data["lagna_chart"]
  ["rasi"])` / `NAKSHATRAS.index(chart_data["lagna_chart"]["nakshatra"])`.
  `find_muhurta_windows()` only needs the integer indices, not precise
  longitude, so this function reuses that exact existing access pattern
  rather than inventing a new ephemeris-based one.
- **evaluated_at_jd default**: `datetime.now(timezone.utc)` ->
  `hour_decimal` -> `swe.julday(...)`, byte-identical to
  `orchestrator.answer_question()`'s own now-capture (orchestrator.py:213-215).
- **Scan window**: `[evaluated_at_jd, evaluated_at_jd + 7.0]`, new module
  constant `_MUHURTA_SCAN_WINDOW_DAYS = 7.0` with the specified
  threshold-discipline comment (Chandrabala ~2.27d/sign, Tarabala
  ~1d/nakshatra cadence; S24 scans measured 4 and 8 windows/7d;
  explicit-date parsing deferred V1.1).
- **Import**: `from agent.calculations.transits.muhurta_scorer import
  find_muhurta_windows` -- direct module path, `transits/__init__.py`
  stays empty (locked convention, matches every other transits import in
  this file).
- **Two distinct "tier" fields, documented, not renamed**: each window
  dict's `"tier"` key is `MuhurtaTier.value` (per-window quality:
  `TIER_1`/`TIER_2`/`TIER_3`). The payload dict's own top-level `"tier"`
  key is the pipeline's `AnswerTier` value, always `"TIER_3_MUHURTA"` --
  same meta-passthrough-key convention `build_arudha_lagna_profile`/
  `build_upapada_profile` already use. Docstring explicitly flags these
  as distinct enums so a future reader doesn't conflate them.
- **sources**: `("muhurta_scorer.py",)` -- the direct call site, matching
  arudha/upapada's own precedent of naming only the immediate module
  `chart_profile.py` calls, not its transitive internals (padas.py's
  precedent: it doesn't list strength.py even though it calls
  `stronger_co_lord()` internally; muhurta_scorer.py composes
  chandrabala/tarabala/panchaka internally the same way).
- **Error handling**: `ValueError` from `find_muhurta_windows()`'s own
  input validation re-raised unmodified (bare `raise`); anything else
  (e.g. `EphemerisError` from a sub-limb finder's Moon/Saturn calc)
  wrapped as `RuntimeError` naming the failing call, matching this file's
  existing wrap-except-ValueError pattern used elsewhere (e.g.
  `_build_bhava_pada_profile`'s own documented precedent).
- **Not wired**: no edit to `build_domain_profile()`'s dispatch or
  `_VALID_DOMAINS` -- this step adds only the standalone builder function,
  same staged-rollout precedent as av_transit/arudha_lagna/upapada_lagna
  landing their builder before their dispatch branch. Nothing calls this
  function yet.

## Return shape

```python
{
    "windows": [
        {
            "start_jd": float,
            "end_jd": float,
            "tier": str,              # MuhurtaTier value, e.g. "TIER_1"
            "favorable_count": int,   # 0-2, Chandrabala + Tarabala only
            "warnings": tuple[str, ...],
        },
        ...
    ],
    "tier": "TIER_3_MUHURTA",         # AnswerTier value, meta passthrough
    "sources": ("muhurta_scorer.py",),
}
```

Recommended values for the later `build_domain_profile()` wiring step
(not applied here, since that branch doesn't exist yet): `stub_caveats =
()` (no ephemeris stubs in the Chandrabala/Tarabala/Panchaka chain --
all three sub-limbs are real, oracle-validated calculations, not
stubbed), `uncertainty_virupa = 0.0` (no virupa-axis concept applies to
Muhurta scoring), `uncertainty_days = 0.0` (payload carries no dated
claims beyond the window boundaries it already returns explicitly).

## Test run

```
python -m pytest -q
3134 passed, 3 skipped, 0 failed  (84.49s)
```

Matches the expected 3134/3/0 baseline exactly -- confirms the new
function is fully inert until wired in a later step.

## Status

Not committed. Awaiting design-chat ratification per the prompt's own
constraint before any commit.
