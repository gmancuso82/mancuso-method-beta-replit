# Mancuso Method Beta

Standalone beta app for test users.

This is intentionally separate from Gina's personal `health-llm` Python coach. It does not use Garmin credentials, Oura credentials, personal token files, or Gina's local conversation history.

## What It Does

- Creates a lightweight athlete profile only for data the connected apps cannot infer
- Starts from Apple Health / Apple Watch because that is where beta users have the body data the coach needs
- Uses Apple Health data as the source of truth when available, and clearly separates synced data from manual context
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

## Beta Integration Roadmap

1. **Apple Health / Apple Watch first** — the beta market user needs sleep, HRV, weight, daily move, exercise time, cardio fitness, and workouts. This requires a native iOS app using HealthKit.
2. **Replit as the coach backend** — Replit hosts the profile, Apple Health snapshot endpoint, daily briefing generation, chat, memory, feedback, and admin review.
3. **TestFlight beta** — first users install the iPhone app, grant HealthKit permission, and use the chat-first coach flow.
4. **Oura / WHOOP / Garmin later** — add these only when they strengthen the coach's body-data layer for the right users.
5. **Strava / Polar as optional activity context** — keep legacy code available, but do not make it a primary beta path because activity-only data is not the product.

## Beta V1 Check-in

Until the iPhone app is sending Apple Health data, the beta asks only for:

- Energy 1-10
- Soreness 1-10
- Life load 1-10
- Prior-day calories
- Prior-day protein, carbs, and fat

The coach must use Apple Health for age, sex, daily move, daily exercise time, cardio fitness, sleep, weight, HRV, and exercise activities once the iOS app is connected.

## Apple Health Snapshot API

The iPhone app sends daily HealthKit data to:

```text
POST /api/apple-health/snapshot
```

See [ios/API_CONTRACT.md](ios/API_CONTRACT.md) for the payload. If `IOS_APP_API_KEY` is set on Replit, the iPhone app must send it in the `X-MM-BETA-KEY` header.

## Strava Setup

Strava is legacy/optional and is not part of the primary Apple Health beta path.

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

Polar is legacy/optional and is not part of the primary Apple Health beta path.

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

For hosted testing, send the Replit equivalent of the fresh tester link to each new tester until the iPhone app is ready. The admin page shows profiles, Apple Health snapshots, check-ins, conversations, and feedback.

If `ANTHROPIC_API_KEY` is not set, the app runs in demo mode.

For local live coaching, create a private `.env` file from `.env.example` and add `ANTHROPIC_API_KEY`.

## Replit

Import this folder as a separate Replit project. Add `ANTHROPIC_API_KEY` as a Replit secret. Add `IOS_APP_API_KEY` before giving the iPhone app to testers.

```bash
ANTHROPIC_API_KEY=your_anthropic_key
IOS_APP_API_KEY=shared_secret_for_ios_app
APP_BASE_URL=your_replit_app_url
```

Suggested run command:

```bash
python app.py
```

Later beta integrations can use the existing Strava/Polar files without touching Gina's private Garmin/Oura app.
