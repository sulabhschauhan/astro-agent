"""
frontend/app.py
Streamlit UI — Vedic astrology assistant (Parashara RAG agent).
"""

import hashlib
import logging
import re
import sys
import os
import datetime
from pathlib import Path

# SessionManager writes to data/sessions/ (relative path) — must be project root
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))
os.chdir(_ROOT)

import streamlit as st

from agent.chart_calculator import calculate_chart, format_kundali_context, geocode_place_candidates
from agent.session_manager import SessionManager
from agent.astrosage_parser import parse_astrosage_pdf, _PRIORITY_ORDER
from PIL import Image
from agent.palm_processor import validate_palm_image, describe_palm_image, describe_hand_detail_image
from agent.interpretive.palm_reading import generate_palm_reading
from agent.infra.orchestrator import answer_question
from agent.interpretive.answer_renderer import render_answer

logger = logging.getLogger(__name__)

# ─── S66 F5: opt-in local dogfood capture ──────────────────────────────────────
# Read once at module scope (re-evaluated every Streamlit script rerun, same
# as any other module-level statement here). Local-only, gitignored (see
# .gitignore) -- never committed. Derived text ONLY: image bytes, image
# hashes, pdf_context, and any AstroSage content are deliberately EXCLUDED
# (no-storage lock ruling 2026-07-12).
_DOGFOOD_CAPTURE  = os.environ.get("ASTRO_DOGFOOD_CAPTURE") == "1"
_DOGFOOD_LOG_PATH = _ROOT / "diagnostics" / "dogfood_capture.md"


def _capture_dogfood_run(palm_left, palm_right, hand_detail, reading) -> None:
    """
    Append one markdown block to diagnostics/dogfood_capture.md for a
    successful generate_palm_reading() call (regardless of Ring 1
    validation outcome -- pass/fail is itself captured data).

    Args:
        palm_left/palm_right/hand_detail: confirmed description strings
            passed to generate_palm_reading(), or None if that hand/photo
            was not confirmed for this run.
        reading: the PalmReadingResult returned by generate_palm_reading().
    """
    lines = [f"## RUN {datetime.datetime.now().isoformat()}", ""]

    lines.append("### Confirmed descriptions")
    if palm_left:
        lines.append("#### LEFT")
        lines.append(palm_left)
    if palm_right:
        lines.append("#### RIGHT")
        lines.append(palm_right)
    if hand_detail:
        lines.append("#### HAND_DETAIL")
        lines.append(hand_detail)
    lines.append("")

    lines.append("### reading_text")
    lines.append(reading.reading_text)
    lines.append("")

    # A1 (S68 F-C F5): raw tagged draft (anchors intact, pre-decline/
    # pre-DISCLAIMER) alongside the stripped/display form above -- Ring 3
    # pass 4 scores claim->anchor fidelity from THIS form; the stripped
    # reading_text alone can't show which retrieved chunk backs which
    # sentence. Wrapped in its own try/except (not just the outer
    # call-site safety net) so a failure capturing this NEW field alone
    # can never also cost the pre-existing capture lines around it.
    lines.append("### READING (TAGGED)")
    try:
        lines.append(reading.reading_text_tagged)
    except Exception as exc:
        lines.append(f"[capture error: reading_text_tagged unavailable: {exc}]")
    lines.append("")

    lines.append("### sources")
    # score is already round(..., 4) at the source (ingestion/query_engine.py)
    # -- same value the UI renders, not reformatted here. S67 R1 added a
    # "feature" tag to every source dict; captured here so Ring 3 pass 3's
    # P1 claim ledger can score per-feature support directly from this
    # capture instead of forensically re-deriving it (pass-2's gap).
    for src in reading.sources:
        lines.append(f"- {src['book']}, p.{src['page']} (score: {src['score']}, feature: {src['feature']})")
    lines.append("")

    # S67 R3: registry-order supported/unsupported feature verdicts,
    # captured verbatim (tuple repr) -- the other half of the P1
    # claim-ledger evidence the source lines' feature tags feed into.
    lines.append("### feature_support")
    lines.append(f"supported_features: {reading.supported_features}")
    lines.append(f"unsupported_features: {reading.unsupported_features}")
    lines.append("")

    lines.append("### ring1_validation")
    lines.append(f"passed: {reading.validation.passed}")
    lines.append(f"failures: {reading.validation.failures}")
    # S67 F2c added retry_used to PalmReadingResult but F5's original
    # capture never recorded it -- Ring 3 pass 2 could not tell whether
    # any of its 3 captured runs needed the validator-fed retry. Captured
    # here, alongside the other Ring 1 outcome fields.
    lines.append(f"retry_used: {reading.retry_used}")

    # A1 (S68 F-C F5): one-line-per-failure form of the SAME
    # ValidationReport.failures tuple already captured above as a single
    # repr'd line -- today only retry_used implies a first-draft failure
    # existed without saying what it was; this makes V-1/V-2 violations
    # (and any display-check failure) grep-able per-run hard data, not a
    # replacement for the existing "failures:" line.
    lines.append("ring1_failures:")
    try:
        if reading.validation.failures:
            lines.extend(reading.validation.failures)
        else:
            lines.append("none")
    except Exception as exc:
        lines.append(f"[capture error: ring1_failures unavailable: {exc}]")

    # A1 (S68 F-C F5): size of the V-2 anchor-legality membership union
    # (valid_chunk_ids in generate_palm_reading) -- a cheap denominator
    # for pass-4's anchor-fidelity spot-check. VERIFIED UNAVAILABLE from
    # any existing app.py-visible surface (verify-before-transcribe,
    # per the instructing prompt's own constraint): valid_chunk_ids is a
    # local computed inside generate_palm_reading() and never returned
    # on PalmReadingResult, and reading.sources' dicts (book/page/score/
    # feature) never carry chunk_id -- the S67 R1 per-feature dedupe
    # also rules out len(reading.sources) as a safe proxy (the SAME
    # chunk_id can legitimately appear under two different features'
    # source entries, see test_per_feature_map_ordering_and_dedupe_
    # for_display). Per the instructing constraint's own fallback:
    # captured as "unavailable" rather than derived from an unreliable
    # proxy or a new dataclass field -- palm_reading.py is out of scope
    # for this task.
    lines.append("valid_chunk_ids_count: unavailable")
    lines.append("")

    _DOGFOOD_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_DOGFOOD_LOG_PATH, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ─── Page config (must be first Streamlit call) ───────────────────────────────

st.set_page_config(
    page_title="Astro Agent",
    page_icon="🪐",
    layout="wide",
)

# ─── Session state defaults ───────────────────────────────────────────────────

if "session_mgr" not in st.session_state:
    st.session_state.session_mgr = SessionManager()
if "chart" not in st.session_state:
    st.session_state.chart = None
if "kundali_str" not in st.session_state:
    st.session_state.kundali_str = ""
if "chart_ready" not in st.session_state:
    st.session_state.chart_ready = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_context" not in st.session_state:
    st.session_state.pdf_context = None
if "_astrosage_pdf_name" not in st.session_state:
    st.session_state["_astrosage_pdf_name"] = None
if "palm_left_str" not in st.session_state:
    st.session_state.palm_left_str = None
if "palm_left_hash" not in st.session_state:
    st.session_state.palm_left_hash = None
if "palm_left_status" not in st.session_state:
    st.session_state.palm_left_status = None
if "palm_right_str" not in st.session_state:
    st.session_state.palm_right_str = None
if "palm_right_hash" not in st.session_state:
    st.session_state.palm_right_hash = None
if "palm_right_status" not in st.session_state:
    st.session_state.palm_right_status = None
if "place_error" not in st.session_state:
    st.session_state.place_error = None
if "selected_place" not in st.session_state:
    st.session_state.selected_place = None
if "place_candidates" not in st.session_state:
    st.session_state.place_candidates = []
if "palm_left_confirmed" not in st.session_state:
    st.session_state.palm_left_confirmed = False
if "palm_right_confirmed" not in st.session_state:
    st.session_state.palm_right_confirmed = False
if "_palm_left_image_name" not in st.session_state:
    st.session_state["_palm_left_image_name"] = None
if "_palm_right_image_name" not in st.session_state:
    st.session_state["_palm_right_image_name"] = None
if "palm_left_bytes" not in st.session_state:
    st.session_state.palm_left_bytes = None
if "palm_right_bytes" not in st.session_state:
    st.session_state.palm_right_bytes = None
if "palm_left_hand_confirmed" not in st.session_state:
    st.session_state.palm_left_hand_confirmed = False
if "palm_right_hand_confirmed" not in st.session_state:
    st.session_state.palm_right_hand_confirmed = False
if "palm_left_needs_reupload" not in st.session_state:
    st.session_state.palm_left_needs_reupload = False
if "palm_right_needs_reupload" not in st.session_state:
    st.session_state.palm_right_needs_reupload = False
if "palm_left_regen_warning" not in st.session_state:
    st.session_state.palm_left_regen_warning = None
if "palm_right_regen_warning" not in st.session_state:
    st.session_state.palm_right_regen_warning = None
if "spouse_pdf_context" not in st.session_state:
    st.session_state.spouse_pdf_context = None
if "_spouse_pdf_name" not in st.session_state:
    st.session_state["_spouse_pdf_name"] = None
if "hand_detail_str" not in st.session_state:
    st.session_state.hand_detail_str = None
if "_hand_detail_image_name" not in st.session_state:
    st.session_state["_hand_detail_image_name"] = None
if "hand_detail_hash" not in st.session_state:
    st.session_state.hand_detail_hash = None
if "hand_detail_bytes" not in st.session_state:
    st.session_state.hand_detail_bytes = None
if "hand_detail_confirmed" not in st.session_state:
    st.session_state.hand_detail_confirmed = False
if "palm_reading_result" not in st.session_state:
    st.session_state.palm_reading_result = None

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Birth Details")

    # ── Step 1: place search (outside form) ──────────────────────────────────
    _place_input = st.text_input(
        "Place of Birth", value="Calcutta, India", placeholder="Mumbai, India",
        key="place_search_text",
    )
    if st.button("Search", key="search_place_btn"):
        _cands = geocode_place_candidates(_place_input)
        st.session_state.place_candidates = _cands
        st.session_state.place_error = None
        if not _cands:
            st.session_state.selected_place = None
            st.session_state.place_error = (
                f"'{_place_input}' not found — try a major nearby city "
                "e.g. 'Mumbai, India' or 'New Delhi, India'."
            )
        elif len(_cands) == 1:
            st.session_state.selected_place = _cands[0]["display_name"]

    if st.session_state.place_error:
        st.error(st.session_state.place_error)
    elif len(st.session_state.place_candidates) > 1:
        _labels = [c["display_name"] for c in st.session_state.place_candidates]
        _choice = st.radio("Select location:", _labels, key="place_radio")
        st.session_state.selected_place = _choice
    elif st.session_state.selected_place:
        st.caption(f"Place confirmed: {st.session_state.selected_place}")

    # ── Step 2: birth details form ────────────────────────────────────────────
    with st.form("birth_form"):
        name = st.text_input("Name", value="Sulabh Singh Chauhan")
        col1, col2, col3 = st.columns(3)
        with col1:
            day   = st.selectbox("Day",   list(range(1, 32)), index=5)
        with col2:
            month = st.selectbox("Month", [
                "January","February","March","April","May","June",
                "July","August","September","October","November","December",
            ], index=3)
        with col3:
            year  = st.selectbox("Year",  list(range(2025, 1939, -1)), index=37)
        dob = f"{day} {month} {year}"
        tob = st.text_input("Time of Birth (IST)", value="00:30", placeholder="HH:MM", key="birth_time_input")
        submitted = st.form_submit_button(
            "Calculate Kundali",
            disabled=st.session_state.selected_place is None,
        )

    if submitted:
        time_val = st.session_state.get("birth_time_input", "")
        if not time_val:
            st.sidebar.warning("Please enter time of birth.")
            st.stop()
        if time_val:
            if not re.match(r'^\d{2}:\d{2}$', time_val):
                st.error("Invalid format — enter time as HH:MM (e.g. 14:30)")
                st.stop()
            hh, mm = int(time_val.split(":")[0]), int(time_val.split(":")[1])
            if not (0 <= hh <= 23 and 0 <= mm <= 59):
                st.error("Invalid time — hours 00-23, minutes 00-59")
                st.stop()
        place = st.session_state.selected_place
        missing = [f for f, v in [("Name", name), ("Place", place or "")] if not v.strip()]
        if missing:
            st.error(f"Required: {', '.join(missing)}")
        else:
            try:
                with st.spinner("Calculating your chart..."):
                    chart = calculate_chart(name.strip(), dob, tob, place)
                st.session_state.chart       = chart
                st.session_state.kundali_str = format_kundali_context(chart)
                st.session_state.chart_ready = True
                st.session_state.place_error = None
            except ValueError as e:
                if "geocode" in str(e).lower() or "cannot geocode" in str(e).lower():
                    st.session_state.place_error = (
                        f"'{place}' not found — try a major nearby city "
                        "e.g. 'Mumbai, India' or 'New Delhi, India'."
                    )
                    st.sidebar.error(st.session_state.place_error)
                else:
                    st.sidebar.error(f"Chart error: {e}")
                st.session_state.chart_ready = False
                st.stop()
            except Exception as e:
                st.sidebar.error(f"Unexpected error: {e}")
                st.session_state.chart_ready = False
                st.stop()

    if st.session_state.chart_ready:
        with st.expander("Kundali Summary"):
            st.text(st.session_state.kundali_str)

    st.divider()
    st.caption(f"Session ID: `{st.session_state.session_mgr.session_id[:8]}…`")
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages    = []
        st.session_state.session_mgr = SessionManager()
        st.rerun()


# ─── Main area ────────────────────────────────────────────────────────────────

# T4 architecture / T4 V1 boundaries lock (CLAUDE.md Session 65): display-
# layer withholding ONLY -- pdf_context (the full parsed string threaded to
# ask()) is NOT modified, and astrosage_parser.py is NOT modified; the RAG/
# LLM path still sees these sections in full. Pratyantar: suppressed per
# the +/-37-day-drift/wrong-lord posture (same root cause as
# prompt_builder.py's kundali-slot carry-forward) -- Pratyantar-level date
# claims aren't reliable enough to show a user as if they were precise.
# Lal Kitab: post-V1 hard gate (CLAUDE.md "Post-V1 design gate: Lal Kitab
# remedy tier", Session 61) -- remedies are out of V1 scope entirely,
# withheld here rather than partially surfaced. Scope guard: this
# frozenset governs ONLY the "Your AstroSage Report" display expander
# below -- no other code path reads it. Revisit trigger: Lal Kitab V1.1
# unlock (gated on that carry-forward's required steps) or a future
# Pratyantar-precision fix.
_WITHHELD_SECTIONS = frozenset({"Pratyantar", "Lal Kitab"})

_SECTION_HEADER_RE = re.compile(
    r"^\[(" + "|".join(re.escape(n) for n in _PRIORITY_ORDER) + r")\]$",
    re.MULTILINE,
)


def _split_astrosage_sections(pdf_context: str) -> list[tuple[str, str]]:
    """
    Split parse_astrosage_pdf()'s combined output into (name, content) pairs
    for verbatim display.

    SENSITIVE_TO astrosage_parser.py's parse_astrosage_pdf() combined-output
    format: `"ASTROSAGE PDF DATA:\\n" + "\\n\\n".join(f"[{name}]\\n{content}"
    for name, content in sections.items())`. Section names auto-track the
    parser via _PRIORITY_ORDER -- only the join format ("[Name]\\ncontent",
    "\\n\\n" separator) remains a manual coupling. This splitter locates each
    known "[Name]" header line and slices the text between headers as that
    section's body; bracketed lines inside a section's own content that
    don't match a known name are left alone. If astrosage_parser.py's join
    format ever changes, this splitter breaks with it -- re-verify against
    the source before trusting this function after any astrosage_parser.py
    edit.

    Fail-soft: if no known "[Name]" headers are found, returns the full
    string (with the "ASTROSAGE PDF DATA:\\n" prefix stripped) unsplit
    under a single "AstroSage Report" label and logs a warning -- never
    raises.
    """
    parts = _SECTION_HEADER_RE.split(pdf_context)
    # parts[0] is whatever precedes the first header (the "ASTROSAGE PDF
    # DATA:" prefix line, not a real section) -- discarded. Remaining
    # parts alternate name, content, name, content, ...
    if len(parts) < 3:
        logger.warning(
            "app.py: no '[Name]' section headers found in AstroSage "
            "pdf_context — displaying unsplit (degraded, not crashing)."
        )
        return [("AstroSage Report", pdf_context.removeprefix("ASTROSAGE PDF DATA:\n"))]

    pairs: list[tuple[str, str]] = []
    for i in range(1, len(parts), 2):
        name = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        pairs.append((name, content))
    return pairs


st.title("Parashara — Vedic Astrology")

with st.expander("Upload context (PDF + palms)", expanded=False):
    # ── PDF ───────────────────────────────────────────────────────────────────
    uploaded_pdf = st.file_uploader("AstroSage PDF (optional)", type=["pdf"])
    if uploaded_pdf is not None:
        if st.session_state["_astrosage_pdf_name"] != uploaded_pdf.name:
            with st.spinner("Parsing AstroSage PDF…"):
                _pdf_parse_result = parse_astrosage_pdf(uploaded_pdf.read())
            if _pdf_parse_result:
                st.session_state.pdf_context = _pdf_parse_result
                st.session_state["_astrosage_pdf_name"] = uploaded_pdf.name
                st.success("AstroSage data loaded.")
            else:
                st.session_state.pdf_context = None
                st.warning("Could not extract sections — check this is an AstroSage PDF.")
    elif st.session_state["_astrosage_pdf_name"] is not None:
        st.session_state.pdf_context = None
        st.session_state["_astrosage_pdf_name"] = None

    # ── Left palm ─────────────────────────────────────────────────────────────
    uploaded_left = st.file_uploader(
        "Left hand (innate potential)", type=["jpg", "jpeg", "png"], key="palm_left_uploader",
    )
    if uploaded_left is not None:
        if st.session_state["_palm_left_image_name"] != uploaded_left.name:
            _lb = uploaded_left.read()
            _lh = hashlib.md5(_lb).hexdigest()
            st.session_state.palm_left_needs_reupload = False
            st.session_state.palm_left_regen_warning  = None
            with st.spinner("Validating left palm…"):
                _vr = validate_palm_image(_lb, "left")
            if _vr["hard_reject"]:
                st.error(_vr["reject_message"])
                st.session_state.palm_left_str       = None
                st.session_state.palm_left_hash      = None
                st.session_state.palm_left_status    = None
                st.session_state.palm_left_bytes     = None
                st.session_state.palm_reading_result = None
            elif st.session_state.palm_right_hash == _lh:
                st.error("Same image uploaded for both hands — please upload each hand separately")
                st.session_state.palm_left_str       = None
                st.session_state.palm_left_hash      = None
                st.session_state.palm_left_status    = None
                st.session_state.palm_left_bytes     = None
                st.session_state.palm_reading_result = None
            else:
                if _vr["warn"]:
                    st.warning(_vr["warn_message"])
                st.session_state.palm_left_hash           = _lh
                st.session_state.palm_left_status         = _vr
                st.session_state.palm_left_bytes          = _lb
                st.session_state.palm_left_hand_confirmed = False
                try:
                    with st.spinner("Reading palm…"):
                        _desc = describe_palm_image(_lb, "left")
                    st.session_state.palm_left_str            = _desc
                    st.session_state["_palm_left_image_name"] = uploaded_left.name
                    st.session_state.palm_left_confirmed      = False
                    st.success("Left palm described — review below")
                except RuntimeError as e:
                    st.error(f"Could not read palm image: {e}")
                    st.session_state.palm_left_str       = None
                    st.session_state.palm_reading_result = None
    elif st.session_state.palm_left_hash is not None or st.session_state.palm_left_needs_reupload:
        st.session_state.palm_left_str            = None
        st.session_state.palm_left_hash           = None
        st.session_state.palm_left_status         = None
        st.session_state.palm_left_bytes          = None
        st.session_state.palm_left_confirmed      = False
        st.session_state.palm_left_hand_confirmed = False
        st.session_state.palm_left_needs_reupload = False
        st.session_state.palm_left_regen_warning  = None
        st.session_state["_palm_left_image_name"] = None
        st.session_state.palm_reading_result      = None

    # ── Left palm: preview, tips, hand confirmation ─────────────────────────────
    if uploaded_left is not None and st.session_state.palm_left_bytes is not None:
        st.image(st.session_state.palm_left_bytes, caption="Left palm", width=150)
        for _tip in (st.session_state.palm_left_status or {}).get("geometry_tips", []):
            st.caption(_tip)
        if st.session_state.palm_left_regen_warning:
            st.warning(st.session_state.palm_left_regen_warning)
        if not st.session_state.palm_left_hand_confirmed:
            st.write("Is this your **Left** hand?")
            _lcy, _lcn = st.columns(2)
            with _lcy:
                if st.button("Yes", key="left_hand_yes"):
                    st.session_state.palm_left_hand_confirmed = True
                    st.rerun()
            with _lcn:
                if st.button("No (swap)", key="left_hand_no"):
                    try:
                        if st.session_state.palm_right_hash is not None:
                            (st.session_state.palm_left_str, st.session_state.palm_right_str) = \
                                (st.session_state.palm_right_str, st.session_state.palm_left_str)
                            (st.session_state.palm_left_hash, st.session_state.palm_right_hash) = \
                                (st.session_state.palm_right_hash, st.session_state.palm_left_hash)
                            (st.session_state.palm_left_status, st.session_state.palm_right_status) = \
                                (st.session_state.palm_right_status, st.session_state.palm_left_status)
                            (st.session_state.palm_left_bytes, st.session_state.palm_right_bytes) = \
                                (st.session_state.palm_right_bytes, st.session_state.palm_left_bytes)
                            (st.session_state.palm_left_confirmed, st.session_state.palm_right_confirmed) = \
                                (st.session_state.palm_right_confirmed, st.session_state.palm_left_confirmed)
                            st.session_state.palm_left_hand_confirmed  = True
                            st.session_state.palm_right_hand_confirmed = True

                            # Regenerate descriptions so hand-framing matches each
                            # slot's new (post-swap) image. On failure, the swapped
                            # string above stays as a fallback — it describes these
                            # bytes already, just with the original hand's framing.
                            with st.spinner("Updating palm readings…"):
                                try:
                                    st.session_state.palm_left_str = describe_palm_image(
                                        st.session_state.palm_left_bytes, "left"
                                    )
                                    st.session_state.palm_left_regen_warning = None
                                    st.session_state.palm_left_confirmed     = False
                                    st.session_state.palm_reading_result     = None
                                except RuntimeError:
                                    st.session_state.palm_left_regen_warning = (
                                        "Could not regenerate the left palm reading after "
                                        "swapping — it may reference the wrong hand. "
                                        "Consider re-uploading this image."
                                    )
                                    st.session_state.palm_reading_result = None
                                try:
                                    st.session_state.palm_right_str = describe_palm_image(
                                        st.session_state.palm_right_bytes, "right"
                                    )
                                    st.session_state.palm_right_regen_warning = None
                                    st.session_state.palm_right_confirmed     = False
                                    st.session_state.palm_reading_result      = None
                                except RuntimeError:
                                    st.session_state.palm_right_regen_warning = (
                                        "Could not regenerate the right palm reading after "
                                        "swapping — it may reference the wrong hand. "
                                        "Consider re-uploading this image."
                                    )
                                    st.session_state.palm_reading_result = None
                        else:
                            st.session_state.palm_left_str            = None
                            st.session_state.palm_left_hash           = None
                            st.session_state.palm_left_status         = None
                            st.session_state.palm_left_bytes          = None
                            st.session_state.palm_left_confirmed      = False
                            st.session_state.palm_left_hand_confirmed = False
                            st.session_state.palm_left_needs_reupload = True
                            st.session_state.palm_reading_result      = None
                    except Exception as e:
                        st.error(f"Could not update palm state: {e}")
                    st.rerun()
        elif not st.session_state.palm_left_confirmed:
            with st.container():
                st.markdown("**Review left palm description**")
                st.markdown(st.session_state.palm_left_str)
            _lky, _lkn = st.columns(2)
            with _lky:
                if st.button("Looks right — use this description", key="left_desc_confirm"):
                    st.session_state.palm_left_confirmed = True
                    st.rerun()
            with _lkn:
                if st.button("Discard — re-upload", key="left_desc_discard"):
                    st.session_state.palm_left_str            = None
                    st.session_state.palm_left_hash           = None
                    st.session_state.palm_left_status         = None
                    st.session_state.palm_left_bytes          = None
                    st.session_state.palm_left_confirmed      = False
                    st.session_state.palm_left_hand_confirmed = False
                    st.session_state.palm_left_needs_reupload = False
                    st.session_state.palm_left_regen_warning  = None
                    st.session_state["_palm_left_image_name"] = None
                    st.session_state.palm_reading_result      = None
                    st.rerun()
        else:
            st.caption("✓ Description confirmed")
            with st.container():
                st.markdown("**Left palm description**")
                st.markdown(st.session_state.palm_left_str)
    elif st.session_state.palm_left_needs_reupload and uploaded_left is not None:
        st.warning(
            "This image doesn't belong in the Left hand slot — please remove it "
            "(✕ above) and upload it using the Right hand uploader instead."
        )

    # ── Right palm ────────────────────────────────────────────────────────────
    uploaded_right = st.file_uploader(
        "Right hand (current trajectory)", type=["jpg", "jpeg", "png"], key="palm_right_uploader",
    )
    if uploaded_right is not None:
        if st.session_state["_palm_right_image_name"] != uploaded_right.name:
            _rb = uploaded_right.read()
            _rh = hashlib.md5(_rb).hexdigest()
            st.session_state.palm_right_needs_reupload = False
            st.session_state.palm_right_regen_warning  = None
            with st.spinner("Validating right palm…"):
                _vr = validate_palm_image(_rb, "right")
            if _vr["hard_reject"]:
                st.error(_vr["reject_message"])
                st.session_state.palm_right_str      = None
                st.session_state.palm_right_hash     = None
                st.session_state.palm_right_status   = None
                st.session_state.palm_right_bytes    = None
                st.session_state.palm_reading_result = None
            elif st.session_state.palm_left_hash == _rh:
                st.error("Same image uploaded for both hands — please upload each hand separately")
                st.session_state.palm_right_str      = None
                st.session_state.palm_right_hash     = None
                st.session_state.palm_right_status   = None
                st.session_state.palm_right_bytes    = None
                st.session_state.palm_reading_result = None
            else:
                if _vr["warn"]:
                    st.warning(_vr["warn_message"])
                st.session_state.palm_right_hash           = _rh
                st.session_state.palm_right_status         = _vr
                st.session_state.palm_right_bytes          = _rb
                st.session_state.palm_right_hand_confirmed = False
                try:
                    with st.spinner("Reading palm…"):
                        _desc = describe_palm_image(_rb, "right")
                    st.session_state.palm_right_str            = _desc
                    st.session_state["_palm_right_image_name"] = uploaded_right.name
                    st.session_state.palm_right_confirmed      = False
                    st.success("Right palm described — review below")
                except RuntimeError as e:
                    st.error(f"Could not read palm image: {e}")
                    st.session_state.palm_right_str      = None
                    st.session_state.palm_reading_result = None
    elif st.session_state.palm_right_hash is not None or st.session_state.palm_right_needs_reupload:
        st.session_state.palm_right_str            = None
        st.session_state.palm_right_hash           = None
        st.session_state.palm_right_status         = None
        st.session_state.palm_right_bytes          = None
        st.session_state.palm_right_confirmed      = False
        st.session_state.palm_right_hand_confirmed = False
        st.session_state.palm_right_needs_reupload = False
        st.session_state.palm_right_regen_warning  = None
        st.session_state["_palm_right_image_name"] = None
        st.session_state.palm_reading_result       = None

    # ── Right palm: preview, tips, hand confirmation ────────────────────────────
    if uploaded_right is not None and st.session_state.palm_right_bytes is not None:
        st.image(st.session_state.palm_right_bytes, caption="Right palm", width=150)
        for _tip in (st.session_state.palm_right_status or {}).get("geometry_tips", []):
            st.caption(_tip)
        if st.session_state.palm_right_regen_warning:
            st.warning(st.session_state.palm_right_regen_warning)
        if not st.session_state.palm_right_hand_confirmed:
            st.write("Is this your **Right** hand?")
            _rcy, _rcn = st.columns(2)
            with _rcy:
                if st.button("Yes", key="right_hand_yes"):
                    st.session_state.palm_right_hand_confirmed = True
                    st.rerun()
            with _rcn:
                if st.button("No (swap)", key="right_hand_no"):
                    try:
                        if st.session_state.palm_left_hash is not None:
                            (st.session_state.palm_left_str, st.session_state.palm_right_str) = \
                                (st.session_state.palm_right_str, st.session_state.palm_left_str)
                            (st.session_state.palm_left_hash, st.session_state.palm_right_hash) = \
                                (st.session_state.palm_right_hash, st.session_state.palm_left_hash)
                            (st.session_state.palm_left_status, st.session_state.palm_right_status) = \
                                (st.session_state.palm_right_status, st.session_state.palm_left_status)
                            (st.session_state.palm_left_bytes, st.session_state.palm_right_bytes) = \
                                (st.session_state.palm_right_bytes, st.session_state.palm_left_bytes)
                            (st.session_state.palm_left_confirmed, st.session_state.palm_right_confirmed) = \
                                (st.session_state.palm_right_confirmed, st.session_state.palm_left_confirmed)
                            st.session_state.palm_left_hand_confirmed  = True
                            st.session_state.palm_right_hand_confirmed = True

                            # Regenerate descriptions so hand-framing matches each
                            # slot's new (post-swap) image. On failure, the swapped
                            # string above stays as a fallback — it describes these
                            # bytes already, just with the original hand's framing.
                            with st.spinner("Updating palm readings…"):
                                try:
                                    st.session_state.palm_left_str = describe_palm_image(
                                        st.session_state.palm_left_bytes, "left"
                                    )
                                    st.session_state.palm_left_regen_warning = None
                                    st.session_state.palm_left_confirmed     = False
                                    st.session_state.palm_reading_result     = None
                                except RuntimeError:
                                    st.session_state.palm_left_regen_warning = (
                                        "Could not regenerate the left palm reading after "
                                        "swapping — it may reference the wrong hand. "
                                        "Consider re-uploading this image."
                                    )
                                    st.session_state.palm_reading_result = None
                                try:
                                    st.session_state.palm_right_str = describe_palm_image(
                                        st.session_state.palm_right_bytes, "right"
                                    )
                                    st.session_state.palm_right_regen_warning = None
                                    st.session_state.palm_right_confirmed     = False
                                    st.session_state.palm_reading_result      = None
                                except RuntimeError:
                                    st.session_state.palm_right_regen_warning = (
                                        "Could not regenerate the right palm reading after "
                                        "swapping — it may reference the wrong hand. "
                                        "Consider re-uploading this image."
                                    )
                                    st.session_state.palm_reading_result = None
                        else:
                            st.session_state.palm_right_str            = None
                            st.session_state.palm_right_hash           = None
                            st.session_state.palm_right_status         = None
                            st.session_state.palm_right_bytes          = None
                            st.session_state.palm_right_confirmed      = False
                            st.session_state.palm_right_hand_confirmed = False
                            st.session_state.palm_right_needs_reupload = True
                            st.session_state.palm_reading_result       = None
                    except Exception as e:
                        st.error(f"Could not update palm state: {e}")
                    st.rerun()
        elif not st.session_state.palm_right_confirmed:
            with st.container():
                st.markdown("**Review right palm description**")
                st.markdown(st.session_state.palm_right_str)
            _rky, _rkn = st.columns(2)
            with _rky:
                if st.button("Looks right — use this description", key="right_desc_confirm"):
                    st.session_state.palm_right_confirmed = True
                    st.rerun()
            with _rkn:
                if st.button("Discard — re-upload", key="right_desc_discard"):
                    st.session_state.palm_right_str            = None
                    st.session_state.palm_right_hash           = None
                    st.session_state.palm_right_status         = None
                    st.session_state.palm_right_bytes          = None
                    st.session_state.palm_right_confirmed      = False
                    st.session_state.palm_right_hand_confirmed = False
                    st.session_state.palm_right_needs_reupload = False
                    st.session_state.palm_right_regen_warning  = None
                    st.session_state["_palm_right_image_name"] = None
                    st.session_state.palm_reading_result       = None
                    st.rerun()
        else:
            st.caption("✓ Description confirmed")
            with st.container():
                st.markdown("**Right palm description**")
                st.markdown(st.session_state.palm_right_str)
    elif st.session_state.palm_right_needs_reupload and uploaded_right is not None:
        st.warning(
            "This image doesn't belong in the Right hand slot — please remove it "
            "(✕ above) and upload it using the Left hand uploader instead."
        )

    # ── Spouse AstroSage PDF ──────────────────────────────────────────────────
    uploaded_spouse_pdf = st.file_uploader(
        "Spouse AstroSage PDF (optional)", type=["pdf"], key="spouse_pdf_uploader",
    )
    if uploaded_spouse_pdf is not None:
        if st.session_state["_spouse_pdf_name"] != uploaded_spouse_pdf.name:
            with st.spinner("Parsing spouse AstroSage PDF…"):
                _spouse_parse_result = parse_astrosage_pdf(uploaded_spouse_pdf.read())
            if _spouse_parse_result:
                st.session_state.spouse_pdf_context = _spouse_parse_result
                st.session_state["_spouse_pdf_name"] = uploaded_spouse_pdf.name
                st.success("Spouse AstroSage data loaded.")
            else:
                st.session_state.spouse_pdf_context = None
                st.warning("Could not extract sections — check this is an AstroSage PDF.")
    elif st.session_state["_spouse_pdf_name"] is not None:
        st.session_state.spouse_pdf_context = None
        st.session_state["_spouse_pdf_name"] = None

    # ── Hand detail photo ─────────────────────────────────────────────────────
    uploaded_hand_detail = st.file_uploader(
        "Hand detail photo (optional — for detailed palm analysis)",
        type=["jpg", "jpeg", "png"], key="hand_detail_uploader",
    )
    if uploaded_hand_detail is not None:
        if st.session_state["_hand_detail_image_name"] != uploaded_hand_detail.name:
            _hdb = uploaded_hand_detail.read()
            _hdh = hashlib.md5(_hdb).hexdigest()
            try:
                with st.spinner("Analysing hand detail…"):
                    import io as _io
                    _hd_img = Image.open(_io.BytesIO(_hdb))
                    _hd_desc = describe_hand_detail_image(_hd_img)
                st.session_state.hand_detail_str       = _hd_desc
                st.session_state.hand_detail_hash      = _hdh
                st.session_state.hand_detail_bytes     = _hdb
                st.session_state.hand_detail_confirmed = False
                st.session_state["_hand_detail_image_name"] = uploaded_hand_detail.name
                st.session_state.palm_reading_result   = None
                st.success("Hand detail analysed — review below")
            except ValueError as e:
                st.error(f"Could not analyse hand detail image: {e}")
                st.session_state.hand_detail_str       = None
                st.session_state.hand_detail_hash      = None
                st.session_state.hand_detail_bytes     = None
                st.session_state.hand_detail_confirmed = False
                st.session_state.palm_reading_result   = None
    elif st.session_state["_hand_detail_image_name"] is not None:
        st.session_state.hand_detail_str       = None
        st.session_state.hand_detail_hash      = None
        st.session_state.hand_detail_bytes     = None
        st.session_state.hand_detail_confirmed = False
        st.session_state["_hand_detail_image_name"] = None
        st.session_state.palm_reading_result   = None

    # ── Hand detail: review, confirm/discard (mirrors palm checkpoint) ────────
    if uploaded_hand_detail is not None and st.session_state.hand_detail_bytes is not None:
        st.image(st.session_state.hand_detail_bytes, caption="Hand detail", width=150)
        if not st.session_state.hand_detail_confirmed:
            with st.container():
                st.markdown("**Review hand detail description**")
                st.markdown(st.session_state.hand_detail_str)
            _hdky, _hdkn = st.columns(2)
            with _hdky:
                if st.button("Looks right — use this description", key="hand_detail_confirm"):
                    st.session_state.hand_detail_confirmed = True
                    st.rerun()
            with _hdkn:
                if st.button("Discard — re-upload", key="hand_detail_discard"):
                    st.session_state.hand_detail_str       = None
                    st.session_state.hand_detail_hash      = None
                    st.session_state.hand_detail_bytes     = None
                    st.session_state.hand_detail_confirmed = False
                    st.session_state["_hand_detail_image_name"] = None
                    st.session_state.palm_reading_result   = None
                    st.rerun()
        else:
            st.caption("✓ Description confirmed")
            with st.container():
                st.markdown("**Hand detail description**")
                st.markdown(st.session_state.hand_detail_str)

    # ── Palm reading generation (Session 65 T4 upload-triggered artifact) ─────
    # Upload-triggered, never question-routed (CLAUDE.md "T4 architecture"
    # lock) — only confirmed vision-derived descriptions are ever passed
    # through (palm_left, palm_right, hand_detail alike, CLAUDE.md "Palm
    # human checkpoint" lock); an unconfirmed description is withheld even
    # if it exists.
    _any_hand_confirmed = (
        st.session_state.palm_left_confirmed and st.session_state.palm_left_str
    ) or (
        st.session_state.palm_right_confirmed and st.session_state.palm_right_str
    )
    if _any_hand_confirmed:
        if st.button("Generate Palm Reading", key="generate_palm_reading_btn"):
            _confirmed_left = (
                st.session_state.palm_left_str if st.session_state.palm_left_confirmed else None
            )
            _confirmed_right = (
                st.session_state.palm_right_str if st.session_state.palm_right_confirmed else None
            )
            _confirmed_hand_detail = (
                st.session_state.hand_detail_str if st.session_state.hand_detail_confirmed else None
            )
            try:
                with st.spinner("Generating your palm reading…"):
                    st.session_state.palm_reading_result = generate_palm_reading(
                        palm_left=_confirmed_left,
                        palm_right=_confirmed_right,
                        hand_detail=_confirmed_hand_detail,
                    )
                if _DOGFOOD_CAPTURE:
                    # Fail-soft: a capture error must NEVER block or alter
                    # generation or display -- already-set session state
                    # above is untouched regardless of what happens here.
                    try:
                        _capture_dogfood_run(
                            _confirmed_left,
                            _confirmed_right,
                            _confirmed_hand_detail,
                            st.session_state.palm_reading_result,
                        )
                        st.caption("captured to dogfood log")
                    except Exception:
                        logger.warning("app.py: dogfood capture failed", exc_info=True)
            except (ValueError, RuntimeError) as e:
                st.error(str(e))

if st.session_state.get("pdf_context"):
    _astrosage_sections = _split_astrosage_sections(st.session_state.pdf_context)
    with st.expander("Your AstroSage Report"):
        for _section_name, _section_content in _astrosage_sections:
            if _section_name in _WITHHELD_SECTIONS:
                continue
            st.subheader(_section_name)
            st.text(_section_content)

if st.session_state.palm_reading_result is not None:
    _reading = st.session_state.palm_reading_result
    if not _reading.validation.passed:
        st.error(
            "Palm reading failed validation and cannot be shown: "
            + "; ".join(_reading.validation.failures)
        )
    else:
        st.markdown(_reading.reading_text)
        with st.expander("Classical sources"):
            for _src in _reading.sources:
                st.caption(f"{_src['book']}, p.{_src['page']} (score: {_src['score']})")

if not st.session_state.chart_ready:
    st.info("Enter your birth details in the sidebar to begin.")

# Render conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input — disabled until chart is ready
prompt = st.chat_input(
    "Enter your birth details in the sidebar first" if not st.session_state.chart_ready else "Ask about your birth chart…",
    disabled=not st.session_state.chart_ready,
)

if prompt:
    if not st.session_state.chart_ready:
        st.warning("Please calculate your birth chart in the sidebar first.")
    else:
        with st.chat_message("user"):
            st.markdown(prompt)

        # Deterministic calc-engine pipeline ONLY (CLAUDE.md "V1 scope" lock):
        # answer_question() routes -> builds a DomainChartProfile -> formats
        # a DomainAnswer (REFUSAL included); render_answer() turns that into
        # display text. No partner chart wiring in V1 -- marriage questions
        # will REFUSAL via has_partner_data, same as any other domain's
        # REFUSAL (rendered like any other answer, not specially handled).
        # Both user+assistant messages are appended together, only after a
        # full success, so a failure anywhere in this chain leaves
        # st.session_state.messages completely unchanged (no partial turn).
        try:
            with st.spinner("Consulting the stars…"):
                domain_answer = answer_question(prompt, st.session_state.chart)
                answer_text = render_answer(domain_answer)

            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("assistant"):
                st.markdown(answer_text)

            st.session_state.messages.append({"role": "assistant", "content": answer_text})

            # Persist session to disk; non-fatal on failure
            try:
                st.session_state.session_mgr.save()
            except RuntimeError:
                st.warning("Session could not be saved. Chat history may not persist.")

        except Exception as e:
            st.error(f"{type(e).__name__}: {e}")
