"""S121 #5A -- STEP 3 firing proof. For FT_001 and FT_009, reads each rule's
OWN full antecedent set straight from the (migrated) JSON, builds a
synthetic observation+targets satisfying every antecedent with canonical
tokens, and asserts the rule fires. Then re-runs the identical synthetic
input with Depth reverted to the pre-canonicalization literal
("well_marked") and asserts the rule does NOT fire -- proving the migrated
rule now speaks only canonical tokens (bridging the synonym back is the
adapter wire's job, not this rule file's)."""
import sys

sys.path.insert(0, ".")

from agent.interpretive import palm_rules_table

rules = palm_rules_table.load_rule_set()
ft001 = next(r for r in rules if r.rule_id == "FT_001")
ft009 = next(r for r in rules if r.rule_id == "FT_009")

print("FT_001 antecedents (from the migrated JSON):")
for a in ft001.antecedents:
    print("  ", a)
print("FT_009 antecedents (from the migrated JSON):")
for a in ft009.antecedents:
    print("  ", a)
print()


def fires(rule_id: str, observation: dict, targets: dict) -> bool:
    fired = palm_rules_table.match(observation, {}, rules, targets=targets)
    return rule_id in {r.rule_id for r in fired}


# FT_001: Line of Fate/Starting_Point -> Line of Life  AND  Line of Fate/Depth = deep
ft001_targets = {"Line of Fate": {"Starting_Point": "Line of Life"}}
ft001_obs_canonical = {"Line of Fate": {"Depth": "deep"}}
ft001_obs_precanonical = {"Line of Fate": {"Depth": "well_marked"}}

ft001_fires_canonical = fires("FT_001", ft001_obs_canonical, ft001_targets)
ft001_fires_precanonical = fires("FT_001", ft001_obs_precanonical, ft001_targets)

print("FT_001, canonical Depth='deep', Starting_Point=Line of Life -> fires:", ft001_fires_canonical)
print("FT_001, pre-canonical Depth='well_marked', SAME targets     -> fires:", ft001_fires_precanonical)
assert ft001_fires_canonical is True, "FT_001 must fire on fully canonical input -- migration did not work"
assert ft001_fires_precanonical is False, "FT_001 must NOT fire on the old literal -- migrated rule must speak only canonical"
print("FT_001: PASS")
print()

# FT_009: Line of Fate/Starting_Point -> Line of Head  AND  Line of Head/Depth = deep
ft009_targets = {"Line of Fate": {"Starting_Point": "Line of Head"}}
ft009_obs_canonical = {"Line of Head": {"Depth": "deep"}}
ft009_obs_precanonical = {"Line of Head": {"Depth": "well_marked"}}

ft009_fires_canonical = fires("FT_009", ft009_obs_canonical, ft009_targets)
ft009_fires_precanonical = fires("FT_009", ft009_obs_precanonical, ft009_targets)

print("FT_009, canonical Depth='deep', Starting_Point=Line of Head -> fires:", ft009_fires_canonical)
print("FT_009, pre-canonical Depth='well_marked', SAME targets     -> fires:", ft009_fires_precanonical)
assert ft009_fires_canonical is True, "FT_009 must fire on fully canonical input -- migration did not work"
assert ft009_fires_precanonical is False, "FT_009 must NOT fire on the old literal -- migrated rule must speak only canonical"
print("FT_009: PASS")
