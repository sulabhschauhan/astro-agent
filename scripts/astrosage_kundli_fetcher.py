"""
scripts/astrosage_kundli_fetcher.py

Standalone backup/reference-data utility -- fetches a Kundli PDF from
astrosage.com's free, no-login Kundli tool given name/DOB/time/place/sex.

This is a SIDE UTILITY, not part of the core answer pipeline: it is not
imported by anything in agent/, calculations/, or query_engine, and must
stay that way. It exists only as a manual backup/reference-data fetcher,
used the same way AstroSage PDFs are already used today per CLAUDE.md's
Reference Materials section ("AstroSage PDFs (4 reference charts) for
secondary parity") -- the project's locked direction is to retire the
AstroSage dependency via in-house calculation modules (vimshottari,
chart_d1), not to build on it further.

Real form structure verified 2026-09-12 by opening https://www.astrosage.com/kundli/
in a non-headless browser and reading the live DOM (not guessed):
  - Name:        input#Name, name="name", type=text
  - Sex:         input#male / input#female, name="sex", type=radio -- a
    hidden-input/styled-label toggle: both inputs collapse to the same
    1x1px hitbox under the "Male" label, so the associated <label> must be
    clicked, never the <input> itself (checking #female directly hits the
    "Male" label and times out -- verified 2026-09-12).
  - Day/Month/Year: input#Day / #Month / #Year, type=number
  - Hrs/Min/Sec:    input#Hrs / #Min / #Sec, type=number
  - Place of birth: input#place, name="place", class "ac_input" -- a
    jQuery-autocomplete widget. Free text alone is NOT enough: hidden
    fields (#LongDeg/#LongMin/#LatDeg/#LatMin/#timeZone) stay EMPTY until
    an actual suggestion from the dropdown (div.ac_results li) is clicked;
    only after clicking a suggestion do they populate (verified: typing
    "New Delhi" and clicking the single suggestion populated
    LongDeg=77 LongMin=13 LatDeg=28 LatMin=38 timeZone=5.5). A submission
    without selecting a suggestion would silently use no/blank location. A
    fully-qualified "City, Region/Country" string frequently fails to match
    at all (verified live: "New Delhi, India" and "Kolkata, Kolkata
    Metropolitan Area" both failed) -- fetch_kundli_pdf() retries once with
    just the text before the first comma before giving up.
    The dropdown itself is backed by GET
    https://www.astrosage.com/kundli/FindPlaces.asp?q=<query> -- a plain
    HTTP endpoint verified live 2026-09-13, needing only a Referer and
    X-Requested-With header (no cookies/session), returning one
    pipe-delimited candidate per line: city|region|country|latdeg|latmin
    |N/S|londeg|lonmin|E/W|tzoffset|tzid. Its order and text are
    byte-identical to the on-site .ac_results list (verified: "Kolk" ->
    both produced "Kolkata, Bengal (India)" first, "Kolkerheide,
    Schleswig-Holstein (Germany)" second, etc., in the same order).
    get_place_suggestions() below wraps this endpoint so a caller (e.g. a
    Streamlit picker) can show the user the REAL candidate list and let
    them disambiguate (e.g. "Paris, France" vs "Paris, Texas (USA)")
    BEFORE calling fetch_kundli_pdf, instead of trusting that whichever
    suggestion the site lists first is the one meant -- pass the chosen
    candidate's "display" string back in as fetch_kundli_pdf's
    place_selection to make it click that EXACT list item.
  - Submit: button#submit (value "Show Kundli") -- navigates to
    https://ascloud.astrosage.com/cloud/home.asp (the chart dashboard).
  - Detailed PDF: on the chart dashboard, a visible link inside the
    "Calculations: If you know Astrology" panel, text "Print Detailed
    Kundali & Reports - PDF", href="https://ascloud.astrosage.com/cloud/vedic-chart-pdf.asp"
    (no ?page= param -- the paged variants are OTHER, narrower reports).
    Clicking it fires a real Playwright download event (verified: saved a
    valid 840KB single PDF, magic bytes b"%PDF-1.4") from
    pdf.astrosage.com/HindiPdfNew.aspx?... -- i.e. this is a real
    session-backed download, not a static file, so it is fetched via
    Playwright's download API rather than a raw requests.get.
  - No login wall or captcha was encountered on this flow as of
    2026-09-12; _detect_block() below still checks narrowly and fails
    loudly rather than assuming that stays true forever.

Politeness: this hits a public, no-login page for personal/reference use
only. One browser, one request at a time -- do not parallelize or loop
this script. Small delays are inserted between filling the form, and
between the chart page loading and the PDF click.
"""
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

KUNDLI_URL = "https://www.astrosage.com/kundli/"
FIND_PLACES_URL = "https://www.astrosage.com/kundli/FindPlaces.asp"

_SEL_NAME = "#Name"
# The male/female radios (input#male / input#female) are a hidden-input,
# styled-label toggle: both inputs collapse to an identical 1x1px hitbox
# sitting under the "Male" label, so clicking/checking the #female input
# directly always hits the "Male" label instead (verified 2026-09-12 --
# Playwright's actionability check reported "label[for=male] intercepts
# pointer events" when checking #female). Click the associated <label>,
# never the underlying <input>.
_SEL_SEX = {"male": "label[for='male']", "female": "label[for='female']"}
_SEL_DAY = "#Day"
_SEL_MONTH = "#Month"
_SEL_YEAR = "#Year"
_SEL_HRS = "#Hrs"
_SEL_MIN = "#Min"
_SEL_SEC = "#Sec"
_SEL_PLACE = "#place"
_SEL_AUTOCOMPLETE_RESULTS = ".ac_results li"
_SEL_SUBMIT = "#submit"
_SEL_PDF_LINK = "a[href$='vedic-chart-pdf.asp']"


class KundliFetchError(Exception):
    """Raised with a 'blocked_by_<reason>' message when the flow cannot proceed.

    Never raised for a captcha/challenge that this script attempted to
    solve or bypass -- only for one that was detected and honestly reported.
    """


def get_place_suggestions(query: str, timeout: float = 5.0) -> list[dict]:
    """
    Return the exact place candidates AstroSage's own autocomplete would
    show for `query`, by calling its FindPlaces.asp endpoint directly (see
    module docstring) -- a lightweight HTTP call, no browser needed.

    Each item: {"city", "region", "country", "display", "timezone_id"}.
    "display" is byte-identical to the on-site suggestion list's text
    (e.g. "Kolkata, Bengal (India)") -- pass it back as fetch_kundli_pdf's
    `place_selection` to make it click that specific candidate rather than
    just the first one, when a query has multiple ambiguous matches (e.g.
    "Paris" -> France vs Texas).

    Fails soft: returns [] on no matches or any network error, since this
    is meant to drive live UI typing and must never raise into a caller
    mid-keystroke.
    """
    try:
        resp = requests.get(
            FIND_PLACES_URL,
            params={"q": query},
            headers={
                "Referer": KUNDLI_URL,
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0",
            },
            timeout=timeout,
        )
        resp.raise_for_status()
    except requests.RequestException:
        return []

    text = resp.text.strip()
    if not text or "not authorized" in text.lower():
        return []

    suggestions = []
    for line in text.splitlines():
        parts = line.split("|")
        if len(parts) < 11:
            continue
        city, region, country = parts[0], parts[1], parts[2]
        suggestions.append({
            "city": city,
            "region": region,
            "country": country,
            "display": f"{city}, {region} ({country})",
            "timezone_id": parts[10],
        })
    return suggestions


def _detect_block(page) -> None:
    """Raise KundliFetchError if a captcha / Cloudflare challenge / login wall
    is present. Narrow, explicit checks only; never tries to defeat anything."""
    title = (page.title() or "").lower()
    if "just a moment" in title or "attention required" in title:
        raise KundliFetchError("blocked_by_cloudflare_challenge")

    if page.locator(
        "iframe[src*='recaptcha'], iframe[src*='hcaptcha'], .g-recaptcha, #cf-challenge-stage"
    ).count() > 0:
        raise KundliFetchError("blocked_by_captcha")

    if page.locator("text=/sign in to continue|please log in|login required/i").count() > 0:
        raise KundliFetchError("blocked_by_login_wall")


def fetch_kundli_pdf(
    name: str,
    birth_date: str,
    birth_time: str,
    birth_place: str,
    sex: str,
    output_dir: str,
    headless: bool = True,
    place_selection: str | None = None,
) -> str:
    """
    Fetch a Kundli PDF from astrosage.com's free, no-login Kundli tool.

    Args:
        name: person's name (used only for the report + output filename)
        birth_date: "YYYY-MM-DD"
        birth_time: "HH:MM" (24-hour)
        birth_place: free-text place name (e.g. "New Delhi, India") typed
            into the site's own place field to produce its autocomplete
            list. Without `place_selection`, the FIRST suggestion is
            selected -- fine for an unambiguous place, but risky for one
            with multiple real candidates (e.g. "Paris" -> France vs
            Texas). AstroSage requires selecting a suggestion; free text
            alone leaves the hidden lat/long/timezone fields blank (see
            module docstring).
        sex: "male" or "female" -- the form only offers this binary choice
            (radio input#male / input#female); passed through as-is so the
            generated report/kundli reflects the actual input.
        output_dir: directory to save the PDF into (created if missing)
        headless: run Chromium headless (default True). Set False to watch
            the flow interactively while debugging.
        place_selection: optional exact suggestion text (e.g. "Kolkata,
            Bengal (India)", from get_place_suggestions()'s "display"
            field) to click that SPECIFIC candidate instead of the first
            one. Raises if no current suggestion matches it exactly --
            never silently falls back to "first" once this is given.

    Returns:
        Path to the saved PDF file, named "<name>_<YYYYMMDD>_<HHMM>.pdf".

    Raises:
        ValueError: sex is not "male" or "female".
        KundliFetchError: message starts with "blocked_by_" -- a captcha,
            Cloudflare challenge, or login wall was detected; the place
            autocomplete produced no suggestion; `place_selection` was
            given but matched none of the current suggestions; the
            detailed-PDF link never appeared; or the click never produced
            a download.
    """
    sex_key = sex.strip().lower()
    if sex_key not in _SEL_SEX:
        raise ValueError(f"sex must be 'male' or 'female', got {sex!r}")

    dob = datetime.strptime(birth_date, "%Y-%m-%d")
    tob = datetime.strptime(birth_time, "%H:%M")

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        try:
            page.goto(KUNDLI_URL, wait_until="domcontentloaded", timeout=30000)
            _detect_block(page)

            page.fill(_SEL_NAME, name)
            page.click(_SEL_SEX[sex_key])
            page.fill(_SEL_DAY, str(dob.day))
            page.fill(_SEL_MONTH, str(dob.month))
            page.fill(_SEL_YEAR, str(dob.year))
            page.fill(_SEL_HRS, str(tob.hour))
            page.fill(_SEL_MIN, str(tob.minute))
            page.fill(_SEL_SEC, "0")

            page.click(_SEL_PLACE)
            page.type(_SEL_PLACE, birth_place, delay=100)

            try:
                page.wait_for_selector(_SEL_AUTOCOMPLETE_RESULTS, timeout=8000)
            except PlaywrightTimeoutError:
                # AstroSage's own place database frequently doesn't match a
                # fully-qualified "City, Region/Country" string -- verified
                # live twice: "New Delhi, India" and a geocoder's "Kolkata,
                # Kolkata Metropolitan Area" both failed to produce a
                # suggestion, while the bare city name matched both times.
                # Retry once with just the text before the first comma.
                _fallback_place = birth_place.split(",")[0].strip()
                if _fallback_place and _fallback_place != birth_place:
                    page.fill(_SEL_PLACE, "")
                    page.click(_SEL_PLACE)
                    page.type(_SEL_PLACE, _fallback_place, delay=100)
                    try:
                        page.wait_for_selector(_SEL_AUTOCOMPLETE_RESULTS, timeout=8000)
                    except PlaywrightTimeoutError:
                        raise KundliFetchError(
                            "blocked_by_place_not_found: no autocomplete suggestion for "
                            f"'{birth_place}' or fallback '{_fallback_place}'"
                        )
                else:
                    raise KundliFetchError(
                        f"blocked_by_place_not_found: no autocomplete suggestion for '{birth_place}'"
                    )

            if place_selection:
                # Click the SPECIFIC candidate the caller disambiguated
                # to (e.g. via get_place_suggestions()), never just the
                # first suggestion -- exact text match, since ambiguous
                # queries ("Paris") return multiple real candidates whose
                # order alone isn't a safe substitute for the caller's
                # actual choice.
                _suggestion_items = page.locator(_SEL_AUTOCOMPLETE_RESULTS)
                _matched_index = None
                for _i in range(_suggestion_items.count()):
                    if _suggestion_items.nth(_i).inner_text().strip() == place_selection.strip():
                        _matched_index = _i
                        break
                if _matched_index is None:
                    _seen = [
                        _suggestion_items.nth(_i).inner_text().strip()
                        for _i in range(_suggestion_items.count())
                    ]
                    raise KundliFetchError(
                        f"blocked_by_place_selection_mismatch: '{place_selection}' not "
                        f"among current suggestions {_seen}"
                    )
                _suggestion_items.nth(_matched_index).click()
            else:
                page.click(_SEL_AUTOCOMPLETE_RESULTS)
            time.sleep(2)  # polite pause between form-fill and submit

            page.click(_SEL_SUBMIT)
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            time.sleep(2)
            _detect_block(page)

            try:
                pdf_link = page.locator(_SEL_PDF_LINK).first
                pdf_link.wait_for(state="visible", timeout=15000)
            except PlaywrightTimeoutError:
                raise KundliFetchError(
                    "blocked_by_missing_pdf_link: chart page loaded but the detailed-PDF link never appeared"
                )

            time.sleep(2)  # polite pause before hitting the PDF endpoint

            try:
                with page.expect_download(timeout=20000) as dl_info:
                    pdf_link.click()
                download = dl_info.value
            except PlaywrightTimeoutError:
                raise KundliFetchError(
                    "blocked_by_no_download_event: PDF link clicked but no download fired"
                )

            safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", name.strip()) or "kundli"
            filename = f"{safe_name}_{dob.strftime('%Y%m%d')}_{tob.strftime('%H%M')}.pdf"
            save_path = out_path / filename
            download.save_as(str(save_path))

            return str(save_path)
        finally:
            browser.close()


def _main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch a Kundli PDF from astrosage.com's free, no-login tool."
    )
    parser.add_argument("--name", default="Test Placeholder")
    parser.add_argument("--birth-date", default="1990-06-15", help="YYYY-MM-DD")
    parser.add_argument("--birth-time", default="10:30", help="HH:MM, 24hr")
    parser.add_argument("--birth-place", default="New Delhi")
    parser.add_argument("--sex", default="male", choices=["male", "female"])
    parser.add_argument("--output-dir", default="diagnostics/kundli_fetch_test")
    parser.add_argument(
        "--place-selection", default=None,
        help="Exact suggestion text (get_place_suggestions()'s 'display' field) to "
             "disambiguate which candidate to click, e.g. 'Kolkata, Bengal (India)'.",
    )
    args = parser.parse_args()

    # No-args run is the placeholder demo (not real personal data); real
    # calls (e.g. frontend/app.py's subprocess invocation, see that file's
    # "Fetch Kundli Online" handler) pass every flag explicitly.
    try:
        saved = fetch_kundli_pdf(
            name=args.name,
            birth_date=args.birth_date,
            birth_time=args.birth_time,
            birth_place=args.birth_place,
            sex=args.sex,
            output_dir=args.output_dir,
            place_selection=args.place_selection,
        )
        print(f"SUCCESS: saved to {saved}")
    except KundliFetchError as e:
        print(f"BLOCKED: {e}")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {type(e).__name__}: {e}")


if __name__ == "__main__":
    _main()
