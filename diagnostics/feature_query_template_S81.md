# _build_feature_query template — origin of stray "3", change provenance — S81

READ-ONLY diagnostic. No source file edited. No re-ingestion. No pytest run.

## 1. `_build_feature_query`, verbatim

`agent/interpretive/palm_reading.py:438-444`

```python
def _build_feature_query(feature: str, quality: str) -> str:
    """Ratified variant (iii), verbatim shape from the S67 probe."""
    noun = feature.split("/")[0]
    return (
        f"what does a {quality} {noun} signify — meaning and indications "
        f"of a {quality} {noun}"
    )
```

## 2. Trace the "3"

**There is no literal "3" anywhere in `_build_feature_query`'s source.** The function
takes `quality: str` as a parameter and only ever interpolates the variables `quality`
and `noun` (`noun = feature.split("/")[0]`). No numeric literal appears in the f-string.

In production, `quality` is supplied by `_resolve_feature_quality()` (called at
`palm_reading.py:481`, one line before the query is built at line 485), which extracts
an adjectival clause from the confirmed field text (e.g. `"deep"`, `"long relative to
the palm / slightly longer than the palm"`). It is a free-text descriptor string, never
a count.

The "3" that appears in `diagnostics/chunk_existence_vs_rank_S81.md` /
`diagnostics/latest_run.md` (both written by commit `99486aa`) — `"what does a 3 fate
line signify..."` for fate_line, head_line, AND heart_line uniformly — is **not
reproducible from the committed production code path**. Evidence:

- `git log -p -S"def _build_feature_query" -- agent/interpretive/palm_reading.py`
  returns exactly ONE commit (`8c1b8ab`, S67) that ever touched this function's body.
  The function is byte-identical today to its S67 landing — nothing changed it, so
  nothing could have changed it "into" producing a literal 3.
- S68's own live probe (`diagnostics/fc_retrieval_probe_S68.md`, quoted in full in §7
  below) exercised this SAME unmodified function and got real adjective strings:
  `"what does a deep heart line signify..."`, `"what does a long relative to the palm /
  slightly longer than the palm fingers signify..."` — never a numeral.
- Repo-wide grep for the literal strings `"3 fate line"`, `"3 head line"`, `"3 heart
  line"` hits ONLY the two diagnostic files from commit `99486aa`. No script, test, or
  prior diagnostic in the tracked repo ever produced this string.

**Verdict: BUG — but not in production code.** The "3" is an artifact of whatever
script generated the `99486aa` report; that script is not present in the repository
(not committed, not found by grep, presumably run ad hoc/from scratch and discarded).
I cannot name the exact offending line — that script does not exist to inspect.
**UNKNOWN — generating script not in repo.**

What I CAN state as fact, not inference: the value is suspicious in exactly the way the
task asked to check — `_N_RESULTS_PER_FEATURE = 3` (the retrieval-count constant,
`palm_reading.py:176`) is numerically identical to the stray "3", and the same value
appears uniformly across all three features (fate/head/heart), which is the signature
of a constant substituted for a per-feature computed string rather than a genuine
per-feature quality extraction result. This is circumstantial, not traced to a line —
flagging it as the likely mix-up class (an int meant for `n_results` landing in the
`quality: str` slot), not as a confirmed root cause.

`99486aa`'s own "Template status: CHANGED from S68" line is contradicted by the
evidence above: the template has not changed since S67 (`8c1b8ab`); §5/§7 confirm this
directly.

## 3. Call site

`agent/interpretive/palm_reading.py:485-489`

```python
        query = _build_feature_query(feature, quality)
        try:
            results[feature] = search(
                query, n_results=_N_RESULTS_PER_FEATURE, book_name=_CHEIRO_BOOK
            )
```

`n_results = _N_RESULTS_PER_FEATURE`, a **named constant** defined at
`palm_reading.py:176`:

```python
_N_RESULTS_PER_FEATURE = 3
```

(not a bare literal at the call site — the literal `3` lives only at the single
definition point, line 176).

## 4. Is n_results justified?

YES. `palm_reading.py:168-175`, immediately above the constant:

```python
# THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
# Justification: S67 probe (diagnostics/latest_run.md, commit 0a738c3)
# measured the worst doctrine-first-hit rank at 2 across all 8 provable
# features under the ratified variant (iii) template -- +1 margin. Scope
# guard: this module's per-feature call sites only -- does not alter
# query_engine.DEFAULT_N_RESULTS or any other caller. Revisit trigger:
# pass-3 claim ledgers showing support routinely landing at rank 3 -- go
# to 4 before blaming the template.
```

## 5. When did the template change?

```
git log --oneline -20 -- agent/interpretive/palm_reading.py
```
(20 most recent commits touching the file — full list captured, template-relevant
commit is `8c1b8ab`, near the bottom of this range, S67-tagged.)

```
git log -S "meaning and indications" --oneline -- agent/interpretive/palm_reading.py
```
returns exactly one commit:

```
8c1b8ab S67 R1: per-feature doctrine-interrogative retrieval in palm_reading (probe-ratified template iii, n=3/feature, hand_detail lock lifted) + Ring 2 update
```

Full commit detail:
- Hash: `8c1b8abd0c64c0515617954dde07864045c3c4d4`
- Date: 2026-07-13 13:16:22 +0400
- Message: `S67 R1: per-feature doctrine-interrogative retrieval in palm_reading (probe-ratified template iii, n=3/feature, hand_detail lock lifted) + Ring 2 update` (plus standard `Co-Authored-By`/`Claude-Session` trailer lines)

The commit message does **NOT** contain the literal string `"RATIFIED: commit
authorized"`.

This is the ONLY commit that has ever touched `_build_feature_query`'s template string.
The template has not changed since (confirmed by the single-commit `-S` search result
and by direct comparison with S68's probe output in §7, which is a later, independent
exercise of the identical unmodified function).

## 6. Was the change recorded?

Searched `CLAUDE.md`, `SESSION_LOG.md`, and `SESSION_LOG_ARCHIVE_S19-S66.md` for any
mention of a query-template CHANGE after Session 68.

- `SESSION_LOG.md:138` documents the template's original S67 introduction: `template
  ("what does a {quality} {feature} signify...", variant iii)` — this is the S67
  record, not a post-S68 change.
- `SESSION_LOG.md:500-501` (S68 F-C) records that a CANDIDATE replacement
  (variant-iv, pure-Python clause assembly) was evaluated and **REJECTED** — the
  production variant-iii template was retained unchanged. This is a decision NOT to
  change the template, not a change.
- `SESSION_LOG_ARCHIVE_S19-S66.md`: no matches for `_build_feature_query`, "query
  template", or "variant iii" — expected, since the function did not exist before S65
  and was not built until S67.
- `CLAUDE.md`: one line references the S68 variant-iv rejection (Locked Decisions,
  "Query-template variant-iv rejected (Session 68...)"), consistent with the above —
  no record of any actual template change, before or after S68.

**NOT RECORDED** — because, per §5, no template change occurred after S68 (or after
S67) to record. The only documented event post-S67 is a rejection of a proposed
change, which correctly left the template untouched.

## 7. What does S68's own probe say the template was?

`diagnostics/fc_retrieval_probe_S68.md:15-16` (BASELINE = variant-iii, unmodified
production `_build_feature_query`, LR and LRH scopes):

```
| BASELINE (variant-iii) | LR | `what does a deep heart line signify — meaning and indications of a deep heart line` |
| BASELINE (variant-iii) | LRH | `what does a deep / the heart line is visible heart line signify — meaning and indications of a deep / the heart line is visible heart line` |
```

Line 7 (methodology note) confirms this is the exact unmodified production call:
"BASELINE = current production variant-iii template (`palm_reading._build_feature_query`,
unmodified) at n=10".

This directly corroborates §2/§5: the real production template has always produced
`{quality} {noun}` strings with genuine adjectival quality text (e.g. "deep"), never a
numeral, at every point it has been independently exercised — S67 (introduction), S68
(F-C/F-D probe), and by direct source inspection today.
