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
    status: str


# DAY form (a, b[, third]); night swaps a,b for every saham.
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
    # --- PENDING: wrong/unverified formula; re-derive from Nilakantha, then
    #     validate on all four charts before promoting. NOT emitted by default. ---
    SahamDef('Gaurava', 'Ju', 'Punya', None, 'Nila -- night form unverified', 'PENDING'),
    SahamDef('Vyapara', 'Ma', 'Sa', None, 'Nila s20 -- diverges from Satru at night', 'PENDING'),
    SahamDef('Samartha', 'Ju', 'Ma', None, 'Nila -- 2024-coincident w/ Kali; wrong', 'PENDING'),
    SahamDef('Bhratru', 'Ju', 'Sa', None, 'Nila -- night form unverified', 'PENDING'),
    SahamDef('Roga', 'Ve', 'Ma', None, 'Nila -- 2024-coincident w/ Sraddha; wrong', 'PENDING'),
    SahamDef('Sastra', 'Me', 'Sa', 'Ju', 'Nila s13 -- +30 edge unresolved', 'PENDING'),
    SahamDef('Karyasiddhi', 'Sa', 'Su', 'Lsun', 'Nila s17 -- night form unverified', 'PENDING'),
    SahamDef('Artha', 'Punya', 'Ve', 'Vidya', 'Nila -- unverified', 'PENDING'),
    SahamDef('Labha', 'Ma', 'Sa', 'Ra', 'Nila -- unverified', 'PENDING'),
    SahamDef('Santapa', 'Sa', 'Mo', 'H7', 'Nila s18 -- bhava term unverified', 'PENDING'),
    SahamDef('Preeti', 'Vidya', 'Punya', 'La', 'Nila s19 -- extra term unresolved', 'PENDING'),
    SahamDef('Jalapatana', 'Sa', 'Mo', 'La', 'Nila s20 -- extra term unresolved', 'PENDING'),
]

_REQUIRED = ('Su', 'Mo', 'Ma', 'Me', 'Ju', 'Ve', 'Sa', 'Ra', 'Ke', 'La')


def _resolve(pts: dict) -> dict:
    t = dict(pts)
    la = pts['La']
    for k in range(1, 13):
        t[f'H{k}'] = (la + (k - 1) * 30.0) % 360.0
    t['Lsun'] = pts[_SIGN_LORD[int(pts['Su'] // 30)]]
    t['Lmoon'] = pts[_SIGN_LORD[int(pts['Mo'] // 30)]]
    return t


def _saham(a: float, b: float, la: float, close: float | None = None) -> float:
    diff = (a - b) % 360.0
    rel = (la - b) % 360.0
    add30 = 0.0 if (0.0 < rel < diff) else 30.0
    return (diff + add30 + (la if close is None else close)) % 360.0


def compute_sahams(pts: dict, night: bool, include_pending: bool = False) -> dict:
    """pts: annual longitudes {'Su','Mo','Ma','Me','Ju','Ve','Sa','Ra','Ke','La'}.

    Returns {saham_name: longitude_deg}. Night swaps A,B for every saham. Fail-soft
    per saham. PENDING sahams emitted only when include_pending=True.
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
            a, b = (d.b, d.a) if night else (d.a, d.b)
            close = t[d.third] if d.third else None
            out[d.name] = _saham(t[a], t[b], la, close)
        except Exception:
            continue
    return out
