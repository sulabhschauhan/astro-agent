"""
frontend/app.py
Streamlit UI — Vedic astrology assistant (Parashara RAG agent).
"""

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
if "palm_str" not in st.session_state:
    _palm_path = _ROOT / "data" / "default_user" / "palm_description.txt"
    try:
        st.session_state.palm_str = _palm_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        st.session_state.palm_str = None
if "pdf_context" not in st.session_state:
    st.session_state.pdf_context = None
if "_astrosage_pdf_name" not in st.session_state:
    st.session_state["_astrosage_pdf_name"] = None
if "palm_bytes" not in st.session_state:
    st.session_state.palm_bytes = None
if "_palm_image_name" not in st.session_state:
    st.session_state["_palm_image_name"] = None
if "place_error" not in st.session_state:
    st.session_state.place_error = None
if "selected_place" not in st.session_state:
    st.session_state.selected_place = None
if "place_candidates" not in st.session_state:
    st.session_state.place_candidates = []

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
        tob_input = st.time_input("Time of Birth (IST)", value=datetime.time(0, 30, 0))
        tob = tob_input.strftime("%H:%M") if tob_input else None
        submitted = st.form_submit_button(
            "Calculate Kundali",
            disabled=st.session_state.selected_place is None,
        )

    if submitted:
        if tob is None:
            st.sidebar.warning("Please select time of birth.")
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

    uploaded_pdf = st.file_uploader("AstroSage PDF (optional)", type=["pdf"])
    if uploaded_pdf is not None:
        if st.session_state["_astrosage_pdf_name"] != uploaded_pdf.name:
            with st.spinner("Parsing AstroSage PDF…"):
                result = parse_astrosage_pdf(uploaded_pdf.read())
            if result:
                st.session_state.pdf_context = result
                st.session_state["_astrosage_pdf_name"] = uploaded_pdf.name
                st.success("AstroSage data loaded.")
            else:
                st.session_state.pdf_context = None
                st.warning("Could not extract sections — check this is an AstroSage PDF.")
    elif st.session_state["_astrosage_pdf_name"] is not None:
        st.session_state.pdf_context = None
        st.session_state["_astrosage_pdf_name"] = None

    uploaded_palm = st.file_uploader("Palm Image (optional)", type=["jpg", "jpeg", "png"])
    if uploaded_palm is not None:
        if st.session_state["_palm_image_name"] != uploaded_palm.name:
            st.session_state.palm_bytes = uploaded_palm.read()
            st.session_state["_palm_image_name"] = uploaded_palm.name
            st.success("Palm image loaded.")
    elif st.session_state["_palm_image_name"] is not None:
        st.session_state.palm_bytes = None
        st.session_state["_palm_image_name"] = None

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
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            try:
                # introduce=True only on the very first turn (just the user message is in list)
                introduce = len(st.session_state.messages) == 1

                _router = route(
                    question=prompt,
                    has_kundali=st.session_state.chart_ready,
                    has_pdf=st.session_state.pdf_context is not None,
                    has_palm=st.session_state.palm_str is not None,
                )
                with st.spinner("Consulting the stars…"):
                    result = ask(
                        question=prompt,
                        kundali_context=st.session_state.kundali_str or None,
                        pdf_context=st.session_state.pdf_context or None,
                        palm_description=st.session_state.palm_str or None,
                        session=st.session_state.session_mgr,
                        introduce=introduce,
                    )

                answer         = result["answer"]
                low_confidence = result["low_confidence"]
                sources        = result["sources"]
                top_score      = sources[0]["score"] if sources else None

                st.write_stream(_stream_answer(answer))

                if _router["nudge"]:
                    st.info(_router["nudge"])

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
