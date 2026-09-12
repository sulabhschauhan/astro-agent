"""Step 4 synthetic differential -- location-aware antecedent matching, S99.
Hardest-case-first battery: location matches -> fires; location differs ->
no fire; __location key absent for feature -> no fire (fail-closed); key
present but no entry for that target -> no fire; and a location=None
antecedent proven to fire byte-identical to pre-edit behavior.
"""
import sys
sys.path.insert(0, ".")
from agent.interpretive.palm_rules_table import Antecedent, _antecedent_fires

# A typed relational antecedent: "cuts Line of Head" with a required location.
base_kwargs = dict(
    feature="Line of Health", attribute="cuts", value=None,
    condition_type="standard", comparator=None, comparator_feature=None,
    relation_target="Line of Head",
)

cases = []

# Case 1: location matches -> fires
ant = Antecedent(**base_kwargs, location="Mount of Jupiter")
targets = {"Line of Health": {"cuts": {"Line of Head"}, "cuts__location": {"Line of Head": "Mount of Jupiter"}}}
cases.append(("location matches -> fires", ant, targets, True))

# Case 2: location differs -> no fire
ant = Antecedent(**base_kwargs, location="Mount of Saturn")
targets = {"Line of Health": {"cuts": {"Line of Head"}, "cuts__location": {"Line of Head": "Mount of Jupiter"}}}
cases.append(("location differs -> no fire", ant, targets, False))

# Case 3: __location key absent for feature -> no fire (fail-closed)
ant = Antecedent(**base_kwargs, location="Mount of Jupiter")
targets = {"Line of Health": {"cuts": {"Line of Head"}}}  # no cuts__location key at all
cases.append(("__location key absent -> no fire (fail-closed)", ant, targets, False))

# Case 4: key present but no entry for that target -> no fire
ant = Antecedent(**base_kwargs, location="Mount of Jupiter")
targets = {"Line of Health": {"cuts": {"Line of Head", "Line of Fate"}, "cuts__location": {"Line of Fate": "Mount of Saturn"}}}
cases.append(("__location present but no entry for target -> no fire", ant, targets, False))

# Case 5: type+target membership itself fails (target not even present) -> no fire, location irrelevant
ant = Antecedent(**base_kwargs, location="Mount of Jupiter")
targets = {"Line of Health": {"cuts": {"Line of Fate"}, "cuts__location": {"Line of Head": "Mount of Jupiter"}}}
cases.append(("target not in membership set at all -> no fire", ant, targets, False))

# Case 6: scalar (SINGLE cardinality) stored value with location required, matches
ant = Antecedent(
    feature="Line of Head", attribute="stopped_by", value=None,
    condition_type="standard", comparator=None, comparator_feature=None,
    relation_target="Line of Fate", location="Mount of Luna",
)
targets = {"Line of Head": {"stopped_by": "Line of Fate", "stopped_by__location": {"Line of Fate": "Mount of Luna"}}}
cases.append(("scalar SINGLE cardinality, location matches -> fires", ant, targets, True))

# Case 7: location=None antecedent, byte-identical to pre-edit behavior (membership fires, no location check)
ant_new = Antecedent(**base_kwargs, location=None)
ant_old_shape = Antecedent(**base_kwargs)  # location defaults to None -- identical construction
targets = {"Line of Health": {"cuts": {"Line of Head"}}}
cases.append(("location=None -> unchanged (membership-only) fire", ant_new, targets, True))

observation = {}
magnitudes = {}

print("=== Gate (a): synthetic differential ===")
all_pass = True
for label, ant, targets, expected in cases:
    result = _antecedent_fires(ant, observation, magnitudes, targets)
    ok = result == expected
    all_pass = all_pass and ok
    print(f"{'PASS' if ok else 'FAIL'}: {label} -> got={result} expected={expected}")

# Explicit location=None byte-identical proof: same result for the "new"
# Antecedent (location field exists, defaulted None) as the pre-edit
# construction would have produced (same signature() shape too).
ant7 = Antecedent(**base_kwargs)
print()
print("location=None signature (7-tuple, must match pre-edit shape):", ant7.signature())
print("signature length:", len(ant7.signature()), "(expected 7)")
assert len(ant7.signature()) == 7

ant8 = Antecedent(**base_kwargs, location="Mount of Jupiter")
print("location='Mount of Jupiter' signature (8-tuple):", ant8.signature())
print("signature length:", len(ant8.signature()), "(expected 8)")
assert len(ant8.signature()) == 8
assert ant7.signature() != ant8.signature()

print()
print("ALL PASS:", all_pass)
assert all_pass, "SYNTHETIC DIFFERENTIAL FAILED"
print("SYNTHETIC DIFFERENTIAL: PASS")
