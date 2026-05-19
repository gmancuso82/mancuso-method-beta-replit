from __future__ import annotations

import os
from datetime import date
from typing import Any

try:
    import anthropic
except ImportError:  # pragma: no cover - useful before dependencies are installed
    anthropic = None


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
                    f"Workout: {item.get('workout_done') or item.get('planned_training') or 'not logged'}",
                    f"Sleep: {item.get('sleep_hours', 'N/A')} hrs, quality {item.get('sleep_quality', 'N/A')}/10",
                    f"Recovery: HRV {item.get('hrv_ms', 'N/A')} ms, readiness {item.get('readiness_score', 'N/A')}",
                    f"Soreness/stress: soreness {item.get('soreness', 'N/A')}/10, stress {item.get('stress', 'N/A')}/10",
                    f"Nutrition: {item.get('nutrition_notes') or 'not logged'}",
                    f"Notes: {item.get('notes') or 'none'}",
                ]
            )
        )
    return "\n\n".join(lines)


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
    return f"""
Generate today's Mancuso Method daily briefing for {profile.get('name') or 'this athlete'}.

TODAY: {checkin.get('date') or date.today().isoformat()}

TODAY'S CHECK-IN:
- Sleep hours: {checkin.get('sleep_hours', 'N/A')}
- Sleep quality: {checkin.get('sleep_quality', 'N/A')}/10
- HRV: {checkin.get('hrv_ms', 'N/A')} ms
- Resting HR: {checkin.get('resting_hr', 'N/A')}
- Readiness/recovery score: {checkin.get('readiness_score', 'N/A')}
- Soreness: {checkin.get('soreness', 'N/A')}/10
- Stress/life load: {checkin.get('stress', 'N/A')}/10
- Menstrual/cycle note: {checkin.get('cycle_note') or 'None'}
- Yesterday/today workout done: {checkin.get('workout_done') or 'None logged'}
- Planned training today: {checkin.get('planned_training') or 'Not set'}
- Nutrition notes: {checkin.get('nutrition_notes') or 'Not logged'}
- Athlete notes: {checkin.get('notes') or 'None'}

CONNECTED ACTIVITY DATA:
{_format_list([
    f"{a.get('date')}: {a.get('activityName')} ({a.get('duration_mins')} min, HR {a.get('averageHR') or 'N/A'}, distance {a.get('distance_m') or 'N/A'}m)"
    for a in connected_activities[:10]
])}

Write a concise daily briefing with these sections:
1. Recovery Status
2. What The Data Says
3. Today's Training Recommendation
4. Fueling Priority
5. One Thing To Watch
6. Coach's Note

Make it specific enough that the user can act today. Do not mention app features.
""".strip()


def call_claude(system: str, messages: list[dict[str, str]], max_tokens: int = 900) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or anthropic is None:
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


def demo_reply(prompt: str) -> str:
    return (
        "Demo mode: add `ANTHROPIC_API_KEY` to the environment to generate live coaching.\n\n"
        "**Recovery Status**\n"
        "Use today's sleep, soreness, stress, and planned training together. If two or more signals "
        "are yellow, reduce intensity and keep the session technical or aerobic.\n\n"
        "**Today's Training Recommendation**\n"
        "Choose the session that supports consistency tomorrow, not the one that only proves effort today.\n\n"
        "**Fueling Priority**\n"
        "Anchor each meal with protein and add carbs around training. Do not let a busy day turn into an "
        "accidental deficit.\n\n"
        "**Coach's Note**\n"
        "The beta coach is wired correctly; live model output will replace this once the API key is set."
    )
