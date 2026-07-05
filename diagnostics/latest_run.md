# helpers/ephemeris.py created (Session 52)

**Added:** `agent/calculations/helpers/ephemeris.py` — replaces the 1-line
stub with `sidereal_longitude()`, `sidereal_position()` (frozen
`SiderealPosition` dataclass: longitude + signed speed), and canonical
`EphemerisError`. Convention confirmed against panchaka.py,
chart_profile.py, combustion.py before writing.

## Scope
File only. No call-site migration, no tests (none reference this file
yet). 13 pending TODO-marked call sites listed in the module CITATION;
migrations are separate follow-up prompts.

Not run: pytest (explicitly out of scope for this prompt).
