"""
scripts/probe_fh_stage1_extraction.py

S69 F-H Stage-1 extraction probe. DIAGNOSTICS ONLY, THROWAWAY, READ-ONLY vs
production: no file under agent/, ingestion/, or frontend/ is imported for
its SIDE EFFECTS, only for pure-Python helpers and a by-id ChromaDB lookup.

PURPOSE: F-H (CLAUDE.md S69 queue) proposes a two-stage extract-then-voice
redesign of palm_reading.py's single-call generation, to retire the
architectural grounding failure Ring 3 pass 4 found (citations decorative,
not load-bearing -- see diagnostics/ring3_palm_rubric_S68_pass4.md). Before
any production change, this probe measures whether a Stage-1 "claim
extraction directly from gated chunks, paraphrase-or-nothing" call actually
grounds better than the current single-call generator did, using the SAME
frozen inputs pass 4 already scored -- not a fresh retrieval, so any
improvement measured here is attributable to the two-stage split itself,
not to different (possibly luckier) retrieval.

INPUTS ARE FROZEN, NOT RE-RETRIEVED. Every run's confirmed hand-description
text, and every recoverable chunk's id + verbatim text, is transplanted
below from two already-committed evidence artifacts:
  - diagnostics/dogfood_capture.md (### RUN <timestamp> blocks for
    2026-07-19T10:40:50 / 10:42:48 / 10:43:39 -- Run A/B/C) -- source of
    the confirmed LEFT/RIGHT/HAND_DETAIL field text AND each run's
    "### sources" section (the FULL per-feature gated set: page + score
    for every chunk retrieval actually surfaced to the pass-4 generator).
  - diagnostics/ring3_evidence_S68_pass4.md (per-run "Verbatim chunk text
    for every cited chunk_id" sections) -- source of chunk_id + exact
    verbatim text, but ONLY for chunks the pass-4 generator actually cited.

DOCUMENTED DATA GAP (per the instructing prompt's explicit STOP-and-report
clause -- this is the report, not a silent workaround): dogfood_capture.md's
"### sources" lists give every gated chunk's PAGE + SCORE, but chunk_id and
verbatim text were never captured for chunks the pass-4 generator did not
cite. Neither frozen artifact records that missing data, and re-retrieving
it live is explicitly out of scope for this probe. Consequence:
  - This probe's per-feature "gated set" fed to Stage-1 is therefore a
    SUBSET of true production n=3 retrieval -- exactly the chunks whose
    id+text ARE recoverable from the frozen artifacts. Every excluded
    (page, score) entry is listed in GATED_SETS' `unrecoverable` field and
    surfaced in the report, never silently dropped.
  - Cross-run inference APPLIED, and its justification: Run A and Run B
    share BYTE-IDENTICAL confirmed LEFT/RIGHT text (evidence file's own
    "byte comparison" claim) and, independently, their "### sources" lists
    show IDENTICAL (page, score, feature) triples for every LR-derived
    feature. Retrieval score is a deterministic function of (fixed chunk
    embedding, query embedding), and query embedding is a deterministic
    function of query text -- identical query text therefore forces
    identical retrieval, so an exact (page, score) match between A and B
    is treated as the SAME chunk_id, letting a chunk cited only in one of
    A/B fill the other's gated set for that entry. This inference is NOT
    applied to Run C (HAND_DETAIL changes the per-feature query text --
    directly evidenced by Run C's differing scores throughout), so Run C's
    gated set uses ONLY its own run's citations, nothing cross-filled.
  - 'markings/other features' is EXCLUDED from the probe entirely: zero of
    its 9 gated-slot appearances (3 per run x 3 runs) were ever cited in
    any of the 3 runs (confirmed directly by pass-4 Finding 5), so there is
    no recoverable chunk_id/text for this feature in any run -- nothing to
    feed Stage-1.
  - 'mount of jupiter' is EXCLUDED: 0 gated chunks in all 3 runs (correctly
    declined by production's own support gate) -- nothing to extract from.
  - Net probed feature set: life line, head line, heart line, fate line,
    thumb, fingers, mount of venus (7 features, uniform across all 3 runs).

MATRIX: 3 runs x 2 models (gpt-4o, gpt-4o-mini) x 2 temperatures (0, 0.3)
= 12 cells; each cell issues one extraction call per probed feature that
has >=1 recoverable gated chunk for that run (all 7, every run).

NO PRODUCTION CODE TOUCHED. NO TESTS ADDED. Output:
diagnostics/fh_stage1_probe_S69.md.
"""

from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from ingestion.query_engine import get_collection  # noqa: E402  -- id-lookup only, never .search()/similarity query
from agent.interpretive.palm_reading import (  # noqa: E402  -- pure-Python parsing helpers only, no retrieval/LLM call triggered by import
    _parse_fields,
    _parse_bullet_fields,
    _gather_feature_texts,
    _READING_TIMEOUT_SECONDS,  # cited value: 30.0s, palm_reading.py's own production timeout for its single generation call -- reused verbatim as this probe's per-call timeout, not re-derived.
)

REPORT_PATH = _REPO_ROOT / "diagnostics" / "fh_stage1_probe_S69.md"

# ─── Frozen chunk text (chunk_id -> verbatim text), transplanted from ─────
# diagnostics/ring3_evidence_S68_pass4.md's per-run "Verbatim chunk text
# for every cited chunk_id" sections. Cross-checked: every chunk_id cited
# in more than one run (p112_c0, p134_c1, p163_c1) shows byte-identical
# text across all runs that cite it in the source file -- transplanted once
# here, not duplicated per run.
KNOWN_CHUNKS: dict[str, str] = {
    "cheiroslanguageo00chei_1_p112_c0": (
        "64 Cheiro’s Language of the Hand.\n\n"
        "Venus be well developed, it indicates strong and robust health. A small\n"
        "Mount of Venus betrays poor health and, consequently, less passion.\n\n"
        "The Mount of Venus, abnormally large, indicates a violent passion for the\n"
        "opposite sex.\n\n"
        "This mount denotes affection, sympathy toward others, benevolence, a\n"
        "desire to please, love and worship of beauty, love of color, and melody in\n"
        "music, and the attraction of the one sex to the other.\n\n"
        "THE MOUNT OF JUPITER.\n\n"
        "This mount is the raised formation at the base of the first finger (Plate\n"
        "XII.). When developed it shows ambition, pride, enthusiasm in anything\n"
        "attempted, and desire for power."
    ),
    "cheiroslanguageo00chei_1_p134_c1": (
        "The line of life should be long, narrow, and deep, without irregularities,\n"
        "breaks, or crosses of any kind. Such a formation promises long life, good\n"
        "health, and vitality.\n\n"
        "When the line is linked (Fig. 10, Plate XIV.) or made up of little pieces\n"
        "hkea chain, it is a sure sign of bad health, and particularly so on a soft hand.\n"
        "When the line recovers its evenness and continuity, health also is regained.\n\n"
        "When broken in the left hand and joined in the right, it threatens some\n"
        "dangerous illness; but if broken in both hands it generally signifies death.\n"
        "This is more decidedly confirmed when one branch turns back on the Mount\n"
        "of Venus (-, Plate X 11.)"
    ),
    "cheiroslanguageo00chei_1_p139_c0": (
        "The Line of Life. 85\n\n"
        "number of these lines of influence (it being remembered that only those near\n"
        "the line of life are important). Numerous lines indicate a nature dependent\n"
        "upon affection. Such people are what is called passionate in their disposition ;\n"
        "they may have many liaisons, but in their eyes love redeems all. On the\n"
        "other hand, the full, smooth Mount of Venns indicates that the individual is\n"
        "less affected by those with whom he is associated.\n\n"
        "When the line of life sweeps far out into the hand, thus allowing the\n"
        "Mount of Venus a greater scope, it is in itself a sign of good physical strength\n"
        "and long life."
    ),
    "cheiroslanguageo00chei_1_p145_c0": (
        "CHAPTER VII.\nTHE LINE OF HEAD.\n\n"
        "“To know is power “—let us then be wise,\n"
        "And use our brains with every good intent,\n"
        "That at the end we come with tired eyes\n"
        "And give to Nature more than what she lent.\nCHEIRO.\n\n"
        "Tue line of head (Plate NUL.) relates principally to the mentality of the\n"
        "subject—to the intellectual strength or weakness, to the temperament in its\n"
        "relation to talent, and to the direction and quality of the talent itself.\n\n"
        "It is of extreme importance in connection with this line that the peculiar-\n"
        "ities of the various types be borne in mind; as, for instance, a sloping line of\n"
        "head on a psychic or conic hand is not of half the importance of a sloping\n"
        "line on a square hand. We will, however, take general characteristics first,\n"
        "and proceed to consider variations afterward."
    ),
    "cheiroslanguageo00chei_1_p147_c1": (
        "When abnormally short, it foreshadows some early death from some\n"
        "mental affection.\n\n"
        "When broken in two under the Mount of Saturn, it tells of an early\n"
        "sudden death by fatality.\n\n"
        "When linked, or made up of little pieces like a chain, it denotes want of\n"
        "fixity of ideas, and indecision.\n\n"
        "When full of little islands and hair-lines, it tells of great pain to the head\n"
        "and danger of brain disease.\n\n"
        "When the line of head is so high on the hand that the space is extremely\n"
        "narrow between it and the line of heart, the head will completely rule the\n"
        "heart, if that line be the strongest, and vice versd."
    ),
    "cheiroslanguageo00chei_1_p123_c0": (
        "The Lines of the Hand. 73\n\n"
        "The main lines are known by other names, as follows:\n\n"
        "The Line of Life is also called the Vital.\n\n"
        "The Line of Head, the Natural or Cerebral.\n\n"
        "The Line of Heart, the Mensal.\n\n"
        "The Line of Fate, the Line of Destiny, or the Saturnian.\nThe Line of Sun, the Line of Brillianey, or Apollo.\n\n"
        "The Line of Health, the Hepatica, or the Liver Line.\n\n"
        "The hand is divided into two parts or hemispheres by the line of head.\n\n"
        "The upper hemisphere, containing the fingers and Mounts of Jupiter,\n"
        "Saturn, the Sun, Mereury, and Mars, represents mind, and the lower, con-\n"
        "taining the base of the hand, represents the material. It will thus be seen\n"
        "that with this clear point as a guide the student will gain an insight at once\n"
        "into the character of the subject under examination. This division has\n"
        "hitherto been ignored, but it is almost infallible in its accuracy; as, for\n"
        "example, when the predisposition is toward crime the line of head rises into\n"
        "the abnormal position shown by Plate XXIV., which, taken from life, is-one\n"
        "instance jn the thousands that can be had of the accuracy of this statement."
    ),
    "cheiroslanguageo00chei_1_p160_c2": (
        "When the line is quite bare of branches and thin, it tells of coldness of\n"
        "heart and want of affection.\n\n"
        "When bare and thin toward the pereussion or side of the hand, it denotes\n"
        "sterility.\n\n"
        "Fine lines rising up to the line of heart from the line of head denote\n"
        "those who influence our thoughts in affairs of the heart, and by being crossed\n"
        "or uncrossed denote if the affection has brought trouble or has been smooth\n"
        "and fortunate.\n\n"
        "When the lines of heart, head and hfe are very much joined together, it\n"
        "is an evil sign; in all matters of affection such a subject would stick at\n"
        "nothing to obtain his or her desires."
    ),
    "cheiroslanguageo00chei_1_p159_c3": (
        "When the line of heart is bright red, it denotes great violence of passion.\n\n"
        "When pale and broad, the subject is blasé and indifferent.\n\n"
        "When low down on the hand and thus close to the line of head, the heart\n"
        "will always interfere with the affairs of the head."
    ),
    "cheiroslanguageo00chei_1_p163_c1": (
        "The line of fate may rise from the line of hfe, the wrist, the Mount of\n"
        "Luna, the line of head, or even the line of heart.\n\n"
        "If the fate-line rise from the line of life and from that poit on 18 strong,\n"
        "suecess and riches will be won by personal merit; but if the lme be marked\n"
        "low down near the wrist and tied down, as it were, by the side of the life-line,\n"
        "it tells that the early portion of the subject’s life will be sacrificed to the\n"
        "wishes of parents or relatives (g-g, Plate XX.).\n\n"
        "When the line of fate rises from the wrist and proceeds straight up the\n"
        "hand to its destination on the Mount of Saturn, it is a sign of extreme good\n"
        "fortune and success."
    ),
    "cheiroslanguageo00chei_1_p88_c0": (
        "45 Cheiro’s Language of the Hand.\n\n"
        "formed thumb denotes strength of intellectual will; the short, thick thumb,\n"
        "brute foree and obstinacy ; the small, weak thumb, weakness of will and want\n"
        "of energy.\n\n"
        "From time immemorial the thumb has been divided into three parts,\n"
        "which are significant of the three great powers that rule the world—love,\n"
        "logie, and will.\n\n"
        "The first or nail phalange denotes will.\n\n"
        "The second phalange, logic.\n\n"
        "The third, which is the boundary of the Mount of Venus, love.\n\n"
        "When the thumb is nmequally developed, as, for instance, the first pha-\n"
        "lange extremely long, we find that the subject depends upon neither 1091 nor\n"
        "‘reason, but simply upon will."
    ),
    "cheiroslanguageo00chei_1_p88_c1": (
        "When the second phalange is much longer than the first, the subject,\n"
        "though having all the calmness and exactitude of reason, vet has not sufficient\n"
        "will and determination to carry out Ins ideas.\n\n"
        "When the third phalange is long and the thumb small, the man or woman\n"
        "is a prey to the more passionate or sensual side of the nature.\n\n"
        "One of the most interesting things in the study of the thumb is to notice\n"
        "whether the first jot is supple or stiff. When supple, the first phalange is\n"
        "allowed to bend back, and forms the thumb into an arch; when, on the con-\n"
        "trary, the thumb is stiff, the first phalange cannot be bent back, even by\n"
        "pressure ; and these two opposite peculiarities bear the greatest possible rela-\n"
        "tion to character."
    ),
    "cheiroslanguageo00chei_1_p96_c0": (
        "ot Cheivo’s Language of the Hand.\n\n"
        "his own comfort before that of others; he will desire luxury in eating, drink-\n"
        "ing, and living. When, on the contrary, the fingers at the base are shaped\n"
        "like a waist, it shows an unselfish disposition in every way, and fastidiousness\n"
        "in matters of food.\n\n"
        "When, with the fingers open, a wide space is seen between the first and\n"
        "second, it indicates great independence of thought. When the space is wide\n"
        "between the third and fourth, it indicates independence of action.\n\n"
        "THE LENGTH OF THE FINGERS IN RELATION TO ONE ANOTHER.\n\n"
        "The first finger on some hands is very short; again, on others, it is as\n"
        "long as the second, and so on."
    ),
    "cheiroslanguageo00chei_1_p98_c1": (
        "If it inclines to the line of life, it promises disappointment and trouble in\n"
        "domestic affairs, and if the rest of the hand denotes ill-health, it is an added\n"
        "sign of delicacy and trouble.\n\n"
        "When the hollow comes under the line of fate, it indicates misfortune in\n"
        "business, money, and worldly affairs.\n\n"
        "When under the Ine of heart it tells of disappoimtment in the closest\n"
        "affections.\n\n"
        "Ido not hold with other works on the subject, that the fingers must be\n"
        "longer than the palm to show the intellectual nature. The palm of the hand is\n"
        "never, properly speaking, exceeded in length by the fingers. How ean we ex-\n"
        "pect this to be the case with the square, spatulate, and philosophic types?\n"
        "The statement that in every case the fingers must be longer than the palm is\n"
        "erroneous and misleading."
    ),
    "cheiroslanguageo00chei_1_p95_c0": (
        "CHAPTER XI.\nTHE FINGERS.\n\n"
        "Frncers are either long or short, irrespective of the length of the palm to\n"
        "which they belong.\n\n"
        "Long fingers give love of detail in everything—in the decoration of a\n"
        "room, in the treatment of servants, in the management of nations, or in the\n"
        "painting of a picture. Long-fingered people are exact in matters of dress,\n"
        "quick to notice small attentions; they worry themselves over little things,\n"
        "and have oceasionally a leaning toward affectation.\n\n"
        "Short fingers are quick and impulsive. They cannot be troubled about\n"
        "little things; they take everything ex masse; they generally jwnp at con-\n"
        "elusions too hastily. They do not care so much about appearances, or for the\n"
        "conventionalities of society; they are quick in thought, and hasty and out-\n"
        "spoken 11 speech."
    ),
}

# ─── Per-run, per-feature gated sets: recoverable chunk_ids + unrecoverable ─
# (page, score) entries. Built from dogfood_capture.md's "### sources"
# lists (full n=3-ish gated set per feature) cross-referenced against which
# chunk_ids were actually cited (ring3_evidence_S68_pass4.md). See module
# docstring for the A/B cross-fill justification. 'markings/other features'
# and 'mount of jupiter' excluded entirely (see docstring).
GATED_SETS: dict[str, dict[str, dict]] = {
    "Run A": {
        "life line": {"recoverable": ["cheiroslanguageo00chei_1_p139_c0", "cheiroslanguageo00chei_1_p134_c1"],
                      "unrecoverable": [("p.134", 0.58)]},
        "head line": {"recoverable": ["cheiroslanguageo00chei_1_p145_c0", "cheiroslanguageo00chei_1_p147_c1"],
                      "unrecoverable": [("p.151", 0.5226)]},
        "heart line": {"recoverable": ["cheiroslanguageo00chei_1_p160_c2"],
                       "unrecoverable": [("p.161", 0.6188), ("p.159", 0.6061)]},
        "fate line": {"recoverable": ["cheiroslanguageo00chei_1_p163_c1"],
                      "unrecoverable": [("p.165", 0.6001), ("p.165", 0.5671)]},
        "thumb": {"recoverable": ["cheiroslanguageo00chei_1_p88_c0"],
                  "unrecoverable": [("p.87", 0.5513), ("p.88", 0.5327)]},
        "fingers": {"recoverable": ["cheiroslanguageo00chei_1_p96_c0", "cheiroslanguageo00chei_1_p98_c1"],
                    "unrecoverable": [("p.98", 0.5307)]},
        "mount of venus": {"recoverable": ["cheiroslanguageo00chei_1_p112_c0"],
                           "unrecoverable": [("p.111", 0.6521), ("p.189", 0.5677)]},
    },
    "Run B": {
        "life line": {"recoverable": ["cheiroslanguageo00chei_1_p139_c0", "cheiroslanguageo00chei_1_p134_c1"],
                      "unrecoverable": [("p.134", 0.58)]},
        "head line": {"recoverable": ["cheiroslanguageo00chei_1_p145_c0", "cheiroslanguageo00chei_1_p147_c1"],
                      "unrecoverable": [("p.151", 0.5226)]},
        "heart line": {"recoverable": ["cheiroslanguageo00chei_1_p160_c2"],
                       "unrecoverable": [("p.161", 0.6188), ("p.159", 0.6061)]},
        "fate line": {"recoverable": ["cheiroslanguageo00chei_1_p163_c1"],
                      "unrecoverable": [("p.165", 0.6001), ("p.165", 0.5671)]},
        "thumb": {"recoverable": ["cheiroslanguageo00chei_1_p88_c0"],
                  "unrecoverable": [("p.87", 0.5513), ("p.88", 0.5327)]},
        "fingers": {"recoverable": ["cheiroslanguageo00chei_1_p98_c1", "cheiroslanguageo00chei_1_p96_c0"],
                    "unrecoverable": [("p.98", 0.5307)]},
        "mount of venus": {"recoverable": ["cheiroslanguageo00chei_1_p112_c0"],
                           "unrecoverable": [("p.111", 0.6521), ("p.189", 0.5677)]},
    },
    "Run C": {
        "life line": {"recoverable": ["cheiroslanguageo00chei_1_p134_c1"],
                      "unrecoverable": [("p.135", 0.6131), ("p.134", 0.6063)]},
        "head line": {"recoverable": ["cheiroslanguageo00chei_1_p123_c0"],
                      "unrecoverable": [("p.151", 0.5897)]},
        "heart line": {"recoverable": ["cheiroslanguageo00chei_1_p159_c3"],
                       "unrecoverable": [("p.160", 0.6068), ("p.161", 0.5971)]},
        "fate line": {"recoverable": ["cheiroslanguageo00chei_1_p163_c1"],
                      "unrecoverable": [("p.162", 0.5732)]},
        "thumb": {"recoverable": ["cheiroslanguageo00chei_1_p88_c1"],
                  "unrecoverable": [("p.87", 0.5581), ("p.89", 0.5331)]},
        "fingers": {"recoverable": ["cheiroslanguageo00chei_1_p95_c0"],
                    "unrecoverable": [("p.98", 0.5694), ("p.96", 0.5251)]},
        "mount of venus": {"recoverable": ["cheiroslanguageo00chei_1_p112_c0"],
                           "unrecoverable": [("p.111", 0.6521), ("p.189", 0.5677)]},
    },
}

PROBED_FEATURES: tuple[str, ...] = (
    "life line", "head line", "heart line", "fate line", "thumb", "fingers", "mount of venus",
)

# ─── Frozen confirmed field text, transplanted verbatim from ─────────────
# dogfood_capture.md's three RUN blocks (10:40:50 / 10:42:48 / 10:43:39).
FROZEN_CONFIRMED: dict[str, dict[str, str]] = {
    "Run A": {
        "timestamp": "2026-07-19T10:40:50.482046",
        "LEFT": (
            "HAND SHAPE: Square palm, overall build is robust.\n\n"
            "FINGERS: Fingers are long relative to the palm, straight, with rounded fingertips, moderate spacing.\n\n"
            "THUMB: Medium size, set moderately low, wide angle from the palm.\n\n"
            "LIFE LINE: Present, deep, long, curves around the base of the thumb, no breaks or chains visible.\n\n"
            "HEAD LINE: Present, deep, long, slightly curved, runs across the palm, no breaks or chains visible.\n\n"
            "HEART LINE: Present, deep, long, curves slightly upward, no breaks or chains visible.\n\n"
            "FATE LINE: Barely visible.\n\n"
            "OTHER LINES: Sun line is not clearly visible; health and marriage lines not clearly visible.\n\n"
            "MOUNTS: Mount of Venus appears developed; other mounts are unremarkable.\n\n"
            "MARKS: No crosses, stars, grilles, squares, or moles clearly visible."
        ),
        "RIGHT": (
            "HAND SHAPE: Square palm, medium build\n\n"
            "FINGERS: Medium length relative to palm, straight, rounded fingertips, moderate spacing\n\n"
            "THUMB: Medium size, low set, wide angle from the palm\n\n"
            "LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks\n\n"
            "HEAD LINE: Present, deep, long, slightly curved, no clear breaks or forks\n\n"
            "HEART LINE: Present, deep, long, curves slightly upward, no clear breaks or forks\n\n"
            "FATE LINE: Barely visible\n\n"
            "OTHER LINES: Not clearly visible\n\n"
            "MOUNTS: Mount of Venus appears developed, other mounts not clearly visible\n\n"
            "MARKS: Not clearly visible"
        ),
        "HAND_DETAIL": None,
    },
    "Run B": {
        "timestamp": "2026-07-19T10:42:48.947566",
        "LEFT": None,  # byte-identical to Run A per evidence file; filled below
        "RIGHT": None,
        "HAND_DETAIL": None,
    },
    "Run C": {
        "timestamp": "2026-07-19T10:43:39.978164",
        "LEFT": None,  # byte-identical to Run A per evidence file; filled below
        "RIGHT": None,
        "HAND_DETAIL": (
            "- **Hand Shape**: The hand appears to be broad with a relatively square palm.\n"
            "- **Finger Lengths**: The fingers are of moderate length. The index finger is slightly shorter than the middle finger, and the ring finger is slightly longer than the index finger. The little finger is noticeably shorter than the others.\n"
            "- **Thumb**: The thumb is of average length and appears to have a moderate angle of flexibility from the palm.\n"
            "- **Visible Lines**:\n"
            "  - **Life Line**: A prominent line curves around the base of the thumb.\n"
            "  - **Head Line**: This line runs horizontally across the palm, starting near the life line.\n"
            "  - **Heart Line**: The heart line is visible, starting under the little finger and curving towards the index finger.\n"
            "  - **Fate Line**: There is a faint line running vertically up the center of the palm.\n"
            "- **Mounts**: The mounts under the fingers appear moderately developed.\n"
            "- **Markings**: There are no unusual markings or features visible.\n"
            "- **Other Features**: There is a presence of hair on the back of the hand and fingers."
        ),
    },
}
FROZEN_CONFIRMED["Run B"]["LEFT"] = FROZEN_CONFIRMED["Run A"]["LEFT"]
FROZEN_CONFIRMED["Run B"]["RIGHT"] = FROZEN_CONFIRMED["Run A"]["RIGHT"]
FROZEN_CONFIRMED["Run C"]["LEFT"] = FROZEN_CONFIRMED["Run A"]["LEFT"]
FROZEN_CONFIRMED["Run C"]["RIGHT"] = FROZEN_CONFIRMED["Run A"]["RIGHT"]

# ─── SC-2: pass-4 U-row (claim, chunk) pairs, transplanted from ──────────
# diagnostics/ring3_palm_rubric_S68_pass4.md's per-run claim ledgers.
# Row numbers cited per that document's own numbering. Only chunk-cited
# U-rows are included (bare [OBS] U-rows have no chunk_id to re-hit).
# p95_c0/fingers/Run C is DELIBERATELY absent (scored C, "correct
# behavior, not a hit" per the instructing prompt).
_PASS4_U_ROW_PAIRS: list[dict] = [
    # Run A
    {"run": "Run A", "rows": "4-5", "feature": "head line", "chunk_id": "cheiroslanguageo00chei_1_p145_c0",
     "clause": "reflects a strong mental capacity and intellectual vigor. Its slight curve suggests a balance between logic and creativity"},
    {"run": "Run A", "rows": "6", "feature": "head line", "chunk_id": "cheiroslanguageo00chei_1_p147_c1",
     "clause": "indicates a stable and consistent mental outlook, free from indecision or mental turmoil"},
    {"run": "Run A", "rows": "7-9", "feature": "heart line", "chunk_id": "cheiroslanguageo00chei_1_p160_c2",
     "clause": "speaks to a warm and affectionate nature. Its unbroken form suggests sincerity in emotional matters and a capacity for deep, enduring affection. This line's upward curve indicates a positive and optimistic approach to relationships"},
    {"run": "Run A", "rows": "10-11", "feature": "fate line", "chunk_id": "cheiroslanguageo00chei_1_p163_c1",
     "clause": "may not be strongly influenced by external forces or predetermined destiny. Instead, it implies that your course is more self-directed, relying on personal choices and actions rather than fate"},
    {"run": "Run A", "rows": "15", "feature": "fingers", "chunk_id": "cheiroslanguageo00chei_1_p96_c0",
     "clause": "further emphasize an intellectual and refined nature, capable of thoughtful and independent action"},
    # Run B
    {"run": "Run B", "rows": "4", "feature": "head line", "chunk_id": "cheiroslanguageo00chei_1_p145_c0",
     "clause": "strong intellect and a balanced approach to life. Its unbroken nature suggests a clear and decisive mind, free from indecision or mental turmoil"},
    {"run": "Run B", "rows": "6", "feature": "heart line", "chunk_id": "cheiroslanguageo00chei_1_p160_c2",
     "clause": "capacity for deep affection and emotional expression. Its unbroken state suggests steadiness in emotional matters, free from the turmoil of inconstancy or fleeting passions"},
    {"run": "Run B", "rows": "8-9", "feature": "fate line", "chunk_id": "cheiroslanguageo00chei_1_p163_c1",
     "clause": "destiny plays a less pronounced role in your life, indicating that personal effort and choices are more significant in shaping your path"},
    {"run": "Run B", "rows": "14", "feature": "fingers", "chunk_id": "cheiroslanguageo00chei_1_p98_c1",
     "clause": "suggest an intellectual nature and a refined approach to life"},  # CONFIRMED INVERSION, row 14
    # Run C
    {"run": "Run C", "rows": "4-5", "feature": "head line", "chunk_id": "cheiroslanguageo00chei_1_p123_c0",
     "clause": "natural balance between intellect and emotion, with a tendency towards practical and clear thinking. mental faculties have been well-developed from potential to present, allowing you to handle life's complexities with a steady mind"},
    {"run": "Run C", "rows": "6-7", "feature": "heart line", "chunk_id": "cheiroslanguageo00chei_1_p159_c3",
     "clause": "capacity for deep affection and emotional engagement. emotional life is stable and sincere, with a straightforward approach to relationships"},
    {"run": "Run C", "rows": "8-9", "feature": "fate line", "chunk_id": "cheiroslanguageo00chei_1_p163_c1",
     "clause": "life path may not be strongly influenced by external forces or destiny. life more shaped by personal choices and internal motivations than by fate or circumstance"},
    {"run": "Run C", "rows": "12-13", "feature": "thumb", "chunk_id": "cheiroslanguageo00chei_1_p88_c1",
     "clause": "balanced will and reason, with enough flexibility to adapt to circumstances. neither overly rigid nor excessively yielding, capable of making decisions with both strength and consideration"},
]

RUNS = ("Run A", "Run B", "Run C")
MODELS = ("gpt-4o", "gpt-4o-mini")
TEMPERATURES = (0, 0.3)

CALL_TIMEOUT_SECONDS = _READING_TIMEOUT_SECONDS  # = 30.0, palm_reading.py's own production reading-call timeout, reused verbatim.


# ─── Reconstruction-fidelity assert ───────────────────────────────────────

def run_fidelity_assert() -> tuple[bool, list[str]]:
    """collection.get by id (not a similarity query) for every KNOWN_CHUNKS
    entry; abort semantics owned by the caller."""
    collection = get_collection()
    ids = list(KNOWN_CHUNKS.keys())
    result = collection.get(ids=ids, include=["documents"])
    fetched = dict(zip(result["ids"], result["documents"]))

    mismatches: list[str] = []
    for cid, expected_text in KNOWN_CHUNKS.items():
        if cid not in fetched:
            mismatches.append(f"MISSING FROM CHROMADB: {cid} (requested but not returned by collection.get)")
            continue
        actual_text = fetched[cid]
        if actual_text.strip() != expected_text.strip():
            mismatches.append(
                f"TEXT MISMATCH: {cid}\n--- transplanted (expected) ---\n{expected_text!r}\n"
                f"--- live ChromaDB (actual) ---\n{actual_text!r}"
            )
    return (len(mismatches) == 0), mismatches


# ─── Extraction prompt ─────────────────────────────────────────────────────

_EXTRACTION_SYSTEM_PROMPT = """You are a claim-extraction engine for a palmistry RAG pipeline. You are given ONE observed hand feature, its confirmed physical observation(s) from a photographed hand, and a small set of retrieved reference passages ("chunks"), each labeled with a chunk_id.

Your ONLY job: for each provided chunk, decide whether it states doctrine (a meaning or interpretation) that applies to this feature, and if so extract it as a claim.

STRICT RULES:
1. Paraphrase-or-nothing: every claim must restate doctrine LITERALLY PRESENT in exactly ONE of the provided chunks. Never invent doctrine, even if you recall real palmistry teaching from training -- if no provided chunk states it, it does not go in a claim.
2. If a chunk's stated doctrine actually REJECTS or CONTRADICTS the natural inference the confirmed observation would suggest, extract it anyway, with valence="corrective".
3. If a chunk's doctrine only holds under a precondition (e.g. "if the line rises from X..."), use valence="conditional" and populate condition_text with that precondition (verbatim or lightly paraphrased). condition_text must be null for any other valence.
4. Otherwise, if a chunk directly and positively supports the observation, use valence="supports".
5. Never merge two chunks into one claim -- one claim cites exactly one chunk_id.
6. If NONE of the provided chunks state doctrine for this feature, return an empty claims list. Do not force a claim.
7. Discuss only the given feature -- do not reference any other palm feature.

Respond with a single JSON object, no prose outside it, matching exactly:
{"feature": "<given feature name, copied exactly>", "claims": [{"claim_id": "C1", "chunk_id": "<must exactly match a provided chunk_id>", "claim_text": "<paraphrase>", "valence": "supports|corrective|conditional", "condition_text": "<precondition or null>", "observation_basis": "<the confirmed observation clause this claim applies to>"}]}"""


def _build_user_prompt(feature: str, observation_texts: list[str], gated_chunks: list[tuple[str, str]]) -> str:
    obs_block = "\n".join(f"- {t}" for t in observation_texts) if observation_texts else "(none recorded)"
    chunk_block = "\n\n".join(f"[{cid}]\n{text}" for cid, text in gated_chunks)
    return (
        f"FEATURE: {feature}\n\n"
        f"CONFIRMED OBSERVATIONS (from the user's photographed hand(s)):\n{obs_block}\n\n"
        f"RETRIEVED CHUNKS (use ONLY these -- do not draw on outside knowledge):\n{chunk_block}\n\n"
        f"Extract claims per your instructions."
    )


# ─── JSON schema validation (plain Python, no pydantic) ───────────────────

_VALID_VALENCE = {"supports", "corrective", "conditional"}


def _validate_extraction_json(raw: str, expected_feature: str, allowed_chunk_ids: set[str]) -> tuple[bool, dict | None, str]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return False, None, f"JSON parse error: {exc}"

    if not isinstance(parsed, dict):
        return False, None, "top-level JSON is not an object"
    if "feature" not in parsed or "claims" not in parsed:
        return False, None, "missing 'feature' or 'claims' key"
    if not isinstance(parsed["claims"], list):
        return False, None, "'claims' is not a list"

    for i, claim in enumerate(parsed["claims"]):
        if not isinstance(claim, dict):
            return False, None, f"claims[{i}] is not an object"
        required = {"claim_id", "chunk_id", "claim_text", "valence", "condition_text", "observation_basis"}
        missing = required - set(claim.keys())
        if missing:
            return False, None, f"claims[{i}] missing keys: {missing}"
        if claim["valence"] not in _VALID_VALENCE:
            return False, None, f"claims[{i}] invalid valence: {claim['valence']!r}"
        if not isinstance(claim["chunk_id"], str) or not claim["chunk_id"]:
            return False, None, f"claims[{i}] chunk_id not a non-empty string"

    return True, parsed, ""


# ─── LLM call (try/except per call, never crashes the probe) ─────────────

@dataclass
class FeatureCallResult:
    feature: str
    status: str  # "ok" | "api_error" | "malformed_json"
    error_detail: str = ""
    claims: list[dict] = field(default_factory=list)
    latency_seconds: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    gated_chunk_ids_offered: list[str] = field(default_factory=list)


def _call_extraction(client, model: str, temperature: float, feature: str,
                      observation_texts: list[str], gated_chunks: list[tuple[str, str]]) -> FeatureCallResult:
    allowed_ids = {cid for cid, _ in gated_chunks}
    user_prompt = _build_user_prompt(feature, observation_texts, gated_chunks)
    t0 = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            timeout=CALL_TIMEOUT_SECONDS,
            response_format={"type": "json_object"},
        )
    except Exception as exc:  # noqa: BLE001 -- one bad call must not kill the probe
        return FeatureCallResult(
            feature=feature, status="api_error", error_detail=str(exc),
            latency_seconds=time.perf_counter() - t0, gated_chunk_ids_offered=sorted(allowed_ids),
        )
    latency = time.perf_counter() - t0
    raw_content = response.choices[0].message.content
    usage = getattr(response, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
    completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

    ok, parsed, err = _validate_extraction_json(raw_content, feature, allowed_ids)
    if not ok:
        return FeatureCallResult(
            feature=feature, status="malformed_json", error_detail=f"{err} | raw={raw_content!r}",
            latency_seconds=latency, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
            gated_chunk_ids_offered=sorted(allowed_ids),
        )
    return FeatureCallResult(
        feature=feature, status="ok", claims=parsed["claims"],
        latency_seconds=latency, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
        gated_chunk_ids_offered=sorted(allowed_ids),
    )


# ─── Content-word overlap (SC-2 matching + comparative metrics) ──────────

_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "of", "in", "on", "at", "to", "for",
    "with", "by", "is", "are", "was", "were", "be", "been", "being", "this",
    "that", "these", "those", "it", "its", "as", "from", "into", "which",
    "who", "whom", "your", "you", "their", "his", "her", "he", "she", "they",
    "not", "no", "than", "then", "so", "such", "if", "when", "while",
    "suggests", "suggest", "indicates", "indicate", "may", "might", "also",
})
_WORD_PATTERN = re.compile(r"[a-z]+")


def _content_words(text: str) -> set[str]:
    return {w for w in _WORD_PATTERN.findall(text.lower()) if w not in _STOPWORDS}


def _overlap_ratio(a: str, b: str) -> float:
    wa, wb = _content_words(a), _content_words(b)
    if not wa or not wb:
        return 0.0
    shared = len(wa & wb)
    return shared / min(len(wa), len(wb))


def _percentile(sorted_vals: list[float], pct: float) -> float | None:
    """Nearest-rank on a 0-indexed linear position, deterministic, no interpolation."""
    if not sorted_vals:
        return None
    idx = min(len(sorted_vals) - 1, max(0, round(pct / 100 * (len(sorted_vals) - 1))))
    return sorted_vals[idx]


# ─── Success criteria evaluation (per cell) ───────────────────────────────

def _all_claims(cell_results: dict[str, FeatureCallResult]) -> list[tuple[str, dict]]:
    """[(feature, claim_dict), ...] across all successfully-parsed feature calls in a cell."""
    out = []
    for feature, res in cell_results.items():
        if res.status == "ok":
            for c in res.claims:
                out.append((feature, c))
    return out


def evaluate_cell(cell_results: dict[str, FeatureCallResult]) -> dict:
    sc = {"SC-1": "PASS", "SC-2": "PASS", "SC-3": "PASS", "SC-4": "PASS", "SC-5": "PASS"}
    evidence: dict[str, list[str]] = {k: [] for k in sc}

    # SC-5: JSON parse rate -- any malformed/api_error feature call fails the cell.
    for feature, res in cell_results.items():
        if res.status == "malformed_json":
            sc["SC-5"] = "FAIL"
            evidence["SC-5"].append(f"{feature}: malformed JSON -- {res.error_detail}")
        elif res.status == "api_error":
            sc["SC-5"] = "FAILED(api)"
            evidence["SC-5"].append(f"{feature}: API error -- {res.error_detail}")

    all_claims = _all_claims(cell_results)

    # SC-1: zero supports-valence claims citing p98_c1.
    for feature, c in all_claims:
        if c["chunk_id"] == "cheiroslanguageo00chei_1_p98_c1" and c["valence"] == "supports":
            sc["SC-1"] = "FAIL"
            evidence["SC-1"].append(f"{feature}/{c['chunk_id']}: valence=supports, claim_text={c['claim_text']!r}")

    # SC-2: no pass-4 U-row (claim, chunk) pair reappears with valence=supports.
    for feature, c in all_claims:
        if c["valence"] != "supports":
            continue
        for u_row in _PASS4_U_ROW_PAIRS:
            if u_row["feature"] != feature or u_row["chunk_id"] != c["chunk_id"]:
                continue
            ratio = _overlap_ratio(c["claim_text"], u_row["clause"])
            shared = len(_content_words(c["claim_text"]) & _content_words(u_row["clause"]))
            if shared >= 3 and ratio >= 0.5:
                sc["SC-2"] = "FAIL"
                evidence["SC-2"].append(
                    f"{feature}/{c['chunk_id']} (pass-4 rows {u_row['rows']}, run {u_row['run']}): "
                    f"NEW claim_text={c['claim_text']!r} vs U-ROW clause={u_row['clause']!r} "
                    f"(shared_content_words={shared}, overlap_ratio={ratio:.2f})"
                )

    # SC-3: 100% of claims cite a chunk_id inside that feature's offered gated set.
    for feature, res in cell_results.items():
        if res.status != "ok":
            continue
        allowed = set(res.gated_chunk_ids_offered)
        for c in res.claims:
            if c["chunk_id"] not in allowed:
                sc["SC-3"] = "FAIL"
                evidence["SC-3"].append(
                    f"{feature}: claim cites {c['chunk_id']!r}, not in offered set {sorted(allowed)}"
                )

    # SC-4: every cell where p163_c1 is offered (fate line, all runs) must have
    # >=1 fate-line claim citing it with condition_text referencing the
    # rises-from-life-line precondition.
    fate_res = cell_results.get("fate line")
    if fate_res is not None and fate_res.status == "ok" and \
       "cheiroslanguageo00chei_1_p163_c1" in fate_res.gated_chunk_ids_offered:
        hits = [
            c for c in fate_res.claims
            if c["chunk_id"] == "cheiroslanguageo00chei_1_p163_c1"
            and c.get("condition_text")
            and ("line of life" in c["condition_text"].lower() or "life line" in c["condition_text"].lower())
        ]
        if not hits:
            sc["SC-4"] = "FAIL"
            evidence["SC-4"].append(
                f"fate line: p163_c1 offered but no claim has condition_text referencing "
                f"'line of life'/'life line'. Fate-line claims extracted: {fate_res.claims!r}"
            )

    return {"sc": sc, "evidence": evidence}


# ─── Main orchestration ───────────────────────────────────────────────────

@dataclass
class CellResult:
    run: str
    model: str
    temperature: float
    feature_results: dict[str, FeatureCallResult]
    sc_eval: dict


def build_gated_chunks(run: str, feature: str) -> list[tuple[str, str]]:
    entry = GATED_SETS[run][feature]
    return [(cid, KNOWN_CHUNKS[cid]) for cid in entry["recoverable"]]


def build_observation_texts(run: str, feature: str) -> list[str]:
    left_fields = _parse_fields(FROZEN_CONFIRMED[run]["LEFT"] or "")
    right_fields = _parse_fields(FROZEN_CONFIRMED[run]["RIGHT"] or "")
    hd_raw = FROZEN_CONFIRMED[run]["HAND_DETAIL"]
    hd_fields = _parse_bullet_fields(hd_raw) if hd_raw else {}
    texts_by_feature = _gather_feature_texts(left_fields, right_fields, hd_fields)
    return texts_by_feature.get(feature, [])


def run_probe() -> tuple[list[CellResult], list[str]]:
    from openai import OpenAI
    client = OpenAI()

    cells: list[CellResult] = []
    fatal_errors: list[str] = []

    for run in RUNS:
        for model in MODELS:
            for temperature in TEMPERATURES:
                feature_results: dict[str, FeatureCallResult] = {}
                for feature in PROBED_FEATURES:
                    gated = build_gated_chunks(run, feature)
                    if not gated:
                        continue
                    obs_texts = build_observation_texts(run, feature)
                    result = _call_extraction(client, model, temperature, feature, obs_texts, gated)
                    feature_results[feature] = result
                sc_eval = evaluate_cell(feature_results)
                cells.append(CellResult(run=run, model=model, temperature=temperature,
                                         feature_results=feature_results, sc_eval=sc_eval))
                print(f"[{datetime.now(timezone.utc).isoformat()}] cell done: "
                      f"run={run} model={model} temp={temperature} -> "
                      f"{sc_eval['sc']}")

    return cells, fatal_errors


# ─── Report writer ─────────────────────────────────────────────────────────

def _fmt_sc_row(cell: CellResult) -> str:
    sc = cell.sc_eval["sc"]
    return f"| {cell.run} | {cell.model} | {cell.temperature} | {sc['SC-1']} | {sc['SC-2']} | {sc['SC-3']} | {sc['SC-4']} | {sc['SC-5']} |"


def write_report(cells: list[CellResult], fidelity_ok: bool, fidelity_mismatches: list[str]) -> None:
    lines: list[str] = []
    lines.append("# S69 F-H Stage-1 extraction probe -- diagnostics only, throwaway")
    lines.append("")
    lines.append(f"Generated {datetime.now(timezone.utc).isoformat()}. Zero recommendations -- "
                 "measure-first; ruling is design chat's. See `scripts/probe_fh_stage1_extraction.py` "
                 "for full methodology, frozen-data provenance, and the documented gated-set-reconstruction gap.")
    lines.append("")

    lines.append("## Reconstruction-fidelity assert")
    lines.append("")
    if fidelity_ok:
        lines.append(f"**PASSED.** All {len(KNOWN_CHUNKS)} transplanted chunk_ids matched live ChromaDB "
                     "content exactly (collection.get by id, not a similarity query). All 12 cells ran.")
    else:
        lines.append(f"**FAILED -- probe aborted, no cells ran.** {len(fidelity_mismatches)} mismatch(es):")
        lines.append("")
        for m in fidelity_mismatches:
            lines.append(f"```\n{m}\n```")
    lines.append("")

    if not fidelity_ok:
        REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
        return

    lines.append("## Methodology note -- gated-set reconstruction gap (documented, not silently patched)")
    lines.append("")
    lines.append(
        "Neither frozen artifact records chunk_id/text for gated-but-never-cited chunks from pass 4's "
        "3 runs. This probe's per-feature gated set is therefore the RECOVERABLE subset only -- see "
        "GATED_SETS in the script for the exact (page, score) entries excluded per run/feature, and the "
        "module docstring for the A/B cross-fill justification (byte-identical LR query text -> "
        "identical retrieval, evidenced by identical (page, score) triples). 'markings/other features' "
        "and 'mount of jupiter' are excluded entirely (0 recoverable chunks / 0 gated chunks respectively "
        "in all 3 runs). Probed feature set: " + ", ".join(PROBED_FEATURES) + "."
    )
    lines.append("")

    lines.append("## 12-cell success-criteria matrix")
    lines.append("")
    lines.append("| Run | Model | Temp | SC-1 (no p98_c1 supports) | SC-2 (no U-row reappear) | "
                 "SC-3 (chunk_id in gated set) | SC-4 (fate-line precondition) | SC-5 (JSON parse rate) |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for cell in cells:
        lines.append(_fmt_sc_row(cell))
    lines.append("")

    lines.append("## SC failures -- verbatim claim + chunk excerpt")
    lines.append("")
    any_failure = False
    for cell in cells:
        for sc_name, ev_list in cell.sc_eval["evidence"].items():
            if not ev_list:
                continue
            any_failure = True
            lines.append(f"### {cell.run} / {cell.model} / temp={cell.temperature} -- {sc_name}")
            for ev in ev_list:
                lines.append(f"- {ev}")
            lines.append("")
    if not any_failure:
        lines.append("(none)")
        lines.append("")

    lines.append("## Full extracted inventories per cell (appendix)")
    lines.append("")
    for cell in cells:
        lines.append(f"<details><summary>{cell.run} / {cell.model} / temp={cell.temperature}</summary>")
        lines.append("")
        for feature, res in cell.feature_results.items():
            lines.append(f"**{feature}** -- status={res.status}"
                         + (f" -- {res.error_detail}" if res.status != "ok" else ""))
            lines.append(f"gated chunks offered: {res.gated_chunk_ids_offered}")
            for c in res.claims:
                lines.append(f"- `{c['claim_id']}` [{c['chunk_id']}] valence={c['valence']} "
                             f"cond={c.get('condition_text')!r}\n  claim_text: {c['claim_text']!r}\n"
                             f"  observation_basis: {c.get('observation_basis')!r}")
            lines.append("")
        lines.append("</details>")
        lines.append("")

    lines.append("## Comparative metrics (report only, no pass/fail, no proposed floor)")
    lines.append("")
    lines.append("Content-word overlap: lowercase alpha tokens minus stopword set "
                 f"({sorted(_STOPWORDS)}), overlap_ratio = |shared| / min(|claim_tokens|, |chunk_tokens|).")
    lines.append("")
    lines.append("| Run | Model | Temp | Total claims | Per-feature yield | "
                 "Overlap min/p25/median/p75/max | Prompt tok | Completion tok | Total latency (s) |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for cell in cells:
        all_claims = _all_claims(cell.feature_results)
        total_claims = len(all_claims)
        per_feature = {f: len(r.claims) for f, r in cell.feature_results.items() if r.status == "ok"}
        ratios = sorted(_overlap_ratio(c["claim_text"], KNOWN_CHUNKS.get(c["chunk_id"], "")) for _, c in all_claims)
        p_str = (f"{ratios[0]:.2f}/{_percentile(ratios,25):.2f}/{_percentile(ratios,50):.2f}/"
                f"{_percentile(ratios,75):.2f}/{ratios[-1]:.2f}") if ratios else "n/a"
        prompt_tok = sum(r.prompt_tokens for r in cell.feature_results.values())
        completion_tok = sum(r.completion_tokens for r in cell.feature_results.values())
        latency = sum(r.latency_seconds for r in cell.feature_results.values())
        lines.append(f"| {cell.run} | {cell.model} | {cell.temperature} | {total_claims} | "
                     f"{per_feature} | {p_str} | {prompt_tok} | {completion_tok} | {latency:.2f} |")
    lines.append("")
    lines.append("Pooled overlap distribution (all cells, all claims):")
    all_ratios = sorted(
        _overlap_ratio(c["claim_text"], KNOWN_CHUNKS.get(c["chunk_id"], ""))
        for cell in cells for _, c in _all_claims(cell.feature_results)
    )
    if all_ratios:
        lines.append(f"min={all_ratios[0]:.2f} p25={_percentile(all_ratios,25):.2f} "
                     f"median={_percentile(all_ratios,50):.2f} p75={_percentile(all_ratios,75):.2f} "
                     f"max={all_ratios[-1]:.2f} (n={len(all_ratios)})")
    else:
        lines.append("(no claims extracted across any cell)")
    lines.append("")
    lines.append("Token-cost note: raw prompt/completion token counts reported above, directly from "
                 "each API response's `usage` field. No dollar-cost conversion performed -- this script "
                 "has no verified current OpenAI pricing to cite as of this run; converting would risk "
                 "reporting a fabricated rate as fact.")
    lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    print("Running reconstruction-fidelity assert...")
    fidelity_ok, mismatches = run_fidelity_assert()
    if not fidelity_ok:
        print(f"FIDELITY ASSERT FAILED -- {len(mismatches)} mismatch(es). Aborting, no cells run.")
        write_report([], fidelity_ok=False, fidelity_mismatches=mismatches)
        return 1
    print("Fidelity assert PASSED. Running 12-cell matrix...")

    cells, fatal = run_probe()
    write_report(cells, fidelity_ok=True, fidelity_mismatches=[])
    print(f"Report written to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
