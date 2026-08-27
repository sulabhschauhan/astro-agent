"""
agent/palm_processor.py
Validates a palm image via GPT-4o vision before it enters the reading pipeline.
"""

import base64
import hashlib
import json
import logging
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a palm image validator. Analyse the image and report objective "
    "observations only — do not identify which hand (left or right) this is.\n"
    "Return ONLY valid JSON, no markdown:\n"
    "{\n"
    "  \"quality\": \"good|poor_readable|unusable\",\n"
    "  \"issues\": [\"blurry\",\"partial\",\"dark\",\"not_a_hand\"],\n"
    "  \"palm_facing\": \"camera|away|unclear\",\n"
    "  \"finger_direction\": \"up|down|sideways|unclear\"\n"
    "}\n"
    "issues is an empty list if none."
)

_VALID_PALM_FACING      = frozenset({"camera", "away", "unclear"})
_VALID_FINGER_DIRECTION = frozenset({"up", "down", "sideways", "unclear"})

# Soft, non-blocking capture guidance (never "wrong"/error framing).
_GEOMETRY_ORIENTATION_TIP = "Tip: for best results, hold your palm facing the camera with fingers pointing up."
_GEOMETRY_ISSUE_TIPS: dict[str, str] = {
    "blurry": "Tip: the image looks a bit blurry — a sharper, in-focus photo will give a more accurate reading.",
    "dark":   "Tip: the image looks a bit dark — better lighting will give a more accurate reading.",
}


def validate_palm_image(image_bytes: bytes, slot: str) -> dict:
    """
    Validate a palm image using GPT-4o vision.

    Args:
        image_bytes: Raw bytes of the uploaded image.
        slot: "left" or "right" — identifies which uploader the image came from.
              Used for logging only; not compared against a detected hand.

    Returns:
        {
            "hash":           str,        # MD5 hex digest of image_bytes
            "quality":        str,        # "good" | "poor_readable" | "unusable" | "unknown"
            "issues":         list[str],  # subset of blurry/partial/dark/not_a_hand
            "hard_reject":    bool,       # True → do not use image for reading
            "warn":           bool,       # True → usable but warn the user
            "warn_message":   str|None,   # set when warn=True
            "reject_message": str|None,   # set when hard_reject=True
            "geometry_tips":  list[str],  # soft, non-blocking capture guidance (never errors)
        }
    """
    image_hash = hashlib.md5(image_bytes).hexdigest()

    mime = "image/png" if image_bytes[:8].startswith(b"\x89PNG") else "image/jpeg"
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    client = OpenAI()
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyse this palm image.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                },
            ],
            max_tokens=200,
            temperature=0,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
    except Exception:
        logger.exception("palm_processor: GPT-4o call failed for slot=%s hash=%s", slot, image_hash)
        return {
            "hash":           image_hash,
            "quality":        "unknown",
            "issues":         [],
            "hard_reject":    False,
            "warn":           True,
            "warn_message":   "Could not validate image — proceeding with caution.",
            "reject_message": None,
            "geometry_tips":  [],
        }

    try:
        parsed           = json.loads(raw)
        quality          = parsed.get("quality", "unknown")
        issues           = parsed.get("issues", [])
        palm_facing      = parsed.get("palm_facing", "unclear")
        finger_direction = parsed.get("finger_direction", "unclear")
        if palm_facing not in _VALID_PALM_FACING:
            palm_facing = "unclear"
        if finger_direction not in _VALID_FINGER_DIRECTION:
            finger_direction = "unclear"
    except (json.JSONDecodeError, ValueError):
        logger.debug("palm_processor: raw GPT response for slot=%s: %r", slot, raw)
        logger.warning("palm_processor: JSON parse failed for slot=%s. raw=%r", slot, raw)
        return {
            "hash":           image_hash,
            "quality":        "unknown",
            "issues":         [],
            "hard_reject":    False,
            "warn":           True,
            "warn_message":   "Could not validate image — proceeding with caution.",
            "reject_message": None,
            "geometry_tips":  [],
        }

    hard_reject    = False
    warn           = False
    warn_message   = None
    reject_message = None

    if "not_a_hand" in issues:
        hard_reject    = True
        reject_message = "This does not appear to be a palm image — please upload a photo of your hand."
    elif quality == "unusable":
        hard_reject    = True
        reject_message = "Image quality is too poor to use — please upload a well-lit, in-focus photo."
    elif quality == "poor_readable":
        warn         = True
        warn_message = "Image quality is reduced — the reading may be less accurate."

    # ── Soft, non-blocking capture guidance (never overrides hard_reject) ──────
    geometry_tips: list[str] = []
    for issue in ("blurry", "dark"):
        if issue in issues:
            geometry_tips.append(_GEOMETRY_ISSUE_TIPS[issue])

    if palm_facing != "camera" or finger_direction != "up":
        geometry_tips.append(_GEOMETRY_ORIENTATION_TIP)

    return {
        "hash":           image_hash,
        "quality":        quality,
        "issues":         issues,
        "hard_reject":    hard_reject,
        "warn":           warn,
        "warn_message":   warn_message,
        "reject_message": reject_message,
        "geometry_tips":  geometry_tips,
    }


_ONTOLOGY_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "ontology_registry.json"
_ONTOLOGY_REGISTRY: dict = json.loads(_ONTOLOGY_REGISTRY_PATH.read_text(encoding="utf-8"))
_VISION_RELATIONAL_MENUS: dict[str, dict[str, list[str]]] = _ONTOLOGY_REGISTRY["vision_relational_menus"]
# The ONE place the convergence-participating line set is declared (Generic
# convergence emission step, S98) -- CONVERGENCE menus are DERIVED from this,
# never hand-listed per line; adding a line here auto-participates with zero
# further vision-prompt edits.
_CONVERGENCE_LINES: list[str] = list(_ONTOLOGY_REGISTRY["convergence_lines"])

# Typed-relationship closed vocabulary (typed-relationship arc Step 2, S99) --
# the 8 tokens added to ontology_registry.json's "relation_types" block at
# Step 1. Asserted present here, fail-closed: a partial vocab must never
# silently degrade the vision prompt (Working Style #22, vocabulary contract).
_TYPED_RELATION_TOKENS: tuple[str, ...] = (
    "joins_at_origin", "meets", "cuts", "cut_by", "touches",
    "stopped_by", "takes_possession_of", "branch_in",
)
_missing_typed_relations = [
    tok for tok in _TYPED_RELATION_TOKENS
    if tok not in _ONTOLOGY_REGISTRY["relation_types"]
]
if _missing_typed_relations:
    raise RuntimeError(
        "palm_processor: typed-relationship vocabulary incomplete in "
        f"ontology_registry.json's 'relation_types' block -- missing "
        f"{_missing_typed_relations}. Refusing to build a vision prompt "
        "against a partial typed-relationship vocabulary (S99 Step 2 "
        "fail-closed contract)."
    )

# Registry-derived mount landmark menu for RELATIONSHIP's optional "at
# <mount>" clause -- filtered from relation_target_registry (the same SSOT
# CONVERGENCE/ORIGIN/TERMINATION already draw from), never hand-listed.
_MOUNT_TARGETS: list[str] = [
    t for t in _ONTOLOGY_REGISTRY["relation_target_registry"] if "Mount" in t
]


def _menu(feature: str, field: str) -> str:
    """Formats a per-line vision-prompt token menu as the "{tok1 | tok2 | ...}"
    brace-and-pipe shape describe_palm_image's prompt uses (Generalization
    step 3, S98). CONVERGENCE is DERIVED, not looked up (Generic convergence
    emission step, S98): convergence_lines minus `feature` itself -- so any
    line may converge against every OTHER participating line, multi-select,
    with no per-pair hardcoding. Every other field (ORIGIN/TERMINATION/
    CONVERGENCE_LOCATION) still reads ontology_registry.json's
    vision_relational_menus[feature][field] directly -- registry is the sole
    source of the token list either way."""
    if field == "CONVERGENCE":
        return "{" + " | ".join(line for line in _CONVERGENCE_LINES if line != feature) + "}"
    return "{" + " | ".join(_VISION_RELATIONAL_MENUS[feature][field]) + "}"


def _relationship_type_menu() -> str:
    """Closed {type1 | type2 | ...} menu of the 8 typed-relationship tokens
    (S99 Step 2) -- identical for every line, since the type vocabulary is
    global, not per-line."""
    return "{" + " | ".join(_TYPED_RELATION_TOKENS) + "}"


def _relationship_target_menu(feature: str) -> str:
    """RELATIONSHIP <target> menu (S99 Step 2): every OTHER convergence-
    participating line, DERIVED by the exact same mechanism as CONVERGENCE's
    menu (convergence_lines minus `feature`, S98) -- plus every registry-
    derived mount landmark (_MOUNT_TARGETS). Union, never hand-listed per
    feature or per pair."""
    lines = [line for line in _CONVERGENCE_LINES if line != feature]
    return "{" + " | ".join(lines + _MOUNT_TARGETS) + "}"


def _mount_menu() -> str:
    """Closed {mount1 | mount2 | ...} menu for RELATIONSHIP's optional "at
    <mount>" clause -- same _MOUNT_TARGETS SSOT as _relationship_target_menu,
    never a separately hand-listed mount list."""
    return "{" + " | ".join(_MOUNT_TARGETS) + "}"


def _relationship_field(feature: str) -> str:
    """Builds the RELATIONSHIP field block text for `feature` (S99 Step 2).
    Additive alongside the existing CONVERGENCE field on every line that
    carries one -- Step 5 migrates CONVERGENCE onto this typed channel; until
    then a real crossing may legitimately be reported on both fields at
    once (double-reporting is expected and fine this step)."""
    return (
        "  RELATIONSHIP: for each other line or mount this line clearly "
        "interacts with, write a separate \"RELATIONSHIP: <type> <target> "
        "[at <mount>]\" line. <type> is exactly one of "
        f"{_relationship_type_menu()}. <target> is exactly one of "
        f"{_relationship_target_menu(feature)}. Append \"at <mount>\" ONLY "
        "for cuts/cut_by/meets where the crossing mount is legible (choose "
        f"from {_mount_menu()}); omit it otherwise. If none clearly "
        "visible, write \"RELATIONSHIP: none\".\n"
    )


def _contacts_field(feature: str) -> str:
    """Builds the free-verb CONTACTS field block text for `feature` (S104
    Step 2). Purely additive alongside the existing RELATIONSHIP field --
    nothing consumes CONTACTS yet (Step 3 wires the extractor); RELATIONSHIP
    stays byte-identical so the live typed-relationship rules keep firing on
    the old path. Wording is the validated position-optional, contact-first
    form from the S103 recall-recovery probe (recall recovered to 3/3,
    position 6/6 real, zero fabrication)."""
    return (
        "  CONTACTS: list EVERY other line or mount this line clearly and "
        "visibly interacts with -- report the contact FIRST, do not withhold "
        "a contact because you are unsure where it happens. For each write a "
        "separate \"CONTACTS: <target> | <your own short word for how they "
        "interact> | <position> | <faint|clear>\" line. <target> is exactly "
        f"one of {_relationship_target_menu(feature)}. <position> is one of "
        "'at start' / 'mid-course' / 'at end' per this line's DIRECTION LAW, "
        "or 'unknown' if you cannot tell confidently -- never drop a contact "
        "just because position is unknown. Use your own natural word for the "
        "interaction; do NOT restrict it to a fixed list. If this line itself "
        "is faint / not clearly visible, write \"CONTACTS: none\".\n"
    )


def _build_description_system_prompt(hand: str) -> str:
    """Builds describe_palm_image's system-message prompt text. Extracted out
    of the inline API-call literal (Generalization step 3, S98) into this pure,
    no-side-effect function purely so the registry-sourced menu substitution
    could be proven byte-identical against the pre-refactor literal for both
    hand values; the returned text is otherwise unchanged."""
    return (
        f"You are a trained observer preparing hand notes for a "
        f"Cheiro-tradition palmist. You are NOT the palmist: record only "
        f"what is physically visible in this {hand} hand image. No "
        "meanings, no character traits, no predictions — never write "
        "'indicating', 'suggesting', or any interpretation. Output "
        "EXACTLY these labeled lines, in this order:\n"
        "HAND SHAPE: palm proportions (square vs elongated), overall build\n"
        "FINGERS: length relative to palm, straightness, fingertip shape, spacing\n"
        "THUMB: relative size, how low or high it is set, angle from the palm\n"
        "LIFE LINE: presence, depth, width (narrow/thin vs broad/thick), length, "
        "course, origin and end, breaks/\n"
        "chains/forks/islands if visible\n"
        f"  CONVERGENCE: for each other line this one clearly crosses or joins, write "
        f"a separate \"CONVERGENCE: <line>\" line choosing only from {_menu('Line of Life', 'CONVERGENCE')} "
        "-- repeat this line once per additional crossing; if none clearly visible, "
        "write \"CONVERGENCE: none\"\n"
        "For HEAD, HEART, and FATE lines, after SLOPE also give ORIGIN, TERMINATION, "
        "PROXIMITY, BRANCHES_TO, RELATIONSHIP as separate indented lines. ORIGIN/TERMINATION: pick "
        "ONLY from that line's listed menu, else 'none'. HEART LINE DIRECTION LAW: the "
        "finger/mount end is ORIGIN and the percussion is TERMINATION (even though common "
        "convention calls the percussion the start). FATE LINE DIRECTION LAW: the "
        "wrist/lower-palm end is ORIGIN and the finger/mount end (toward Saturn) is "
        "TERMINATION (even if the line appears to start from the top). HEAD LINE "
        "DIRECTION LAW: the thumb-side edge near the Life line's start is ORIGIN and "
        "the percussion/Mount of Luna end is TERMINATION. PROXIMITY/BRANCHES_TO landmark names: "
        "Line of Life/Head/Heart/Fate/Sun; Mount of Jupiter/Saturn/the Sun/Mercury/Venus/"
        "Luna; Upper Mount of Mars; Lower Mount of Mars; Junction of First and Second "
        "Fingers; Wrist; Percussion. PROXIMITY format: \"<touching|medium|distant|n/a> to <landmark or none>\".\n"
        "HEAD LINE: presence, depth, width, length, direction (straight across vs sloping "
        "downward toward the wrist/Mount of Luna), breaks/chains/forks/islands\n"
        "  SLOPE: exactly one of {upward | downward | straight | not clearly visible}\n"
        f"  ORIGIN: exactly one of {_menu('Line of Head', 'ORIGIN')} or 'none'\n"
        f"  TERMINATION: exactly one of {_menu('Line of Head', 'TERMINATION')} or 'none' if the line is short and ends mid-palm\n"
        "  PROXIMITY: <touching|medium|distant|n/a> to <landmark or none>\n"
        "  BRANCHES_TO: landmark(s) any branch is directed toward, or 'none'\n"
        f"{_relationship_field('Line of Head')}"
        f"{_contacts_field('Line of Head')}"
        "HEART LINE: same attributes (depth, width, length, direction, breaks/chains/forks/islands)\n"
        "  SLOPE: exactly one of {upward | downward | straight | not clearly visible}\n"
        f"  ORIGIN: exactly one of {_menu('Line of Heart', 'ORIGIN')} or 'none'\n"
        f"  TERMINATION: exactly one of {_menu('Line of Heart', 'TERMINATION')} or 'none'\n"
        "  PROXIMITY: <touching|medium|distant|n/a> to <landmark or none>\n"
        "  BRANCHES_TO: landmark(s) any branch is directed toward, or 'none'\n"
        f"{_relationship_field('Line of Heart')}"
        f"{_contacts_field('Line of Heart')}"
        "FATE LINE: same attributes (state plainly if absent or barely visible)\n"
        "  SLOPE: exactly one of {upward | downward | straight | not clearly visible}\n"
        f"  ORIGIN: exactly one of {_menu('Line of Fate', 'ORIGIN')} or 'none'\n"
        f"  TERMINATION: exactly one of {_menu('Line of Fate', 'TERMINATION')} or 'none'\n"
        "  PROXIMITY: <touching|medium|distant|n/a> to <landmark or none>\n"
        "  BRANCHES_TO: landmark(s) any branch is directed toward, or 'none'\n"
        "  BREAK TYPE: if the fate line has a break, exactly one of {broken | broken_overlapping} — "
        "broken: the line stops and the next segment starts after a visible gap (clean break); "
        "broken_overlapping: the second segment begins before the first one ends, so the two "
        "segments run alongside for a short stretch. If the line has no break, write 'n/a'.\n"
        "  LENGTH EXTENT: if the fate line runs beyond the palm's edge and visibly continues into "
        "the base of the Second Finger (Saturn finger), write 'cutting_into_finger_of_Saturn'. If "
        "the line ends within the palm, write 'n/a'.\n"
        f"{_relationship_field('Line of Fate')}"
        f"{_contacts_field('Line of Fate')}"
        "LINE OF HEALTH: presence, only if clearly visible\n"
        f"{_relationship_field('Line of Health')}"
        f"{_contacts_field('Line of Health')}"
        "LINE OF MARRIAGE: presence, only if clearly visible\n"
        f"{_relationship_field('Line of Marriage')}"
        "OTHER LINES: sun/intuition lines only if clearly visible\n"
        "MOUNTS: which pads appear developed, flat, or unremarkable\n"
        "MARKS: crosses, stars, grilles, squares, moles — only if clearly visible\n"
        "For any attribute not clearly visible, write 'not clearly visible' — "
        "never guess or fill in what a typical hand would show."
    )


def describe_palm_image(image_bytes: bytes, hand: str, temperature: float = 0.0) -> str:
    """
    Generate a textual palm reading description via GPT-4o vision.

    Args:
        image_bytes: Raw bytes of the palm image.
        hand: "left" or "right" — inserted into the system prompt.
        temperature: defaults to 0.0 — unchanged app behavior, the confirmed-
            description path a user checkpoints against must stay
            reproducible (see the THRESHOLD DISCIPLINE note below). A
            non-zero value is used ONLY by the missing-block retry guard /
            calibration probe, which intentionally trades a little
            determinism to recover a dropped RELATIONAL block on retry.

    Returns:
        Description string from GPT-4o.

    Raises:
        RuntimeError: If the GPT-4o call fails for any reason.
    """
    mime = "image/png" if image_bytes[:8].startswith(b"\x89PNG") else "image/jpeg"
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    client = OpenAI()
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": _build_description_system_prompt(hand),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        }
                    ],
                },
            ],
            # temperature=0 (not 0.3): checkpoint reproducibility -- the
            # description a user confirms must be the description the run
            # would regenerate. This rationale applies to the default-0.0
            # confirmed-description path; the retry path (non-zero
            # temperature, see the temperature arg docstring above)
            # intentionally trades a little determinism to recover a
            # dropped RELATIONAL block.
            #
            # THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
            # max_tokens=600 (not 400): derived from ~10 labeled fields x
            # ~1-2 lines each. Scope guard: this call site only. Revisit
            # trigger: if the step-3 probe shows truncation.
            max_tokens=600,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as exc:
        raise RuntimeError(
            f"palm_processor: GPT-4o description call failed for hand={hand}: {exc}"
        ) from exc


def describe_hand_detail_image(image) -> str:
    """
    Generate a detailed observational description of a hand photograph via GPT-4o vision.

    Args:
        image: PIL Image object of the hand.

    Returns:
        Plain string description from GPT-4o.

    Raises:
        ValueError: If the API call fails or returns an empty response.
    """
    import io
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    client = OpenAI()
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                        },
                        {
                            "type": "text",
                            "text": (
                                "You are a Cheiro-tradition palmist. Examine this hand photograph carefully. "
                                "Describe only what you can physically observe: hand shape, finger lengths "
                                "relative to each other, thumb angle and flexibility, visible lines (life, "
                                "head, heart, fate, sun), any notable mounts, markings, or unusual features. "
                                "Be precise and observational. Do not interpret or predict — only describe."
                            ),
                        },
                    ],
                }
            ],
            max_tokens=400,
            temperature=0,
        )
        content = response.choices[0].message.content
    except Exception as exc:
        raise ValueError(
            f"palm_processor: GPT-4o hand detail call failed: {exc}"
        ) from exc

    if not content:
        raise ValueError("palm_processor: GPT-4o returned an empty response for hand detail image.")
    return content
