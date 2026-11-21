# S166 de-minify corpus JSONs + grouped commits

- de-minify: both JSONs re-pretty-printed at HEAD's indent (2, LF). Diff +651/-3 total (domain_tags +637, chapter_index +17/-3). segments 5187->5229 (+42), units 109->110. Not a full-file rewrite.
- suite (before commits): 5427 passed, 9 skipped, 2 xfailed, 1 warning (195.57s)
- commit B (corpus): cfbb189
- commit C (docs): 69e7733
- commit D (probes/diagnostics housekeeping): the HEAD commit after this file was committed (see git log -1)
- not pushed. diagnostics/latest_run.md is gitignored, so it was not added to group D.
