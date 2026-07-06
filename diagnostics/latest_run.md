# Session 54: PyJHora Ashtakavarga indexing diagnostic + David BAV/SAV fixture

**Diagnostic (read-only, no files modified):** PyJHora's `get_ashtaka_varga()`
(ashtakavarga.py:27-58) is always Aries-absolute (index 0=Aries). GUI display
diverges by chart style: North Indian/Sudarshan rotates to lagna-relative at
display time (horo_chart_tabs.py:5754); South/East Indian stay Aries-absolute
on a fixed grid with ascendant marked via lookup table, not rotation. Full
findings: diagnostics/pyjhora_ashtakavarga_indexing_20260706.md.

**Fixture:** tests/fixtures/jhora_david_ashtakavarga.md (JHora v8, David,
reference=Virgo lagna). Found and fixed a transcription error (Sun-Leo 4->5)
via 21-checksum cross-verification (8 row totals + 12 column sums + 337
grand total) — all now pass. User confirmed the correction before writing.

Both files committed (8a3a493) and pushed to origin/main. No source or
test files touched.
