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


def describe_palm_image(image_bytes: bytes, hand: str) -> str:
    """
    Generate a textual palm reading description via GPT-4o vision.

    Args:
        image_bytes: Raw bytes of the palm image.
        hand: "left" or "right" — inserted into the system prompt.

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
                    "content": (
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
                        "HEAD LINE: presence, depth, width, length, direction (straight across vs sloping "
                        "downward toward the wrist/Mount of Luna), origin and end, breaks/chains/forks/islands\n"
                        "HEART LINE: same attributes\n"
                        "FATE LINE: same attributes (state plainly if absent or barely visible)\n"
                        "OTHER LINES: sun/health/marriage lines only if clearly visible\n"
                        "MOUNTS: which pads appear developed, flat, or unremarkable\n"
                        "MARKS: crosses, stars, grilles, squares, moles — only if clearly visible\n"
                        "For any attribute not clearly visible, write 'not clearly visible' — "
                        "never guess or fill in what a typical hand would show."
                    ),
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
            # would regenerate.
            #
            # THRESHOLD DISCIPLINE (CLAUDE.md Working Style #4).
            # max_tokens=600 (not 400): derived from ~10 labeled fields x
            # ~1-2 lines each. Scope guard: this call site only. Revisit
            # trigger: if the step-3 probe shows truncation.
            max_tokens=600,
            temperature=0,
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
