"""Jaimini Chara Karakas -- P6, Master Build Plan order.

CITATION (PVR Narasimha Rao, "Vedic Astrology: An Integrated Approach",
Ch.8 "Karakas", printed pp.79-81 / PDF pp.90-92, Table 13 -- verbatim
extraction ratified in the Session 57 source-verification pass):

  Scheme: 8 chara karakas, Rahu included, Ketu excluded ("Ketu stands for
  moksha ... and does not stand for any person who affects one's
  sustenance", Section 8.1). This is PVR's own stated scheme, not a
  project choice between competing traditions -- the alternate 7-karaka
  scheme (which drops a separate Pitri Karaka) is a different author's
  system, not something PVR himself offers as an option.

  Advancement rule (Section 8.2, step 1): "For each planet, find its
  advancement from the beginning of the rasi occupied by it. For Rahu,
  measure the advancement from the end of his rasi." Confirmed
  numerically in PVR's own worked Example 28: Rahu at 1 Cn 43 ->
  advancement = 30(deg) - 1(deg)43' = 28(deg)17'.

  Rank order, highest advancement first (Table 13): Atma Karaka (AK),
  Amatya Karaka (AmK), Bhratri Karaka (BK), Matri Karaka (MK), Pitri
  Karaka (PiK), Putra Karaka (PK), Jnaati Karaka (GK), Dara Karaka (DK).

  Tie-break (Section 8.2): "If two planets have the same degrees, we
  should compare minutes. If minutes are same, we should compare the
  seconds." -- i.e. plain descending-float comparison at full precision,
  no rounding/truncation at any stage (this module never rounds an
  advancement value before comparing it).

  Exact tie (Section 8.2): "If two planets are exactly at the same
  longitude, then they will hold a karakatwa (signification) together
  and the next karakatwa will have no ruler. We should use the
  corresponding sthira karaka in that case." PVR immediately adds this
  "rarely becomes necessary, as two planets are rarely at exactly the
  same longitude." Joint-karakatwa-with-sthira-karaka-fallback is
  explicitly OUT of V1 scope (sthira karakas are a separate significator
  system, not wired into this module or any caller yet) -- an exact tie
  fails closed with ValueError rather than being silently resolved by
  insertion order.

Oracle (for the P6 validation pass that follows this kernel commit, NOT
performed here -- this is a pure-function kernel with no test file):
JHora v8, 4 reference charts, karaka-scheme preference = 8 (matches this
module's scheme).

Pure function, NO ephemeris calls (same pattern as
agent/calculations/transits/av_transit_scorer.py): the caller supplies
precomputed sidereal longitudes; this module does no swisseph/ephemeris
lookups of its own.
"""

from __future__ import annotations

from dataclasses import dataclass

_CHARA_PLANETS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu",
)

# PVR Table 13 rank order, highest advancement first -- fixed, does not
# depend on which planet ends up where.
_KARAKA_ORDER: tuple[str, ...] = (
    "AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK",
)


@dataclass(frozen=True)
class CharaKarakasResult:
    # (karaka abbreviation, planet name), in PVR Table 13 rank order
    # (AK first ... DK last). Tuple of pairs, not a dict, so the result
    # stays hashable/frozen like the project's other frozen result
    # dataclasses (e.g. compatibility/koota_types.py's KootaResult family).
    karakas: tuple[tuple[str, str], ...]
    # (planet, advancement-in-degrees), in canonical _CHARA_PLANETS order.
    # Diagnostics only -- not re-derivable from `karakas` alone, since
    # `karakas` discards the actual advancement values.
    advancement: tuple[tuple[str, float], ...]


def compute_chara_karakas(
    planet_longitudes: dict[str, float],
) -> CharaKarakasResult:
    """Compute the 8 Jaimini chara karakas (PVR Ch.8 Section 8.2).

    Args:
        planet_longitudes: absolute sidereal longitudes in degrees
            ([0, 360) expected), Title-case planet-name keys. Exactly
            the 8 keys in _CHARA_PLANETS are required -- Sun, Moon, Mars,
            Mercury, Jupiter, Venus, Saturn, Rahu.

    Returns:
        CharaKarakasResult.

    Raises:
        ValueError: "Ketu" is present (chara karakas exclude Ketu by
            PVR's own design, see module CITATION -- not a generic
            unknown-key message); any other required key missing or any
            other unexpected key present; two planets share the exact
            same advancement value (fail-closed tie, see module
            CITATION).
    """
    if "Ketu" in planet_longitudes:
        raise ValueError(
            "Ketu is excluded from chara karakas by PVR's own design "
            "(Ch.8 Section 8.1): Ketu stands for moksha (emancipation), "
            "not for a person who affects one's sustenance, so he is "
            "never assigned a chara karaka. Remove 'Ketu' from "
            "planet_longitudes -- this is not a generic unknown-planet "
            "error."
        )

    expected = set(_CHARA_PLANETS)
    given = set(planet_longitudes)
    missing = sorted(expected - given)
    extra = sorted(given - expected)
    if missing or extra:
        problems = []
        if missing:
            problems.append(f"missing required key(s) {missing}")
        if extra:
            problems.append(f"unexpected key(s) {extra}")
        raise ValueError(
            f"planet_longitudes must have exactly the 8 keys "
            f"{list(_CHARA_PLANETS)}: {'; '.join(problems)}"
        )

    advancement: dict[str, float] = {}
    for planet in _CHARA_PLANETS:
        longitude = planet_longitudes[planet]
        if planet == "Rahu":
            advancement[planet] = 30.0 - (longitude % 30.0)
        else:
            advancement[planet] = longitude % 30.0

    values = list(advancement.values())
    if len(set(values)) != len(values):
        tied = sorted(
            planet
            for planet in _CHARA_PLANETS
            if values.count(advancement[planet]) > 1
        )
        raise ValueError(
            f"exact advancement tie between {tied} (identical to full "
            f"float precision): PVR Ch.8 Section 8.2 resolves this by "
            f"joint karakatwa falling back to the corresponding sthira "
            f"karaka, which is out of V1 scope (sthira karakas are not "
            f"wired into this module). PVR himself notes this 'rarely "
            f"becomes necessary, as two planets are rarely at exactly "
            f"the same longitude' -- failing closed rather than "
            f"silently ordering the tie."
        )

    ranked_planets = sorted(
        _CHARA_PLANETS, key=lambda p: advancement[p], reverse=True
    )
    karakas = tuple(zip(_KARAKA_ORDER, ranked_planets))
    advancement_out = tuple((p, advancement[p]) for p in _CHARA_PLANETS)

    return CharaKarakasResult(karakas=karakas, advancement=advancement_out)
