"""Checks every D5-class rule (the 7 rule ids the S121 ledger's synonym-table
seeded from) to see whether the vocab_adapter wire breaks its OLD-literal
antecedent, given the rule files still carry the pre-canonicalization token."""
import json
import sys

sys.path.insert(0, ".")

from agent.interpretive import palm_rules_table
from agent.interpretive import vocab_adapter

D5_RULE_IDS = {"FT_001", "FT_009", "H_004", "H_018", "H_019", "HL_012", "HL_013", "HL_014", "HL_018", "HL_020"}

rules = palm_rules_table.load_rule_set()
for r in rules:
    if r.rule_id not in D5_RULE_IDS:
        continue
    for a in r.antecedents:
        if a.value is None:
            continue
        result = vocab_adapter.adapt(a.feature, a.attribute, a.value)
        if isinstance(result, vocab_adapter.Mapped) and result.token != a.value:
            print(f"{r.rule_id}: antecedent ({a.feature!r}, {a.attribute!r}, value={a.value!r}) "
                  f"-> vocab_adapter canonicalizes emitted vision text to {result.token!r} -- "
                  f"BROKEN unless the rule's own literal is migrated to {result.token!r} too.")
        elif isinstance(result, vocab_adapter.Mapped):
            print(f"{r.rule_id}: antecedent ({a.feature!r}, {a.attribute!r}, value={a.value!r}) "
                  f"already canonical -- unaffected.")
        else:
            print(f"{r.rule_id}: antecedent ({a.feature!r}, {a.attribute!r}, value={a.value!r}) "
                  f"-> vocab_adapter says {result!r} (not a value antecedent this table covers, or attribute unbound)")
