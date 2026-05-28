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
    "You are a palm image validator. Analyse the image and return \n"
    "ONLY valid JSON, no markdown:\n"
    "{\n"
    "  'hand': 'left|right|unknown',\n"
    "  'quality': 'good|poor_readable|unusable',\n"
    "  'issues': ['blurry','partial','dark','not_a_hand']\n"
    "}\n"
    "issues is empty list if none."
)


def validate_palm_image(image_bytes: bytes, slot: str) -> dict:
    """
    Validate a palm image using GPT-4o vision.

    Args:
        image_bytes: Raw bytes of the uploaded image.
        slot: "left" or "right" — identifies which uploader the image came from.

    Returns:
        {
            "hash":           str,        # MD5 hex digest of image_bytes
            "hand":           str,        # "left" | "right" | "unknown"
            "quality":        str,        # "good" | "poor_readable" | "unusable" | "unknown"
            "issues":         list[str],  # subset of blurry/partial/dark/not_a_hand
            "hard_reject":    bool,       # True → do not use image for reading
            "warn":           bool,       # True → usable but warn the user
            "warn_message":   str|None,   # set when warn=True
            "reject_message": str|None,   # set when hard_reject=True
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
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        }
                    ],
                },
            ],
            max_tokens=200,
            temperature=0,
        )
        raw = response.choices[0].message.content
    except Exception:
        logger.exception("palm_processor: GPT-4o call failed for slot=%s hash=%s", slot, image_hash)
        return {
            "hash":           image_hash,
            "hand":           "unknown",
            "quality":        "unknown",
            "issues":         [],
            "hard_reject":    False,
            "warn":           True,
            "warn_message":   "Could not validate image — proceeding with caution.",
            "reject_message": None,
        }

    try:
        parsed  = json.loads(raw)
        hand    = parsed.get("hand", "unknown")
        quality = parsed.get("quality", "unknown")
        issues  = parsed.get("issues", [])
    except (json.JSONDecodeError, ValueError):
        logger.warning("palm_processor: JSON parse failed for slot=%s. raw=%r", slot, raw)
        return {
            "hash":           image_hash,
            "hand":           "unknown",
            "quality":        "unknown",
            "issues":         [],
            "hard_reject":    False,
            "warn":           True,
            "warn_message":   "Could not validate image — proceeding with caution.",
            "reject_message": None,
        }

    hard_reject    = False
    warn           = False
    warn_message   = None
    reject_message = None

    if hand == "unknown":
        hard_reject    = True
        reject_message = "Hand orientation could not be determined — please upload a clearer palm image."
    elif "not_a_hand" in issues:
        hard_reject    = True
        reject_message = "This does not appear to be a palm image — please upload a photo of your hand."
    elif quality == "unusable":
        hard_reject    = True
        reject_message = "Image quality is too poor to use — please upload a well-lit, in-focus photo."
    elif quality == "poor_readable":
        warn         = True
        warn_message = "Image quality is reduced — the reading may be less accurate."

    return {
        "hash":           image_hash,
        "hand":           hand,
        "quality":        quality,
        "issues":         issues,
        "hard_reject":    hard_reject,
        "warn":           warn,
        "warn_message":   warn_message,
        "reject_message": reject_message,
    }
