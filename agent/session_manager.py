"""
session_manager.py
Stores conversation history, session notes, and default user context per session.
Persists to data/sessions/{session_id}.json via atomic write (.tmp then os.replace).
"""

import json
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SESSIONS_DIR = Path("data/sessions")
DEFAULT_USER_DIR = Path("data/default_user")
VALID_ROLES = {"user", "assistant"}
MAX_HISTORY_SAVE = 100   # turns; if exceeded, oldest 20 turns are trimmed on save()
_TRIM_TO_TURNS   = 80    # turns kept after trim (MAX_HISTORY_SAVE - 20)


class SessionManager:
    def __init__(self, session_id: str | None = None) -> None:
        self.session_id: str = session_id or str(uuid.uuid4())
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self._history: list[dict] = []
        self._notes: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_message(self, role: str, content: str) -> None:
        """Append a message to the conversation history.

        Raises:
            ValueError: role is not "user" or "assistant".
        """
        if role not in VALID_ROLES:
            raise ValueError(f"role must be one of {VALID_ROLES}, got: {role!r}")
        self._history.append({"role": role, "content": content})

    def add_note(self, key: str, value: str) -> None:
        """Store a key fact learned about the user during this session."""
        self._notes[key] = value

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_history(self) -> list[dict]:
        """Return a copy of conversation history in OpenAI message format."""
        return list(self._history)

    def get_notes(self) -> dict:
        """Return a copy of session notes."""
        return dict(self._notes)

    def get_recent_history(self, n: int = 6) -> list[dict]:
        """Return the last n complete turns (user+assistant pairs) as a flat message list.

        Args:
            n: Number of complete turns (pairs) to return. Returns up to n*2 messages.
               If history is shorter, returns all available messages.

        Returns:
            List of {"role": str, "content": str} dicts, always starting on a "user" message.
        """
        if n <= 0:
            return []
        recent = list(self._history[-(n * 2):])
        # Guard: if odd-length history left a leading assistant message, drop it
        if recent and recent[0]["role"] != "user":
            recent = recent[1:]
        return recent

    def get_default_context(self) -> dict:
        """Load default user context files from data/default_user/.

        Returns None for each file that does not exist — missing files are
        expected on a fresh clone and are not an error condition.

        Returns:
            {"kundali_summary": str | None, "palm_description": str | None}
        """
        def _read(filename: str) -> str | None:
            path = DEFAULT_USER_DIR / filename
            try:
                text = path.read_text(encoding="utf-8").strip()
                return text or None
            except FileNotFoundError:
                return None

        return {
            "kundali_summary":  _read("kundali_summary.txt"),
            "palm_description": _read("palm_description.txt"),
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, sessions_dir: Path = SESSIONS_DIR) -> None:
        """Atomically write session to {sessions_dir}/{session_id}.json.

        Uses write-to-.tmp-then-os.replace to avoid partial writes on crash.

        Raises:
            RuntimeError: File could not be written.
        """
        sessions_dir.mkdir(parents=True, exist_ok=True)

        # Trim in-memory history if over cap before writing to disk.
        # get_recent_history() is unaffected — it slices from whatever _history holds.
        cap_messages  = MAX_HISTORY_SAVE * 2   # 200 messages
        keep_messages = _TRIM_TO_TURNS * 2     # 160 messages
        if len(self._history) > cap_messages:
            dropped = len(self._history) - keep_messages
            self._history = self._history[-keep_messages:]
            logger.info(
                "Session %s: history trimmed — dropped %d messages, kept last %d turns",
                self.session_id, dropped, _TRIM_TO_TURNS,
            )

        data = {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "history":    self._history,
            "notes":      self._notes,
        }

        target = sessions_dir / f"{self.session_id}.json"
        tmp    = sessions_dir / f"{self.session_id}.tmp"

        try:
            tmp.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp.replace(target)
        except Exception as e:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(
                f"Failed to save session '{self.session_id}': {e}"
            ) from e

        logger.debug("Session %s saved to %s", self.session_id, target)

    @classmethod
    def load(cls, session_id: str, sessions_dir: Path = SESSIONS_DIR) -> "SessionManager":
        """Load session from disk.

        Raises:
            FileNotFoundError: Session does not exist.
            RuntimeError: Session file is corrupted (invalid JSON).
        """
        path = sessions_dir / f"{session_id}.json"

        if not path.exists():
            raise FileNotFoundError(
                f"Session '{session_id}' not found — start a new session."
            )

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Session '{session_id}' is corrupted — start a new session. ({e})"
            ) from e

        instance = cls(session_id=data["session_id"])
        instance.created_at = data["created_at"]
        instance._history   = data.get("history", [])
        instance._notes     = data.get("notes", {})
        return instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

    sm = SessionManager()
    sm.add_message("user", "What is Jupiter in the 7th house?")
    sm.add_message("assistant", "Jupiter in the 7th house brings a harmonious marriage...")
    sm.add_note("birth_date", "1990-01-15")
    sm.save()

    loaded = SessionManager.load(sm.session_id)
    print(f"session_id:  {loaded.session_id}")
    print(f"history:     {loaded.get_history()}")
    print(f"notes:       {loaded.get_notes()}")
    print(f"default ctx: {loaded.get_default_context()}")
