"""Single source of truth for the Swiss Ephemeris (.se1) data path.

Importing this module points pyswisseph at the bundled .se1 files
PROCESS-GLOBALLY, so every ``FLG_SWIEPH`` call in the process resolves to the
Swiss Ephemeris instead of silently falling back to the lower-precision
Moshier model.

WHY THIS EXISTS (S162):
  The whole engine already issues ``FLG_SWIEPH`` calls -- but pyswisseph only
  reads the .se1 files if ``set_ephe_path`` has been called to point at them.
  Before this module, nothing set the path except ``varsha_pravesh`` (which
  then had to restore it to avoid the S156 process-global leak), so every
  other call site ran on the Moshier fallback. That split was an accident of
  a missing path call, never a design decision (SESSION_LOG S157: "the rest of
  the engine ... never calls set_ephe_path, so it runs on the Moshier
  fallback"). Setting the path ONCE here -- imported by both
  ``chart_calculator`` and ``helpers/ephemeris`` -- makes .se1 the uniform
  backend and removes the per-call set/restore dance.

SAFE EVERYWHERE:
  ``set_ephe_path`` to a directory that does not contain the .se1 files does
  NOT raise -- pyswisseph simply falls back to Moshier. So on a bare CI
  sandbox without the bundled files this is a no-op that preserves prior
  behavior, while on any real checkout (the files are committed under
  PyJHora-main/.../ephe) it flips the whole process to .se1.
"""

import os

import swisseph as swe

# The bundled Swiss Ephemeris files live inside the vendored PyJHora tree. This
# is the ONLY copy in the repo; keep this the single definition of the path
# string (varsha_pravesh imports EPHE_PATH from here rather than redefining it).
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
EPHE_PATH = os.path.join(
    _REPO_ROOT, "PyJHora-main", "src", "jhora", "data", "ephe"
)


def configure_ephemeris() -> None:
    """Point pyswisseph at the bundled .se1 files.

    Idempotent and process-global. A missing directory is a safe no-op
    (Moshier fallback), so this never needs a try/except for the file-absent
    case; it only guards against a genuinely broken swisseph binding.
    """
    try:
        swe.set_ephe_path(EPHE_PATH)
    except Exception as exc:  # pragma: no cover - defensive; never seen in practice
        raise RuntimeError(
            f"ephemeris_config: swe.set_ephe_path({EPHE_PATH!r}) failed: {exc}"
        ) from exc


# Applied at import so any module importing this (directly, or transitively via
# helpers/ephemeris or chart_calculator) runs on .se1 without an explicit
# startup call.
configure_ephemeris()
