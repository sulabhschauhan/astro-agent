"""Compute-then-compare probe for the yoga layer, over BOTH reference charts.

P-027 DISCIPLINE. Every value here is computed from BIRTH DETAILS ONLY, then
compared to the oracle fixture AFTERWARDS. No oracle value is ever fed into a
calculation. The oracle fixtures are Traditional-Lahiri (matched mode), which
is what calculate_chart() produces, so compute and oracle are the same setting.

WHAT IS AUTO-CHECKED (mechanically unambiguous): the three special lagnas
(sign + degree, arcsecond delta) and the eight chara karakas (planet per
karaka). WHAT IS HUMAN-CHECKED: the fired-yoga set against the oracle's Yogas
tab -- the name mapping is fuzzy, so the probe prints the detector's fired and
not-fired verdicts beside the fixture's raw Yogas rows and leaves the
adjudication to Sulabh (Working Style #5, #9). It never declares a yoga
oracle-validated on its own.

Writes the full run to diagnostics/latest_run.md (truncate-first, overwrite-
only per the diagnostics convention) and prints a <=10 line summary to stdout.

Run on Sulabh's machine: it needs the swiss ephemeris and the geocoder, which
a Claude sandbox does not have. No OpenAI is used anywhere.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

_FULL_SIGN = {
    "Ar": "Aries", "Ta": "Taurus", "Ge": "Gemini", "Cn": "Cancer",
    "Le": "Leo", "Vi": "Virgo", "Li": "Libra", "Sc": "Scorpio",
    "Sg": "Sagittarius", "Cp": "Capricorn", "Aq": "Aquarius", "Pi": "Pisces",
}
_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
          "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")

# name, dob, tob, place, oracle-fixture filename
CHARTS = [
    ("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India", "sulabh.md"),
    ("Surbhi", "11 Sep 1992", "10:30", "Patna, India", "surbhi.md"),
]

_LAGNA_LINE = re.compile(
    r"^\s*(Bhava|Hora|Ghati(?:ka)?)\s+Lagna\s+(\d+)\s+([A-Z][a-z])\s+(\d+)'?\s*([\d.]+)")
_KARAKA_LINE = re.compile(
    r"^\s*([A-Z][a-z]+)\s*(?:\(R\))?\s*-\s*(AK|AmK|BK|MK|PiK|PK|GK|DK)\b")


# ---------------------------------------------------------------- oracle parse

def parse_oracle_lagnas(text: str) -> dict:
    """{'bhava'|'hora'|'ghati': (sign, degree_in_sign)} from the fixture's
    Traditional-Lahiri block. Returns whatever it finds."""
    out = {}
    for line in text.splitlines():
        m = _LAGNA_LINE.match(line)
        if not m:
            continue
        which = m.group(1).lower().replace("ghatika", "ghati")
        sign = _FULL_SIGN.get(m.group(3))
        if not sign:
            continue
        deg = int(m.group(2)) + int(m.group(4)) / 60.0 + float(m.group(5)) / 3600.0
        out.setdefault(which, (sign, round(deg, 4)))  # first (Traditional block)
    return out


def parse_oracle_karakas(text: str) -> dict:
    """{karaka_abbr: planet} from the fixture's Traditional-Lahiri planet block
    ('Jupiter - AK', 'Rahu - AmK', ...)."""
    out = {}
    for line in text.splitlines():
        m = _KARAKA_LINE.match(line)
        if m:
            out.setdefault(m.group(2), m.group(1))
    return out


def oracle_yoga_block(text: str) -> str:
    """The raw 'Yogas' section, dumped verbatim for human comparison. Handles
    both the markdown-table form (sulabh.md 10c) and the fixed-width form
    (surbhi.md)."""
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if re.search(r"\bYogas?\b", ln) and ("Yoga" in ln or "10c" in ln
                                              or ln.strip().endswith(":")):
            start = i
            break
    if start is None:
        return "(no Yogas section found in fixture)"
    chunk = []
    for ln in lines[start:start + 60]:
        chunk.append(ln)
        if len(chunk) > 4 and ln.strip() == "" and any(c.strip() for c in chunk[-3:-1]) is False:
            break
    return "\n".join(chunk).rstrip()


# ---------------------------------------------------------------- compute side

def build_fact_block(name, dob, tob, place):
    """The full fact block the detector consumes, composed exactly as PATH B
    does (navamsa per app.py S130) plus the karakas and special lagnas the
    yoga layer additionally needs. Computed from birth details only."""
    from agent.chart_calculator import (calculate_chart, geocode_place,
                                         to_julian_day, _local_datetime)
    from agent.astro.chart_facts import build_chart_facts
    from agent.calculations.vargas.navamsa import compute_navamsa
    from agent.calculations.jaimini.karakas import compute_chara_karakas
    from agent.calculations.jaimini.special_lagnas import compute_special_lagnas

    chart = calculate_chart(name, dob, tob, place)
    meta = chart.get("meta") or {}

    # D9, composed as app.py does; dignity is sign-only here (feeds only the
    # Neecha navamsa-exaltation check).
    try:
        d9 = compute_navamsa(meta["jd_ut"], meta["asc_lon_sidereal"])
        chart = dict(chart, navamsa={
            "d9_lagna_sign": d9.d9_lagna_sign,
            "placements": {p: {"sign": pl.d9_sign, "house": pl.d9_house,
                               "dignity": _sign_dignity(p, pl.d9_sign)}
                           for p, pl in d9.placements.items()},
        })
    except Exception as e:  # noqa: BLE001
        print(f"  ! navamsa unavailable: {type(e).__name__}: {e}")

    facts = build_chart_facts(chart)

    # Chara karakas from the eight sidereal longitudes calculate_chart returns.
    pp = chart["planetary_positions"]
    lons = {g: pp[g]["longitude"] for g in
            ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu")}
    facts["chara_karakas"] = {abbr: planet
                              for abbr, planet in compute_chara_karakas(lons).karakas}

    # Special lagnas from the same birth moment/coords calculate_chart used.
    lat, lon = geocode_place(place)
    _, utc_dt = to_julian_day(dob, tob, lat, lon)
    birth_local = _local_datetime(utc_dt, lat, lon)
    sl = compute_special_lagnas(birth_local, lat, lon)
    facts["ghati_lagna_sign"] = sl["ghati_lagna"]["sign"]
    facts["hora_lagna_sign"] = sl["hora_lagna"]["sign"]
    # Degree-in-sign per graha -> enables the degree-accurate Pancha
    # Mahapurusha check (moolatrikona). Detector-only; never enters the
    # interpreter payload (that block stays degree-free by lock).
    facts["planet_degrees"] = {g: (r["longitude"] % 30.0)
                               for g, r in pp.items()
                               if isinstance(r, dict) and "longitude" in r}
    facts["_special_lagnas"] = sl  # diagnostics only
    return facts


def _sign_dignity(planet: str, sign: str) -> str:
    """Sign-only dignity for the navamsa placement (no degree): Exalted / Own
    Sign / Debilitated / Neutral. Matches the uncontested tiers the fact block
    keeps (S130)."""
    exalt = {"Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
             "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces",
             "Saturn": "Libra"}
    debil = {"Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
             "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo",
             "Saturn": "Aries"}
    own = {"Sun": {"Leo"}, "Moon": {"Cancer"}, "Mars": {"Aries", "Scorpio"},
           "Mercury": {"Gemini", "Virgo"}, "Jupiter": {"Sagittarius", "Pisces"},
           "Venus": {"Taurus", "Libra"}, "Saturn": {"Capricorn", "Aquarius"}}
    if sign == exalt.get(planet):
        return "Exalted"
    if sign == debil.get(planet):
        return "Debilitated"
    if sign in own.get(planet, set()):
        return "Own Sign"
    return "Neutral"


# ---------------------------------------------------------------- report

def _arcsec_delta(a_sign, a_deg, b_sign, b_deg):
    if a_sign != b_sign:
        return f"SIGN MISMATCH ({a_sign} vs {b_sign})"
    return f'{abs(a_deg - b_deg) * 3600:.0f}"'


def run() -> str:
    from agent.calculations.yogas.detector import detect_yogas
    fixtures = REPO / "reference" / "oracle_fixtures"
    lines = ["# Yoga layer -- compute-then-compare probe (both charts)", ""]
    summary = []

    for name, dob, tob, place, fixture in CHARTS:
        lines += [f"## {name}  ({dob} {tob}, {place})", ""]
        text = (fixtures / fixture).read_text(encoding="utf-8", errors="replace")
        try:
            facts = build_fact_block(name, dob, tob, place)
        except Exception as e:  # noqa: BLE001
            lines += [f"COMPUTE FAILED: {type(e).__name__}: {e}", ""]
            summary.append(f"{name}: compute FAILED ({type(e).__name__})")
            continue

        # --- special lagnas, auto-checked
        lines.append("### Special lagnas (computed vs oracle Traditional-Lahiri)")
        o_lag = parse_oracle_lagnas(text)
        sl = facts["_special_lagnas"]
        for key in ("bhava", "hora", "ghati"):
            c = sl[f"{key}_lagna"]
            cs, cd = c["sign"], c["degree_in_sign"]
            if key in o_lag:
                os_, od = o_lag[key]
                lines.append(f"  {key:<6} computed {cs} {cd:.4f}  | oracle {os_} {od:.4f}"
                             f"  | Δ {_arcsec_delta(cs, cd, os_, od)}")
            else:
                lines.append(f"  {key:<6} computed {cs} {cd:.4f}  | oracle NOT PARSED")
        lines.append("")

        # --- chara karakas, auto-checked
        lines.append("### Chara karakas (computed vs oracle)")
        o_k = parse_oracle_karakas(text)
        ck = facts["chara_karakas"]
        k_ok = 0
        for abbr in ("AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK"):
            c = ck.get(abbr, "-")
            o = o_k.get(abbr, "?")
            match = "ok" if (o != "?" and c == o) else ("REVIEW" if o == "?" else "MISMATCH")
            if match == "ok":
                k_ok += 1
            lines.append(f"  {abbr:<4} computed {c:<8} oracle {o:<8} {match}")
        lines.append("")

        # --- yogas: detector output + oracle dump, human-checked
        report = detect_yogas(facts)
        fired = report.fired
        lines.append(f"### Detector FIRED ({len(fired)})")
        for v in fired:
            lines.append(f"  [{v.id}] {v.name}: {v.reason}")
        lines.append("")
        lines.append(f"### Detector NOT-FIRED ({len(report.ruled_out)})")
        for v in report.ruled_out:
            lines.append(f"  [{v.id}] {v.name}: {v.reason}")
        if report.errors:
            lines += ["", "### Detector errors", *(f"  {e}" for e in report.errors)]
        lines += ["", "### Oracle Yogas tab (verbatim -- human compares fired set)",
                  "```", oracle_yoga_block(text), "```", ""]

        summary.append(f"{name}: {len(fired)} fired, {len(report.ruled_out)} not-fired, "
                       f"karakas {k_ok}/8 auto-matched")

    out = "\n".join(lines) + "\n"
    (REPO / "diagnostics" / "latest_run.md").write_text(out, encoding="utf-8")
    return "\n".join(summary)


if __name__ == "__main__":
    print("Yoga probe -- computing both charts from birth details...\n")
    print(run())
    print("\nFull run -> diagnostics/latest_run.md. Confirm the fired set "
          "against each oracle Yogas tab by eye.")
