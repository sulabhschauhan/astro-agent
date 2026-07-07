# P6 Jaimini: Chara Karakas kernel (PVR Ch.8 Section 8.2)

**Task type:** implementation. One file only.

## File touched

`agent/calculations/jaimini/karakas.py` — full replacement of the 1-line
stub with a pure-function kernel:

- `compute_chara_karakas(planet_longitudes: dict[str, float]) -> CharaKarakasResult`
- `CharaKarakasResult` — frozen dataclass, two tuple-of-pairs fields
  (`karakas`, `advancement`), genuinely hashable (no dict fields).

No other file in `agent/calculations/jaimini/` was touched — `arudha.py`
and `padas.py` remain 1-line stubs. No test file added. `CLAUDE.md` and
`SESSION_LOG.md` not touched (per task scope).

## Spec source

PVR Narasimha Rao, "Vedic Astrology: An Integrated Approach", Ch.8
"Karakas", Section 8.1-8.2, printed pp.79-81 (PDF pp.90-92), Table 13 —
verbatim text as ratified in the prior Session 57 source-verification
pass (`diagnostics/latest_run.md` at that time; superseded by this file).

## Design points implemented

1. **Pure function, no ephemeris calls** — same pattern as
   `agent/calculations/transits/av_transit_scorer.py`. Caller supplies
   `planet_longitudes`.
2. **Key validation**: exactly 8 required keys (Sun, Moon, Mars, Mercury,
   Jupiter, Venus, Saturn, Rahu). Missing/extra keys raise `ValueError`
   naming them. `"Ketu"` present raises a **distinct** `ValueError`
   citing PVR Section 8.1's own reasoning (Ketu = moksha karaka, excluded
   from chara karakas by design) — not folded into the generic
   missing/extra message.
3. **Advancement rule**: 7 planets = `longitude % 30.0`; Rahu =
   `30.0 - (longitude % 30.0)`. No rounding/truncation at any stage —
   ranking uses full float precision (`sorted(..., reverse=True)` on the
   raw advancement values), so the PVR degree→minute→second tie-break
   cascade is satisfied automatically by ordinary float comparison.
4. **Karaka order**: Table 13 rank order, AK…DK, assigned via
   `zip(_KARAKA_ORDER, ranked_planets)` after descending sort.
5. **Exact-tie handling**: if any two planets share the *exact* same
   float advancement, raises `ValueError` naming the tied planets, citing
   PVR's joint-karakatwa/sthira-karaka fallback as out-of-V1-scope and
   quoting PVR's own "rarely becomes necessary" line. Fails closed —
   never silently orders a tie by insertion order.
6. **Result shape**: `karakas: tuple[tuple[str, str], ...]` (Table-13
   order) and `advancement: tuple[tuple[str, float], ...]` (canonical
   planet order, diagnostics) — both tuple-of-pairs rather than dicts, so
   `CharaKarakasResult` is truly hashable, matching the project's other
   frozen result dataclasses (`compatibility/koota_types.py`'s
   `KootaResult`/`AshtakootResult` family).
7. Module docstring carries the full CITATION block (verbatim PVR quotes,
   page numbers, scheme justification, oracle note for the future
   validation pass). try/except limited to the three meaningful failure
   modes (Ketu, missing/extra keys, exact tie) — no blanket wrapping.

## Manual verification (not a persisted test — no test file per task scope)

Ran `compute_chara_karakas` against PVR's own worked Example 28 (Ch.8
p.81, Table 14): input longitudes Sun 12Ge47 / Moon 20Ar28 / Mars 13Ge51 /
Mercury 25Ge18 / Jupiter 5Ta40 / Venus 17Ge21 / Saturn 2Ta28 / Rahu 1Cn43.

Result matched PVR's table exactly: AK=Rahu (28°17'), AmK=Mercury
(25°18'), BK=Moon (20°28'), MK=Venus (17°21'), PiK=Mars (13°51'),
PK=Sun (12°47'), GK=Jupiter (5°40'), DK=Saturn (2°28').

Also manually exercised: Ketu-present error, missing-key error,
extra-key error, and an isolated exact-tie error (Mars/Moon forced to
identical advancement) — all four raised the expected distinct
`ValueError` messages.

## Test suite

```
2948 passed, 3 skipped, 0 failed
```

**Zero delta** from the expected baseline (2948 passed / 3 skipped / 0
failed) — no existing test imports the former stub, so this was a
no-regression change as predicted. No deviation to report.
