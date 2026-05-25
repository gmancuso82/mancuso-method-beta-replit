import Foundation
import HealthKit

@MainActor
final class HealthKitManager: ObservableObject {
    @Published var isAuthorized = false

    private let store = HKHealthStore()
    private let calendar = Calendar.current

    var isHealthDataAvailable: Bool {
        HKHealthStore.isHealthDataAvailable()
    }

    func requestAuthorization() async throws {
        guard isHealthDataAvailable else {
            throw HealthKitError.notAvailable
        }

        let typesToRead: Set<HKObjectType> = [
            HKObjectType.characteristicType(forIdentifier: .dateOfBirth)!,
            HKObjectType.characteristicType(forIdentifier: .biologicalSex)!,
            HKObjectType.quantityType(forIdentifier: .bodyMass)!,
            HKObjectType.quantityType(forIdentifier: .activeEnergyBurned)!,
            HKObjectType.quantityType(forIdentifier: .appleExerciseTime)!,
            HKObjectType.quantityType(forIdentifier: .vo2Max)!,
            HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN)!,
            HKObjectType.quantityType(forIdentifier: .restingHeartRate)!,
            HKObjectType.categoryType(forIdentifier: .sleepAnalysis)!,
            HKObjectType.workoutType()
        ]

        try await store.requestAuthorization(toShare: [], read: typesToRead)
        isAuthorized = true
    }

    func buildTodaySnapshot(userId: String) async throws -> AppleHealthSnapshot {
        let now = Date()
        let startOfDay = calendar.startOfDay(for: now)
        let dateString = Self.isoDay.string(from: now)
        let workouts = try await readWorkouts(start: startOfDay, end: now)
        let sleepMinutes = try await readSleepMinutes(end: now)

        return AppleHealthSnapshot(
            userId: userId,
            date: dateString,
            age: readAge(),
            sex: readSex(),
            dailyMoveKcal: try await readCumulativeQuantity(.activeEnergyBurned, unit: .kilocalorie(), start: startOfDay, end: now),
            exerciseMinutes: try await readCumulativeQuantity(.appleExerciseTime, unit: .minute(), start: startOfDay, end: now),
            cardioFitnessVO2Max: try await readMostRecentQuantity(.vo2Max, unit: HKUnit(from: "mL/kg*min")),
            sleepScore: sleepMinutes.map(Self.derivedSleepScore),
            sleepDurationMinutes: sleepMinutes,
            weight: try await readMostRecentQuantity(.bodyMass, unit: .pound()),
            hrvMs: try await readMostRecentQuantity(.heartRateVariabilitySDNN, unit: .secondUnit(with: .milli)),
            restingHR: try await readMostRecentQuantity(.restingHeartRate, unit: HKUnit.count().unitDivided(by: .minute())),
            workouts: workouts
        )
    }

    private func readAge() -> Int? {
        guard let dateOfBirth = try? store.dateOfBirthComponents(),
              let birthday = calendar.date(from: dateOfBirth) else {
            return nil
        }
        return calendar.dateComponents([.year], from: birthday, to: Date()).year
    }

    private func readSex() -> String? {
        guard let biologicalSex = try? store.biologicalSex().biologicalSex else {
            return nil
        }
        switch biologicalSex {
        case .female: return "female"
        case .male: return "male"
        case .other: return "other"
        default: return nil
        }
    }

    private func readMostRecentQuantity(_ identifier: HKQuantityTypeIdentifier, unit: HKUnit) async throws -> Double? {
        guard let type = HKQuantityType.quantityType(forIdentifier: identifier) else {
            return nil
        }

        let sort = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)
        return try await withCheckedThrowingContinuation { continuation in
            let query = HKSampleQuery(sampleType: type, predicate: nil, limit: 1, sortDescriptors: [sort]) { _, samples, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                let quantity = (samples?.first as? HKQuantitySample)?.quantity.doubleValue(for: unit)
                continuation.resume(returning: quantity)
            }
            store.execute(query)
        }
    }

    private func readCumulativeQuantity(_ identifier: HKQuantityTypeIdentifier, unit: HKUnit, start: Date, end: Date) async throws -> Double? {
        guard let type = HKQuantityType.quantityType(forIdentifier: identifier) else {
            return nil
        }

        let predicate = HKQuery.predicateForSamples(withStart: start, end: end)
        return try await withCheckedThrowingContinuation { continuation in
            let query = HKStatisticsQuery(quantityType: type, quantitySamplePredicate: predicate, options: .cumulativeSum) { _, result, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                continuation.resume(returning: result?.sumQuantity()?.doubleValue(for: unit))
            }
            store.execute(query)
        }
    }

    private func readSleepMinutes(end: Date) async throws -> Double? {
        guard let type = HKCategoryType.categoryType(forIdentifier: .sleepAnalysis) else {
            return nil
        }
        let start = calendar.date(byAdding: .hour, value: -24, to: end) ?? calendar.startOfDay(for: end)
        let predicate = HKQuery.predicateForSamples(withStart: start, end: end)

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKSampleQuery(sampleType: type, predicate: predicate, limit: HKObjectQueryNoLimit, sortDescriptors: nil) { _, samples, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                let minutes = (samples as? [HKCategorySample] ?? [])
                    .filter { sample in
                        sample.value == HKCategoryValueSleepAnalysis.asleepCore.rawValue ||
                        sample.value == HKCategoryValueSleepAnalysis.asleepDeep.rawValue ||
                        sample.value == HKCategoryValueSleepAnalysis.asleepREM.rawValue ||
                        sample.value == HKCategoryValueSleepAnalysis.asleepUnspecified.rawValue
                    }
                    .reduce(0.0) { total, sample in
                        total + sample.endDate.timeIntervalSince(sample.startDate) / 60
                    }
                continuation.resume(returning: minutes > 0 ? minutes : nil)
            }
            store.execute(query)
        }
    }

    private func readWorkouts(start: Date, end: Date) async throws -> [AppleWorkoutSnapshot] {
        let predicate = HKQuery.predicateForSamples(withStart: start, end: end)
        let sort = NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: false)

        return try await withCheckedThrowingContinuation { continuation in
            let query = HKSampleQuery(sampleType: .workoutType(), predicate: predicate, limit: 12, sortDescriptors: [sort]) { _, samples, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                let workouts = (samples as? [HKWorkout] ?? []).map { workout in
                    AppleWorkoutSnapshot(
                        activityType: workout.workoutActivityType.displayName,
                        start: Self.isoDateTime.string(from: workout.startDate),
                        durationMinutes: workout.duration / 60,
                        activeEnergyKcal: workout.totalEnergyBurned?.doubleValue(for: .kilocalorie()),
                        averageHR: nil,
                        distanceM: workout.totalDistance?.doubleValue(for: .meter())
                    )
                }
                continuation.resume(returning: workouts)
            }
            store.execute(query)
        }
    }

    private static func derivedSleepScore(minutes: Double) -> Int {
        let target = 8.0 * 60.0
        return min(100, max(0, Int((minutes / target) * 100)))
    }

    private static let isoDay: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()

    private static let isoDateTime: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        return formatter
    }()
}

enum HealthKitError: Error, LocalizedError {
    case notAvailable

    var errorDescription: String? {
        "Apple Health data is not available on this device."
    }
}

private extension HKWorkoutActivityType {
    var displayName: String {
        switch self {
        case .cycling: return "Cycling"
        case .running: return "Running"
        case .walking: return "Walking"
        case .traditionalStrengthTraining: return "Strength Training"
        case .functionalStrengthTraining: return "Functional Strength Training"
        case .highIntensityIntervalTraining: return "HIIT"
        case .yoga: return "Yoga"
        case .rowing: return "Rowing"
        case .elliptical: return "Elliptical"
        case .swimming: return "Swimming"
        default: return "Workout"
        }
    }
}
