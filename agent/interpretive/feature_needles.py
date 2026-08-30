"""
agent/interpretive/feature_needles.py
THE single source of truth for the per-feature needle vocabulary -- the
short noun forms that mean "this text is about that palm feature".

WHY THIS MODULE EXISTS (S119 Step 7). The table used to live in
`palm_reading.py`, and `claim_voicing.py` could not import it: since
`palm_reading` imports `claim_voicing` at module level (to run Stage 2),
the reverse import would close a cycle. The workaround was a VERBATIM
COPY in `claim_voicing` (`_FEATURE_TRAIT_NEEDLES`), commented "kept
identical anyway so the two dictionaries never drift apart for no
reason". It drifted regardless: by S119 the copy carried 10 features
against the real 16, missing every mount added at S117 -- silently
blinding `claim_voicing`'s V-5 doctrine guard to saturn/mars/mercury/
apollo/luna/moon mentions in model output for as long as the mounts had
shipped. The copy is DELETED, not re-synced; this LEAF module is the fix
that makes re-syncing unnecessary.

LEAF MODULE -- HARD CONSTRAINT: this module must import NOTHING from
`agent.interpretive` (nor anything that transitively does). That is the
entire property that lets both `palm_reading` and `claim_voicing` import
it without reintroducing the cycle. Adding such an import would silently
re-create the exact problem this module was built to remove.
`tests/interpretive/test_feature_needles.py` pins both facts.

TWO PURPOSE-NAMED VIEWS (S119 Step 6, moved here intact at Step 7). One
table served two jobs with genuinely different requirements, and a value
edit made for one silently changed the other:

  JOB A -- RETRIEVAL_NEEDLES: does a CORPUS CHUNK talk about this
  feature? Plain substring containment against OCR-scanned book text
  (`palm_reading._chunk_supports_feature`). Wants PERMISSIVE, short,
  OCR-robust forms; the failure to avoid is a false NEGATIVE.

  JOB B -- OUTPUT_FEATURE_IDENTIFIERS: does this text NAME this feature?
  Word-boundary regex against the model's own fluent English
  (`palm_reading._check_banned_feature_mentions` + the S118
  allowed-needle derivation, and `claim_voicing`'s V-5 [FLOW] doctrine
  guard). Wants PRECISE forms that do not collide with ordinary English
  ("sunny"/"remarkable"); the failure to avoid is a false POSITIVE.

The two views hold IDENTICAL values today and are separate dict OBJECTS,
so a future per-job value edit cannot reach the other job. The asymmetric
MATCHING LOGIC (substring vs word-boundary) is NOT here -- it stays in
each consumer; this module owns only the vocabulary.
"""

from __future__ import annotations

# Needles are deliberately SHORT, single-word forms for OCR robustness.
# This corpus is OCR-scanned and unreliable at the word level -- e.g.
# pass-1's p.163 chunk renders "life" as "hfe" in one instance ("The
# line of fate may rise from the line of hfe, the wrist, the Mount of
# Luna..."). A short needle can still register a match against another,
# correctly-OCR'd occurrence of the same word elsewhere in a longer
# passage, whereas a longer/stricter multi-word phrase requirement would
# be more likely to be defeated by a single garbled word anywhere in it.
FEATURE_NEEDLES_BASE: dict[str, tuple[str, ...]] = {
    "life line": ("life",),
    "head line": ("head",),
    "heart line": ("heart",),
    "fate line": ("fate",),
    "sun line": ("sun",),
    "thumb": ("thumb",),
    "fingers": ("finger",),
    "mount of venus": ("venus",),
    "mount of jupiter": ("jupiter",),
    "mount of saturn": ("saturn",),
    # both corpus-attested for this mount (cheiro_clean_v1.json p112:
    # "THE MOUNT OF THE SUN... also called the Mount of Apollo").
    "mount of apollo": ("apollo", "sun"),
    "mount of mercury": ("mercury",),
    # Cheiro's own prose (p113) calls these "the first"/"the second"
    # mount of this name, never "positive"/"negative" or "upper"/
    # "lower" -- no single-word needle in the corpus text can tell them
    # apart, so both share the same needle. Accepted imprecision, not
    # silently patched: a chunk mentioning either Mars mount will
    # support-gate-pass for both features. Flagged in diagnostics/
    # latest_run.md, not a new mechanism.
    "mount of mars positive": ("mars",),
    "mount of mars negative": ("mars",),
    # both corpus-attested (p113 "THE MOUNT OF LUNA"; p191 "Mount of
    # the Moon").
    "mount of luna": ("luna", "moon"),
    "markings/other features": (
        "mark", "star", "cross", "island", "square", "circle", "hair",
    ),
}

# S119 STEP 6 (moved to this leaf module at Step 7): the one needle table
# above served TWO jobs with genuinely
# different requirements, and a value edit made for one silently changed
# the other. They are now two separately-named, separately-addressable
# tables, both initialised from the SAME literal -- so this split is
# value-identical by construction today (pinned by
# test_step6_both_tables_equal_the_pre_split_values) and a future
# divergence has to be written deliberately into ONE of them.
#
#   JOB A -- RETRIEVAL_NEEDLES: does a CORPUS CHUNK talk about this
#   feature? Matched with plain substring containment against OCR-scanned
#   book text (_chunk_supports_feature). Wants PERMISSIVE, short,
#   OCR-robust forms; the failure to avoid is a false NEGATIVE (dropping a
#   genuinely relevant chunk because OCR mangled a word boundary).
#
#   JOB B -- OUTPUT_FEATURE_IDENTIFIERS: does this text NAME this
#   feature? Matched with word-boundary regex against the model's own
#   fluent English (_check_banned_feature_mentions, the S118 censor, and
#   _allowed_needles_for_claimed_features which feeds it). Wants PRECISE
#   forms that do not collide with ordinary English ("sunny"/"remarkable");
#   the failure to avoid is a false POSITIVE (failing a clean reading).
#
# The asymmetric MATCHING LOGIC (substring vs word-boundary) is unchanged
# and still lives in each consumer -- Step 6 moved only which named table
# each one reads.
RETRIEVAL_NEEDLES: dict[str, tuple[str, ...]] = dict(FEATURE_NEEDLES_BASE)
OUTPUT_FEATURE_IDENTIFIERS: dict[str, tuple[str, ...]] = dict(FEATURE_NEEDLES_BASE)
