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


def _parse_date(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return date.today()


def _date_label(value: str | None) -> str:
    day = _parse_date(value)
    return day.strftime("%A, %B %-d, %Y")


def _schedule_context(profile: dict[str, Any], today: str) -> str:
    day = _parse_date(today)
    tomorrow = day + timedelta(days=1)
    return "\n".join(
        [
            f"Today weekday: {day.strftime('%A')}",
            f"Tomorrow: {tomorrow.strftime('%A, %B %-d, %Y')}",
            f"Training days: {_format_list(profile.get('training_days'))}",
        ]
    )


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


def _value_or_na(value: Any, suffix: str = "") -> str:
    if value in [None, ""]:
        return "N/A"
    return f"{value}{suffix}"


def format_apple_health(snapshot: dict[str, Any] | None) -> str:
    if not snapshot:
        return "No Apple Health snapshot has been received yet."

    workouts = snapshot.get("workouts") or snapshot.get("exercise_activities") or []
    workout_lines = []
    for workout in workouts[:8]:
        workout_lines.append(
            "; ".join(
                [
                    f"- {workout.get('activity_type') or workout.get('type') or 'Workout'}",
                    f"start: {workout.get('start') or workout.get('start_time') or 'N/A'}",
                    f"duration: {_value_or_na(workout.get('duration_minutes') or workout.get('duration_mins'), ' min')}",
                    f"calories: {_value_or_na(workout.get('active_energy_kcal') or workout.get('calories'), ' kcal')}",
                    f"avg HR: {_value_or_na(workout.get('average_hr') or workout.get('averageHR'), ' bpm')}",
                    f"distance: {_value_or_na(workout.get('distance_m') or workout.get('distance'), '')}",
                ]
            )
        )

    return "\n".join(
        [
            f"Snapshot date: {snapshot.get('date') or 'N/A'}",
            f"Age: {_value_or_na(snapshot.get('age'))}",
            f"Sex: {_value_or_na(snapshot.get('sex'))}",
            f"Weight: {_value_or_na(snapshot.get('weight'))}",
            f"Daily move / active energy: {_value_or_na(snapshot.get('daily_move_kcal') or snapshot.get('active_energy_kcal'), ' kcal')}",
            f"Exercise time: {_value_or_na(snapshot.get('exercise_minutes'), ' min')}",
            f"Cardio fitness / VO2 max: {_value_or_na(snapshot.get('cardio_fitness_vo2max'))}",
            f"Sleep score: {_value_or_na(snapshot.get('sleep_score'))}",
            f"Sleep duration: {_value_or_na(snapshot.get('sleep_duration_minutes'), ' min')}",
            f"HRV: {_value_or_na(snapshot.get('hrv_ms'), ' ms')}",
            f"Resting HR: {_value_or_na(snapshot.get('resting_hr'), ' bpm')}",
            f"Workouts:\n{chr(10).join(workout_lines) if workout_lines else 'No workouts reported in this snapshot.'}",
        ]
    )


def format_recent_apple_health(snapshots: list[dict[str, Any]]) -> str:
    if not snapshots:
        return "No Apple Health history yet."
    lines = []
    for item in snapshots[:7]:
        workouts = item.get("workouts") or item.get("exercise_activities") or []
        workout_summary = ", ".join(
            (workout.get("activity_type") or workout.get("type") or "Workout")
            for workout in workouts[:4]
        )
        lines.append(
            "\n".join(
                [
                    f"Date: {item.get('date', 'unknown')}",
                    f"Sleep score: {_value_or_na(item.get('sleep_score'))}; sleep duration: {_value_or_na(item.get('sleep_duration_minutes'), ' min')}",
                    f"HRV: {_value_or_na(item.get('hrv_ms'), ' ms')}; resting HR: {_value_or_na(item.get('resting_hr'), ' bpm')}",
                    f"Move: {_value_or_na(item.get('daily_move_kcal') or item.get('active_energy_kcal'), ' kcal')}; exercise: {_value_or_na(item.get('exercise_minutes'), ' min')}",
                    f"Activities: {workout_summary or 'none'}",
                ]
            )
        )
    return "\n\n".join(lines)


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
            f"- Source: {activity.get('source') or 'Connected activity app'}",
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
You are the Mancuso Method coach: a calm, direct, emotionally aware AI performance coach.

Your job is not to be a wearable dashboard. Your job is to interpret the athlete's Apple Health,
training, recovery, nutrition, stress, injury constraints, goals, and prior conversations, then turn
that data into a clear personalized plan for today.

COACHING PRINCIPLES:
- Reason from patterns, not isolated metrics.
- Be specific about what to do today.
- Protect injury constraints and recovery.
- Treat nutrition as fuel and adaptation support, not body-size commentary.
- If the user expresses fear around food/body image, stay compassionate and performance-focused.
- Do not diagnose medical issues. Suggest professional support when appropriate.
- Keep tone direct, warm, and athlete-to-coach, not generic wellness app.
- The user's product vision is a conversational coach. Never sound like a dashboard explaining metrics.
- Use age and sex as physiological context when useful, but do not call them out unless relevant.

ATHLETE PROFILE:
- Name: {name}
- Age: {profile.get('age') or 'Not connected yet'}
- Sex: {profile.get('sex') or 'Not connected yet'}
- Weight: {profile.get('weight') or 'Not connected yet'}
- Training goals: {_format_list(profile.get('training_goals') or profile.get('fitness_goals'))}
- Upcoming competition: {profile.get('upcoming_competition') or profile.get('upcoming_event') or 'None reported'}
- Competition date: {profile.get('competition_date') or 'None reported'}
- Experience level: {profile.get('experience_level') or 'Not entered'}
- Wearables/data sources: {_format_list(profile.get('data_sources'))}
- Injuries/limitations: {profile.get('injury_limitations') or 'None reported'}
- Nutrition restrictions: {profile.get('nutrition_restrictions') or 'None reported'}

DURABLE COACH MEMORY:
{memory}

RECENT CHECK-INS:
{_format_recent_checkins(recent_checkins)}
""".strip()


def build_briefing_prompt(profile: dict[str, Any], checkin: dict[str, Any], recent_checkins: list[dict[str, Any]]) -> str:
    connected_activities = checkin.get("connected_activities") or []
    apple_snapshot = checkin.get("apple_health") or {}
    recent_apple = checkin.get("recent_apple_health") or []
    today = checkin.get('date') or date.today().isoformat()
    event = profile.get("upcoming_competition") or profile.get("upcoming_event") or ""
    competition_date = profile.get("competition_date") or ""
    event_line = "No event countdown available."
    if event and competition_date:
        try:
            days_out = (_parse_date(competition_date) - _parse_date(today)).days
            event_line = f"{days_out} days to {event}" if days_out >= 0 else f"{event} has passed"
        except Exception:
            event_line = event
    elif event:
        event_line = event

    return f"""
Generate today's Mancuso Method morning briefing for {profile.get('name') or 'this athlete'}.

TODAY: {_date_label(today)} ({today})
EVENT CONTEXT: {event_line}

DATA SOURCE RULES:
- Apple Health / Apple Watch is the primary beta data source.
- Do not invent unavailable data. If Apple Health has not sent a field yet, use the manual check-in and say less, not more.
- The coach should interpret what the metrics mean for this athlete today. Do not explain the app or list raw data like a dashboard.
- Do not say "yesterday" unless the source date is actually yesterday.
- Do not say a workout is completed today unless Apple Health activity date equals TODAY, connected activity date equals TODAY, or the user manually says it was completed today.
- Use prior conversation memory, injury limitations, goals, nutrition, and recent trend context as the heart of the coaching.
- Do not mention sex, weight, or age unless directly relevant to coaching. They are background physiological context, not a headline.
- Today's recommendation should be specific, with duration and intensity when training is appropriate.

ATHLETE PROFILE:
- Name: {profile.get('name') or 'Unknown'}
- Phone: {profile.get('phone') or 'Not entered'}
- Email: {profile.get('email') or 'Not entered'}
- Training goals: {_format_list(profile.get('training_goals') or profile.get('fitness_goals'))}
- Upcoming competition: {event or 'None reported'}
- Competition date: {competition_date or 'None reported'}
- Experience level: {profile.get('experience_level') or 'Not entered'}
- Injuries/limitations: {profile.get('injury_limitations') or 'None reported'}
- Nutrition restrictions: {profile.get('nutrition_restrictions') or 'None reported'}

APPLE HEALTH / APPLE WATCH SNAPSHOT:
{format_apple_health(apple_snapshot)}

RECENT APPLE HEALTH HISTORY:
{format_recent_apple_health(recent_apple)}

MANUAL CHECK-IN:
- Energy: {checkin.get('energy', 'N/A')}/10
- Soreness: {checkin.get('soreness', 'N/A')}/10
- Life load: {checkin.get('stress', 'N/A')}/10
- Prior-day nutrition: {format_nutrition(checkin)}
- Athlete notes: {checkin.get('notes') or 'None'}

LEGACY CONNECTED ACTIVITY DATA IF PRESENT:
{format_connected_activities(connected_activities, today)}

Write the briefing in this exact structure:

# 🌅 Morning Briefing — {_parse_date(today).strftime('%A, %B %-d')}
### {profile.get('name') or 'Athlete'} | {event_line}

## 1. Recovery Status
1-2 direct sentences.

## 2. What the Data Says
2-3 bullets or short paragraphs with the most important signals.

## 3. Today's Training Recommendation
Specific recommendation with duration and intensity. If today's workout is already logged, say that and shift to recovery execution.

## 4. Nutrition
Actionable advice based on prior-day calories, protein, carbs, fat, restrictions, and today's training.

## 5. One Thing to Watch Today
One specific risk, limit, or signal to monitor.

## 6. Coach's Note
1-2 honest, motivating sentences.

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

    client = anthropic.Anthropic(
        api_key=api_key,
        timeout=float(os.getenv("ANTHROPIC_TIMEOUT", "30")),
    )
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
        "# 🌅 Morning Briefing\n\n"
        "## 1. Recovery Status\n"
        "Use Apple Health recovery data, subjective energy, soreness, and life load together. Do not reduce the athlete to a score.\n\n"
        "## 2. What the Data Says\n"
        "The coach will explain what sleep, HRV, movement, workouts, nutrition, and recent conversation history mean for this person today.\n\n"
        "## 3. Today's Training Recommendation\n"
        "Choose the session that supports adaptation, consistency, and injury constraints.\n\n"
        "## 4. Nutrition\n"
        "Anchor the day with enough calories, protein, carbs, and fat to support training and recovery.\n\n"
        "## 5. One Thing to Watch Today\n"
        "Watch the most important signal for this athlete, not every metric at once.\n\n"
        "## 6. Coach's Note\n"
        "The beta coach is wired for the Apple Health direction; live model output will replace this once the API key is set."
    )
