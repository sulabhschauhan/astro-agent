"""Conversation thread -> a compact context block (Path B, S147).

Astro Agent is a CONVERSATIONAL, personalised reader: a follow-up ("okay, any
date after the 24th?") must resolve against what was already said, and the
answer may legitimately shift given the thread. Path B was single-shot (S129),
so this is the one place history enters -- fed to the PLANNER (to resolve a
follow-up into a self-contained intent) and the INTERPRETER (for continuity).

STANDING PROJECT REQUIREMENT (Sulabh, S147): conversation context applies across
the whole project, not just muhurta.

FIDELITY GUARDRAIL (enforced in the interpreter prompt, stated here for the
record): history is for resolving references and keeping the thread coherent --
it is NEVER a source of chart facts. Every chart fact an answer states must come
from the CURRENT turn's fact block, never from memory of a prior turn.

This is a LEAF module (imports nothing from agent.astro) so both planner and
interpreter can import it without a cycle -- the single source for how a thread
is rendered.

Python 3.11.
"""
from __future__ import annotations

__all__ = ["render_history"]

DEFAULT_MAX_MESSAGES = 6        # ~3 Q&A pairs -- enough to resolve a follow-up
DEFAULT_MAX_CHARS = 600         # truncate each turn so planner tokens stay bounded


def render_history(
    messages: list | None,
    *,
    max_messages: int = DEFAULT_MAX_MESSAGES,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> str:
    """Render recent {"role","content"} turns into a compact text block.

    Args:
        messages: the app's chat thread (list of {"role","content"}), oldest
            first. The CURRENT question must NOT be in here -- only prior turns.
        max_messages: keep at most this many most-recent messages.
        max_chars: truncate each message's content to this many characters.

    Returns:
        "" when there is nothing usable (so callers can treat empty as "no
        history" and keep the single-shot prompt byte-identical). Otherwise a
        labelled block, most-recent last.
    """
    if not messages:
        return ""
    recent = [m for m in messages
              if isinstance(m, dict) and str(m.get("content") or "").strip()]
    recent = recent[-max_messages:]
    if not recent:
        return ""
    lines = []
    for m in recent:
        role = "You" if m.get("role") == "user" else "Astrologer"
        text = " ".join(str(m.get("content") or "").split())   # collapse whitespace
        if len(text) > max_chars:
            text = text[:max_chars].rstrip() + " ..."
        lines.append(f"- {role}: {text}")
    return "RECENT CONVERSATION (most recent last):\n" + "\n".join(lines)
