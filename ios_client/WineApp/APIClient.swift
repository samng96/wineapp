import Foundation

// MARK: - API Error

enum APIError: Error, LocalizedError {
    case httpError(Int, String)
    case decodingError(Error)

    var errorDescription: String? {
        switch self {
        case .httpError(let code, let message):
            return "HTTP \(code): \(message)"
        case .decodingError(let error):
            return "Decoding error: \(error.localizedDescription)"
        }
    }
}

// MARK: - API Endpoint Constants

enum API {
    static let wineReferences      = "/wine-references"
    static let userWineReferences  = "/user-wine-references"
    static let wineInstances       = "/wine-instances"
    static let cellars             = "/cellars"

    static func consume(_ id: String) -> String {
        "/wine-instances/\(id)/consume"
    }

    static func coravin(_ id: String) -> String {
        "/wine-instances/\(id)/coravin"
    }

    static func instanceLocation(_ id: String) -> String {
        "/wine-instances/\(id)/location"
    }

    static func updateInstance(_ id: String) -> String {
        "/wine-instances/\(id)"
    }

    static func updateUserRef(_ id: String) -> String {
        "/user-wine-references/\(id)"
    }

    static func deleteCellar(_ id: String) -> String {
        "/cellars/\(id)"
    }

    /// Builds /vivino/search?name=<encoded>&limit=<limit>
    static func vivinoSearch(query: String, limit: Int = 10) -> String {
        let encoded = query.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? query
        return "/vivino/search?name=\(encoded)&limit=\(limit)"
    }
}

// MARK: - APIClient

actor APIClient {
    static let shared = APIClient()

    /// Base URL – change to your Mac's LAN IP when running on a real device.
    nonisolated let baseURL = URL(string: "http://localhost:5001")!

    private let session = URLSession.shared
    private let decoder = JSONDecoder()
    private let encoder = JSONEncoder()

    // MARK: Generic GET

    func get<T: Decodable>(_ path: String) async throws -> T {
        let url = baseURL.appendingPath(path)
        var request = URLRequest(url: url)
        request.httpMethod = "GET"

        let (data, response) = try await session.data(for: request)
        try validateResponse(response, data: data)

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    // MARK: Generic POST

    func post<B: Encodable, T: Decodable>(_ path: String, body: B) async throws -> T {
        let url = baseURL.appendingPath(path)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(body)

        let (data, response) = try await session.data(for: request)
        try validateResponse(response, data: data)

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    // MARK: Generic PUT

    func put<B: Encodable, T: Decodable>(_ path: String, body: B) async throws -> T {
        let url = baseURL.appendingPath(path)
        var request = URLRequest(url: url)
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(body)

        let (data, response) = try await session.data(for: request)
        try validateResponse(response, data: data)

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    // MARK: createOrConflict

    /// POSTs the body. If the server returns 409 (Conflict) it decodes the existing
    /// object from the `reference` key in the JSON error envelope; otherwise it
    /// decodes the normal 201 response.
    func createOrConflict<B: Encodable, T: Decodable>(_ path: String, body: B) async throws -> T {
        let url = baseURL.appendingPath(path)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(body)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }

        if httpResponse.statusCode == 409 {
            // The server returns { "error": "...", "reference": { … } }
            // Try to pull the nested object out of the `reference` key.
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let nested = json["reference"],
               let nestedData = try? JSONSerialization.data(withJSONObject: nested) {
                do {
                    return try decoder.decode(T.self, from: nestedData)
                } catch {
                    throw APIError.decodingError(error)
                }
            }
            // Fall through to generic error if we couldn't extract the object.
            let message = extractErrorMessage(from: data) ?? "Conflict"
            throw APIError.httpError(409, message)
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            let message = extractErrorMessage(from: data) ?? HTTPURLResponse.localizedString(forStatusCode: httpResponse.statusCode)
            throw APIError.httpError(httpResponse.statusCode, message)
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    // MARK: Generic DELETE

    func delete(_ path: String) async throws {
        let url = baseURL.appendingPath(path)
        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        let (data, response) = try await session.data(for: request)
        try validateResponse(response, data: data)
    }

    // MARK: postEmpty

    /// POST with no request body.
    func postEmpty<T: Decodable>(_ path: String) async throws -> T {
        let url = baseURL.appendingPath(path)
        var request = URLRequest(url: url)
        request.httpMethod = "POST"

        let (data, response) = try await session.data(for: request)
        try validateResponse(response, data: data)

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    // MARK: resolveImageURL

    nonisolated func resolveImageURL(_ rawUrl: String?) -> URL? {
        guard let raw = rawUrl, !raw.isEmpty else { return nil }
        if raw.hasPrefix("http") { return URL(string: raw) }
        let clean = raw.hasPrefix("/") ? String(raw.dropFirst()) : raw
        return baseURL.appendingPathComponent(clean)
    }

    // MARK: Private Helpers

    private func validateResponse(_ response: URLResponse, data: Data) throws {
        guard let httpResponse = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }
        guard (200...299).contains(httpResponse.statusCode) else {
            let message = extractErrorMessage(from: data) ?? HTTPURLResponse.localizedString(forStatusCode: httpResponse.statusCode)
            throw APIError.httpError(httpResponse.statusCode, message)
        }
    }

    private func extractErrorMessage(from data: Data) -> String? {
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let message = json["error"] as? String else {
            return nil
        }
        return message
    }
}

// MARK: - URL Helper

private extension URL {
    /// Append a path that may contain a query string (appendingPathComponent would encode '?' and '=').
    func appendingPath(_ path: String) -> URL {
        guard var components = URLComponents(url: self, resolvingAgainstBaseURL: false) else {
            return appendingPathComponent(path)
        }

        // Split on '?' so we preserve any query items already in `path`.
        let parts = path.split(separator: "?", maxSplits: 1)
        let rawPath = String(parts[0])

        // Merge existing path with the new segment.
        let existingPath = components.path.hasSuffix("/") ? String(components.path.dropLast()) : components.path
        components.path = existingPath + rawPath

        if parts.count == 2 {
            let queryString = String(parts[1])
            var items = components.queryItems ?? []
            let newItems = queryString.split(separator: "&").compactMap { pair -> URLQueryItem? in
                let kv = pair.split(separator: "=", maxSplits: 1)
                guard kv.count == 2 else { return nil }
                return URLQueryItem(
                    name: String(kv[0]).removingPercentEncoding ?? String(kv[0]),
                    value: String(kv[1]).removingPercentEncoding ?? String(kv[1])
                )
            }
            items.append(contentsOf: newItems)
            components.queryItems = items
        }

        return components.url ?? appendingPathComponent(path)
    }
}
