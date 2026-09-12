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
    without selecting a suggestion would silently use no/blank location.
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

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

KUNDLI_URL = "https://www.astrosage.com/kundli/"

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
) -> str:
    """
    Fetch a Kundli PDF from astrosage.com's free, no-login Kundli tool.

    Args:
        name: person's name (used only for the report + output filename)
        birth_date: "YYYY-MM-DD"
        birth_time: "HH:MM" (24-hour)
        birth_place: free-text place name (e.g. "New Delhi, India"). The
            FIRST autocomplete suggestion is selected -- AstroSage requires
            selecting a suggestion; free text alone leaves the hidden
            lat/long/timezone fields blank (see module docstring).
        sex: "male" or "female" -- the form only offers this binary choice
            (radio input#male / input#female); passed through as-is so the
            generated report/kundli reflects the actual input.
        output_dir: directory to save the PDF into (created if missing)
        headless: run Chromium headless (default True). Set False to watch
            the flow interactively while debugging.

    Returns:
        Path to the saved PDF file, named "<name>_<YYYYMMDD>_<HHMM>.pdf".

    Raises:
        ValueError: sex is not "male" or "female".
        KundliFetchError: message starts with "blocked_by_" -- a captcha,
            Cloudflare challenge, or login wall was detected; the place
            autocomplete produced no suggestion; the detailed-PDF link
            never appeared; or the click never produced a download.
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
                raise KundliFetchError(
                    f"blocked_by_place_not_found: no autocomplete suggestion for '{birth_place}'"
                )

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


if __name__ == "__main__":
    # Placeholder test case -- not real personal data.
    try:
        saved = fetch_kundli_pdf(
            name="Test Placeholder",
            birth_date="1990-06-15",
            birth_time="10:30",
            birth_place="New Delhi",
            sex="male",
            output_dir="diagnostics/kundli_fetch_test",
        )
        print(f"SUCCESS: saved to {saved}")
    except KundliFetchError as e:
        print(f"BLOCKED: {e}")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {type(e).__name__}: {e}")
