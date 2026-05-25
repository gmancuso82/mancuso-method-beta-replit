import SwiftUI

struct ContentView: View {
    @StateObject private var healthKit = HealthKitManager()
    private let api = APIClient()

    @State private var name = ""
    @State private var phone = ""
    @State private var email = ""
    @State private var goals = ""
    @State private var competition = ""
    @State private var competitionDate = ""
    @State private var experienceLevel = "Beginner"
    @State private var injuries = ""
    @State private var nutritionRestrictions = ""

    @State private var energy = ""
    @State private var soreness = ""
    @State private var lifeLoad = ""
    @State private var calories = ""
    @State private var protein = ""
    @State private var carbs = ""
    @State private var fat = ""
    @State private var nutritionNotes = ""
    @State private var notes = ""

    @State private var briefing = ""
    @State private var status = "Ready"
    @State private var isBusy = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Profile") {
                    TextField("Name", text: $name)
                    TextField("Phone number", text: $phone)
                        .keyboardType(.phonePad)
                    TextField("Email", text: $email)
                        .keyboardType(.emailAddress)
                        .textInputAutocapitalization(.never)
                    TextField("Training goals", text: $goals, axis: .vertical)
                    TextField("Upcoming competition", text: $competition)
                    TextField("Competition date YYYY-MM-DD", text: $competitionDate)
                    Picker("Experience level", selection: $experienceLevel) {
                        Text("Beginner").tag("Beginner")
                        Text("Intermediate").tag("Intermediate")
                        Text("Advanced").tag("Advanced")
                    }
                    TextField("Injury or limitations", text: $injuries, axis: .vertical)
                    TextField("Nutrition restrictions", text: $nutritionRestrictions, axis: .vertical)
                }

                Section("Apple Health") {
                    Button("Allow Apple Health Access") {
                        Task { await authorizeHealth() }
                    }
                    Button("Sync Today") {
                        Task { await syncToday() }
                    }
                    Text(status)
                        .foregroundStyle(.secondary)
                }

                Section("Daily Check-in") {
                    TextField("Energy 1-10", text: $energy)
                        .keyboardType(.numberPad)
                    TextField("Soreness 1-10", text: $soreness)
                        .keyboardType(.numberPad)
                    TextField("Life load 1-10", text: $lifeLoad)
                        .keyboardType(.numberPad)
                    TextField("Calories yesterday", text: $calories)
                        .keyboardType(.numberPad)
                    TextField("Protein g", text: $protein)
                        .keyboardType(.numberPad)
                    TextField("Carbs g", text: $carbs)
                        .keyboardType(.numberPad)
                    TextField("Fat g", text: $fat)
                        .keyboardType(.numberPad)
                    TextField("Nutrition notes", text: $nutritionNotes, axis: .vertical)
                    TextField("Anything else", text: $notes, axis: .vertical)
                }

                Section {
                    Button(isBusy ? "Working..." : "Generate Briefing") {
                        Task { await generateBriefing() }
                    }
                    .disabled(isBusy || userId.isEmpty)
                }

                if !briefing.isEmpty {
                    Section("Morning Briefing") {
                        Text(briefing)
                    }
                }
            }
            .navigationTitle("Mancuso Method")
        }
    }

    private var userId: String {
        let trimmedEmail = email.trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmedEmail.isEmpty { return trimmedEmail }
        return name.trimmingCharacters(in: .whitespacesAndNewlines).lowercased().replacingOccurrences(of: " ", with: "-")
    }

    private func profile() -> AthleteProfile {
        AthleteProfile(
            userId: userId,
            name: name,
            phone: phone,
            email: email,
            trainingGoals: goals.split(separator: ",").map { $0.trimmingCharacters(in: .whitespacesAndNewlines) },
            upcomingCompetition: competition,
            competitionDate: competitionDate,
            experienceLevel: experienceLevel,
            injuryLimitations: injuries,
            nutritionRestrictions: nutritionRestrictions
        )
    }

    private func authorizeHealth() async {
        await run("Requesting Apple Health access") {
            try await healthKit.requestAuthorization()
            status = "Apple Health access ready"
        }
    }

    private func syncToday() async {
        await run("Syncing Apple Health") {
            try await api.saveProfile(profile())
            let snapshot = try await healthKit.buildTodaySnapshot(userId: userId)
            try await api.sendAppleHealthSnapshot(snapshot)
            status = "Apple Health synced for today"
        }
    }

    private func generateBriefing() async {
        await run("Generating briefing") {
            try await api.saveProfile(profile())
            let checkin = CheckinPayload(
                userId: userId,
                date: Self.todayString(),
                energy: Int(energy),
                soreness: Int(soreness),
                stress: Int(lifeLoad),
                nutritionCalories: Int(calories),
                nutritionProtein: Int(protein),
                nutritionCarbs: Int(carbs),
                nutritionFat: Int(fat),
                nutritionNotes: nutritionNotes,
                notes: notes
            )
            try await api.saveCheckin(checkin)
            briefing = try await api.generateBriefing(userId: userId)
            status = "Briefing ready"
        }
    }

    private func run(_ message: String, operation: @escaping () async throws -> Void) async {
        isBusy = true
        status = message
        do {
            try await operation()
        } catch {
            status = error.localizedDescription
        }
        isBusy = false
    }

    private static func todayString() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: Date())
    }
}
