"""
agent/context_bundle.py
Plain data container for all user-supplied context.
Zero imports from agent/ — this module sits at the bottom of the dependency graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ContextBundle:
    kundali:    str | None = None
    own_pdf:    str | None = None
    spouse_pdf: str | None = None
    palm_left:  str | None = None
    palm_right: str | None = None
    hand_detail: str | None = None

    def availability_map(self) -> dict[str, bool]:
        """Return presence flag for each context field."""
        return {
            "kundali":    self.kundali    is not None,
            "own_pdf":    self.own_pdf    is not None,
            "spouse_pdf": self.spouse_pdf is not None,
            "palm_left":  self.palm_left  is not None,
            "palm_right": self.palm_right is not None,
            "hand_detail": self.hand_detail is not None,
        }
