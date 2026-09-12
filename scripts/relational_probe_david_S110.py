"""
scripts/relational_probe_david_S110.py

S110 -- first LIVE relational-rule probe on a THIRD real hand
(David_right.jpeg). READ-ONLY -- no production file is imported for
mutation, no source commit follows this run.

Measures whether L_026 (Head+Heart+Life triple-join) and any Fate-
crossing rule fire end-to-end on a REAL palm photograph for the first
time -- the whole S104-S109 relational arc is complete and committed,
but those rules have only ever fired on synthetic fixtures. The two
standing test images (palm_left_test.jpg/palm_right_test.jpg) lack a
clear heart-join or prominent Fate line; David_right is a candidate
third hand that might surface them.

Runs the FULL deterministic-rules pipeline (agent.interpretive.
palm_reading.prepare_palm_reading, REAL client, REAL retrieval) 3x on
the one image (David_right is a right hand -> palm_right, palm_left=
None), temp=0. For each run, captures:
  1. The complete raw vision text verbatim.
  2. Every parsed CONTACTS entry (feature/target/verb/position/clarity),
     via observation_extractor.extract_relations directly (no LLM).
  3. Each contact's resolution disposition + final token -- classified
     as exact-deterministic / S106-inflected / already_resolved (both
     via a "spy" wrapper around palm_reading._log_fallback_audits that
     captures the SAME audit records the real pipeline computes
     internally, so no second LLM-fallback call is ever made) / one of
     contact_llm_fallback's own LLM-consulted dispositions (resolved /
     llm_unclear / hallucination / position_unresolved / batch_*).
  4. The full fired rule-set for the run (prep.diagnostics["rules_engine"]
     ["fired_rule_ids"]).
  5. Fallback LLM call count for the run, DERIVED from the audit
     dispositions (resolve_unresolved_contacts makes at most ONE call
     per invocation; any audit disposition other than
     "already_resolved_no_llm_needed" implies that one call happened).

FAIL-CLOSED: a run that errors is recorded as such, never skipped
silently. Each pipeline call is wrapped in its own try/except; one
failed run must not abort the sweep.
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from openai import OpenAI  # noqa: E402

import agent.interpretive.palm_reading as palm_reading  # noqa: E402
from agent.interpretive import observation_extractor, palm_rules_table  # noqa: E402
from agent.interpretive.contact_mapper import (  # noqa: E402
    _DISTINCT_VERB_TABLE, _JOIN_FAMILY_VERBS, _INFLECTION_MAP,
)
from agent.palm_processor import describe_palm_image  # noqa: E402

IMAGE_PATH = _REPO_ROOT / "data" / "test_images" / "David_right.jpeg"
N_RUNS = 3

OUT_PATH = _REPO_ROOT / "diagnostics" / "relational_probe_david_S110_raw.json"

# ─── Spy wrapper: captures the SAME audit records prepare_palm_reading's
# internal _assemble_relational_targets_with_fallback call produces,
# without a second LLM-fallback call. Restored at script end. ────────────
_captured_audits: list[dict] = []
_real_log_fallback_audits = palm_reading._log_fallback_audits


def _spy_log_fallback_audits(audits):
    _captured_audits.extend(audits)
    return _real_log_fallback_audits(audits)


palm_reading._log_fallback_audits = _spy_log_fallback_audits

# REQUIRED: the deterministic rules engine (fired_rule_ids, the S107/S109
# CONTACTS->targets bridge) only runs when this flag is True -- without
# it, prepare_palm_reading takes the LLM Stage-1 claim_extraction path
# instead (a different, per-feature-call-count LLM path entirely). Set
# here, not just in an interactive shell, so a bare `python scripts/...`
# invocation is correct standalone.
palm_reading._DETERMINISTIC_RULES_ENABLED = True


def _classify_verb_source(raw_verb: str) -> str:
    """Classifies HOW a verb would resolve, independent of position --
    exact-deterministic (a literal declared table key) vs S106-inflected
    (a generated tense/aspect sibling) vs neither (would need the LLM
    fallback). Read-only classification against the live contact_mapper
    tables, mirrors the S105 sweep's own census method."""
    verb_norm = str(raw_verb).strip().lower()
    if verb_norm in _DISTINCT_VERB_TABLE or verb_norm in _JOIN_FAMILY_VERBS:
        return "exact_deterministic"
    if verb_norm in _INFLECTION_MAP:
        return "s106_inflected"
    return "needs_llm_fallback"


def _run_one(run_idx: int, cached_raw_text: str | None = None) -> dict:
    record: dict = {
        "run": run_idx, "error": None, "raw_text": None,
        "contacts": None, "per_contact_disposition": None,
        "fired_rule_ids": None, "fallback_call_count": None,
        "audits": None,
    }
    _captured_audits.clear()

    if cached_raw_text is not None:
        # RECOVERY MODE: reuses a raw vision text captured by an earlier,
        # buggy run of THIS SAME script (the deterministic-rules flag was
        # not set, so that run's downstream processing went down the
        # wrong path and its rules-engine data is unusable -- but its
        # vision call was genuine and its output is not being discarded).
        # Makes ZERO additional vision calls.
        raw_text = cached_raw_text
    else:
        image_bytes = IMAGE_PATH.read_bytes()
        try:
            raw_text = describe_palm_image(image_bytes, "right", temperature=0.0)
        except Exception as exc:  # noqa: BLE001 -- one failed call must not abort the sweep
            record["error"] = f"describe_palm_image failed: {type(exc).__name__}: {exc}"
            print(f"  [ERROR] run={run_idx}: {record['error']}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return record

    record["raw_text"] = raw_text

    try:
        rel = observation_extractor.extract_relations(raw_text)
        record["contacts"] = rel["contacts"]

        client = OpenAI()
        prep = palm_reading.prepare_palm_reading(palm_left=None, palm_right=raw_text, client=client)
        diag = prep.diagnostics["rules_engine"]
        record["fired_rule_ids"] = diag.get("fired_rule_ids")
    except Exception as exc:  # noqa: BLE001 -- one failed run must not abort the sweep
        record["error"] = f"pipeline failed: {type(exc).__name__}: {exc}"
        print(f"  [ERROR] run={run_idx}: {record['error']}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return record

    audits = list(_captured_audits)
    record["audits"] = audits
    non_already_resolved = [a for a in audits if a.get("disposition") != "already_resolved_no_llm_needed"]
    record["fallback_call_count"] = 1 if non_already_resolved else 0

    # POSITIONAL alignment, not a (verb,target,position)-keyed dict: audit
    # records carry no `feature` field (same limitation
    # _assemble_relational_targets_with_fallback's own docstring notes for
    # contacts), so two contacts sharing an identical (verb, target,
    # position) triple under different features would collide in a keyed
    # lookup. _assemble_relational_targets_with_fallback flattens
    # ("left", {}), ("right", rel["contacts"]) in that exact order, then
    # each feature's contact_list in dict-iteration order -- reproducing
    # that SAME flattening here and zipping positionally with the
    # captured audits (guaranteed same length/order per
    # resolve_unresolved_contacts' own contract) is exact, never
    # ambiguous.
    flat_contacts_with_feature: list[tuple[str, dict]] = []
    for feature, contact_list in (rel["contacts"] or {}).items():
        for c in contact_list:
            flat_contacts_with_feature.append((feature, c))

    if len(flat_contacts_with_feature) != len(audits):
        record["error"] = (
            f"positional alignment mismatch: {len(flat_contacts_with_feature)} "
            f"contacts vs {len(audits)} audits -- cannot safely attribute "
            "dispositions, reporting raw audits only."
        )
        print(f"  [ERROR] run={run_idx}: {record['error']}", file=sys.stderr)
        record["per_contact_disposition"] = None
        return record

    per_contact = []
    for (feature, c), audit in zip(flat_contacts_with_feature, audits):
        per_contact.append({
            "feature": feature,
            "target": c.get("target"),
            "raw_verb": c.get("verb"),
            "position": c.get("position"),
            "clarity": c.get("clarity"),
            "verb_source_class": _classify_verb_source(c.get("verb", "")),
            "disposition": audit.get("disposition"),
            "final_token": audit.get("final_token"),
            "llm_canonical_choice": audit.get("llm_canonical_choice"),
        })
    record["per_contact_disposition"] = per_contact

    print(
        f"  run={run_idx} -> OK ({len(per_contact)} contact(s), "
        f"fired={record['fired_rule_ids']}, fallback_calls={record['fallback_call_count']})"
    )
    return record


def main() -> None:
    t0 = time.time()

    cached_raw_texts: list[str | None] = [None] * N_RUNS
    if OUT_PATH.exists():
        try:
            prior = json.loads(OUT_PATH.read_text(encoding="utf-8"))
            for rec in prior:
                idx = rec.get("run")
                if isinstance(idx, int) and 0 <= idx < N_RUNS and rec.get("raw_text"):
                    cached_raw_texts[idx] = rec["raw_text"]
        except Exception as exc:  # noqa: BLE001 -- a bad prior dump must not block a fresh run
            print(f"  [WARN] could not read prior dump for cache reuse: {exc}", file=sys.stderr)

    all_records: list[dict] = []
    for run_idx in range(N_RUNS):
        print(f"Run {run_idx + 1}/{N_RUNS} ...")
        rec = _run_one(run_idx, cached_raw_text=cached_raw_texts[run_idx])
        all_records.append(rec)

    palm_reading._log_fallback_audits = _real_log_fallback_audits  # restore

    OUT_PATH.write_text(json.dumps(all_records, indent=2, default=str), encoding="utf-8")

    elapsed = time.time() - t0
    n_errors = sum(1 for r in all_records if r["error"] is not None)
    print(f"\nDone in {elapsed:.1f}s. {len(all_records)} run(s), {n_errors} error(s).")
    print(f"Raw dump written to: {OUT_PATH}")


if __name__ == "__main__":
    main()
