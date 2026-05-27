"""
config.py
Project-level configuration constants for the astro agent.
"""

import re

_HOUSE_RE = re.compile(r'\b\d+(?:st|nd|rd|th) house\b', re.IGNORECASE)


def _strip_house_numbers(mapping: dict[str, str]) -> dict[str, str]:
    result = {}
    for k, v in mapping.items():
        cleaned = _HOUSE_RE.sub('', v)
        result[k] = ' '.join(cleaned.split())  # collapse leftover whitespace
    return result


_RAW_REWRITE_MAP: dict[str, str] = {
    "rich":      "wealth financial prosperity 2nd house 11th house",
    "money":     "wealth income financial gains",
    "love":      "relationship marriage 7th house Venus",
    "marriage":  "marriage partner 7th house",
    "job":       "career profession 10th house",
    "health":    "health vitality 6th house",
    "children":  "children 5th house Jupiter",
    "travel":    "foreign travel 12th house",
}

REWRITE_MAP: dict[str, str] = _strip_house_numbers(_RAW_REWRITE_MAP)
