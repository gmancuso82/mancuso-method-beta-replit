from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

import beta_coach
import beta_store
import polar_data
import strava_data


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"

app = Flask(__name__, static_folder=str(STATIC_DIR))
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
CORS(app)


def external_base_url() -> str:
    configured = os.getenv("APP_BASE_URL", "").strip()
    if configured:
        return configured.rstrip("/")
    return request.url_root.rstrip("/")


def oauth_callback_url(provider: str) -> str:
    return f"{external_base_url()}/api/integrations/{provider}/callback"


def enrich_checkin_with_integrations(user_id: str, checkin: dict) -> dict:
    enriched = dict(checkin)
    connected_activities = []
    strava = beta_store.get_integration(user_id, "strava") or {}
    if strava.get("recent_activities"):
        connected_activities.extend(strava["recent_activities"])
    if strava.get("athlete"):
        enriched["connected_athlete_profile"] = strava["athlete"]
    polar = beta_store.get_integration(user_id, "polar") or {}
    if polar.get("recent_activities"):
        connected_activities.extend(polar["recent_activities"])
    if polar.get("athlete"):
        enriched["connected_polar_profile"] = polar["athlete"]
    if connected_activities:
        enriched["connected_activities"] = sorted(
            connected_activities,
            key=lambda item: item.get("date") or "",
            reverse=True,
        )
    return enriched


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def refresh_memory(user_id: str, checkin: dict | None, messages: list[dict] | None, feedback: dict | None = None) -> None:
    if not os.getenv("ANTHROPIC_API_KEY", "").strip():
        return
    profile = beta_store.get_profile(user_id)
    if not profile:
        return
    try:
        updated = beta_coach.update_memory_summary(profile, checkin, messages or [], feedback)
        beta_store.update_memory(user_id, updated)
    except Exception as exc:
        print(f"Memory update skipped for {user_id}: {exc}")


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "beta.html")


@app.get("/admin")
def admin():
    return send_from_directory(STATIC_DIR, "admin.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "app": "mancuso-method-beta"})


@app.get("/api/integrations/diagnostics")
def integration_diagnostics():
    return jsonify(
        {
            "app_base_url": external_base_url(),
            "strava": {
                "configured": strava_data.configured(),
                "callback_url": oauth_callback_url("strava"),
            },
            "polar": {
                "configured": polar_data.configured(),
                "callback_url": oauth_callback_url("polar"),
            },
        }
    )


@app.get("/api/integrations/strava/debug-url")
def strava_debug_url():
    user_id = request.args.get("user_id", "debug-user").strip() or "debug-user"
    state = beta_store.create_oauth_state(user_id, "strava")
    callback_url = oauth_callback_url("strava")
    return jsonify(
        {
            "configured": strava_data.configured(),
            "callback_url": callback_url,
            "authorize_url": strava_data.authorize_url(state, callback_url) if strava_data.configured() else None,
        }
    )


@app.get("/api/users")
def users():
    return jsonify({"users": beta_store.list_profiles()})


@app.get("/api/admin/overview")
def admin_overview():
    return jsonify(
        {
            "users": beta_store.list_profiles(),
            "checkins": beta_store.list_checkins(),
            "conversations": beta_store.list_conversations(),
            "feedback": beta_store.list_feedback(),
            "integrations": beta_store.list_integration_summaries(),
        }
    )


@app.get("/api/integrations/status/<user_id>")
def integration_status(user_id: str):
    strava = beta_store.get_integration(user_id, "strava")
    polar = beta_store.get_integration(user_id, "polar")
    return jsonify(
        {
            "strava": {
                "configured": strava_data.configured(),
                "connected": bool(strava and strava.get("token")),
                "athlete": (strava or {}).get("athlete"),
                "last_sync_at": (strava or {}).get("last_sync_at"),
                "recent_activities": (strava or {}).get("recent_activities", []),
            },
            "polar": {
                "configured": polar_data.configured(),
                "connected": bool(polar and polar.get("token")),
                "athlete": (polar or {}).get("athlete"),
                "last_sync_at": (polar or {}).get("last_sync_at"),
                "recent_activities": (polar or {}).get("recent_activities", []),
            },
            "apple_health": {"connected": False, "planned": True},
            "apple_watch": {"connected": False, "planned": True},
            "oura": {"connected": False, "planned": True},
            "whoop": {"connected": False, "planned": True},
            "garmin": {"connected": False, "planned": True},
        }
    )


@app.get("/api/integrations/strava/connect")
def strava_connect():
    user_id = request.args.get("user_id", "").strip()
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    if not strava_data.configured():
        return jsonify({"error": "Missing STRAVA_CLIENT_ID or STRAVA_CLIENT_SECRET"}), 400
    state = beta_store.create_oauth_state(user_id, "strava")
    return redirect(strava_data.authorize_url(state, oauth_callback_url("strava")))


@app.get("/api/integrations/strava/callback")
def strava_callback():
    code = request.args.get("code", "").strip()
    state = request.args.get("state", "").strip()
    if not code or not state:
        return "Missing Strava code or state.", 400

    state_payload = beta_store.consume_oauth_state(state)
    if not state_payload or state_payload.get("provider") != "strava":
        return "Invalid or expired Strava authorization state.", 400

    user_id = state_payload["user_id"]
    token_payload = strava_data.exchange_code(code)
    athlete = token_payload.get("athlete") or strava_data.get_athlete(token_payload)
    normalized_athlete = strava_data.normalize_athlete(athlete)
    recent_activities = []
    try:
        recent_activities = [
            strava_data.normalize_activity(activity)
            for activity in strava_data.get_activities(token_payload, days=45)
        ]
    except Exception as exc:
        print(f"Strava activity sync skipped during connect for {user_id}: {exc}")
    beta_store.save_integration(
        user_id,
        "strava",
        {
            "token": {key: token_payload.get(key) for key in ["access_token", "refresh_token", "expires_at", "expires_in", "token_type", "scope"]},
            "athlete": normalized_athlete,
            "raw_athlete": athlete,
            "recent_activities": recent_activities,
            "last_sync_at": now_iso() if recent_activities else None,
        },
    )

    profile = beta_store.get_profile(user_id) or {"user_id": user_id}
    if normalized_athlete.get("name") and not profile.get("name"):
        profile["name"] = normalized_athlete["name"]
    if normalized_athlete.get("sex"):
        profile["sex"] = normalized_athlete["sex"]
    if normalized_athlete.get("weight"):
        profile["weight"] = normalized_athlete["weight"]
    sources = set(profile.get("data_sources") or [])
    sources.add("Strava")
    profile["data_sources"] = sorted(sources)
    beta_store.save_profile(profile)

    return redirect(f"/?connected=strava&user_id={user_id}")


@app.get("/api/integrations/polar/connect")
def polar_connect():
    user_id = request.args.get("user_id", "").strip()
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    if not polar_data.configured():
        return jsonify({"error": "Missing POLAR_CLIENT_ID or POLAR_CLIENT_SECRET"}), 400
    state = beta_store.create_oauth_state(user_id, "polar")
    return redirect(polar_data.authorize_url(state, oauth_callback_url("polar")))


@app.get("/api/integrations/polar/callback")
def polar_callback():
    code = request.args.get("code", "").strip()
    state = request.args.get("state", "").strip()
    if not code or not state:
        return "Missing Polar code or state.", 400

    state_payload = beta_store.consume_oauth_state(state)
    if not state_payload or state_payload.get("provider") != "polar":
        return "Invalid or expired Polar authorization state.", 400

    user_id = state_payload["user_id"]
    try:
        token_payload = polar_data.exchange_code(code, oauth_callback_url("polar"))
        registration = polar_data.register_user(token_payload)
        athlete = polar_data.get_user(token_payload)
    except Exception as exc:
        return f"Polar connection failed: {exc}", 400
    normalized_athlete = polar_data.normalize_athlete(athlete, token_payload)
    beta_store.save_integration(
        user_id,
        "polar",
        {
            "token": {
                key: token_payload.get(key)
                for key in ["access_token", "refresh_token", "expires_at", "expires_in", "token_type", "scope", "x_user_id", "user_id"]
            },
            "athlete": normalized_athlete,
            "raw_athlete": athlete,
            "registration": registration,
            "last_sync_at": None,
        },
    )

    profile = beta_store.get_profile(user_id) or {"user_id": user_id}
    for key in ["name", "sex", "age", "height", "weight"]:
        if normalized_athlete.get(key) and not profile.get(key):
            profile[key] = normalized_athlete[key]
    sources = set(profile.get("data_sources") or [])
    sources.add("Polar")
    profile["data_sources"] = sorted(sources)
    beta_store.save_profile(profile)

    return redirect(f"/?connected=polar&user_id={user_id}")


@app.post("/api/integrations/strava/sync")
def strava_sync():
    payload = request.get_json(force=True)
    user_id = payload.get("user_id", "").strip()
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    integration = beta_store.get_integration(user_id, "strava")
    if not integration or not integration.get("token"):
        return jsonify({"error": "Strava is not connected"}), 400

    token = strava_data.ensure_fresh_token(integration["token"])
    athlete = strava_data.get_athlete(token)
    activities = strava_data.get_activities(token, days=int(payload.get("days", 45)))
    normalized = [strava_data.normalize_activity(activity) for activity in activities]

    integration = beta_store.save_integration(
        user_id,
        "strava",
        {
            **integration,
            "token": token,
            "athlete": strava_data.normalize_athlete(athlete),
            "raw_athlete": athlete,
            "recent_activities": normalized,
            "last_sync_at": now_iso(),
        },
    )
    return jsonify(
        {
            "athlete": integration.get("athlete"),
            "activities": normalized,
            "count": len(normalized),
        }
    )


@app.post("/api/integrations/polar/sync")
def polar_sync():
    payload = request.get_json(force=True)
    user_id = payload.get("user_id", "").strip()
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    integration = beta_store.get_integration(user_id, "polar")
    if not integration or not integration.get("token"):
        return jsonify({"error": "Polar is not connected"}), 400

    token = polar_data.ensure_fresh_token(integration["token"])
    athlete = polar_data.get_user(token)
    exercises = polar_data.list_exercises(token)
    normalized = [polar_data.normalize_exercise(exercise) for exercise in exercises]

    integration = beta_store.save_integration(
        user_id,
        "polar",
        {
            **integration,
            "token": token,
            "athlete": polar_data.normalize_athlete(athlete, token),
            "raw_athlete": athlete,
            "recent_activities": normalized,
            "last_sync_at": now_iso(),
        },
    )
    return jsonify(
        {
            "athlete": integration.get("athlete"),
            "activities": normalized,
            "count": len(normalized),
        }
    )


@app.get("/api/profile/<user_id>")
def get_profile(user_id: str):
    profile = beta_store.get_profile(user_id)
    if not profile:
        return jsonify({"error": "profile not found"}), 404
    return jsonify({"profile": profile})


@app.post("/api/profile")
def save_profile():
    payload = request.get_json(force=True)
    profile = beta_store.save_profile(payload)
    return jsonify({"profile": profile})


@app.get("/api/checkin/<user_id>")
def get_checkin(user_id: str):
    checkin = beta_store.get_checkin(user_id)
    return jsonify({"checkin": checkin})


@app.post("/api/checkin")
def save_checkin():
    payload = request.get_json(force=True)
    user_id = payload.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    checkin = beta_store.save_checkin(user_id, payload)
    return jsonify({"checkin": checkin})


@app.post("/api/briefing")
def briefing():
    payload = request.get_json(force=True)
    user_id = payload.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    profile = beta_store.get_profile(user_id)
    if not profile:
        return jsonify({"error": "profile not found"}), 404

    checkin = payload.get("checkin") or beta_store.get_checkin(user_id)
    if not checkin:
        return jsonify({"error": "checkin not found"}), 404

    checkin = enrich_checkin_with_integrations(user_id, checkin)
    recent = beta_store.recent_checkins(user_id)
    text = beta_coach.generate_briefing(profile, checkin, recent)

    messages = [
        {"role": "user", "content": f"Daily check-in submitted: {checkin}"},
        {"role": "assistant", "content": text},
    ]
    beta_store.save_conversation(user_id, messages, checkin.get("date"))
    return jsonify({"briefing": text, "messages": messages})


@app.post("/api/chat")
def chat():
    payload = request.get_json(force=True)
    user_id = payload.get("user_id")
    text = payload.get("message", "").strip()
    if not user_id or not text:
        return jsonify({"error": "user_id and message are required"}), 400

    profile = beta_store.get_profile(user_id)
    checkin = beta_store.get_checkin(user_id)
    if not profile:
        return jsonify({"error": "profile not found"}), 404
    if not checkin:
        return jsonify({"error": "checkin not found"}), 404

    checkin = enrich_checkin_with_integrations(user_id, checkin)
    messages = beta_store.get_conversation(user_id, checkin.get("date"))
    messages.append({"role": "user", "content": text})
    reply = beta_coach.chat_reply(profile, checkin, beta_store.recent_checkins(user_id), messages)
    messages.append({"role": "assistant", "content": reply})
    beta_store.save_conversation(user_id, messages, checkin.get("date"))
    refresh_memory(user_id, checkin, messages)
    return jsonify({"reply": reply, "messages": messages})


@app.post("/api/feedback")
def feedback():
    payload = request.get_json(force=True)
    user_id = payload.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    item = beta_store.save_feedback(user_id, payload)
    checkin = beta_store.get_checkin(user_id)
    messages = beta_store.get_conversation(user_id, (checkin or {}).get("date") if checkin else None)
    refresh_memory(user_id, checkin, messages, item)
    return jsonify({"feedback": item})


if __name__ == "__main__":
    beta_store.ensure_data_dirs()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5002")), debug=False)
