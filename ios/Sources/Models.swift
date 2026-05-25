import Foundation

struct AthleteProfile: Codable {
    var userId: String
    var name: String
    var phone: String
    var email: String
    var trainingGoals: [String]
    var upcomingCompetition: String
    var competitionDate: String
    var experienceLevel: String
    var injuryLimitations: String
    var nutritionRestrictions: String
    var dataSources: [String] = ["Apple Health"]

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case name
        case phone
        case email
        case trainingGoals = "training_goals"
        case upcomingCompetition = "upcoming_competition"
        case competitionDate = "competition_date"
        case experienceLevel = "experience_level"
        case injuryLimitations = "injury_limitations"
        case nutritionRestrictions = "nutrition_restrictions"
        case dataSources = "data_sources"
    }
}

struct AppleWorkoutSnapshot: Codable, Identifiable {
    var id = UUID()
    var activityType: String
    var start: String
    var durationMinutes: Double
    var activeEnergyKcal: Double?
    var averageHR: Double?
    var distanceM: Double?

    enum CodingKeys: String, CodingKey {
        case activityType = "activity_type"
        case start
        case durationMinutes = "duration_minutes"
        case activeEnergyKcal = "active_energy_kcal"
        case averageHR = "average_hr"
        case distanceM = "distance_m"
    }
}

struct AppleHealthSnapshot: Codable {
    var userId: String
    var date: String
    var age: Int?
    var sex: String?
    var dailyMoveKcal: Double?
    var exerciseMinutes: Double?
    var cardioFitnessVO2Max: Double?
    var sleepScore: Int?
    var sleepDurationMinutes: Double?
    var weight: Double?
    var hrvMs: Double?
    var restingHR: Double?
    var workouts: [AppleWorkoutSnapshot]

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case date
        case age
        case sex
        case dailyMoveKcal = "daily_move_kcal"
        case exerciseMinutes = "exercise_minutes"
        case cardioFitnessVO2Max = "cardio_fitness_vo2max"
        case sleepScore = "sleep_score"
        case sleepDurationMinutes = "sleep_duration_minutes"
        case weight
        case hrvMs = "hrv_ms"
        case restingHR = "resting_hr"
        case workouts
    }
}

struct CheckinPayload: Codable {
    var userId: String
    var date: String
    var energy: Int?
    var soreness: Int?
    var stress: Int?
    var nutritionCalories: Int?
    var nutritionProtein: Int?
    var nutritionCarbs: Int?
    var nutritionFat: Int?
    var nutritionNotes: String
    var notes: String

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case date
        case energy
        case soreness
        case stress
        case nutritionCalories = "nutrition_calories"
        case nutritionProtein = "nutrition_protein"
        case nutritionCarbs = "nutrition_carbs"
        case nutritionFat = "nutrition_fat"
        case nutritionNotes = "nutrition_notes"
        case notes
    }
}
