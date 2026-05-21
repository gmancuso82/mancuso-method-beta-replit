# Mancuso Method Beta — Product Baseline

This app is not a wearable dashboard, Garmin clone, Oura clone, or generic fitness tracker.

It is a connect-first conversational coaching platform that turns wearable, fitness, nutrition, recovery, injury, and life-context data into personal guidance in plain language.

## North Star

Every athlete should feel:

> My coach understands my body, my life, and my goals better every day.

The user should not have to interpret sleep scores, HRV values, readiness numbers, strain scores, calorie gaps, or training-load charts. The app should interpret those signals and explain what they mean for that person today.

## Core Product Belief

Metrics are ingredients. The coach is the product.

The goal is not to show:

- Sleep 86
- HRV 42
- Readiness 77
- Calories 1,420
- Training load high

The goal is to say:

> Here is what your body is telling us today. Here is what to train. Here is what to eat. Here is what to watch. Here is how this fits your goal, your history, your stress, your injuries, and your life.

Then the user talks to the coach.

## Baseline Test App Priorities

1. The experience starts with connecting data sources, not manually building a dashboard.
2. Profile setup only asks for information that connected apps cannot reliably infer.
3. Daily use should feel like opening a coach conversation.
4. The morning briefing is the main daily product surface.
5. Weekly schedule, training adjustments, and nutrition guidance should be delivered conversationally.
6. Visuals are secondary and should support clarity only when useful.
7. The app should learn each user's personal hierarchy of signals.
8. The app should preserve memory over time so coaching improves across weeks.

## Future Coaching Intelligence Notes

- The coach should know what time the briefing is being generated and use that in context. Example: if the briefing is pulled at 2pm and a planned morning spin class has not been logged, the coach should not talk as if the athlete is still likely to do that morning session. It should recognize that the planned window probably passed, ask what happened if needed, and adjust the rest of the day accordingly.

## Personal Signal Hierarchy

The app should not assume one device is the universal source of truth.

For each user, it should learn:

- Which device is most reliable for sleep
- Which device is most reliable for readiness/recovery
- Which device best captures workout load
- Which HRV source predicts the user's actual performance and recovery best
- Which signals are noisy and should be downweighted
- Which subjective inputs should override wearable data

For Gina right now, the working hypothesis is:

- Sleep may be strongest from Garmin
- Readiness may be strongest from Oura
- Training/activity may come from Garmin, Strava, and Polar
- Heart-rate effort context may be strongest from Polar for early testers who use it
- Apple Health may become the best long-term body/profile bridge
- Subjective hip status from conversation is critical and cannot be replaced by a wearable

For another athlete, the hierarchy may be completely different.

## Integration Roadmap

1. Strava first for activity sync and low-friction test-user onboarding.
2. Polar in the first rollout for users who have it, because heart-rate effort and intensity context can be more coaching-relevant than activity type alone.
3. Oura for sleep, readiness, HRV, temperature, and profile context.
4. WHOOP for recovery, strain, sleep, and body measurement data.
5. Plan Apple Health and Apple Watch in parallel because they are essential to the broader consumer product, but technically more complex than OAuth web integrations.
6. Add Garmin later, with the understanding that serious/pro beta users may tolerate daily MFA/code entry if the coaching value is high enough.
7. Start nutrition manually with prior-day calories, protein, carbs, and fat; evaluate food integrations after the coaching loop works.

## What Makes This Different

Wearables collect data. Mancuso Method interprets it.

The product should help users answer:

- What does this mean for me?
- Should I train today?
- How hard?
- What should I eat?
- What should I watch?
- How does this connect to my goal?
- What pattern is my coach seeing that I cannot see?

## Development Rule

Gina calls the product shots from day one. The beta should be built in small steps, but every step should move toward the end goal: individual personal life, fitness, nutrition, and recovery coaches for athletes and everyday active people.
