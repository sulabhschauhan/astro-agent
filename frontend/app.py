"""
frontend/app.py
Streamlit UI — Vedic astrology assistant (Parashara RAG agent).
"""

import hashlib
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
from agent.astrologer import ask
from agent.session_manager import SessionManager
from agent.astrosage_parser import parse_astrosage_pdf
from agent.context_router import route
from agent.palm_processor import validate_palm_image, describe_palm_image

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
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

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


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _stream_answer(text: str):
    for word in text.split():
        if word:
            yield word + " "


# ─── Main area ────────────────────────────────────────────────────────────────

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
            with st.spinner("Validating left palm…"):
                _vr = validate_palm_image(_lb, "left")
            if _vr["hard_reject"]:
                st.error(_vr["reject_message"])
                st.session_state.palm_left_str    = None
                st.session_state.palm_left_hash   = None
                st.session_state.palm_left_status = None
            elif st.session_state.palm_right_hash == _lh:
                st.error("Same image uploaded for both hands — please upload each hand separately")
                st.session_state.palm_left_str    = None
                st.session_state.palm_left_hash   = None
                st.session_state.palm_left_status = None
            else:
                if _vr["warn"]:
                    st.warning(_vr["warn_message"])
                st.session_state.palm_left_hash   = _lh
                st.session_state.palm_left_status = _vr
                try:
                    with st.spinner("Reading palm…"):
                        _desc = describe_palm_image(_lb, "left")
                    st.session_state.palm_left_str            = _desc
                    st.session_state["_palm_left_image_name"] = uploaded_left.name
                    st.session_state.palm_left_confirmed      = True
                    st.success("Left palm read ✓")
                except RuntimeError as e:
                    st.error(f"Could not read palm image: {e}")
                    st.session_state.palm_left_str = None
    elif st.session_state.palm_left_hash is not None:
        st.session_state.palm_left_str            = None
        st.session_state.palm_left_hash           = None
        st.session_state.palm_left_status         = None
        st.session_state.palm_left_confirmed      = False
        st.session_state["_palm_left_image_name"] = None

    _ls = st.session_state.palm_left_status
    if _ls and not _ls.get("swapped_to") and not _ls.get("confirmed"):
        if _ls["hand"] == "left":
            st.success("Left hand confirmed.")
            st.session_state.palm_left_status["confirmed"] = True
        else:
            st.info(f"Detected: {_ls['hand']} hand — correct?")
            _lcy, _lcs = st.columns(2)
            with _lcy:
                if st.button("Yes, correct", key="left_confirm"):
                    st.session_state.palm_left_status["confirmed"] = True
                    st.rerun()
            with _lcs:
                if st.button("Swap to other hand", key="left_swap"):
                    st.session_state.palm_right_hash   = st.session_state.palm_left_hash
                    st.session_state.palm_right_status = _ls
                    st.session_state.palm_right_str    = None
                    st.session_state.palm_left_status  = {"swapped_to": "right"}
                    st.session_state.palm_left_str     = None
                    st.rerun()

    # ── Right palm ────────────────────────────────────────────────────────────
    uploaded_right = st.file_uploader(
        "Right hand (current trajectory)", type=["jpg", "jpeg", "png"], key="palm_right_uploader",
    )
    if uploaded_right is not None:
        if st.session_state["_palm_right_image_name"] != uploaded_right.name:
            _rb = uploaded_right.read()
            _rh = hashlib.md5(_rb).hexdigest()
            with st.spinner("Validating right palm…"):
                _vr = validate_palm_image(_rb, "right")
            if _vr["hard_reject"]:
                st.error(_vr["reject_message"])
                st.session_state.palm_right_str    = None
                st.session_state.palm_right_hash   = None
                st.session_state.palm_right_status = None
            elif st.session_state.palm_left_hash == _rh:
                st.error("Same image uploaded for both hands — please upload each hand separately")
                st.session_state.palm_right_str    = None
                st.session_state.palm_right_hash   = None
                st.session_state.palm_right_status = None
            else:
                if _vr["warn"]:
                    st.warning(_vr["warn_message"])
                st.session_state.palm_right_hash   = _rh
                st.session_state.palm_right_status = _vr
                try:
                    with st.spinner("Reading palm…"):
                        _desc = describe_palm_image(_rb, "right")
                    st.session_state.palm_right_str            = _desc
                    st.session_state["_palm_right_image_name"] = uploaded_right.name
                    st.session_state.palm_right_confirmed      = True
                    st.success("Right palm read ✓")
                except RuntimeError as e:
                    st.error(f"Could not read palm image: {e}")
                    st.session_state.palm_right_str = None
    elif st.session_state.palm_right_hash is not None:
        st.session_state.palm_right_str            = None
        st.session_state.palm_right_hash           = None
        st.session_state.palm_right_status         = None
        st.session_state.palm_right_confirmed      = False
        st.session_state["_palm_right_image_name"] = None

    _rs = st.session_state.palm_right_status
    if _rs and not _rs.get("swapped_to") and not _rs.get("confirmed"):
        if _rs["hand"] == "right":
            st.success("Right hand confirmed.")
            st.session_state.palm_right_status["confirmed"] = True
        else:
            st.info(f"Detected: {_rs['hand']} hand — correct?")
            _rcy, _rcs = st.columns(2)
            with _rcy:
                if st.button("Yes, correct", key="right_confirm"):
                    st.session_state.palm_right_status["confirmed"] = True
                    st.rerun()
            with _rcs:
                if st.button("Swap to other hand", key="right_swap"):
                    st.session_state.palm_left_hash   = st.session_state.palm_right_hash
                    st.session_state.palm_left_status = _rs
                    st.session_state.palm_left_str    = None
                    st.session_state.palm_right_status = {"swapped_to": "left"}
                    st.session_state.palm_right_str    = None
                    st.rerun()

if not st.session_state.chart_ready:
    st.info("Enter your birth details in the sidebar to begin.")

# Render conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if msg.get("top_score") is not None:
                st.caption(f"Confidence: {msg['top_score']:.2f}")
            if msg.get("low_confidence"):
                st.warning("Low confidence — answer may be general")

# ─── "Generate My Reading" button ────────────────────────────────────────────
# Shown when a question was gated and context has since been uploaded.
_has_new_context = (
    st.session_state.get("palm_left_str") is not None
    or st.session_state.get("palm_right_str") is not None
    or st.session_state.pdf_context is not None
)
if st.session_state.pending_question is not None and _has_new_context:
    if st.button("✋ Generate My Reading"):
        _pq = st.session_state.pending_question
        st.session_state.pending_question = None
        _introduce = len(st.session_state.messages) == 0
        _router_pq = route(
            question=_pq,
            has_kundali=st.session_state.chart_ready,
            has_pdf=st.session_state.pdf_context is not None,
            has_palm=(
                st.session_state.palm_left_str is not None
                or st.session_state.palm_right_str is not None
            ),
        )
        with st.spinner("Consulting the stars…"):
            _btn_result = ask(
                question=_pq,
                kundali_context=st.session_state.kundali_str or None,
                pdf_context=st.session_state.pdf_context or None,
                palm_left=st.session_state.get("palm_left_str"),
                palm_right=st.session_state.get("palm_right_str"),
                session=st.session_state.session_mgr,
                introduce=_introduce,
                context_order=_router_pq.get("context_order", ["rag", "kundali", "pdf"]),
            )
        _btn_answer     = _btn_result["answer"]
        _btn_lc         = _btn_result["low_confidence"]
        _btn_sources    = _btn_result["sources"]
        _btn_top_score  = _btn_sources[0]["score"] if _btn_sources else None
        st.session_state.messages.append({"role": "user", "content": _pq})
        st.session_state.messages.append({
            "role":           "assistant",
            "content":        _btn_answer,
            "low_confidence": _btn_lc,
            "top_score":      _btn_top_score,
        })
        try:
            st.session_state.session_mgr.save()
        except RuntimeError:
            pass
        st.rerun()

# Chat input — disabled until chart is ready
prompt = st.chat_input(
    "Enter your birth details in the sidebar first" if not st.session_state.chart_ready else "Ask about your birth chart…",
    disabled=not st.session_state.chart_ready,
)

if prompt:
    if not st.session_state.chart_ready:
        st.warning("Please calculate your birth chart in the sidebar first.")
    else:
        # introduce=True only on the very first real answer (no messages yet)
        introduce = len(st.session_state.messages) == 0

        _router = route(
            question=prompt,
            has_kundali=st.session_state.chart_ready,
            has_pdf=st.session_state.pdf_context is not None,
            has_palm=(
                st.session_state.palm_left_str is not None
                or st.session_state.palm_right_str is not None
            ),
        )
        try:
            with st.spinner("Consulting the stars…"):
                result = ask(
                    question=prompt,
                    kundali_context=st.session_state.kundali_str or None,
                    pdf_context=st.session_state.pdf_context or None,
                    palm_left=st.session_state.get("palm_left_str"),
                    palm_right=st.session_state.get("palm_right_str"),
                    session=st.session_state.session_mgr,
                    introduce=introduce,
                    context_order=_router.get("context_order", ["rag", "kundali", "pdf"]),
                )

            if result["gated"]:
                st.session_state.pending_question = prompt
                st.warning(result["answer"])
            else:
                with st.chat_message("user"):
                    st.markdown(prompt)
                st.session_state.messages.append({"role": "user", "content": prompt})

                with st.chat_message("assistant"):
                    answer         = result["answer"]
                    low_confidence = result["low_confidence"]
                    sources        = result["sources"]
                    top_score      = sources[0]["score"] if sources else None

                    st.write_stream(_stream_answer(answer))

                    st.session_state.messages.append({
                        "role":           "assistant",
                        "content":        answer,
                        "low_confidence": low_confidence,
                        "top_score":      top_score,
                    })

                    # Persist session to disk; non-fatal on failure
                    try:
                        st.session_state.session_mgr.save()
                    except RuntimeError:
                        st.warning("Session could not be saved. Chat history may not persist.")

        except ValueError as e:
            st.error(f"Invalid input: {e}")
        except RuntimeError as e:
            st.error(f"Database error: {e}")
        except Exception as e:
            err = str(e).lower()
            if "api_key" in err or "authentication" in err:
                st.error("OpenAI API key missing or invalid — check your .env file.")
            else:
                st.error(f"{type(e).__name__}: {e}")
