# Session: Cross-chart Ashtakavarga oracle + Sulabh grid supersession annotation

## Part 1 — new file
`tests/fixtures/jhora_ashtakavarga_cross_charts.md` — Sulabh (ref=Sagittarius),
Surbhi (ref=Libra), Sheridan (ref=Taurus) BAV/SAV grids, each with its own
21-checksum section (8 row totals + 12 column sums + grand total 337).

**Verified computationally before writing** (all three charts, all 21
checksums each): all 8 BAV row totals match canonical totals
(48/49/39/54/56/52/39/49), all 12 SAV column sums match the 7-planet sums,
and all 3 grand totals equal 337. Zero mismatches — no transcription
corrections needed this time (unlike the earlier David Sun-Leo fixture).

## Part 2 — surgical annotation
`tests/fixtures/jhora_sulabh.md` — added the SUPERSEDED notice immediately
above its Session-27 Ashtakavarga section, pointing to the new
checksum-validated cross-chart file. Old grid left in place, not deleted.

**Old-vs-new comparison (requested finding):** decoded the old grid's South
Indian fixed-grid screen positions to Aries-absolute order:
`[25,25,18,26,28,33,33,25,28,36,31,29]`. Compared against the new
Chart 1 (Sulabh, reference=Sagittarius) SAV row: **identical, cell-for-cell,
all 12 signs.** The old capture's reference sign was never recorded, but
this match strongly suggests it also happened to use the natal lagna
(Sagittarius) — coincidence or default UI state, not verifiable now. Old
grid is superseded on provenance grounds (undocumented reference), not
because its values are shown to be wrong.

## Verification before editing
`grep -rl jhora_sulabh --include=*.py .` (excluding PyJHora-main): zero
hits — no test consumes the old grid, confirming the annotation-only edit
carries no test risk.

## Full suite

```
2018 passed, 3 skipped, 1 warning in 87.20s (0:01:27)
```

Unchanged, as required. Fixture files only — no source or test logic
touched.
