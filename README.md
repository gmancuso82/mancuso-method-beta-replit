# Mancuso Method Beta

Standalone beta app for test users.

This is intentionally separate from Gina's personal `health-llm` Python coach. It does not use Garmin credentials, Oura credentials, personal token files, or Gina's local conversation history.

## What It Does

- Creates a lightweight athlete profile only for data the connected apps cannot infer
- Starts from connectable fitness sources: Strava first, Polar next, then Oura/WHOOP/Apple Health
- Uses device/app data as the source of truth when available, and clearly separates synced data from manual context
- Generates a daily morning briefing as the main experience
- Supports follow-up coach chat in a mostly conversational interface
- Preserves a durable coach memory summary on each athlete profile
- Can deliver weekly schedule and nutrition guidance through chat instead of dashboard-heavy screens
- Saves feedback for product learning
- Stores beta data as local JSON under `data/`

## Product Direction

This is not an Oura clone, Garmin clone, or wearable dashboard. The beta app is a conversational coaching layer that sits above wearable and fitness-app data. The user should log in, let the app update from their connected sources, read the morning briefing, and then talk to the coach.

Gina's personal Python coach is the reference implementation for coaching behavior. This beta app is a separate test-user version built with the same coaching model but without Gina's Garmin/Oura credentials, token files, or personal conversation history.

See [PRODUCT_BASELINE.md](PRODUCT_BASELINE.md) for the product principles that should guide all beta decisions.

## Integration Roadmap

1. **Strava first** — first beta users can connect Strava so the coach can read recent workouts, sport type, distance, duration, pace, heart rate when available, sex, and weight when available.
2. **Polar next** — early testers with Polar can provide stronger heart-rate, effort, and intensity context than Strava alone.
3. **Oura next** — Oura OAuth can add readiness, sleep, HRV, temperature, and recovery context.
4. **WHOOP after Oura** — WHOOP OAuth can add recovery, strain, sleep, workout, profile, and body measurement data.
5. **Apple Health / Apple Watch parallel plan** — Apple HealthKit is the long-term path for Apple Watch profile, workout, sleep, and heart data, but it is more complex than web OAuth integrations.
6. **Garmin later / pro-athlete beta exception** — Garmin is difficult for hosted beta because of MFA and IP limits. For a professional athlete in beta, daily code entry is acceptable if the value is high enough.

## Beta V1 Check-in

Until recovery integrations are connected, the beta asks for:

- Energy 1-10
- Soreness 1-10
- Life load 1-10
- Prior-day calories
- Prior-day protein, carbs, and fat
- Planned training
- What the synced data missed

The coach must not infer sleep, readiness, HRV, or stress from Strava.

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

## Polar Setup

Create a Polar AccessLink application, then set these environment variables locally or as Replit secrets:

```bash
POLAR_CLIENT_ID=your_client_id
POLAR_CLIENT_SECRET=your_client_secret
APP_BASE_URL=http://127.0.0.1:5002
```

For local testing, the Polar redirect URL should be:

```text
http://127.0.0.1:5002/api/integrations/polar/callback
```

## Run Locally

```bash
cd /Users/ginamancuso/Documents/Codex/mancuso-method-beta
/opt/miniconda3/bin/python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5002
```

Fresh local tester profile:

```text
http://127.0.0.1:5002/?new=1
```

Admin review page:

```text
http://127.0.0.1:5002/admin
```

For hosted testing, send the Replit equivalent of the fresh tester link to each new tester. The admin page shows profiles, connected sources, check-ins, conversations, and feedback.

If `ANTHROPIC_API_KEY` is not set, the app runs in demo mode.

For local live coaching, create a private `.env` file from `.env.example` and add `ANTHROPIC_API_KEY`.

## Replit

Import this folder as a separate Replit project. Add `ANTHROPIC_API_KEY` as a Replit secret. Add Strava secrets when testing Strava connection:

```bash
STRAVA_CLIENT_ID=your_client_id
STRAVA_CLIENT_SECRET=your_client_secret
APP_BASE_URL=your_replit_app_url
```

Suggested run command:

```bash
python app.py
```

Later beta integrations can add `strava_data.py` without touching Gina's private Garmin/Oura app.
