"""Step 3 synthetic differential -- typed-relationship arc, S99.
Hand-crafted hardest-case-first battery covering all 8 typed tokens: multi
accumulation, single-scalar + duplicate-guard, location present/absent,
off-registry type/target/mount, malformed line, "none", header-recognized-
but-no-data, and duplicate-location-for-same-target-within-a-multi-type.
"""
import sys
sys.path.insert(0, ".")
from agent.interpretive.observation_extractor import extract_relations

RAW = """\
HEAD LINE: present
  RELATIONSHIP: cuts Line of Heart at Mount of Jupiter
  RELATIONSHIP: cuts Line of Fate
  RELATIONSHIP: cut_by Line of Life
  RELATIONSHIP: touches Mount of Saturn
  RELATIONSHIP: meets Line of Health at Mount of Mercury
  RELATIONSHIP: joins_at_origin Line of Life
  RELATIONSHIP: stopped_by Line of Fate at Mount of Luna
  RELATIONSHIP: takes_possession_of Mount of Venus
  RELATIONSHIP: branch_in Mount of Jupiter
  RELATIONSHIP: stopped_by Line of Heart
  RELATIONSHIP: cuts Line of Heart at Mount of Saturn
  RELATIONSHIP: cuts NotARealTarget
  RELATIONSHIP: not_a_real_type Line of Fate
  RELATIONSHIP: malformednospace
  RELATIONSHIP: touches Mount of Jupiter at NotARealMount

HEART LINE: present
  RELATIONSHIP: none

LINE OF HEALTH: present
  RELATIONSHIP: cuts Line of Head
  RELATIONSHIP: cuts Line of Fate at Mount of Saturn

LINE OF MARRIAGE: not clearly visible
"""

EXPECTED = {
    "Line of Head": {
        "cuts": {"Line of Heart", "Line of Fate"},
        "cuts__location": {"Line of Heart": "Mount of Jupiter"},
        "cut_by": {"Line of Life"},
        "touches": {"Mount of Saturn", "Mount of Jupiter"},
        "meets": {"Line of Health"},
        "meets__location": {"Line of Health": "Mount of Mercury"},
        "joins_at_origin": {"Line of Life"},
        "stopped_by": "Line of Fate",
        "stopped_by__location": {"Line of Fate": "Mount of Luna"},
        "takes_possession_of": "Mount of Venus",
        "branch_in": "Mount of Jupiter",
    },
    "Line of Health": {
        "cuts": {"Line of Head", "Line of Fate"},
        "cuts__location": {"Line of Fate": "Mount of Saturn"},
    },
}

result = extract_relations(RAW)
targets = result["targets"]

print("=== Full parsed targets dict ===")
import pprint
pprint.pprint(targets)
print()

print("=== Diff against hand-expected ===")
all_match = True
all_features = set(targets) | set(EXPECTED)
for feat in sorted(all_features):
    got = targets.get(feat, "<ABSENT>")
    exp = EXPECTED.get(feat, "<ABSENT>")
    match = got == exp
    all_match = all_match and match
    print(f"{feat}: MATCH={match}")
    if not match:
        print("  expected:", exp)
        print("  got     :", got)

print()
print("Line of Heart present in targets (should be False -- 'none' line):", "Line of Heart" in targets)
print("Line of Marriage present in targets (should be False -- no RELATIONSHIP line emitted):", "Line of Marriage" in targets)
print()
print("ALL MATCH:", all_match)
assert all_match, "SYNTHETIC DIFFERENTIAL FAILED"
assert "Line of Heart" not in targets
assert "Line of Marriage" not in targets
print("SYNTHETIC DIFFERENTIAL: PASS")
