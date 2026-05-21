from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Any


MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")


def _format_list(items: Any) -> str:
    if not items:
        return "None reported"
    if isinstance(items, str):
        return items
    if isinstance(items, list):
        return "\n".join(f"- {item}" for item in items if item)
    return str(items)


def _format_recent_checkins(checkins: list[dict[str, Any]]) -> str:
    if not checkins:
        return "No prior check-ins yet."

    lines = []
    for item in checkins:
        lines.append(
            "\n".join(
                [
                    f"Date: {item.get('date', 'unknown')}",
                    f"Manual context: {item.get('data_missed') or 'none'}",
                    f"Planned training: {item.get('planned_training') or 'not logged'}",
                    f"Sleep: {item.get('sleep_hours', 'N/A')} hrs, quality {item.get('sleep_quality', 'N/A')}/10",
                    f"Recovery: HRV {item.get('hrv_ms', 'N/A')} ms, readiness {item.get('readiness_score', 'N/A')}",
                    f"Subjective status: energy {item.get('energy', 'N/A')}/10, soreness {item.get('soreness', 'N/A')}/10, life load {item.get('stress', 'N/A')}/10",
                    f"Prior-day nutrition: {format_nutrition(item)}",
                    f"Notes: {item.get('notes') or 'none'}",
                ]
            )
        )
    return "\n\n".join(lines)


def format_nutrition(checkin: dict[str, Any]) -> str:
    macros = []
    if checkin.get("nutrition_calories") is not None:
        macros.append(f"{checkin.get('nutrition_calories')} cal")
    if checkin.get("nutrition_protein") is not None:
        macros.append(f"{checkin.get('nutrition_protein')}g protein")
    if checkin.get("nutrition_carbs") is not None:
        macros.append(f"{checkin.get('nutrition_carbs')}g carbs")
    if checkin.get("nutrition_fat") is not None:
        macros.append(f"{checkin.get('nutrition_fat')}g fat")
    if checkin.get("nutrition_notes"):
        macros.append(f"notes: {checkin.get('nutrition_notes')}")
    return ", ".join(macros) if macros else "not logged"


def format_connected_activities(activities: list[dict[str, Any]], today: str) -> str:
    if not activities:
        return "No synced activities available."

    lines = []
    yesterday = (date.fromisoformat(today) - timedelta(days=1)).isoformat()
    for activity in activities[:12]:
        activity_date = activity.get("date") or "unknown date"
        if activity_date == today:
            label = "today"
        elif activity_date == yesterday:
            label = "yesterday"
        else:
            label = "prior"
        parts = [
            f"- Source: Strava",
            f"date: {activity_date} ({label})",
            f"name: {activity.get('activityName') or 'Activity'}",
            f"sport: {activity.get('sport_type') or 'N/A'}",
            f"duration: {activity.get('duration_mins') or 'N/A'} min",
            f"HR: {activity.get('averageHR') or 'N/A'} avg / {activity.get('maxHR') or 'N/A'} max",
            f"distance: {activity.get('distance_m') or 'N/A'}m",
        ]
        if activity.get("relative_effort") is not None:
            parts.append(f"relative effort: {activity.get('relative_effort')}")
        lines.append("; ".join(parts))
    return "\n".join(lines)


def build_system_prompt(profile: dict[str, Any], recent_checkins: list[dict[str, Any]]) -> str:
    name = profile.get("name") or "this athlete"
    memory = profile.get("coach_memory_summary") or "No durable memory summary yet."
    return f"""
You are the Mancuso Method coach: a calm, direct, emotionally aware AI performance coach for women.

Your job is not to be a wearable dashboard. Your job is to interpret patterns across training,
recovery, nutrition, stress, injury constraints, goals, and prior conversations, then turn that
into a clear next action.

COACHING PRINCIPLES:
- Reason from patterns, not isolated metrics.
- Be specific about what to do today.
- Protect injury constraints and recovery.
- Treat nutrition as fuel and adaptation support, not body-size commentary.
- If the user expresses fear around food/body image, stay compassionate and performance-focused.
- Do not diagnose medical issues. Suggest professional support when appropriate.
- Keep tone direct, warm, and athlete-to-coach, not generic wellness app.

ATHLETE PROFILE:
- Name: {name}
- Age: {profile.get('age') or 'Not connected yet'}
- Sex: {profile.get('sex') or 'Not connected yet'}
- Height: {profile.get('height') or 'Not connected yet'}
- Weight: {profile.get('weight') or 'Not connected yet'}
- Primary fitness goals: {_format_list(profile.get('fitness_goals'))}
- Upcoming event: {profile.get('upcoming_event') or 'None reported'}
- Training days: {_format_list(profile.get('training_days'))}
- Wearables/data sources: {_format_list(profile.get('data_sources'))}
- Injuries/limitations: {profile.get('injury_limitations') or 'None reported'}
- Nutrition restrictions: {profile.get('nutrition_restrictions') or 'None reported'}
- Coaching style preference: {profile.get('coaching_style') or 'direct but supportive'}

DURABLE COACH MEMORY:
{memory}

RECENT CHECK-INS:
{_format_recent_checkins(recent_checkins)}
""".strip()


def build_briefing_prompt(profile: dict[str, Any], checkin: dict[str, Any], recent_checkins: list[dict[str, Any]]) -> str:
    connected_activities = checkin.get("connected_activities") or []
    connected_athlete = checkin.get("connected_athlete_profile") or {}
    today = checkin.get('date') or date.today().isoformat()
    has_wearable_recovery = any(
        checkin.get(key) not in [None, ""]
        for key in ["sleep_hours", "sleep_quality", "hrv_ms", "resting_hr", "readiness_score"]
    )
    return f"""
Generate today's Mancuso Method daily briefing for {profile.get('name') or 'this athlete'}.

TODAY: {today}

DATA SOURCE RULES:
- Strava provides training/activity context only. It does not provide sleep, HRV, readiness, or wearable stress.
- If wearable recovery data is unavailable, do not pretend it exists and do not make the briefing about missing metrics.
- For Strava-only users, base guidance on synced activities, sport type, training load, planned training, soreness, energy, life load, prior-day nutrition, and injuries.
- Once Apple Health, Apple Watch, Oura, WHOOP, or Garmin is connected, sleep/readiness/HRV can become core coaching signals.
- Do not say "yesterday" unless a source date is actually yesterday.
- Do not say a workout is completed today unless Strava activity date equals TODAY or the user manually says it was completed today.
- Manual context is not wearable data. Treat it as user-reported context.
- Do not mention sex, weight, or age unless directly relevant to coaching. They are background physiological context, not a headline.

WEARABLE RECOVERY DATA AVAILABLE: {"Yes" if has_wearable_recovery else "No"}

CONNECTED ATHLETE PROFILE:
- Source: Strava
- Name: {connected_athlete.get('name') or profile.get('name') or 'Not connected'}
- Sex: {connected_athlete.get('sex') or profile.get('sex') or 'Not connected'}
- Weight: {connected_athlete.get('weight') or profile.get('weight') or 'Not connected'}
- Age: {profile.get('age') or 'Not connected yet'}

MANUAL CHECK-IN:
- Sleep hours: {checkin.get('sleep_hours', 'N/A')}
- Sleep quality: {checkin.get('sleep_quality', 'N/A')}/10
- HRV: {checkin.get('hrv_ms', 'N/A')} ms
- Resting HR: {checkin.get('resting_hr', 'N/A')}
- Readiness/recovery score: {checkin.get('readiness_score', 'N/A')}
- Energy: {checkin.get('energy', 'N/A')}/10
- Soreness: {checkin.get('soreness', 'N/A')}/10
- Life load: {checkin.get('stress', 'N/A')}/10
- What the data missed: {checkin.get('data_missed') or 'None reported'}
- Planned training today: {checkin.get('planned_training') or 'Not set'}
- Prior-day nutrition: {format_nutrition(checkin)}
- Athlete notes: {checkin.get('notes') or 'None'}

SYNCED ACTIVITY DATA:
{format_connected_activities(connected_activities, today)}

Write a concise daily briefing with these sections:
1. Current Status
2. What The Data Says
3. Today's Training Recommendation
4. Fueling Priority
5. One Thing To Watch
6. Coach's Note

Make it specific enough that the user can act today. Do not mention app features.
""".strip()


def call_claude(system: str, messages: list[dict[str, str]], max_tokens: int = 900) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return demo_reply(messages[-1]["content"] if messages else "")

    try:
        import anthropic
    except ImportError:
        return demo_reply(messages[-1]["content"] if messages else "")

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )
    return response.content[0].text


def generate_briefing(profile: dict[str, Any], checkin: dict[str, Any], recent_checkins: list[dict[str, Any]]) -> str:
    system = build_system_prompt(profile, recent_checkins)
    prompt = build_briefing_prompt(profile, checkin, recent_checkins)
    return call_claude(system, [{"role": "user", "content": prompt}], max_tokens=1000)


def chat_reply(
    profile: dict[str, Any],
    checkin: dict[str, Any],
    recent_checkins: list[dict[str, Any]],
    messages: list[dict[str, str]],
) -> str:
    system = build_system_prompt(profile, recent_checkins)
    today_context = {
        "role": "user",
        "content": (
            "Current check-in context for today's coaching conversation:\n"
            f"{build_briefing_prompt(profile, checkin, recent_checkins)}"
        ),
    }
    context_messages = [today_context] + messages[-12:]
    return call_claude(system, context_messages, max_tokens=650)


def update_memory_summary(
    profile: dict[str, Any],
    checkin: dict[str, Any] | None,
    messages: list[dict[str, str]],
    feedback: dict[str, Any] | None = None,
) -> str:
    existing = profile.get("coach_memory_summary") or "No durable memory yet."
    recent_messages = "\n".join(
        f"{message.get('role', 'unknown')}: {message.get('content', '')[:700]}"
        for message in messages[-10:]
    )
    feedback_text = ""
    if feedback:
        feedback_text = f"\nLATEST USER FEEDBACK:\nRating: {feedback.get('rating') or 'none'}\nText: {feedback.get('text') or 'none'}"

    prompt = f"""
Update the durable coach memory for this athlete.

Rules:
- Keep only information that should help future coaching.
- Preserve injuries, goals, preferences, repeated patterns, nutrition tendencies, what advice worked, and what advice was wrong.
- Do not store trivial one-off details unless they affect coaching.
- Be concise but specific.
- Write in third person. Do not address the athlete directly.

ATHLETE PROFILE:
Name: {profile.get('name') or 'Unknown'}
Goals: {_format_list(profile.get('fitness_goals'))}
Injuries/limitations: {profile.get('injury_limitations') or 'None reported'}
Data sources: {_format_list(profile.get('data_sources'))}

CURRENT MEMORY:
{existing}

LATEST CHECK-IN:
{checkin or 'No check-in available'}

LATEST CONVERSATION:
{recent_messages or 'No conversation available'}
{feedback_text}

Return only the updated memory summary.
""".strip()

    return call_claude(
        "You update concise durable memory for a personal performance coach.",
        [{"role": "user", "content": prompt}],
        max_tokens=500,
    )


def demo_reply(prompt: str) -> str:
    return (
        "Demo mode: add `ANTHROPIC_API_KEY` to the environment to generate live coaching.\n\n"
        "**Current Status**\n"
        "Use today's activity data, soreness, energy, life load, and planned training together. "
        "For Strava-only users, sleep and readiness stay out of the analysis until a wearable is connected.\n\n"
        "**Today's Training Recommendation**\n"
        "Choose the session that supports consistency tomorrow, not the one that only proves effort today.\n\n"
        "**Fueling Priority**\n"
        "Anchor each meal with protein and add carbs around training. Do not let a busy day turn into an "
        "accidental deficit.\n\n"
        "**Coach's Note**\n"
        "The beta coach is wired correctly; live model output will replace this once the API key is set."
    )
