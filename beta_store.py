from __future__ import annotations

import json
import re
import secrets
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
USERS_DIR = DATA_DIR / "users"
CHECKINS_DIR = DATA_DIR / "checkins"
CONVERSATIONS_DIR = DATA_DIR / "conversations"
FEEDBACK_DIR = DATA_DIR / "feedback"
INTEGRATIONS_DIR = DATA_DIR / "integrations"


def ensure_data_dirs() -> None:
    for path in [USERS_DIR, CHECKINS_DIR, CONVERSATIONS_DIR, FEEDBACK_DIR, INTEGRATIONS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def slugify_user_id(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    if not cleaned:
        cleaned = f"user-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return cleaned[:48]


def today_key() -> str:
    return date.today().isoformat()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    ensure_data_dirs()
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)


def user_path(user_id: str) -> Path:
    return USERS_DIR / f"{slugify_user_id(user_id)}.json"


def checkin_path(user_id: str, day: str) -> Path:
    return CHECKINS_DIR / f"{slugify_user_id(user_id)}__{day}.json"


def conversation_path(user_id: str, day: str) -> Path:
    return CONVERSATIONS_DIR / f"{slugify_user_id(user_id)}__{day}.json"


def feedback_path(user_id: str, day: str) -> Path:
    return FEEDBACK_DIR / f"{slugify_user_id(user_id)}__{day}.json"


def integration_path(user_id: str, provider: str) -> Path:
    safe_provider = slugify_user_id(provider)
    return INTEGRATIONS_DIR / f"{slugify_user_id(user_id)}__{safe_provider}.json"


def oauth_state_path(state: str) -> Path:
    return INTEGRATIONS_DIR / f"oauth_state__{slugify_user_id(state)}.json"


def save_profile(profile: dict[str, Any]) -> dict[str, Any]:
    ensure_data_dirs()
    user_id = slugify_user_id(profile.get("user_id") or profile.get("name") or "")
    saved = {
        **profile,
        "user_id": user_id,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    existing = get_profile(user_id) or {}
    saved.setdefault("coach_memory_summary", existing.get("coach_memory_summary", ""))
    write_json(user_path(user_id), saved)
    return saved


def get_profile(user_id: str) -> dict[str, Any] | None:
    return read_json(user_path(user_id), None)


def list_profiles() -> list[dict[str, Any]]:
    ensure_data_dirs()
    return [read_json(path, {}) for path in sorted(USERS_DIR.glob("*.json"))]


def list_checkins() -> list[dict[str, Any]]:
    ensure_data_dirs()
    return [read_json(path, {}) for path in sorted(CHECKINS_DIR.glob("*.json"), reverse=True)]


def list_conversations() -> list[dict[str, Any]]:
    ensure_data_dirs()
    return [read_json(path, {}) for path in sorted(CONVERSATIONS_DIR.glob("*.json"), reverse=True)]


def list_feedback() -> list[dict[str, Any]]:
    ensure_data_dirs()
    return [read_json(path, {}) for path in sorted(FEEDBACK_DIR.glob("*.json"), reverse=True)]


def save_checkin(user_id: str, checkin: dict[str, Any]) -> dict[str, Any]:
    day = checkin.get("date") or today_key()
    saved = {
        **checkin,
        "user_id": slugify_user_id(user_id),
        "date": day,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_json(checkin_path(user_id, day), saved)
    return saved


def get_checkin(user_id: str, day: str | None = None) -> dict[str, Any] | None:
    return read_json(checkin_path(user_id, day or today_key()), None)


def recent_checkins(user_id: str, limit: int = 7) -> list[dict[str, Any]]:
    ensure_data_dirs()
    prefix = f"{slugify_user_id(user_id)}__"
    paths = sorted(CHECKINS_DIR.glob(f"{prefix}*.json"), reverse=True)
    return [read_json(path, {}) for path in paths[:limit]]


def get_conversation(user_id: str, day: str | None = None) -> list[dict[str, str]]:
    payload = read_json(conversation_path(user_id, day or today_key()), {"messages": []})
    return payload.get("messages", [])


def save_conversation(user_id: str, messages: list[dict[str, str]], day: str | None = None) -> None:
    write_json(
        conversation_path(user_id, day or today_key()),
        {
            "user_id": slugify_user_id(user_id),
            "date": day or today_key(),
            "messages": messages,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        },
    )


def save_feedback(user_id: str, feedback: dict[str, Any]) -> dict[str, Any]:
    day = feedback.get("date") or today_key()
    existing = read_json(feedback_path(user_id, day), {"items": []})
    item = {
        **feedback,
        "user_id": slugify_user_id(user_id),
        "date": day,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    existing.setdefault("items", []).append(item)
    write_json(feedback_path(user_id, day), existing)
    return item


def update_memory(user_id: str, memory_summary: str) -> None:
    profile = get_profile(user_id)
    if not profile:
        return
    profile["coach_memory_summary"] = memory_summary.strip()
    profile["updated_at"] = datetime.now().isoformat(timespec="seconds")
    write_json(user_path(user_id), profile)


def save_integration(user_id: str, provider: str, payload: dict[str, Any]) -> dict[str, Any]:
    saved = {
        **payload,
        "user_id": slugify_user_id(user_id),
        "provider": slugify_user_id(provider),
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_json(integration_path(user_id, provider), saved)
    return saved


def get_integration(user_id: str, provider: str) -> dict[str, Any] | None:
    return read_json(integration_path(user_id, provider), None)


def create_oauth_state(user_id: str, provider: str) -> str:
    state = secrets.token_urlsafe(24)
    write_json(
        oauth_state_path(state),
        {
            "state": state,
            "user_id": slugify_user_id(user_id),
            "provider": slugify_user_id(provider),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    return state


def consume_oauth_state(state: str) -> dict[str, Any] | None:
    path = oauth_state_path(state)
    payload = read_json(path, None)
    if path.exists():
        path.unlink()
    return payload
