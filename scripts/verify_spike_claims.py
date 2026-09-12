"""
verify_spike_claims.py -- ONE-SHOT feasibility spike, THROWAWAY, not product code.

Mechanical verifier for diagnostics/spike_career_claims.json. Loads the claims
produced by Claude Code acting as the interpreter (Step A of the instructing
prompt) and checks each claim against data/chapter_index_bphs.json:
  (a) unit_id is one of the three supplied units
  (b) the quote appears VERBATIM (whitespace/case normalised only) in that
      unit's text
  (c) LOW-CONFIDENCE best-effort check: does the statement name a chart fact
      absent from the fact block?

ABSOLUTE RULE (per the instructing prompt): after running this verifier, the
claims file, the quotes, or this script's matching logic may NOT be edited to
improve the numbers. A failure is the result and must be reported as such.

Run:
    $env:PYTHONIOENCODING='utf-8'; python scripts/verify_spike_claims.py
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CLAIMS_PATH = REPO_ROOT / "diagnostics" / "spike_career_claims.json"
CHAPTER_INDEX_PATH = REPO_ROOT / "data" / "chapter_index_bphs.json"
FACT_BLOCK_PATH = REPO_ROOT / "diagnostics" / "_spike_fact_block.txt"
OUTPUT_PATH = REPO_ROOT / "diagnostics" / "_spike_verification_result.json"

TARGET_UNIT_IDS = {"bphs1_ch21", "bphs1_ch24", "bphs1_ch34"}


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def _closest_substring(quote_norm: str, haystack_norm: str) -> str:
    q_words = quote_norm.split()
    if not q_words:
        return "(empty quote)"
    h_words = haystack_norm.split()
    best_len = 0
    best_start = 0
    for i in range(len(h_words)):
        run = 0
        while i + run < len(h_words) and run < len(q_words) and h_words[i + run] == q_words[run]:
            run += 1
        if run > best_len:
            best_len = run
            best_start = i
    if best_len == 0:
        return " ".join(h_words[:15]) + " ..."
    lo = max(0, best_start - 5)
    hi = min(len(h_words), best_start + best_len + 5)
    return "..." + " ".join(h_words[lo:hi]) + "..."


def main() -> None:
    claims_doc = json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))
    claims = claims_doc.get("claims", [])

    index_doc = json.loads(CHAPTER_INDEX_PATH.read_text(encoding="utf-8"))
    units_by_id = {u["unit_id"]: u for u in index_doc["units"]}

    fact_block = FACT_BLOCK_PATH.read_text(encoding="utf-8")
    fact_block_norm = _normalize(fact_block)

    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    dignities = ["exalted", "debilitated", "own sign", "friendly", "inimical", "neutral"]
    house_words = [f"{n}th house" for n in range(1, 13)] + [
        "1st house", "2nd house", "3rd house", "10th house"
    ]

    results = []
    for idx, claim in enumerate(claims):
        row = {"index": idx, "claim": claim}

        unit_id = claim.get("unit_id")
        check_a = unit_id in TARGET_UNIT_IDS
        row["check_a_pass"] = check_a
        row["check_a_detail"] = (
            f"unit_id '{unit_id}' is one of the 3 supplied unit_ids"
            if check_a
            else f"unit_id '{unit_id}' is NOT one of the 3 supplied unit_ids {sorted(TARGET_UNIT_IDS)}"
        )

        quote = claim.get("quote", "") or ""
        quote_norm = _normalize(quote)
        if check_a and unit_id in units_by_id:
            source_text_norm = _normalize(units_by_id[unit_id]["text"])
            check_b = bool(quote_norm) and quote_norm in source_text_norm
        else:
            source_text_norm = ""
            check_b = False
        row["check_b_pass"] = check_b
        row["check_b_quote"] = quote
        if not check_b:
            row["check_b_closest_source_text"] = (
                _closest_substring(quote_norm, source_text_norm)
                if source_text_norm
                else "(source unit unavailable -- check (a) already failed)"
            )

        statement = claim.get("statement", "") or ""
        statement_norm = _normalize(statement)
        found_facts = []
        for token_list, label in (
            (signs, "sign"), (planets, "planet"), (dignities, "dignity"), (house_words, "house"),
        ):
            for token in token_list:
                token_norm = _normalize(token)
                if token_norm and re.search(rf"\b{re.escape(token_norm)}\b", statement_norm):
                    present = token_norm in fact_block_norm
                    found_facts.append({"type": label, "token": token, "present_in_fact_block": present})
        row["check_c_low_confidence_facts_found"] = found_facts
        row["check_c_any_fact_not_in_block"] = any(not f["present_in_fact_block"] for f in found_facts)

        results.append(row)

    total = len(results)
    passed_ab = sum(1 for r in results if r["check_a_pass"] and r["check_b_pass"])
    failed_ab = total - passed_ab
    c_flagged = sum(1 for r in results if r["check_c_any_fact_not_in_block"])

    print(f"Total claims: {total}, passed (a)+(b): {passed_ab}, failed: {failed_ab}, "
          f"(c)-flagged (informational): {c_flagged}")
    for r in results:
        print(
            f"  claim {r['index']}: unit_id={r['claim'].get('unit_id')} "
            f"a={'PASS' if r['check_a_pass'] else 'FAIL'} "
            f"b={'PASS' if r['check_b_pass'] else 'FAIL'}"
        )

    OUTPUT_PATH.write_text(
        json.dumps({"results": results, "total": total, "passed_ab": passed_ab,
                     "failed_ab": failed_ab, "c_flagged": c_flagged}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nWrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
