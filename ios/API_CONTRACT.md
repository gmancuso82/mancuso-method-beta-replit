# Mancuso Method iOS API Contract

The iPhone app is the Apple Health data pipe. Replit is the coach backend.

## Base URL

Use the deployed Replit app URL:

```text
https://your-replit-app-url
```

## Authentication

If `IOS_APP_API_KEY` is set in Replit secrets, send it with every iOS request:

```http
X-MM-BETA-KEY: your_shared_secret
```

## Create Or Update Profile

```http
POST /api/profile
Content-Type: application/json
```

```json
{
  "user_id": "email-or-generated-id",
  "name": "Gina Mancuso",
  "phone": "555-0100",
  "email": "gina@example.com",
  "training_goals": ["Hyrox", "strength", "endurance"],
  "upcoming_competition": "Hyrox Open",
  "competition_date": "2026-07-25",
  "experience_level": "Advanced",
  "injury_limitations": "Left hip sensitivity",
  "nutrition_restrictions": "None",
  "data_sources": ["Apple Health"]
}
```

## Send Daily Apple Health Snapshot

```http
POST /api/apple-health/snapshot
Content-Type: application/json
```

```json
{
  "user_id": "gina@example.com",
  "date": "2026-05-24",
  "age": 43,
  "sex": "female",
  "daily_move_kcal": 620,
  "exercise_minutes": 54,
  "cardio_fitness_vo2max": 42.1,
  "sleep_score": 82,
  "sleep_duration_minutes": 455,
  "weight": 145,
  "hrv_ms": 48,
  "resting_hr": 57,
  "workouts": [
    {
      "activity_type": "Strength Training",
      "start": "2026-05-24T07:15:00",
      "duration_minutes": 42,
      "active_energy_kcal": 260,
      "average_hr": 118,
      "distance_m": null
    }
  ]
}
```

## Manual Daily Check-in

Apple Health supplies body and activity data. The user only adds subjective context and prior-day nutrition.

```http
POST /api/checkin
Content-Type: application/json
```

```json
{
  "user_id": "gina@example.com",
  "date": "2026-05-24",
  "energy": 7,
  "soreness": 3,
  "stress": 4,
  "nutrition_calories": 1850,
  "nutrition_protein": 140,
  "nutrition_carbs": 180,
  "nutrition_fat": 58,
  "nutrition_notes": "Felt fueled yesterday",
  "notes": "Busy afternoon schedule"
}
```

## Generate Morning Briefing

```http
POST /api/briefing
Content-Type: application/json
```

```json
{
  "user_id": "gina@example.com"
}
```

The response contains the morning briefing in the Mancuso Method format.

## Chat With Coach

```http
POST /api/chat
Content-Type: application/json
```

```json
{
  "user_id": "gina@example.com",
  "message": "My hip feels tired but not painful. Should I still train?"
}
```

## Feedback

```http
POST /api/feedback
Content-Type: application/json
```

```json
{
  "user_id": "gina@example.com",
  "date": "2026-05-24",
  "rating": "off",
  "text": "The coach assumed I trained, but I had not worked out yet."
}
```

## HealthKit Fields To Request

- Date of birth, biological sex, body mass
- Active energy burned
- Apple Exercise Time
- VO2 max / cardio fitness
- Sleep analysis
- Heart rate variability
- Resting heart rate
- Workouts, including type, start time, duration, calories, distance, and heart rate when available
