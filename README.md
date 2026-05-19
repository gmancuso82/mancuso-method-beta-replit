# Mancuso Method Beta

Standalone beta app for test users.

This is intentionally separate from Gina's personal `health-llm` Python coach. It does not use Garmin credentials, Oura credentials, personal token files, or Gina's local conversation history.

## What It Does

- Creates a lightweight athlete profile only for data the connected apps cannot infer
- Starts from connectable fitness sources: Strava, Oura, Apple Watch, and Apple Health
- Uses device/app data as the source of truth for demographics, workouts, sleep, recovery, and trends when available
- Generates a daily morning briefing as the main experience
- Supports follow-up coach chat in a mostly conversational interface
- Can deliver weekly schedule and nutrition guidance through chat instead of dashboard-heavy screens
- Saves feedback for product learning
- Stores beta data as local JSON under `data/`

## Product Direction

This is not an Oura clone, Garmin clone, or wearable dashboard. The beta app is a conversational coaching layer that sits above wearable and fitness-app data. The user should log in, let the app update from their connected sources, read the morning briefing, and then talk to the coach.

Gina's personal Python coach is the reference implementation for coaching behavior. This beta app is a separate test-user version built with the same coaching model but without Gina's Garmin/Oura credentials, token files, or personal conversation history.

See [PRODUCT_BASELINE.md](PRODUCT_BASELINE.md) for the product principles that should guide all beta decisions.

## Integration Roadmap

1. **Strava first** — first beta users can connect Strava so the coach can read recent workouts, sport type, distance, duration, pace, heart rate when available, sex, and weight when available.
2. **Apple Health / Apple Watch planning now** — Apple HealthKit is the long-term path for Apple Watch profile, workout, sleep, and heart data. Web beta can use Strava as the bridge while the native HealthKit path is planned.
3. **Oura next** — Oura OAuth can add readiness, sleep, HRV, temperature, age, height, weight, and biological sex through Oura API scopes.
4. **WHOOP after Oura** — WHOOP OAuth can add recovery, strain, sleep, workout, profile, and body measurement data.
5. **Garmin later / pro-athlete beta exception** — Garmin is difficult for hosted beta because of MFA and IP limits. For a professional athlete in beta, daily code entry is acceptable if the value is high enough.

## Strava Setup

Set these environment variables locally or as Replit secrets:

```bash
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
APP_BASE_URL=http://127.0.0.1:5002
```

For Replit, `APP_BASE_URL` should be the Replit app URL and the Strava app callback should be:

```text
{APP_BASE_URL}/api/integrations/strava/callback
```

## Run Locally

```bash
cd /Users/ginamancuso/Documents/Codex/mancuso-method-beta
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
python app.py
```

Open:

```text
http://127.0.0.1:5002
```

If `ANTHROPIC_API_KEY` is not set, the app runs in demo mode.

## Replit

Import this folder as a separate Replit project. Add `ANTHROPIC_API_KEY` as a Replit secret.

Suggested run command:

```bash
python app.py
```

Later beta integrations can add `strava_data.py` without touching Gina's private Garmin/Oura app.
