"""Tajaka annual Sahams (sensitive points) -- sub-engine (S162).

SPEC SOURCE (P-028): B.V. Raman, *Varshaphal*, Ch.VII (Sahams) pp.34-36 for the
core set, and Tajika Nilakanthi (Nilakantha Daivajna) Saham adhyaya for the
general rule. JHora v8 (tests/fixtures/jhora_sulabh.md section 9) GRADES ONLY.

RULES (both validated against FOUR Sulabh annual charts -- 2024/25 day,
2026/27 night -- not fitted to one):
  * Two-point Saham = (A - B); if the Lagna is NOT in the forward arc B->A, add
    30 deg; then add the Lagna.
  * Three-point Saham: same (A - B) + 30-deg rule, but the THIRD point closes it
    instead of the Lagna.
  * NIGHT (pravesh Sun below horizon): A and B swap for EVERY saham. This is
    JHora's measured convention (reverse-all), which differs from Raman's text
    (where a few sahams are "day or night" the same); since we grade against
    JHora, reverse-all is used. Day/night is of the pravesh instant at the cast
    place (S158 _is_night).

STATUS:
  CONFIRMED -- reproduces JHora on all four charts (day AND night) to <0.5 deg.
  PENDING   -- formula not yet verified from the source across all four charts
               (several earlier values were brute-forced to 2024 and are wrong
               on other charts). PENDING sahams are NOT emitted by default and
               NOT asserted anywhere until each is re-derived from Nilakantha and
               passes all four charts. See docs/sahams_reconciliation_S162.md.
"""
from dataclasses import dataclass

_SIGN_LORD = {0: 'Ma', 1: 'Ve', 2: 'Me', 3: 'Mo', 4: 'Su', 5: 'Me',
              6: 'Ve', 7: 'Ma', 8: 'Ju', 9: 'Sa', 10: 'Sa', 11: 'Ju'}


@dataclass(frozen=True)
class SahamDef:
    name: str
    a: str
    b: str
    third: str | None   # None = two-point (close with Lagna); else three-point
    source: str
    status: str   # CONFIRMED (oracle-validated) | SOURCE (book formula, no oracle
                  # grade -- emitted, flagged) | PENDING (no formula -- not emitted)
    no_swap: bool = False   # True = NO night reversal (day form holds day & night),
                            # e.g. Nila "dinaratri" sahams and JHora's non-reversing
                            # Vyapara/Bhratru/Roga/Artha/Labha.
    # Day/night-DISTINCT sahams: when set AND the chart is night, these three
    # replace (a, b, third) wholesale -- the points themselves change by branch,
    # which a simple A,B swap cannot express. Karyasiddhi (Nila #31) is the case:
    # day (Sa-Su)+Lsun, night (Sa-Mo)+Lmoon.
    night_a: str | None = None
    night_b: str | None = None
    night_third: str | None = None


# DAY form (a, b[, third]); night swaps a,b for every saham UNLESS the def carries
# an explicit night_* triple (day/night-distinct).
TABLE = [
    # --- CONFIRMED: validated on 2024/25 day + 2026/27 night ---
    SahamDef('Punya', 'Mo', 'Su', None, 'Raman p.34 s65', 'CONFIRMED'),
    SahamDef('Vidya', 'Su', 'Mo', None, 'Raman p.34 s66 (Guru)', 'CONFIRMED'),
    SahamDef('Yasas', 'Ju', 'Punya', None, 'Raman p.35 s67 (Kirthi)', 'CONFIRMED'),
    SahamDef('Mitra', 'Ju', 'Punya', 'Ve', 'Raman p.35 s68', 'CONFIRMED'),
    SahamDef('Pitru', 'Sa', 'Su', None, 'Raman p.35 s69 (Raja)', 'CONFIRMED'),
    SahamDef('Rajya', 'Sa', 'Su', None, 'Raman p.35 s69 (Raja)', 'CONFIRMED'),
    SahamDef('Putra', 'Ju', 'Mo', None, 'Raman p.36 s70', 'CONFIRMED'),
    SahamDef('Jeeva', 'Sa', 'Ju', None, 'Raman p.36 s71', 'CONFIRMED'),
    SahamDef('Karma', 'Ma', 'Me', None, 'Raman p.36 s72 (Vyapara)', 'CONFIRMED'),
    SahamDef('Vivaha', 'Ve', 'Sa', None, 'Raman p.36 s73 / Nila s17', 'CONFIRMED'),
    SahamDef('Satru', 'Ma', 'Sa', None, 'Raman p.36 s74', 'CONFIRMED'),
    SahamDef('Mahatmya', 'Punya', 'Ma', None, 'Nila Saham', 'CONFIRMED'),
    SahamDef('Asha', 'Sa', 'Ma', None, 'Nila Saham', 'CONFIRMED'),
    SahamDef('Matru', 'Mo', 'Ve', None, 'Nila Saham', 'CONFIRMED'),
    SahamDef('Sraddha', 'Ve', 'Ma', None, 'Nila s18 (l.3584)', 'CONFIRMED'),
    SahamDef('Kali', 'Ju', 'Ma', None, 'Nila Saham', 'CONFIRMED'),
    SahamDef('Bandhu', 'Me', 'Mo', None, 'Nila s14 (l.3539)', 'CONFIRMED'),
    SahamDef('Paradara', 'Ve', 'Su', None, 'Nila s16 (l.3554)', 'CONFIRMED'),
    SahamDef('Vanik', 'Mo', 'Me', None, 'Nila s16 (l.3558)', 'CONFIRMED'),
    SahamDef('Bandhana', 'Punya', 'Sa', None, 'Nila s23 (l.3657)', 'CONFIRMED'),
    SahamDef('Jadya', 'Ma', 'Sa', 'Me', 'Nila s19', 'CONFIRMED'),
    # --- Promoted S163: source shloka + JHora oracle agree on all four charts ---
    SahamDef('Sastra', 'Ju', 'Sa', 'Me', 'Nila #22 l.3527', 'CONFIRMED'),
    SahamDef('Santapa', 'Sa', 'Mo', 'H6', 'Nila #34 l.3560 (sixth bhava)', 'CONFIRMED'),
    SahamDef('Karyasiddhi', 'Sa', 'Su', 'Lsun', 'Nila #31 l.3530 (day/night-distinct)',
             'CONFIRMED', night_a='Sa', night_b='Mo', night_third='Lmoon'),
    # --- Promoted S164 (house-lord terms + no-night-swap added). All six
    #     reproduce JHora on all four charts <0.5deg. Artha is Nilakantha's
    #     Dhana #26; Gaurava is Nilakantha's Guruta #45; Labha/Bhratru/Vyapara/
    #     Roga reproduce JHora but the name is not in Nilakantha's 50 (JHora
    #     tradition) -- shipped on 4-chart oracle match per Sulabh. Note JHora's
    #     Vyapara (Ma-Sa) is NOT Nilakantha's Vyapara (Ma-Me = Karma). ---
    SahamDef('Artha', 'H2', 'L2', None, 'Nila Dhana #26 (H2-L2) + oracle', 'CONFIRMED', no_swap=True),
    SahamDef('Labha', 'H11', 'L11', None, 'house-lord family (H11-L11) + oracle', 'CONFIRMED', no_swap=True),
    SahamDef('Gaurava', 'Ju', 'Mo', 'Su', 'Nila Guruta #45 + oracle', 'CONFIRMED'),
    SahamDef('Bhratru', 'Ju', 'Sa', None, 'JHora (Ju-Sa, no reversal) + oracle', 'CONFIRMED', no_swap=True),
    SahamDef('Vyapara', 'Ma', 'Sa', None, 'JHora (Ma-Sa, no reversal) + oracle', 'CONFIRMED', no_swap=True),
    SahamDef('Roga', 'H12', 'Mo', None, 'JHora (H12-Mo, no reversal) + oracle', 'CONFIRMED', no_swap=True),
    # Samartha (S164): PyJHora horoscope/transit/saham.py -- base (Mars - LagnaLord)
    # + Lagna, reverse-all night; EXCEPTION handled in compute_sahams -- if Mars
    # owns the lagna sign, Jupiter replaces the lagna lord AND day/night flips.
    # Validated <0.07deg on all four charts.
    SahamDef('Samartha', 'Ma', 'L1', None, 'PyJHora saham.py (Mars-LagnaLord; Mars-owns-lagna special)', 'CONFIRMED'),
    # Preeti/Jalapatana (S165): PyJHora formulas, now oracle-validated against the
    # JHora v8 desktop Sahama tables (all 4 charts <0.5deg). JHora's formulas
    # DIFFER from Nilakantha's for both (Sastra not Vidya; 15deg Cancer not Moon).
    SahamDef('Preeti', 'Sastra', 'Punya', None, 'PyJHora (Sastra-Punya) + desktop oracle', 'CONFIRMED'),
    SahamDef('Jalapatana', 'Cn15', 'Sa', None, 'PyJHora (15deg Cancer - Saturn) + desktop oracle', 'CONFIRMED'),
    # The three "death"-group sahams (S165): PyJHora formulas, desktop-oracle
    # validated (<0.5deg, 4 charts). The answer layer suppresses these by prompt.
    SahamDef('Mrityu', 'H8', 'Mo', None, 'PyJHora (8th-Moon) + desktop oracle', 'CONFIRMED', no_swap=True),
    SahamDef('Paradesa', 'H9', 'L9', None, 'PyJHora (9th-9thlord) + desktop oracle', 'CONFIRMED', no_swap=True),
    SahamDef('Apamrityu', 'H8', 'Ma', None, 'PyJHora (8th-Mars) + desktop oracle', 'CONFIRMED'),
]

_REQUIRED = ('Su', 'Mo', 'Ma', 'Me', 'Ju', 'Ve', 'Sa', 'Ra', 'Ke', 'La')


def _resolve(pts: dict) -> dict:
    t = dict(pts)
    la = pts['La']
    lagna_sign = int(la // 30) % 12
    for k in range(1, 13):
        t[f'H{k}'] = (la + (k - 1) * 30.0) % 360.0
        # L1..L12: lord of the sign on each house cusp (house-lord). Nilakantha
        # uses these for the bhava sahams -- Dhana/Artha = (H2 - L2) + lagna, etc.
        t[f'L{k}'] = pts[_SIGN_LORD[(lagna_sign + k - 1) % 12]]
    t['Lsun'] = pts[_SIGN_LORD[int(pts['Su'] // 30)]]
    t['Lmoon'] = pts[_SIGN_LORD[int(pts['Mo'] // 30)]]
    t['Cn15'] = 105.0   # fixed zodiacal point 15 deg Cancer (JHora's Jalapatana)
    return t


def _saham(a: float, b: float, la: float, close: float | None = None) -> float:
    diff = (a - b) % 360.0
    rel = (la - b) % 360.0
    add30 = 0.0 if (0.0 < rel < diff) else 30.0
    return (diff + add30 + (la if close is None else close)) % 360.0


def compute_sahams(pts: dict, night: bool, include_pending: bool = False) -> dict:
    """pts: annual longitudes {'Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke','La'}.

    Returns {saham_name: longitude_deg}. At night A,B swap by default, UNLESS the
    def sets no_swap (day form holds) or carries a night_* triple (day/night-
    distinct). CONFIRMED (oracle-validated) and SOURCE (book formula, no oracle
    grade) sahams are emitted; PENDING only when include_pending=True. Fail-soft
    per saham.
    """
    for k in _REQUIRED:
        if k not in pts:
            raise ValueError(f"compute_sahams: missing annual longitude {k!r}")
    la = pts['La']
    t = _resolve(pts)
    # parents first (they are referenced by Yasas/Mitra/Mahatmya/Artha/Bandhana...)
    t['Punya'] = _saham(t['Su'], t['Mo'], la) if night else _saham(t['Mo'], t['Su'], la)
    t['Vidya'] = _saham(t['Mo'], t['Su'], la) if night else _saham(t['Su'], t['Mo'], la)
    out = {'Punya': t['Punya'], 'Vidya': t['Vidya']}
    for d in TABLE:
        if d.name in ('Punya', 'Vidya'):
            continue
        if d.status == 'PENDING' and not include_pending:
            continue
        try:
            _b, _night = d.b, night
            # Samartha (PyJHora): if Mars owns the lagna sign, substitute Jupiter
            # for the lagna lord AND flip day/night (their "swap ABC" exception).
            if d.name == 'Samartha' and _SIGN_LORD[int(la // 30) % 12] == 'Ma':
                _b, _night = 'Ju', not night
            if _night and d.night_a is not None:
                # day/night-DISTINCT: the night triple replaces (a,b,third) wholesale
                a, b, third = d.night_a, d.night_b, d.night_third
            elif _night and not d.no_swap:
                a, b, third = _b, d.a, d.third   # reverse-all (A,B swap)
            else:
                a, b, third = d.a, _b, d.third   # day form (also night if no_swap)
            close = t[third] if third else None
            out[d.name] = _saham(t[a], t[b], la, close)
            t[d.name] = out[d.name]   # make it available as a component to later
            # sahams in TABLE order (e.g. Preeti = Sastra - Punya + Lagna).
        except Exception:
            continue
    return out
