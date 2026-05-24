from __future__ import annotations

import base64
import os
import time
from datetime import date, datetime
from urllib.parse import urlencode

import requests


AUTH_URL = "https://flow.polar.com/oauth2/authorization"
TOKEN_URL = "https://polarremote.com/v2/oauth2/token"
API_BASE = "https://www.polaraccesslink.com/v3"
DEFAULT_SCOPE = "accesslink.read_all"


def _client_id() -> str:
    return os.getenv("POLAR_CLIENT_ID", "").strip()


def _client_secret() -> str:
    return os.getenv("POLAR_CLIENT_SECRET", "").strip()


def redirect_uri() -> str:
    explicit = os.getenv("POLAR_REDIRECT_URI", "").strip()
    if explicit:
        return explicit
    base = os.getenv("APP_BASE_URL", "http://127.0.0.1:5002").rstrip("/")
    return f"{base}/api/integrations/polar/callback"


def configured() -> bool:
    return bool(_client_id() and _client_secret())


def authorize_url(state: str, callback_url: str | None = None) -> str:
    if not _client_id():
        raise RuntimeError("Missing POLAR_CLIENT_ID")
    params = {
        "response_type": "code",
        "client_id": _client_id(),
        "redirect_uri": callback_url or redirect_uri(),
        "scope": os.getenv("POLAR_SCOPE", DEFAULT_SCOPE),
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def _basic_auth_header() -> str:
    raw = f"{_client_id()}:{_client_secret()}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def exchange_code(code: str, callback_url: str | None = None) -> dict:
    response = requests.post(
        TOKEN_URL,
        headers={"Authorization": _basic_auth_header()},
        data={"grant_type": "authorization_code", "code": code, "redirect_uri": callback_url or redirect_uri()},
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(f"Polar token exchange failed ({response.status_code}): {response.text}")
    payload = response.json()
    return _with_expiry(payload)


def refresh_token(token_payload: dict) -> dict:
    refresh = token_payload.get("refresh_token")
    if not refresh:
        return token_payload
    response = requests.post(
        TOKEN_URL,
        headers={"Authorization": _basic_auth_header()},
        data={"grant_type": "refresh_token", "refresh_token": refresh},
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(f"Polar token refresh failed ({response.status_code}): {response.text}")
    return {**token_payload, **_with_expiry(response.json())}


def ensure_fresh_token(token_payload: dict) -> dict:
    expires_at = int(token_payload.get("expires_at") or 0)
    if expires_at and expires_at <= int(time.time()) + 120:
        return refresh_token(token_payload)
    return token_payload


def _with_expiry(token_payload: dict) -> dict:
    if token_payload.get("expires_in") and not token_payload.get("expires_at"):
        token_payload["expires_at"] = int(time.time()) + int(token_payload["expires_in"])
    return token_payload


def _headers(token_payload: dict) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token_payload['access_token']}",
        "Accept": "application/json",
    }


def _user_id(token_payload: dict) -> str | None:
    return token_payload.get("x_user_id") or token_payload.get("user_id")


def register_user(token_payload: dict) -> dict:
    token_payload = ensure_fresh_token(token_payload)
    member_id = _user_id(token_payload)
    if not member_id:
        return {"registered": False, "reason": "No Polar user id in token payload"}

    response = requests.post(
        f"{API_BASE}/users",
        headers={**_headers(token_payload), "Content-Type": "application/json"},
        json={"member-id": str(member_id)},
        timeout=20,
    )
    if response.status_code == 409:
        return {"registered": True, "already_registered": True, "member-id": str(member_id)}
    response.raise_for_status()
    payload = response.json() if response.content else {}
    return {"registered": True, "member-id": str(member_id), **payload}


def get_user(token_payload: dict) -> dict:
    token_payload = ensure_fresh_token(token_payload)
    user_id = _user_id(token_payload)
    if not user_id:
        return {}
    response = requests.get(f"{API_BASE}/users/{user_id}", headers=_headers(token_payload), timeout=20)
    if response.status_code in [403, 404]:
        return {}
    response.raise_for_status()
    return response.json()


def list_exercises(token_payload: dict) -> list[dict]:
    token_payload = ensure_fresh_token(token_payload)
    response = requests.get(f"{API_BASE}/exercises", headers=_headers(token_payload), timeout=20)
    if response.status_code in [204, 404]:
        return []
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, list):
        return payload
    return payload.get("exercises", [])


def normalize_athlete(user: dict, token_payload: dict | None = None) -> dict:
    birthdate = user.get("birthdate") or user.get("date-of-birth")
    age = None
    if birthdate:
        try:
            born = date.fromisoformat(birthdate[:10])
            today = date.today()
            age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        except ValueError:
            age = None
    return {
        "polar_user_id": user.get("polar-user-id") or user.get("id") or (token_payload or {}).get("x_user_id"),
        "name": " ".join(
            part for part in [user.get("first-name"), user.get("last-name")] if part
        ).strip(),
        "sex": user.get("gender"),
        "age": age,
        "height": user.get("height"),
        "weight": user.get("weight"),
    }


def normalize_exercise(exercise: dict) -> dict:
    start = exercise.get("start-time") or exercise.get("start_time") or exercise.get("created")
    duration_seconds = exercise.get("duration") or exercise.get("duration_seconds")
    if isinstance(duration_seconds, str):
        duration_seconds = parse_iso_duration(duration_seconds)
    return {
        "source": "polar",
        "source_id": exercise.get("id") or exercise.get("upload-time"),
        "date": (start or "")[:10],
        "activityName": exercise.get("sport") or exercise.get("name") or "Polar exercise",
        "sport_type": exercise.get("sport"),
        "duration_mins": round((duration_seconds or 0) / 60, 1) if duration_seconds else None,
        "distance_m": exercise.get("distance"),
        "calories": exercise.get("calories"),
        "averageHR": exercise.get("heart-rate", {}).get("average") if isinstance(exercise.get("heart-rate"), dict) else exercise.get("average-heart-rate"),
        "maxHR": exercise.get("heart-rate", {}).get("maximum") if isinstance(exercise.get("heart-rate"), dict) else exercise.get("maximum-heart-rate"),
        "training_load": exercise.get("training-load") or exercise.get("training_load"),
    }


def parse_iso_duration(value: str) -> int | None:
    try:
        # Supports common Polar-style PT1H20M30S durations without pulling in extra deps.
        if not value.startswith("PT"):
            return None
        hours = minutes = seconds = 0
        number = ""
        for char in value[2:]:
            if char.isdigit() or char == ".":
                number += char
            elif char == "H":
                hours = float(number or 0)
                number = ""
            elif char == "M":
                minutes = float(number or 0)
                number = ""
            elif char == "S":
                seconds = float(number or 0)
                number = ""
        return int(hours * 3600 + minutes * 60 + seconds)
    except Exception:
        return None
