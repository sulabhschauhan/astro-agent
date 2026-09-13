"""Yoga detection engine -- scans a chart against the yoga catalog.

Fills the Phase-0 stub of the same name.

CONTRACT
--------
`detect_yogas(chart_facts)` runs every catalogue module over the ALREADY
COMPUTED fact block and returns one verdict per rule -- FIRED and NOT-FIRED
alike. It computes no chart fact (S124), imports no ephemeris, and never
touches `chart_calculator` (S20). Each catalogue module is a plain function
returning plain dicts, so nothing in `catalog/` imports this module and there
is no cycle to manage.

WHY NOT-FIRED IS RETURNED
-------------------------
It is the "what I am ruling out and why" half of an answer, which this
pipeline could not produce at all before. A not-fired verdict is a chart
FACT, derived deterministically from the fact block -- it is not the model
recalling doctrine from training, which the S124 lock forbids.

NEVER RAISES. A malformed or partial fact block yields fewer verdicts, never
an exception: a yoga detector failing must cost the reader a yoga, never the
answer. Same fail-soft posture as the D9 wiring (S130).

Python 3.11.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from agent.calculations.yogas import rules

DETECTOR_VERSION = "yoga-detector-1.0"

# Catalogue modules, in report order. A module is just `detect(facts) -> list[dict]`.
_CATALOG: tuple[tuple[str, Callable], ...] = (
    ("rules", rules.detect),
)


@dataclass(frozen=True)
class YogaVerdict:
    """One rule's ruling on one chart.

    Attributes:
        id: stable rule id, never user-visible.
        name: the classical name, as a reader would meet it.
        fired: whether this chart satisfies the rule.
        reason: plain-language WHY, true in both directions.
        evidence: the fact-block references the ruling rests on, so a reader
            (or a test) can re-check it without re-running the detector.
        source: the classical text the rule is drawn from.
        contested: the definition itself is disputed between sources.
        contested_note: what the dispute is, when `contested`.
        module: which catalogue module produced it.
    """
    id: str
    name: str
    fired: bool
    reason: str
    evidence: tuple[str, ...] = ()
    source: str = ""
    contested: bool = False
    contested_note: str = ""
    module: str = ""

    def to_dict(self) -> dict:
        d = {"id": self.id, "name": self.name, "fired": self.fired,
             "reason": self.reason, "evidence": list(self.evidence),
             "source": self.source, "module": self.module}
        if self.contested:
            d["contested"] = True
            d["contested_note"] = self.contested_note
        return d


@dataclass
class YogaReport:
    verdicts: list[YogaVerdict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    detector_version: str = DETECTOR_VERSION

    @property
    def fired(self) -> list[YogaVerdict]:
        return [v for v in self.verdicts if v.fired]

    @property
    def ruled_out(self) -> list[YogaVerdict]:
        return [v for v in self.verdicts if not v.fired]

    def to_dict(self) -> dict:
        return {"fired": [v.to_dict() for v in self.fired],
                "ruled_out": [v.to_dict() for v in self.ruled_out],
                "errors": list(self.errors),
                "detector_version": self.detector_version}


def detect_yogas(chart_facts: dict) -> YogaReport:
    """Run the whole catalogue. Never raises."""
    report = YogaReport()
    if not isinstance(chart_facts, dict):
        report.errors.append("chart_facts is not a dict; no yoga was evaluated")
        return report

    for module_name, fn in _CATALOG:
        try:
            rows = fn(chart_facts) or []
        except Exception as e:  # noqa: BLE001 -- one bad rule must not cost the rest
            report.errors.append(f"{module_name}: {type(e).__name__}: {e}")
            continue
        for row in rows:
            if not isinstance(row, dict) or "id" not in row:
                report.errors.append(f"{module_name}: malformed verdict {row!r}")
                continue
            report.verdicts.append(YogaVerdict(
                id=str(row["id"]),
                name=str(row.get("name", row["id"])),
                fired=bool(row.get("fired")),
                reason=str(row.get("reason", "")),
                evidence=tuple(row.get("evidence") or ()),
                source=str(row.get("source", "")),
                contested=bool(row.get("contested")),
                contested_note=str(row.get("contested_note", "")),
                module=module_name,
            ))
    return report
