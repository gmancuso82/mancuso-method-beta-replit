from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import requests


AUTH_URL = "https://www.strava.com/oauth/authorize"
TOKEN_URL = "https://www.strava.com/oauth/token"
API_BASE = "https://www.strava.com/api/v3"
DEFAULT_SCOPE = "read,profile:read_all,activity:read_all"


def _client_id() -> str:
    return os.getenv("STRAVA_CLIENT_ID", "").strip()


def _client_secret() -> str:
    return os.getenv("STRAVA_CLIENT_SECRET", "").strip()


def redirect_uri() -> str:
    explicit = os.getenv("STRAVA_REDIRECT_URI", "").strip()
    if explicit:
        return explicit
    base = os.getenv("APP_BASE_URL", "http://127.0.0.1:5002").rstrip("/")
    return f"{base}/api/integrations/strava/callback"


def configured() -> bool:
    return bool(_client_id() and _client_secret())


def authorize_url(state: str) -> str:
    if not _client_id():
        raise RuntimeError("Missing STRAVA_CLIENT_ID")
    params = {
        "client_id": _client_id(),
        "response_type": "code",
        "redirect_uri": redirect_uri(),
        "approval_prompt": "auto",
        "scope": DEFAULT_SCOPE,
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str) -> dict:
    response = requests.post(
        TOKEN_URL,
        data={
            "client_id": _client_id(),
            "client_secret": _client_secret(),
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def refresh_token(token_payload: dict) -> dict:
    response = requests.post(
        TOKEN_URL,
        data={
            "client_id": _client_id(),
            "client_secret": _client_secret(),
            "grant_type": "refresh_token",
            "refresh_token": token_payload["refresh_token"],
        },
        timeout=20,
    )
    response.raise_for_status()
    refreshed = response.json()
    return {**token_payload, **refreshed}


def ensure_fresh_token(token_payload: dict) -> dict:
    expires_at = int(token_payload.get("expires_at") or 0)
    if expires_at <= int(time.time()) + 120:
        return refresh_token(token_payload)
    return token_payload


def _headers(token_payload: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_payload['access_token']}"}


def get_athlete(token_payload: dict) -> dict:
    token_payload = ensure_fresh_token(token_payload)
    response = requests.get(f"{API_BASE}/athlete", headers=_headers(token_payload), timeout=20)
    response.raise_for_status()
    return response.json()


def get_activities(
    token_payload: dict,
    days: int = 45,
    per_page: int = 100,
    max_pages: int = 5,
) -> list[dict]:
    token_payload = ensure_fresh_token(token_payload)
    after = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    activities = []
    for page in range(1, max_pages + 1):
        response = requests.get(
            f"{API_BASE}/athlete/activities",
            headers=_headers(token_payload),
            params={"after": after, "per_page": per_page, "page": page},
            timeout=20,
        )
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break
        activities.extend(batch)
        if len(batch) < per_page:
            break

    return sorted(
        activities,
        key=lambda activity: activity.get("start_date_local") or activity.get("start_date") or "",
        reverse=True,
    )


def normalize_activity(activity: dict) -> dict:
    moving_seconds = activity.get("moving_time") or activity.get("elapsed_time") or 0
    start = activity.get("start_date_local") or activity.get("start_date")
    return {
        "source": "strava",
        "source_id": activity.get("id"),
        "date": (start or "")[:10],
        "activityName": activity.get("name") or activity.get("sport_type") or activity.get("type"),
        "sport_type": activity.get("sport_type") or activity.get("type"),
        "duration_mins": round(moving_seconds / 60, 1),
        "distance_m": activity.get("distance"),
        "calories": activity.get("calories"),
        "averageHR": activity.get("average_heartrate"),
        "maxHR": activity.get("max_heartrate"),
        "relative_effort": activity.get("suffer_score"),
    }


def normalize_athlete(athlete: dict) -> dict:
    return {
        "strava_athlete_id": athlete.get("id"),
        "name": " ".join(
            part for part in [athlete.get("firstname"), athlete.get("lastname")] if part
        ).strip(),
        "sex": athlete.get("sex"),
        "weight": athlete.get("weight"),
        "profile_medium": athlete.get("profile_medium"),
    }
