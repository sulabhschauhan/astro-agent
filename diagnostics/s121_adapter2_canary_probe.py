"""Throwaway probe (not the formal canary) -- verifies exactly what happens
when a live rule's antecedent literal is a pre-canonicalization synonym."""
import sys
sys.path.insert(0, ".")

from agent.interpretive import observation_extractor as oe
from agent.interpretive import observation_to_tokens as ott
from agent.interpretive import palm_rules_table


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, content):
        self._content = content
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeResponse(self._content)


class _FakeClient:
    def __init__(self, content):
        self.completions = _FakeCompletions(content)
        self.chat = type("_FakeChat", (), {"completions": self.completions})()


import json

fake = _FakeClient(json.dumps({
    "observations": {
        "Line of Head": {"Depth": {"value": "well_marked"}},
    },
    "unmapped": {},
}))

record = oe.extract_observation({"head line": ["the head line is well marked"]}, client=fake)
print("record.features['Line of Head'].tokens:", record.features["Line of Head"].tokens)

vision_payload = oe.to_vision_payload(record, enabled_features={"Line of Head"})
print("vision_payload:", vision_payload)

observation, magnitudes = ott.to_tokens(vision_payload)
print("observation (AFTER wire):", observation)
print("dropped:", magnitudes["_dropped"])

targets = {"Line of Fate": {"Starting_Point": "Line of Head"}}
rules = palm_rules_table.load_rule_set()
fired = palm_rules_table.match(observation, magnitudes, rules, targets=targets)
print("fired rule ids:", sorted(r.rule_id for r in fired))
ft009 = [r for r in rules if r.rule_id == "FT_009"]
print("FT_009 antecedents:", ft009[0].antecedents if ft009 else "NOT FOUND")
