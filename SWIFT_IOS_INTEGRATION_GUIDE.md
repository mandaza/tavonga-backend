# Swift iOS Integration Guide - Tavonga CareConnect API

## Overview

This guide provides comprehensive documentation for integrating your Swift iOS app with the Tavonga CareConnect Django backend API. The API is designed for autism and intellectual disability support systems.

**Base URL**: `https://jellyfish-app-ho48c.ondigitalocean.app/`  
**API Version**: v1  
**Authentication**: JWT Bearer Token

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Network Manager Setup](#network-manager-setup)
4. [Data Models](#data-models)
5. [API Endpoints](#api-endpoints)
6. [Code Examples](#code-examples)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)

## Quick Start

### 1. Add Dependencies

Add these to your `Package.swift` or use Swift Package Manager:

```swift
// No external dependencies required - using URLSession
// Optional: Add Alamofire for enhanced networking
```

### 2. Basic Setup

```swift
import Foundation

struct APIConfig {
    static let baseURL = "https://jellyfish-app-ho48c.ondigitalocean.app/api/v1"
    static let authEndpoint = "/auth/login/"
    static let refreshEndpoint = "/auth/refresh/"
}
```

## Authentication

### JWT Token Management

```swift
class AuthManager: ObservableObject {
    @Published var isLoggedIn = false
    @Published var currentUser: User?
    
    private let accessTokenKey = "access_token"
    private let refreshTokenKey = "refresh_token"
    
    var accessToken: String? {
        get { UserDefaults.standard.string(forKey: accessTokenKey) }
        set { 
            UserDefaults.standard.set(newValue, forKey: accessTokenKey)
            isLoggedIn = newValue != nil
        }
    }
    
    var refreshToken: String? {
        get { UserDefaults.standard.string(forKey: refreshTokenKey) }
        set { UserDefaults.standard.set(newValue, forKey: refreshTokenKey) }
    }
    
    func login(email: String, password: String) async throws -> Bool {
        let loginData = LoginRequest(email: email, password: password)
        let response: LoginResponse = try await NetworkManager.shared.request(
            endpoint: "/auth/login/",
            method: .POST,
            body: loginData
        )
        
        accessToken = response.access
        refreshToken = response.refresh
        // Fetch user profile after login
        currentUser = try await fetchUserProfile()
        return true
    }
    
    func refreshAccessToken() async throws -> Bool {
        guard let refreshToken = refreshToken else { return false }
        
        let refreshData = RefreshRequest(refresh: refreshToken)
        let response: RefreshResponse = try await NetworkManager.shared.request(
            endpoint: "/auth/refresh/",
            method: .POST,
            body: refreshData
        )
        
        accessToken = response.access
        return true
    }
    
    func logout() {
        accessToken = nil
        refreshToken = nil
        currentUser = nil
    }
    
    private func fetchUserProfile() async throws -> User {
        return try await NetworkManager.shared.request(
            endpoint: "/users/profile/",
            method: .GET
        )
    }
}
```

### Login Models

```swift
struct LoginRequest: Codable {
    let email: String
    let password: String
}

struct LoginResponse: Codable {
    let access: String
    let refresh: String
}

struct RefreshRequest: Codable {
    let refresh: String
}

struct RefreshResponse: Codable {
    let access: String
}
```

## Network Manager Setup

```swift
enum HTTPMethod: String {
    case GET = "GET"
    case POST = "POST"
    case PUT = "PUT"
    case PATCH = "PATCH"
    case DELETE = "DELETE"
}

enum NetworkError: Error {
    case invalidURL
    case noData
    case decodingError
    case unauthorized
    case serverError(Int)
    case unknown
}

class NetworkManager {
    static let shared = NetworkManager()
    private let session = URLSession.shared
    
    private init() {}
    
    func request<T: Codable>(
        endpoint: String,
        method: HTTPMethod = .GET,
        body: Codable? = nil,
        requiresAuth: Bool = true
    ) async throws -> T {
        
        guard let url = URL(string: APIConfig.baseURL + endpoint) else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Add authentication header
        if requiresAuth, let token = AuthManager.shared.accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        // Add request body
        if let body = body {
            request.httpBody = try JSONEncoder().encode(body)
        }
        
        do {
            let (data, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw NetworkError.unknown
            }
            
            // Handle different status codes
            switch httpResponse.statusCode {
            case 200...299:
                break
            case 401:
                // Try to refresh token
                if requiresAuth && endpoint != "/auth/refresh/" {
                    let refreshed = try await AuthManager.shared.refreshAccessToken()
                    if refreshed {
                        // Retry the original request
                        return try await request(endpoint: endpoint, method: method, body: body, requiresAuth: requiresAuth)
                    }
                }
                throw NetworkError.unauthorized
            case 400...499:
                throw NetworkError.serverError(httpResponse.statusCode)
            case 500...599:
                throw NetworkError.serverError(httpResponse.statusCode)
            default:
                throw NetworkError.unknown
            }
            
            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            return try decoder.decode(T.self, from: data)
            
        } catch {
            throw error
        }
    }
    
    // Upload media files
    func uploadMedia(
        data: Data,
        fileName: String,
        mimeType: String,
        context: String? = nil,
        activityLogId: String? = nil,
        behaviorLogId: String? = nil
    ) async throws -> MediaFile {
        
        guard let url = URL(string: APIConfig.baseURL + "/media/") else {
            throw NetworkError.invalidURL
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        if let token = AuthManager.shared.accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        
        var body = Data()
        
        // Add file data
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(fileName)\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        body.append(data)
        body.append("\r\n".data(using: .utf8)!)
        
        // Add metadata fields
        if let context = context {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"context\"\r\n\r\n".data(using: .utf8)!)
            body.append(context.data(using: .utf8)!)
            body.append("\r\n".data(using: .utf8)!)
        }
        
        if let activityLogId = activityLogId {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"activity_log\"\r\n\r\n".data(using: .utf8)!)
            body.append(activityLogId.data(using: .utf8)!)
            body.append("\r\n".data(using: .utf8)!)
        }
        
        if let behaviorLogId = behaviorLogId {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"behavior_log\"\r\n\r\n".data(using: .utf8)!)
            body.append(behaviorLogId.data(using: .utf8)!)
            body.append("\r\n".data(using: .utf8)!)
        }
        
        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        
        request.httpBody = body
        
        let (data, _) = try await session.data(for: request)
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return try decoder.decode(MediaFile.self, from: data)
    }
}
```

## Data Models

### User Models

```swift
struct User: Codable, Identifiable {
    let id: Int
    let username: String
    let email: String
    let firstName: String
    let lastName: String
    let role: UserRole
    let isAdmin: Bool
    let approved: Bool
    let phone: String?
    let address: String?
    let emergencyContact: String?
    let emergencyPhone: String?
    let profileImage: String?
    let dateOfBirth: String?
    let hireDate: String?
    let isActiveCarer: Bool
    let createdAt: String
    let updatedAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, username, email, role, approved, phone, address
        case firstName = "first_name"
        case lastName = "last_name"
        case isAdmin = "is_admin"
        case emergencyContact = "emergency_contact"
        case emergencyPhone = "emergency_phone"
        case profileImage = "profile_image"
        case dateOfBirth = "date_of_birth"
        case hireDate = "hire_date"
        case isActiveCarer = "is_active_carer"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

enum UserRole: String, Codable, CaseIterable {
    case supportWorker = "support_worker"
    case practitioner = "practitioner"
    case family = "family"
    case superAdmin = "super_admin"
    
    var displayName: String {
        switch self {
        case .supportWorker: return "Support Worker"
        case .practitioner: return "Practitioner"
        case .family: return "Family"
        case .superAdmin: return "Super Admin"
        }
    }
}
```

### Client Models

```swift
struct Client: Codable, Identifiable {
    let id: String
    let clientId: String
    let firstName: String
    let middleName: String?
    let lastName: String
    let preferredName: String?
    let dateOfBirth: String
    let gender: Gender
    let address: String?
    let phone: String?
    let email: String?
    let diagnosis: String
    let secondaryDiagnoses: String?
    let allergies: String?
    let medications: String?
    let medicalNotes: String?
    let careLevel: CareLevel
    let interests: String?
    let likes: String?
    let dislikes: String?
    let communicationPreferences: String?
    let behavioralTriggers: [String]
    let calmingStrategies: [String]
    let profilePicture: String?
    let additionalPhotos: [String]
    let isActive: Bool
    let notes: String?
    let primarySupportWorker: User?
    let supportTeam: [User]
    let caseManager: User?
    let contacts: [Contact]
    let documents: [ClientDocument]
    let createdAt: String
    let updatedAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, email, diagnosis, allergies, medications, interests, likes, dislikes, notes, contacts, documents
        case clientId = "client_id"
        case firstName = "first_name"
        case middleName = "middle_name"
        case lastName = "last_name"
        case preferredName = "preferred_name"
        case dateOfBirth = "date_of_birth"
        case gender, address, phone
        case secondaryDiagnoses = "secondary_diagnoses"
        case medicalNotes = "medical_notes"
        case careLevel = "care_level"
        case communicationPreferences = "communication_preferences"
        case behavioralTriggers = "behavioral_triggers"
        case calmingStrategies = "calming_strategies"
        case profilePicture = "profile_picture"
        case additionalPhotos = "additional_photos"
        case isActive = "is_active"
        case primarySupportWorker = "primary_support_worker"
        case supportTeam = "support_team"
        case caseManager = "case_manager"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

enum Gender: String, Codable, CaseIterable {
    case male = "male"
    case female = "female"
    case other = "other"
    case preferNotToSay = "prefer_not_to_say"
}

enum CareLevel: String, Codable, CaseIterable {
    case low = "low"
    case medium = "medium"
    case high = "high"
    case critical = "critical"
}

struct Contact: Codable, Identifiable {
    let id: String
    let contactType: ContactType
    let firstName: String
    let lastName: String
    let relationship: Relationship?
    let relationshipDescription: String?
    let phonePrimary: String?
    let phoneSecondary: String?
    let email: String?
    let address: String?
    let practiceName: String?
    let specialty: String?
    let licenseNumber: String?
    let isPrimaryContact: Bool
    let canPickUp: Bool
    let canReceiveUpdates: Bool
    let emergencyOnly: Bool
    let preferredContactMethod: ContactMethod
    let notes: String?
    let isActive: Bool
    
    enum CodingKeys: String, CodingKey {
        case id, email, address, specialty, notes
        case contactType = "contact_type"
        case firstName = "first_name"
        case lastName = "last_name"
        case relationship
        case relationshipDescription = "relationship_description"
        case phonePrimary = "phone_primary"
        case phoneSecondary = "phone_secondary"
        case practiceName = "practice_name"
        case licenseNumber = "license_number"
        case isPrimaryContact = "is_primary_contact"
        case canPickUp = "can_pick_up"
        case canReceiveUpdates = "can_receive_updates"
        case emergencyOnly = "emergency_only"
        case preferredContactMethod = "preferred_contact_method"
        case isActive = "is_active"
    }
}

enum ContactType: String, Codable, CaseIterable {
    case emergency = "emergency"
    case family = "family"
    case guardian = "guardian"
    case gp = "gp"
    case specialist = "specialist"
    case therapist = "therapist"
    case socialWorker = "social_worker"
    case advocate = "advocate"
    case friend = "friend"
    case other = "other"
}

enum Relationship: String, Codable, CaseIterable {
    case parent = "parent"
    case sibling = "sibling"
    case guardian = "guardian"
    case grandparent = "grandparent"
    case auntUncle = "aunt_uncle"
    case cousin = "cousin"
    case friend = "friend"
    case doctor = "doctor"
    case therapist = "therapist"
    case socialWorker = "social_worker"
    case advocate = "advocate"
    case other = "other"
}

enum ContactMethod: String, Codable, CaseIterable {
    case phone = "phone"
    case email = "email"
    case text = "text"
}
```

### Activity Models

```swift
struct Activity: Codable, Identifiable {
    let id: Int
    let name: String
    let description: String
    let category: ActivityCategory
    let difficulty: Difficulty
    let instructions: String
    let prerequisites: String?
    let estimatedDuration: Int?
    let primaryGoal: Goal?
    let relatedGoals: [Goal]
    let goalContributionWeight: Int
    let imageUrl: String?
    let videoUrl: String?
    let isActive: Bool
    let createdBy: User
    let completionRate: Double
    let createdAt: String
    let updatedAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, name, description, category, difficulty, instructions, prerequisites
        case estimatedDuration = "estimated_duration"
        case primaryGoal = "primary_goal"
        case relatedGoals = "related_goals"
        case goalContributionWeight = "goal_contribution_weight"
        case imageUrl = "image_url"
        case videoUrl = "video_url"
        case isActive = "is_active"
        case createdBy = "created_by"
        case completionRate = "completion_rate"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

enum ActivityCategory: String, Codable, CaseIterable {
    case dailyLiving = "daily_living"
    case social = "social"
    case educational = "educational"
    case recreational = "recreational"
    case therapeutic = "therapeutic"
    case other = "other"
}

enum Difficulty: String, Codable, CaseIterable {
    case easy = "easy"
    case medium = "medium"
    case hard = "hard"
}

struct ActivityLog: Codable, Identifiable {
    let id: Int
    let activity: Activity
    let user: User
    let date: String
    let scheduledTime: String?
    let startTime: String?
    let endTime: String?
    let status: ActivityStatus
    let completed: Bool
    let completionNotes: String?
    let difficultyRating: Int?
    let satisfactionRating: Int?
    let photos: [String]
    let videos: [String]
    let notes: String?
    let challenges: String?
    let successes: String?
    let createdAt: String
    let updatedAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, activity, user, date, status, completed, photos, videos, notes, challenges, successes
        case scheduledTime = "scheduled_time"
        case startTime = "start_time"
        case endTime = "end_time"
        case completionNotes = "completion_notes"
        case difficultyRating = "difficulty_rating"
        case satisfactionRating = "satisfaction_rating"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

enum ActivityStatus: String, Codable, CaseIterable {
    case scheduled = "scheduled"
    case inProgress = "in_progress"
    case completed = "completed"
    case cancelled = "cancelled"
    case skipped = "skipped"
}
```

### Goal Models

```swift
struct Goal: Codable, Identifiable {
    let id: Int
    let name: String
    let description: String
    let category: String?
    let targetDate: String?
    let status: GoalStatus
    let priority: Priority
    let assignedCarers: [User]
    let createdBy: User
    let progressPercentage: Int
    let notes: String?
    let requiredActivitiesCount: Int
    let completionThreshold: Int
    let createdAt: String
    let updatedAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, name, description, category, status, priority, notes
        case targetDate = "target_date"
        case assignedCarers = "assigned_carers"
        case createdBy = "created_by"
        case progressPercentage = "progress_percentage"
        case requiredActivitiesCount = "required_activities_count"
        case completionThreshold = "completion_threshold"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

enum GoalStatus: String, Codable, CaseIterable {
    case active = "active"
    case completed = "completed"
    case paused = "paused"
    case cancelled = "cancelled"
}

enum Priority: String, Codable, CaseIterable {
    case low = "low"
    case medium = "medium"
    case high = "high"
    case urgent = "urgent"
}
```

### Behavior Models

```swift
struct BehaviorLog: Codable, Identifiable {
    let id: Int
    let user: User
    let date: String
    let time: String
    let location: Location
    let specificLocation: String?
    let relatedActivity: Activity?
    let behaviorOccurrence: BehaviorOccurrence
    let activityBefore: String?
    let behaviorType: BehaviorType
    let behaviors: [String]
    let warningSign: [String]
    let durationMinutes: Int?
    let severity: Severity
    let harmToSelf: Bool
    let harmToOthers: Bool
    let propertyDamage: Bool
    let damageDescription: String?
    let interventionUsed: String
    let interventionEffective: Bool?
    let interventionNotes: String?
    let followUpRequired: Bool
    let followUpNotes: String?
    let photos: [String]
    let videos: [String]
    let notes: String?
    let triggersIdentified: [String]
    let createdAt: String
    let updatedAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, user, date, time, location, behaviors, notes
        case specificLocation = "specific_location"
        case relatedActivity = "related_activity"
        case behaviorOccurrence = "behavior_occurrence"
        case activityBefore = "activity_before"
        case behaviorType = "behavior_type"
        case warningSign = "warning_signs"
        case durationMinutes = "duration_minutes"
        case severity
        case harmToSelf = "harm_to_self"
        case harmToOthers = "harm_to_others"
        case propertyDamage = "property_damage"
        case damageDescription = "damage_description"
        case interventionUsed = "intervention_used"
        case interventionEffective = "intervention_effective"
        case interventionNotes = "intervention_notes"
        case followUpRequired = "follow_up_required"
        case followUpNotes = "follow_up_notes"
        case photos, videos
        case triggersIdentified = "triggers_identified"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

enum Location: String, Codable, CaseIterable {
    case home = "home"
    case school = "school"
    case community = "community"
    case therapy = "therapy"
    case transport = "transport"
    case other = "other"
}

enum BehaviorOccurrence: String, Codable, CaseIterable {
    case beforeActivity = "before_activity"
    case duringActivity = "during_activity"
    case afterActivity = "after_activity"
    case unrelated = "unrelated"
}

enum BehaviorType: String, Codable, CaseIterable {
    case aggression = "aggression"
    case selfInjury = "self_injury"
    case propertyDamage = "property_damage"
    case elopement = "elopement"
    case nonCompliance = "non_compliance"
    case disruption = "disruption"
    case other = "other"
}

enum Severity: String, Codable, CaseIterable {
    case low = "low"
    case medium = "medium"
    case high = "high"
    case critical = "critical"
}
```

### Shift Models

```swift
struct Shift: Codable, Identifiable {
    let id: Int
    let carer: User
    let date: String
    let shiftType: ShiftType
    let startTime: String
    let endTime: String
    let breakDuration: Int
    let clockIn: String?
    let clockOut: String?
    let clockInLocation: String?
    let clockOutLocation: String?
    let status: ShiftStatus
    let assignedBy: User?
    let location: String?
    let clientName: String?
    let clientAddress: String?
    let notes: String?
    let specialInstructions: String?
    let emergencyContact: String?
    let performanceRating: Int?
    let supervisorNotes: String?
    let createdAt: String
    let updatedAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, carer, date, status, location, notes
        case shiftType = "shift_type"
        case startTime = "start_time"
        case endTime = "end_time"
        case breakDuration = "break_duration"
        case clockIn = "clock_in"
        case clockOut = "clock_out"
        case clockInLocation = "clock_in_location"
        case clockOutLocation = "clock_out_location"
        case assignedBy = "assigned_by"
        case clientName = "client_name"
        case clientAddress = "client_address"
        case specialInstructions = "special_instructions"
        case emergencyContact = "emergency_contact"
        case performanceRating = "performance_rating"
        case supervisorNotes = "supervisor_notes"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

enum ShiftType: String, Codable, CaseIterable {
    case morning = "morning"
    case afternoon = "afternoon"
    case evening = "evening"
    case night = "night"
    case fullDay = "full_day"
    case custom = "custom"
}

enum ShiftStatus: String, Codable, CaseIterable {
    case scheduled = "scheduled"
    case inProgress = "in_progress"
    case completed = "completed"
    case cancelled = "cancelled"
    case noShow = "no_show"
}
```

### Media Models

```swift
struct MediaFile: Codable, Identifiable {
    let id: Int
    let fileName: String
    let fileUrl: String
    let fileSize: Int?
    let mimeType: String?
    let uploadedBy: User
    let context: String?
    let activityLog: ActivityLog?
    let behaviorLog: BehaviorLog?
    let thumbnail: String?
    let createdAt: String
    let updatedAt: String
    
    enum CodingKeys: String, CodingKey {
        case id, context, thumbnail
        case fileName = "file_name"
        case fileUrl = "file_url"
        case fileSize = "file_size"
        case mimeType = "mime_type"
        case uploadedBy = "uploaded_by"
        case activityLog = "activity_log"
        case behaviorLog = "behavior_log"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}
```

## API Endpoints

### Authentication Endpoints

```swift
class AuthService {
    // POST /api/v1/auth/login/
    func login(email: String, password: String) async throws -> LoginResponse {
        let request = LoginRequest(email: email, password: password)
        return try await NetworkManager.shared.request(
            endpoint: "/auth/login/",
            method: .POST,
            body: request,
            requiresAuth: false
        )
    }
    
    // POST /api/v1/auth/refresh/
    func refreshToken(refreshToken: String) async throws -> RefreshResponse {
        let request = RefreshRequest(refresh: refreshToken)
        return try await NetworkManager.shared.request(
            endpoint: "/auth/refresh/",
            method: .POST,
            body: request,
            requiresAuth: false
        )
    }
}
```

### User Endpoints

```swift
class UserService {
    // GET /api/v1/users/
    func getAllUsers() async throws -> [User] {
        return try await NetworkManager.shared.request(endpoint: "/users/")
    }
    
    // GET /api/v1/users/profile/
    func getUserProfile() async throws -> User {
        return try await NetworkManager.shared.request(endpoint: "/users/profile/")
    }
    
    // PUT /api/v1/users/profile/
    func updateProfile(user: User) async throws -> User {
        return try await NetworkManager.shared.request(
            endpoint: "/users/profile/",
            method: .PUT,
            body: user
        )
    }
    
    // POST /api/v1/users/
    func registerUser(userData: UserRegistration) async throws -> User {
        return try await NetworkManager.shared.request(
            endpoint: "/users/",
            method: .POST,
            body: userData,
            requiresAuth: false
        )
    }
    
    // POST /api/v1/users/{id}/approve/
    func approveUser(userId: Int) async throws -> User {
        return try await NetworkManager.shared.request(
            endpoint: "/users/\(userId)/approve/",
            method: .POST
        )
    }
}

struct UserRegistration: Codable {
    let username: String
    let email: String
    let password: String
    let firstName: String
    let lastName: String
    let role: UserRole
    let phone: String?
}
```

### Client Endpoints

```swift
class ClientService {
    // GET /api/v1/clients/clients/
    func getAllClients() async throws -> [Client] {
        return try await NetworkManager.shared.request(endpoint: "/clients/clients/")
    }
    
    // GET /api/v1/clients/clients/{id}/
    func getClient(id: String) async throws -> Client {
        return try await NetworkManager.shared.request(endpoint: "/clients/clients/\(id)/")
    }
    
    // POST /api/v1/clients/clients/
    func createClient(client: ClientCreate) async throws -> Client {
        return try await NetworkManager.shared.request(
            endpoint: "/clients/clients/",
            method: .POST,
            body: client
        )
    }
    
    // PUT /api/v1/clients/clients/{id}/
    func updateClient(id: String, client: Client) async throws -> Client {
        return try await NetworkManager.shared.request(
            endpoint: "/clients/clients/\(id)/",
            method: .PUT,
            body: client
        )
    }
    
    // GET /api/v1/clients/clients/{id}/contacts/
    func getClientContacts(clientId: String) async throws -> [Contact] {
        return try await NetworkManager.shared.request(endpoint: "/clients/clients/\(clientId)/contacts/")
    }
    
    // GET /api/v1/clients/clients/{id}/documents/
    func getClientDocuments(clientId: String) async throws -> [ClientDocument] {
        return try await NetworkManager.shared.request(endpoint: "/clients/clients/\(clientId)/documents/")
    }
}
```

### Activity Endpoints

```swift
class ActivityService {
    // GET /api/v1/activities/
    func getAllActivities() async throws -> [Activity] {
        return try await NetworkManager.shared.request(endpoint: "/activities/")
    }
    
    // POST /api/v1/activities/
    func createActivity(activity: ActivityCreate) async throws -> Activity {
        return try await NetworkManager.shared.request(
            endpoint: "/activities/",
            method: .POST,
            body: activity
        )
    }
    
    // GET /api/v1/activities/logs/
    func getActivityLogs() async throws -> [ActivityLog] {
        return try await NetworkManager.shared.request(endpoint: "/activities/logs/")
    }
    
    // POST /api/v1/activities/logs/
    func createActivityLog(log: ActivityLogCreate) async throws -> ActivityLog {
        return try await NetworkManager.shared.request(
            endpoint: "/activities/logs/",
            method: .POST,
            body: log
        )
    }
    
    // PUT /api/v1/activities/logs/{id}/
    func updateActivityLog(id: Int, log: ActivityLog) async throws -> ActivityLog {
        return try await NetworkManager.shared.request(
            endpoint: "/activities/logs/\(id)/",
            method: .PUT,
            body: log
        )
    }
    
    // GET /api/v1/activities/logs/today/
    func getTodayActivityLogs() async throws -> [ActivityLog] {
        return try await NetworkManager.shared.request(endpoint: "/activities/logs/today/")
    }
}

struct ActivityCreate: Codable {
    let name: String
    let description: String
    let category: ActivityCategory
    let difficulty: Difficulty
    let instructions: String
    let prerequisites: String?
    let estimatedDuration: Int?
    let primaryGoal: Int?
    let goalContributionWeight: Int
    let imageUrl: String?
    let videoUrl: String?
}

struct ActivityLogCreate: Codable {
    let activity: Int
    let date: String
    let scheduledTime: String?
    let status: ActivityStatus
    let notes: String?
    let challenges: String?
    let successes: String?
}
```

### Goal Endpoints

```swift
class GoalService {
    // GET /api/v1/goals/
    func getAllGoals() async throws -> [Goal] {
        return try await NetworkManager.shared.request(endpoint: "/goals/")
    }
    
    // POST /api/v1/goals/
    func createGoal(goal: GoalCreate) async throws -> Goal {
        return try await NetworkManager.shared.request(
            endpoint: "/goals/",
            method: .POST,
            body: goal
        )
    }
    
    // PUT /api/v1/goals/{id}/
    func updateGoal(id: Int, goal: Goal) async throws -> Goal {
        return try await NetworkManager.shared.request(
            endpoint: "/goals/\(id)/",
            method: .PUT,
            body: goal
        )
    }
    
    // GET /api/v1/goals/active/
    func getActiveGoals() async throws -> [Goal] {
        return try await NetworkManager.shared.request(endpoint: "/goals/active/")
    }
    
    // GET /api/v1/goals/progress/
    func getGoalProgress() async throws -> [GoalProgress] {
        return try await NetworkManager.shared.request(endpoint: "/goals/progress/")
    }
}

struct GoalCreate: Codable {
    let name: String
    let description: String
    let category: String?
    let targetDate: String?
    let priority: Priority
    let assignedCarers: [Int]
    let completionThreshold: Int
}

struct GoalProgress: Codable {
    let goal: Goal
    let progressPercentage: Int
    let completedActivities: Int
    let totalActivities: Int
    let lastActivity: String?
}
```

### Behavior Endpoints

```swift
class BehaviorService {
    // GET /api/v1/behaviors/
    func getAllBehaviorLogs() async throws -> [BehaviorLog] {
        return try await NetworkManager.shared.request(endpoint: "/behaviors/")
    }
    
    // POST /api/v1/behaviors/
    func createBehaviorLog(log: BehaviorLogCreate) async throws -> BehaviorLog {
        return try await NetworkManager.shared.request(
            endpoint: "/behaviors/",
            method: .POST,
            body: log
        )
    }
    
    // PUT /api/v1/behaviors/{id}/
    func updateBehaviorLog(id: Int, log: BehaviorLog) async throws -> BehaviorLog {
        return try await NetworkManager.shared.request(
            endpoint: "/behaviors/\(id)/",
            method: .PUT,
            body: log
        )
    }
    
    // GET /api/v1/behaviors/today/
    func getTodayBehaviorLogs() async throws -> [BehaviorLog] {
        return try await NetworkManager.shared.request(endpoint: "/behaviors/today/")
    }
    
    // GET /api/v1/behaviors/critical/
    func getCriticalBehaviorLogs() async throws -> [BehaviorLog] {
        return try await NetworkManager.shared.request(endpoint: "/behaviors/critical/")
    }
}

struct BehaviorLogCreate: Codable {
    let date: String
    let time: String
    let location: Location
    let specificLocation: String?
    let relatedActivity: Int?
    let behaviorOccurrence: BehaviorOccurrence
    let behaviorType: BehaviorType
    let behaviors: [String]
    let warningSign: [String]
    let durationMinutes: Int?
    let severity: Severity
    let harmToSelf: Bool
    let harmToOthers: Bool
    let propertyDamage: Bool
    let interventionUsed: String
    let interventionEffective: Bool?
    let notes: String?
}
```

### Shift Endpoints

```swift
class ShiftService {
    // GET /api/v1/shifts/
    func getAllShifts() async throws -> [Shift] {
        return try await NetworkManager.shared.request(endpoint: "/shifts/")
    }
    
    // POST /api/v1/shifts/
    func createShift(shift: ShiftCreate) async throws -> Shift {
        return try await NetworkManager.shared.request(
            endpoint: "/shifts/",
            method: .POST,
            body: shift
        )
    }
    
    // GET /api/v1/shifts/my_shifts/
    func getMyShifts() async throws -> [Shift] {
        return try await NetworkManager.shared.request(endpoint: "/shifts/my_shifts/")
    }
    
    // POST /api/v1/shifts/{id}/clock_in/
    func clockIn(shiftId: Int, location: String?) async throws -> Shift {
        let request = ClockInRequest(location: location)
        return try await NetworkManager.shared.request(
            endpoint: "/shifts/\(shiftId)/clock_in/",
            method: .POST,
            body: request
        )
    }
    
    // POST /api/v1/shifts/{id}/clock_out/
    func clockOut(shiftId: Int, location: String?) async throws -> Shift {
        let request = ClockOutRequest(location: location)
        return try await NetworkManager.shared.request(
            endpoint: "/shifts/\(shiftId)/clock_out/",
            method: .POST,
            body: request
        )
    }
    
    // GET /api/v1/shifts/today/
    func getTodayShifts() async throws -> [Shift] {
        return try await NetworkManager.shared.request(endpoint: "/shifts/today/")
    }
}

struct ShiftCreate: Codable {
    let carer: Int
    let date: String
    let shiftType: ShiftType
    let startTime: String
    let endTime: String
    let location: String?
    let clientName: String?
    let specialInstructions: String?
}

struct ClockInRequest: Codable {
    let location: String?
}

struct ClockOutRequest: Codable {
    let location: String?
}
```

### Media Endpoints

```swift
class MediaService {
    // POST /api/v1/media/
    func uploadMedia(
        data: Data,
        fileName: String,
        mimeType: String,
        context: String? = nil,
        activityLogId: String? = nil,
        behaviorLogId: String? = nil
    ) async throws -> MediaFile {
        return try await NetworkManager.shared.uploadMedia(
            data: data,
            fileName: fileName,
            mimeType: mimeType,
            context: context,
            activityLogId: activityLogId,
            behaviorLogId: behaviorLogId
        )
    }
    
    // GET /api/v1/media/
    func getAllMedia() async throws -> [MediaFile] {
        return try await NetworkManager.shared.request(endpoint: "/media/")
    }
    
    // DELETE /api/v1/media/{id}/
    func deleteMedia(id: Int) async throws {
        let _: EmptyResponse = try await NetworkManager.shared.request(
            endpoint: "/media/\(id)/",
            method: .DELETE
        )
    }
}

struct EmptyResponse: Codable {}
```

### Dashboard Endpoints

```swift
class DashboardService {
    // GET /api/v1/dashboard/stats/
    func getDashboardStats() async throws -> DashboardStats {
        return try await NetworkManager.shared.request(endpoint: "/dashboard/stats/")
    }
}

struct DashboardStats: Codable {
    let totalCarers: Int
    let activeCarers: Int
    let behaviorsToday: Int
    let activitiesCompleted: Int
    let activeShifts: Int
    
    enum CodingKeys: String, CodingKey {
        case totalCarers = "total_carers"
        case activeCarers = "active_carers"
        case behaviorsToday = "behaviors_today"
        case activitiesCompleted = "activities_completed"
        case activeShifts = "active_shifts"
    }
}
```

## Code Examples

### Login Flow

```swift
struct LoginView: View {
    @StateObject private var authManager = AuthManager.shared
    @State private var email = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var errorMessage = ""
    
    var body: some View {
        VStack(spacing: 20) {
            TextField("Email", text: $email)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .keyboardType(.emailAddress)
                .autocapitalization(.none)
            
            SecureField("Password", text: $password)
                .textFieldStyle(RoundedBorderTextFieldStyle())
            
            Button("Login") {
                Task {
                    await login()
                }
            }
            .disabled(isLoading)
            
            if !errorMessage.isEmpty {
                Text(errorMessage)
                    .foregroundColor(.red)
            }
        }
        .padding()
    }
    
    private func login() async {
        isLoading = true
        errorMessage = ""
        
        do {
            let success = try await authManager.login(email: email, password: password)
            if success {
                // Navigation handled by AuthManager's @Published isLoggedIn
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
}
```

### Activity Logging

```swift
struct ActivityLogView: View {
    @State private var activities: [Activity] = []
    @State private var selectedActivity: Activity?
    @State private var notes = ""
    @State private var isCompleted = false
    
    var body: some View {
        NavigationView {
            VStack {
                Picker("Select Activity", selection: $selectedActivity) {
                    ForEach(activities) { activity in
                        Text(activity.name).tag(activity as Activity?)
                    }
                }
                .pickerStyle(MenuPickerStyle())
                
                TextEditor(text: $notes)
                    .border(Color.gray, width: 1)
                    .frame(height: 100)
                
                Toggle("Completed", isOn: $isCompleted)
                
                Button("Save Log") {
                    Task {
                        await saveActivityLog()
                    }
                }
                .disabled(selectedActivity == nil)
            }
            .padding()
            .navigationTitle("Log Activity")
        }
        .onAppear {
            Task {
                await loadActivities()
            }
        }
    }
    
    private func loadActivities() async {
        do {
            activities = try await ActivityService().getAllActivities()
        } catch {
            print("Error loading activities: \(error)")
        }
    }
    
    private func saveActivityLog() async {
        guard let activity = selectedActivity else { return }
        
        let log = ActivityLogCreate(
            activity: activity.id,
            date: ISO8601DateFormatter().string(from: Date()),
            scheduledTime: nil,
            status: isCompleted ? .completed : .inProgress,
            notes: notes.isEmpty ? nil : notes,
            challenges: nil,
            successes: nil
        )
        
        do {
            let _ = try await ActivityService().createActivityLog(log: log)
            // Reset form or navigate back
            notes = ""
            isCompleted = false
        } catch {
            print("Error saving activity log: \(error)")
        }
    }
}
```

### Behavior Incident Reporting

```swift
struct BehaviorLogView: View {
    @State private var behaviorType: BehaviorType = .other
    @State private var severity: Severity = .medium
    @State private var location: Location = .other
    @State private var interventionUsed = ""
    @State private var notes = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section("Behavior Details") {
                    Picker("Behavior Type", selection: $behaviorType) {
                        ForEach(BehaviorType.allCases, id: \.self) { type in
                            Text(type.rawValue.capitalized).tag(type)
                        }
                    }
                    
                    Picker("Severity", selection: $severity) {
                        ForEach(Severity.allCases, id: \.self) { severity in
                            Text(severity.rawValue.capitalized).tag(severity)
                        }
                    }
                    
                    Picker("Location", selection: $location) {
                        ForEach(Location.allCases, id: \.self) { location in
                            Text(location.rawValue.capitalized).tag(location)
                        }
                    }
                }
                
                Section("Intervention") {
                    TextEditor(text: $interventionUsed)
                        .frame(height: 80)
                }
                
                Section("Additional Notes") {
                    TextEditor(text: $notes)
                        .frame(height: 100)
                }
                
                Button("Submit Report") {
                    Task {
                        await submitBehaviorLog()
                    }
                }
            }
            .navigationTitle("Behavior Incident")
        }
    }
    
    private func submitBehaviorLog() async {
        let log = BehaviorLogCreate(
            date: ISO8601DateFormatter().string(from: Date()),
            time: ISO8601DateFormatter().string(from: Date()),
            location: location,
            specificLocation: nil,
            relatedActivity: nil,
            behaviorOccurrence: .unrelated,
            behaviorType: behaviorType,
            behaviors: [],
            warningSign: [],
            durationMinutes: nil,
            severity: severity,
            harmToSelf: false,
            harmToOthers: false,
            propertyDamage: false,
            interventionUsed: interventionUsed,
            interventionEffective: nil,
            notes: notes.isEmpty ? nil : notes
        )
        
        do {
            let _ = try await BehaviorService().createBehaviorLog(log: log)
            // Handle success
        } catch {
            print("Error submitting behavior log: \(error)")
        }
    }
}
```

### Clock In/Out for Shifts

```swift
struct ShiftClockView: View {
    @State private var currentShift: Shift?
    @State private var isLoading = false
    
    var body: some View {
        VStack(spacing: 20) {
            if let shift = currentShift {
                VStack {
                    Text("Current Shift")
                        .font(.headline)
                    
                    Text("\(shift.startTime) - \(shift.endTime)")
                    Text("Client: \(shift.clientName ?? "N/A")")
                    Text("Location: \(shift.location ?? "N/A")")
                    
                    if shift.clockIn == nil {
                        Button("Clock In") {
                            Task {
                                await clockIn()
                            }
                        }
                        .disabled(isLoading)
                    } else if shift.clockOut == nil {
                        Button("Clock Out") {
                            Task {
                                await clockOut()
                            }
                        }
                        .disabled(isLoading)
                    } else {
                        Text("Shift Completed")
                            .foregroundColor(.green)
                    }
                }
                .padding()
                .border(Color.gray, width: 1)
            } else {
                Text("No active shift")
            }
        }
        .onAppear {
            Task {
                await loadTodayShifts()
            }
        }
    }
    
    private func loadTodayShifts() async {
        do {
            let shifts = try await ShiftService().getTodayShifts()
            currentShift = shifts.first { $0.status == .scheduled || $0.status == .inProgress }
        } catch {
            print("Error loading shifts: \(error)")
        }
    }
    
    private func clockIn() async {
        guard let shift = currentShift else { return }
        
        isLoading = true
        do {
            let updatedShift = try await ShiftService().clockIn(shiftId: shift.id, location: nil)
            currentShift = updatedShift
        } catch {
            print("Error clocking in: \(error)")
        }
        isLoading = false
    }
    
    private func clockOut() async {
        guard let shift = currentShift else { return }
        
        isLoading = true
        do {
            let updatedShift = try await ShiftService().clockOut(shiftId: shift.id, location: nil)
            currentShift = updatedShift
        } catch {
            print("Error clocking out: \(error)")
        }
        isLoading = false
    }
}
```

## Error Handling

### Error Types

```swift
enum APIError: Error, LocalizedError {
    case networkError(Error)
    case decodingError(Error)
    case unauthorized
    case notFound
    case serverError(Int, String?)
    case validationError([String: [String]])
    
    var errorDescription: String? {
        switch self {
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .decodingError(let error):
            return "Data parsing error: \(error.localizedDescription)"
        case .unauthorized:
            return "Authentication required. Please log in again."
        case .notFound:
            return "The requested resource was not found."
        case .serverError(let code, let message):
            return "Server error (\(code)): \(message ?? "Unknown error")"
        case .validationError(let errors):
            let messages = errors.flatMap { $0.value }.joined(separator: ", ")
            return "Validation error: \(messages)"
        }
    }
}
```

### Error Handling in Views

```swift
struct ContentView: View {
    @State private var errorAlert: ErrorAlert?
    
    var body: some View {
        // Your content here
        NavigationView {
            // Your navigation content
        }
        .alert(item: $errorAlert) { errorAlert in
            Alert(
                title: Text("Error"),
                message: Text(errorAlert.message),
                dismissButton: .default(Text("OK"))
            )
        }
    }
    
    private func handleError(_ error: Error) {
        let message: String
        if let apiError = error as? APIError {
            message = apiError.localizedDescription
        } else {
            message = error.localizedDescription
        }
        
        errorAlert = ErrorAlert(message: message)
    }
}

struct ErrorAlert: Identifiable {
    let id = UUID()
    let message: String
}
```

## Best Practices

### 1. Data Caching

```swift
class DataCache {
    private var cache: [String: Any] = [:]
    private let cacheQueue = DispatchQueue(label: "cache.queue", attributes: .concurrent)
    
    func get<T: Codable>(_ key: String, type: T.Type) -> T? {
        return cacheQueue.sync {
            return cache[key] as? T
        }
    }
    
    func set<T: Codable>(_ key: String, value: T) {
        cacheQueue.async(flags: .barrier) {
            self.cache[key] = value
        }
    }
    
    func remove(_ key: String) {
        cacheQueue.async(flags: .barrier) {
            self.cache.removeValue(forKey: key)
        }
    }
}
```

### 2. Offline Support

```swift
class OfflineManager {
    private let userDefaults = UserDefaults.standard
    
    func saveForOffline<T: Codable>(_ data: T, key: String) {
        do {
            let encoded = try JSONEncoder().encode(data)
            userDefaults.set(encoded, forKey: key)
        } catch {
            print("Failed to save offline data: \(error)")
        }
    }
    
    func loadFromOffline<T: Codable>(key: String, type: T.Type) -> T? {
        guard let data = userDefaults.data(forKey: key) else { return nil }
        
        do {
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            print("Failed to load offline data: \(error)")
            return nil
        }
    }
}
```

### 3. Image Loading and Caching

```swift
class ImageLoader: ObservableObject {
    @Published var image: UIImage?
    @Published var isLoading = false
    
    private let cache = NSCache<NSString, UIImage>()
    
    func load(from url: String) {
        guard let imageURL = URL(string: url) else { return }
        
        let key = NSString(string: url)
        
        if let cachedImage = cache.object(forKey: key) {
            self.image = cachedImage
            return
        }
        
        isLoading = true
        
        URLSession.shared.dataTask(with: imageURL) { [weak self] data, _, _ in
            guard let data = data, let image = UIImage(data: data) else {
                DispatchQueue.main.async {
                    self?.isLoading = false
                }
                return
            }
            
            self?.cache.setObject(image, forKey: key)
            
            DispatchQueue.main.async {
                self?.image = image
                self?.isLoading = false
            }
        }.resume()
    }
}

struct AsyncImage: View {
    @StateObject private var loader = ImageLoader()
    let url: String
    
    var body: some View {
        Group {
            if let image = loader.image {
                Image(uiImage: image)
                    .resizable()
            } else if loader.isLoading {
                ProgressView()
            } else {
                Image(systemName: "photo")
                    .foregroundColor(.gray)
            }
        }
        .onAppear {
            loader.load(from: url)
        }
    }
}
```

### 4. Pagination Support

```swift
class PaginatedDataSource<T: Codable>: ObservableObject {
    @Published var items: [T] = []
    @Published var isLoading = false
    @Published var hasMorePages = true
    
    private var currentPage = 1
    private let pageSize = 20
    private let endpoint: String
    
    init(endpoint: String) {
        self.endpoint = endpoint
    }
    
    func loadNextPage() async {
        guard !isLoading && hasMorePages else { return }
        
        isLoading = true
        
        do {
            let response: PaginatedResponse<T> = try await NetworkManager.shared.request(
                endpoint: "\(endpoint)?page=\(currentPage)&page_size=\(pageSize)"
            )
            
            await MainActor.run {
                self.items.append(contentsOf: response.results)
                self.hasMorePages = response.next != nil
                self.currentPage += 1
                self.isLoading = false
            }
        } catch {
            await MainActor.run {
                self.isLoading = false
            }
        }
    }
    
    func refresh() async {
        currentPage = 1
        hasMorePages = true
        items.removeAll()
        await loadNextPage()
    }
}

struct PaginatedResponse<T: Codable>: Codable {
    let count: Int
    let next: String?
    let previous: String?
    let results: [T]
}
```

### 5. Real-time Updates (Optional)

If you want to implement real-time updates, you can use polling or WebSockets:

```swift
class RealTimeManager: ObservableObject {
    private var timer: Timer?
    
    func startPolling(interval: TimeInterval = 30) {
        timer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { _ in
            Task {
                await self.fetchUpdates()
            }
        }
    }
    
    func stopPolling() {
        timer?.invalidate()
        timer = nil
    }
    
    private func fetchUpdates() async {
        // Fetch latest data from API
        // Update your data models
    }
}
```

## Testing

### Unit Tests Example

```swift
import XCTest
@testable import YourApp

class NetworkManagerTests: XCTestCase {
    
    func testLoginSuccess() async throws {
        // Mock successful login
        let authManager = AuthManager()
        
        // Use a test environment or mock network calls
        // Test your authentication flow
    }
    
    func testTokenRefresh() async throws {
        // Test token refresh functionality
    }
    
    func testNetworkErrorHandling() async {
        // Test error handling scenarios
    }
}
```

## Security Considerations

1. **Token Storage**: Use Keychain for storing sensitive tokens instead of UserDefaults in production
2. **SSL Pinning**: Implement certificate pinning for production
3. **Data Validation**: Always validate data received from the API
4. **Offline Data**: Encrypt sensitive offline data
5. **Logging**: Avoid logging sensitive information in production

## API Rate Limiting

The API may implement rate limiting. Handle `429 Too Many Requests` responses:

```swift
func handleRateLimit() async throws {
    // Implement exponential backoff
    try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
    // Retry the request
}
```

## Conclusion

This guide provides a comprehensive foundation for integrating your Swift iOS app with the Tavonga CareConnect Django backend. The API supports all major features needed for autism and intellectual disability support systems, including user management, client tracking, activity logging, behavior incident reporting, goal setting, and shift management.

Remember to:
- Always handle errors gracefully
- Implement proper data caching for offline support
- Use secure storage for tokens
- Test thoroughly with different network conditions
- Follow iOS development best practices

For additional questions or issues, refer to the API documentation at `/swagger/` or `/redoc/` endpoints of your backend. 