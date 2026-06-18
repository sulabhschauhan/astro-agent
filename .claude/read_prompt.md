# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"

TASK: Create tests/calculations/test__friendship_tables.py — structural
invariant tests for agent/calculations/core/_friendship_tables.py.
Test-only; do not modify _friendship_tables.py, dignity.py,
_dignity_tables.py, or any other file.

PATTERN: Match the style of test__dignity_tables.py — function-style
pytest, parametrize where it shrinks code without obscuring failure
messages, descriptive assertion messages on every assert. Independent of
other test files — redefine constants here rather than importing across
test files.

IMPORTS: NATURAL_FRIENDSHIP and COMPOUND_RELATIONSHIP_MAP from
agent.calculations.core._friendship_tables.

CANONICAL_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
"Saturn"] — 7 only, no Rahu/Ketu (define inline).

SECTION 1 — Completeness:
Assert NATURAL_FRIENDSHIP has exactly 7 keys, matching CANONICAL_PLANETS
exactly (as a set).

SECTION 2 — Partition completeness, all 7 planets:
For each planet, take the union of its "friends" + "neutral" + "enemies"
lists. Assert: (a) this union, as a set, equals "the other 6 canonical
planets" (i.e. CANONICAL_PLANETS minus the planet itself); (b) the three
lists have zero overlap with each other (no planet appears in two of the
three lists); (c) the planet does not appear in its own lists
(no self-reference); (d) total combined length across the three lists is
exactly 6 (catches accidental duplicates within a single list, which a
set-equality check alone could mask).

SECTION 3 — Planet-name validity (typo / scope guard):
Every planet name appearing anywhere inside any of NATURAL_FRIENDSHIP's
friends/neutral/enemies lists must be a member of CANONICAL_PLANETS. This
also catches Rahu/Ketu being accidentally included.

SECTION 4 — Full directed cross-check against the literal source grid
(this is the important one — proves asymmetry was preserved correctly,
not silently collapsed into a symmetric matrix):

Build this 7x7 directed expected-relation grid inside the test file as a
literal nested dict, exactly as given below — this is transcribed
directly from PVR's Table 7 (equivalently, the "Permanent Friendship"
table appearing identically in all 4 AstroSage reference PDFs). Row =
acting planet, column = target planet, value = the acting planet's
relation to the target. Diagonal entries (a planet's relation to itself)
are not applicable — skip those cells entirely, do not assert on them.

  EXPECTED_RELATION = {
    "Sun":     {"Moon": "Friend",  "Mars": "Friend",  "Mercury": "Neutral", "Jupiter": "Friend",  "Venus": "Enemy",   "Saturn": "Enemy"},
    "Moon":    {"Sun": "Friend",   "Mars": "Neutral", "Mercury": "Friend",  "Jupiter": "Neutral", "Venus": "Neutral", "Saturn": "Neutral"},
    "Mars":    {"Sun": "Friend",   "Moon": "Friend",  "Mercury": "Enemy",   "Jupiter": "Friend",  "Venus": "Neutral", "Saturn": "Neutral"},
    "Mercury": {"Sun": "Friend",   "Moon": "Enemy",   "Mars": "Neutral",    "Jupiter": "Neutral", "Venus": "Friend",  "Saturn": "Neutral"},
    "Jupiter": {"Sun": "Friend",   "Moon": "Friend",  "Mars": "Friend",     "Mercury": "Enemy",   "Venus": "Enemy",   "Saturn": "Neutral"},
    "Venus":   {"Sun": "Enemy",    "Moon": "Enemy",   "Mars": "Neutral",    "Mercury": "Friend",  "Jupiter": "Neutral","Saturn": "Friend"},
    "Saturn":  {"Sun": "Enemy",    "Moon": "Enemy",   "Mars": "Enemy",      "Mercury": "Friend",  "Jupiter": "Neutral","Venus": "Friend"},
  }

Write a small test-local helper that, given (actor, target), looks up
actor's relation to target by checking which of NATURAL_FRIENDSHIP[actor]'s
three lists contains target (raise a clear error in the helper if target
appears in none or more than one — that itself would indicate a data bug,
not just a test gap). Parametrize a test over all 42 ordered (actor,
target) pairs where actor != target, and assert the helper's result
matches EXPECTED_RELATION[actor][target] for every single one.

This test should incidentally prove the asymmetry is real and preserved:
do NOT add any logic that would make it pass if the data were
symmetrized — it must compare directed pairs independently, e.g.
("Moon","Mercury") and ("Mercury","Moon") are two separate parametrize
cases with two different expected values, not derived from each other.

SECTION 5 — Compound relationship map completeness:
Assert COMPOUND_RELATIONSHIP_MAP has exactly 6 keys. Assert the key set
equals the full cross product of {"Friend", "Neutral", "Enemy"} x
{"Friend", "Enemy"} exactly (6 combinations, each present once). Assert
the 6 values match PVR Table 8 exactly:
  ("Friend","Friend") -> "Good Friend"
  ("Friend","Enemy") -> "Neutral"
  ("Neutral","Friend") -> "Friend"
  ("Neutral","Enemy") -> "Enemy"
  ("Enemy","Friend") -> "Neutral"
  ("Enemy","Enemy") -> "Bad Enemy"

CONSTRAINTS:
  - Do not modify _friendship_tables.py under any circumstance, even if a
    test surfaces something unexpected — STOP and report instead.
  - Do not add tests for tatkalika friendship or pancha-dha-maitri — they
    don't exist as code yet.

AFTER EDIT: run pytest -q and report pass/fail counts. Expected: 211 + N
passing (N = new test count, no skips expected this time — every planet
pair and every compound-map entry has a definite, testable value). commit and push all to git