# Mancuso Method Beta iOS

This folder holds the iPhone/TestFlight starter for the Apple Health beta path.

## Current Blocker

This Mac currently has Apple Command Line Tools active, not full Xcode. TestFlight requires full Xcode.

Install Xcode from the Mac App Store, open it once, then run:

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

After that, `xcodebuild -version` and `xcrun simctl list devices available` should work.

## Xcode Project Setup

1. Open Xcode.
2. Create a new iOS App project.
3. Product name: `MancusoMethodBeta`.
4. Interface: SwiftUI.
5. Language: Swift.
6. Add the Swift files from `ios/Sources/` into the app target.
7. Add HealthKit in Signing & Capabilities.
8. Add these Info.plist values:
   - `NSHealthShareUsageDescription`
   - Value: `Mancuso Method reads Apple Health data to generate your personalized daily coaching briefing.`
9. Add your Replit URL and iOS shared key in a local `AppConfig.swift`.

Do not commit real secrets.

## TestFlight Setup

1. Join the Apple Developer Program if needed.
2. Create the app record in App Store Connect.
3. Archive from Xcode.
4. Upload to App Store Connect.
5. Add TestFlight test information.
6. Invite the first internal testers.
7. Move to external testers once the first build is stable.

## Beta V1 User Flow

1. User opens iPhone app.
2. User enters name, phone, email, goals, event, experience level, limitations, and nutrition restrictions.
3. User grants Apple Health permission.
4. App sends profile to Replit.
5. App sends daily Apple Health snapshot to Replit.
6. User generates morning briefing and chats with coach.
