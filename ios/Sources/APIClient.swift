import Foundation

final class APIClient {
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()

    func saveProfile(_ profile: AthleteProfile) async throws {
        try await post("/api/profile", body: profile)
    }

    func sendAppleHealthSnapshot(_ snapshot: AppleHealthSnapshot) async throws {
        try await post("/api/apple-health/snapshot", body: snapshot)
    }

    func saveCheckin(_ checkin: CheckinPayload) async throws {
        try await post("/api/checkin", body: checkin)
    }

    func generateBriefing(userId: String) async throws -> String {
        struct Request: Codable { let userId: String; enum CodingKeys: String, CodingKey { case userId = "user_id" } }
        struct Response: Codable { let briefing: String }
        let response: Response = try await postForResponse("/api/briefing", body: Request(userId: userId))
        return response.briefing
    }

    private func post<T: Encodable>(_ path: String, body: T) async throws {
        let _: EmptyResponse = try await postForResponse(path, body: body)
    }

    private func postForResponse<T: Encodable, R: Decodable>(_ path: String, body: T) async throws -> R {
        let cleanPath = path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        var request = URLRequest(url: AppConfig.baseURL.appendingPathComponent(cleanPath))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(AppConfig.iosAppAPIKey, forHTTPHeaderField: "X-MM-BETA-KEY")
        request.httpBody = try encoder.encode(body)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            let message = String(data: data, encoding: .utf8) ?? "Request failed"
            throw APIError.requestFailed(message)
        }
        if R.self == EmptyResponse.self {
            return EmptyResponse() as! R
        }
        return try decoder.decode(R.self, from: data)
    }
}

struct EmptyResponse: Codable {}

enum APIError: Error, LocalizedError {
    case requestFailed(String)

    var errorDescription: String? {
        switch self {
        case .requestFailed(let message): return message
        }
    }
}
