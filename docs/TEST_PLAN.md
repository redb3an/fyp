# Chatbot System Test Plan

## 5.2. Test Plan

### 5.2.1 Unit Testing

#### Name of program: User Authentication System (register_user, login_user, logout_user)

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Register with blank email | email: "", password: "test123", name: "Test User" | "Email, password, and full name are required" | | |
| TC2 | Register with blank password | email: "test@example.com", password: "", name: "Test User" | "Email, password, and full name are required" | | |
| TC3 | Register with blank name | email: "test@example.com", password: "test123", name: "" | "Email, password, and full name are required" | | |
| TC4 | Register with short password | email: "test@example.com", password: "123", name: "Test User" | "Password must be at least 8 characters long" | | |
| TC5 | Register with mismatched passwords | email: "test@example.com", password: "test123", confirmPassword: "test456", name: "Test User" | "Passwords do not match" | | |
| TC6 | Register with existing email | email: "existing@example.com", password: "test123", name: "Test User" | "An account with this email already exists" | | |
| TC7 | Register with valid data | email: "newuser@example.com", password: "test123", confirmPassword: "test123", name: "New User" | Success response with user created | | |
| TC8 | Login with blank email | email: "", password: "test123" | "Email and password are required" | | |
| TC9 | Login with blank password | email: "test@example.com", password: "" | "Email and password are required" | | |
| TC10 | Login with invalid credentials | email: "wrong@example.com", password: "wrongpass" | "Invalid email or password" | | |
| TC11 | Login with valid credentials | email: "valid@example.com", password: "validpass" | Success response with JWT token | | |
| TC12 | Logout with valid token | Valid JWT token | Success response | | |
| TC13 | Logout with invalid token | Invalid JWT token | "Invalid token" | | |

**Description:** Tests user registration, login, and logout functionality with various input scenarios including validation, authentication, and error handling.

#### Name of program: Conversation Management System (create_conversation, get_conversations, delete_conversation)

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Create conversation without authentication | No auth token | "Authentication required" | | |
| TC2 | Create conversation with valid auth | Valid JWT token | Success response with conversation ID | | |
| TC3 | Get conversations without authentication | No auth token | "Authentication required" | | |
| TC4 | Get conversations with valid auth | Valid JWT token | List of user's conversations | | |
| TC5 | Get conversations for user with no conversations | Valid JWT token for new user | Empty list | | |
| TC6 | Delete conversation without authentication | No auth token | "Authentication required" | | |
| TC7 | Delete conversation with invalid ID | Valid JWT token, invalid conversation ID | "Conversation not found" | | |
| TC8 | Delete conversation with valid ID | Valid JWT token, valid conversation ID | Success response | | |
| TC9 | Delete conversation owned by different user | Valid JWT token, other user's conversation ID | "Access denied" | | |
| TC10 | Rename conversation without authentication | No auth token | "Authentication required" | | |
| TC11 | Rename conversation with valid data | Valid JWT token, valid conversation ID, new title | Success response | | |
| TC12 | Rename conversation with blank title | Valid JWT token, valid conversation ID, "" | "Title cannot be blank" | | |

**Description:** Tests conversation creation, retrieval, deletion, and renaming functionality with proper authentication and authorization checks.

#### Name of program: Chat Message System (chat_endpoint, get_conversation_messages)

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Send message without authentication | No auth token | "Authentication required" | | |
| TC2 | Send message with blank content | Valid JWT token, message: "" | "Message content is required" | | |
| TC3 | Send message with valid content | Valid JWT token, message: "Hello Gigi" | Bot response | | |
| TC4 | Send message to non-existent conversation | Valid JWT token, invalid conversation ID | "Conversation not found" | | |
| TC5 | Send message to other user's conversation | Valid JWT token, other user's conversation ID | "Access denied" | | |
| TC6 | Get messages without authentication | No auth token | "Authentication required" | | |
| TC7 | Get messages for valid conversation | Valid JWT token, valid conversation ID | List of messages | | |
| TC8 | Get messages for non-existent conversation | Valid JWT token, invalid conversation ID | "Conversation not found" | | |
| TC9 | Send message with very long content | Valid JWT token, message: 10000+ characters | "Message too long" or truncated | | |
| TC10 | Send message with special characters | Valid JWT token, message: "Hello! @#$%^&*()" | Bot response | | |

**Description:** Tests message sending and retrieval functionality, including authentication, validation, and conversation access control.

#### Name of program: Admin Dashboard System (admin_dashboard, get_admin_analytics)

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Access admin dashboard without authentication | No auth token | "Authentication required" | | |
| TC2 | Access admin dashboard as regular user | Valid JWT token (regular user) | "Access denied" | | |
| TC3 | Access admin dashboard as superuser | Valid JWT token (superuser) | Admin dashboard with analytics | | |
| TC4 | Get analytics without authentication | No auth token | "Authentication required" | | |
| TC5 | Get analytics as regular user | Valid JWT token (regular user) | "Access denied" | | |
| TC6 | Get analytics as superuser | Valid JWT token (superuser) | Analytics data (users, chats, etc.) | | |
| TC7 | Create user as admin | Valid JWT token (superuser), user data | Success response | | |
| TC8 | Create user as regular user | Valid JWT token (regular user), user data | "Access denied" | | |
| TC9 | Update user as admin | Valid JWT token (superuser), user ID, updated data | Success response | | |
| TC10 | Delete user as admin | Valid JWT token (superuser), user ID | Success response | | |
| TC11 | Delete user as regular user | Valid JWT token (regular user), user ID | "Access denied" | | |

**Description:** Tests admin dashboard access, analytics retrieval, and user management functionality with proper role-based access control.

#### Name of program: Session Management System (session_heartbeat, get_active_sessions)

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Session heartbeat without authentication | No auth token | "Authentication required" | | |
| TC2 | Session heartbeat with valid auth | Valid JWT token | Success response | | |
| TC3 | Session heartbeat with expired token | Expired JWT token | "Token expired" | | |
| TC4 | Get active sessions without authentication | No auth token | "Authentication required" | | |
| TC5 | Get active sessions as regular user | Valid JWT token (regular user) | "Access denied" | | |
| TC6 | Get active sessions as superuser | Valid JWT token (superuser) | List of active sessions | | |
| TC7 | Terminate session as admin | Valid JWT token (superuser), session ID | Success response | | |
| TC8 | Terminate all sessions as admin | Valid JWT token (superuser) | Success response | | |
| TC9 | Session auto-expiry | Wait for session expiry | Session marked as expired | | |
| TC10 | Session cleanup | Run cleanup command | Expired sessions removed | | |

**Description:** Tests session management functionality including heartbeat, session monitoring, and cleanup operations.

#### Name of program: Chatbot Service (GroqChatbot)

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Get response with blank prompt | prompt: "" | Error or default response | | |
| TC2 | Get response with valid prompt | prompt: "Hello Gigi" | Bot response | | |
| TC3 | Get response with very long prompt | prompt: 5000+ characters | Response or error | | |
| TC4 | Get response with special characters | prompt: "Hello! @#$%^&*()" | Bot response | | |
| TC5 | Get response with conversation context | prompt: "Hello", conversation object | Context-aware response | | |
| TC6 | Get response with user context | prompt: "Hello", user object | User-aware response | | |
| TC7 | Get response with memory extraction | prompt: "Hello", extract_memory: True | Response with memory data | | |
| TC8 | Model refresh functionality | Call refresh_model() | Model updated | | |
| TC9 | Get response with knowledge context | prompt: "APU programs" | Response with APU knowledge | | |
| TC10 | Get response with program recommendations | prompt: "recommend programs" | Program recommendations | | |

**Description:** Tests the core chatbot service functionality including response generation, context handling, and memory management.

#### Name of program: RAG Service (Enhanced RAG)

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Get context with blank prompt | prompt: "" | Empty context or error | | |
| TC2 | Get context with valid prompt | prompt: "APU programs" | Relevant context | | |
| TC3 | Get context with conversation | prompt: "programs", conversation object | Context-aware results | | |
| TC4 | Get context with user preferences | prompt: "programs", user object | Personalized context | | |
| TC5 | Search programs with valid query | query: "computer science" | Program results | | |
| TC6 | Search programs with invalid query | query: "" | Empty results or error | | |
| TC7 | Get faculty programs | faculty: "Computing" | Faculty programs | | |
| TC8 | Get faculty programs with invalid faculty | faculty: "InvalidFaculty" | Empty results | | |
| TC9 | Knowledge base search | query: "fees" | Fee information | | |
| TC10 | Knowledge base search with no results | query: "nonexistent" | Empty results | | |

**Description:** Tests the RAG (Retrieval-Augmented Generation) service functionality for context retrieval and knowledge base search.

#### Name of program: Speech Services (Transcription, TTS)

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Transcribe audio without file | No audio file | "No audio file provided" | | |
| TC2 | Transcribe audio with invalid file | Invalid file format | "Invalid file format" | | |
| TC3 | Transcribe audio with valid file | Valid audio file | Transcribed text | | |
| TC4 | Text-to-speech with blank text | text: "" | Error or silence | | |
| TC5 | Text-to-speech with valid text | text: "Hello Gigi" | Audio file | | |
| TC6 | Start recording without authentication | No auth token | "Authentication required" | | |
| TC7 | Start recording with valid auth | Valid JWT token | Success response | | |
| TC8 | Stop recording without session | No recording session | "No active recording" | | |
| TC9 | Stop recording with valid session | Valid recording session | Audio file | | |
| TC10 | Transcribe from microphone | Valid audio input | Transcribed text | | |

**Description:** Tests speech-to-text and text-to-speech functionality including audio file handling and real-time recording.

#### Name of program: File Upload System

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Upload without file | No file | "No file provided" | | |
| TC2 | Upload with invalid file type | Invalid file type | "Invalid file type" | | |
| TC3 | Upload with large file | File > 10MB | "File too large" | | |
| TC4 | Upload with valid file | Valid file | Success response with file URL | | |
| TC5 | Upload with authentication required | No auth token | "Authentication required" | | |
| TC6 | Upload with valid authentication | Valid JWT token, valid file | Success response | | |

**Description:** Tests file upload functionality including validation, size limits, and authentication requirements.

#### Name of program: User Profile Management

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Get user theme without authentication | No auth token | "Authentication required" | | |
| TC2 | Get user theme with valid auth | Valid JWT token | User's theme preference | | |
| TC3 | Set user theme without authentication | No auth token | "Authentication required" | | |
| TC4 | Set user theme with valid data | Valid JWT token, theme: "dark" | Success response | | |
| TC5 | Set user theme with invalid theme | Valid JWT token, theme: "invalid" | "Invalid theme" | | |
| TC6 | Update user profile | Valid JWT token, profile data | Success response | | |
| TC7 | Get user profile | Valid JWT token | User profile data | | |

**Description:** Tests user profile management including theme preferences and profile updates.

#### Name of program: Memory Management System

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Extract memory from message | Message object | Memory objects | | |
| TC2 | Get short-term context | Conversation object | Recent messages | | |
| TC3 | Get cross-learning insights | User object | Learning insights | | |
| TC4 | Get RAG context memories | Conversation object | RAG context | | |
| TC5 | Memory cleanup | Run cleanup | Expired memories removed | | |
| TC6 | Memory access tracking | Access memory | Access count incremented | | |
| TC7 | Memory expiry check | Check expired memory | Memory marked as expired | | |
| TC8 | Memory strategy selection | Different strategies | Appropriate memory handling | | |

**Description:** Tests conversation memory management including extraction, storage, retrieval, and cleanup functionality.

#### Name of program: Program Recommendation System

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Get recommendations with blank criteria | academic_background: "", interests: [] | Error or default recommendations | | |
| TC2 | Get recommendations with valid data | Valid academic background, interests, goals | Program recommendations | | |
| TC3 | Get recommendations with budget filter | Valid criteria, budget_range: "50000-100000" | Filtered recommendations | | |
| TC4 | Get recommendations with study mode filter | Valid criteria, study_mode: "full-time" | Filtered recommendations | | |
| TC5 | Save recommendation | Valid recommendation data | Success response | | |
| TC6 | Get user recommendations | User object | User's recommendations | | |
| TC7 | Update recommendation status | Recommendation ID, new status | Success response | | |

**Description:** Tests program recommendation functionality including criteria-based filtering and recommendation tracking.









### 5.2.2 Integration Testing

#### Name of program: End-to-End Chat Flow

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Complete user registration and chat | Register → Login → Create conversation → Send message | Full chat interaction | | |
| TC2 | Chat with memory persistence | Multiple messages in conversation | Context-aware responses | | |
| TC3 | Chat with file upload | Send message → Upload file → Continue chat | File-aware responses | | |
| TC4 | Chat with speech input | Voice message → Transcription → Response | Speech-enabled chat | | |
| TC5 | Chat with program recommendations | Ask for recommendations → Get suggestions → Save preferences | Recommendation flow | | |
| TC6 | Admin monitoring of chat | Admin dashboard → View user chats → Analytics | Admin oversight | | |
| TC7 | Session management during chat | Long chat session → Heartbeat → Session extension | Session persistence | | |

**Description:** Tests complete user workflows from registration through chat interactions with all system components.

### 5.2.3 Performance Testing

#### Name of program: System Performance

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Response time under normal load | 10 concurrent users | Response time < 2 seconds | | |
| TC2 | Response time under high load | 100 concurrent users | Response time < 5 seconds | | |
| TC3 | Memory usage during chat | Long conversation (50+ messages) | Memory usage < 512MB | | |
| TC4 | Database query performance | Large dataset (1000+ users) | Query time < 1 second | | |
| TC5 | File upload performance | 5MB file upload | Upload time < 30 seconds | | |
| TC6 | Speech processing performance | 30-second audio file | Processing time < 60 seconds | | |
| TC7 | Concurrent session handling | 50 active sessions | All sessions maintained | | |

**Description:** Tests system performance under various load conditions and resource usage patterns.

### 5.2.4 Security Testing

#### Name of program: Security Validation

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | SQL injection attempt | Malicious SQL in input | Input sanitized or rejected | | |
| TC2 | XSS attack attempt | Malicious JavaScript in input | Input sanitized or rejected | | |
| TC3 | CSRF attack attempt | Forged request | Request rejected | | |
| TC4 | JWT token tampering | Modified token | Authentication failed | | |
| TC5 | File upload security | Malicious file upload | File rejected | | |
| TC6 | Session hijacking attempt | Stolen session token | Session invalidated | | |
| TC7 | Privilege escalation attempt | Regular user accessing admin | Access denied | | |
| TC8 | Rate limiting | Multiple rapid requests | Requests throttled | | |

**Description:** Tests security measures including input validation, authentication, authorization, and attack prevention.

### 5.2.5 User Interface Testing

#### Name of program: Frontend Components

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Login form validation | Invalid email format | Error message displayed | | |
| TC2 | Registration form validation | Missing required fields | Error messages displayed | | |
| TC3 | Chat interface responsiveness | Different screen sizes | Interface adapts properly | | |
| TC4 | Theme switching | Toggle between light/dark | Theme changes immediately | | |
| TC5 | File upload interface | Drag and drop file | File uploaded successfully | | |
| TC6 | Voice recording interface | Click record button | Recording starts/stops | | |
| TC7 | Admin dashboard navigation | Click different sections | Correct data displayed | | |
| TC8 | Mobile responsiveness | Mobile device access | Mobile-friendly interface | | |

**Description:** Tests user interface functionality, responsiveness, and user experience across different devices and scenarios.

### 5.2.6 Database Testing

#### Name of program: Data Persistence

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | User data persistence | Create user → Restart system → Login | User data preserved | | |
| TC2 | Conversation data persistence | Create conversation → Restart system → Retrieve | Conversation preserved | | |
| TC3 | Message data persistence | Send message → Restart system → Retrieve | Message preserved | | |
| TC4 | Soft delete functionality | Delete conversation → Check database | Record marked as deleted | | |
| TC5 | Data integrity constraints | Invalid foreign key | Constraint violation | | |
| TC6 | Database backup and restore | Backup → Restore → Verify data | Data integrity maintained | | |
| TC7 | Concurrent data access | Multiple users modifying same data | Data consistency maintained | | |

**Description:** Tests database operations, data persistence, and integrity across system restarts and concurrent access.

### 5.2.7 API Testing

#### Name of program: REST API Endpoints

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | API endpoint availability | GET /api/health | Service status | | |
| TC2 | API authentication | POST /api/login | JWT token returned | | |
| TC3 | API authorization | Protected endpoint without token | 401 Unauthorized | | |
| TC4 | API rate limiting | Multiple rapid requests | 429 Too Many Requests | | |
| TC5 | API error handling | Invalid request data | Appropriate error response | | |
| TC6 | API response format | Valid request | JSON response with correct structure | | |
| TC7 | API versioning | Different API versions | Correct version handling | | |

**Description:** Tests REST API functionality, authentication, authorization, and error handling.

### 5.2.8 Accessibility Testing

#### Name of program: Accessibility Compliance

| TC-No | Test Case | Input Data | Expected Output | Actual Output | Status (Passed/Failed) |
|-------|-----------|------------|-----------------|---------------|------------------------|
| TC1 | Screen reader compatibility | Use screen reader | All elements announced | | |
| TC2 | Keyboard navigation | Navigate with keyboard only | All functions accessible | | |
| TC3 | Color contrast | Check color combinations | WCAG AA compliance | | |
| TC4 | Alt text for images | Check image alt attributes | All images have alt text | | |
| TC5 | Form labels | Check form accessibility | All inputs have labels | | |
| TC6 | Focus indicators | Tab through interface | Clear focus indicators | | |
| TC7 | Error message accessibility | Trigger errors | Errors announced to screen readers | | |

**Description:** Tests accessibility features and compliance with WCAG guidelines for users with disabilities.

## Test Execution Guidelines

### Prerequisites
1. Set up test environment with clean database
2. Configure test API keys and external services
3. Prepare test data sets
4. Set up monitoring and logging for test execution

### Test Data Requirements
1. Test user accounts (regular users, admin users)
2. Sample conversations and messages
3. Test files (audio, documents)
4. Mock external service responses

### Test Environment Setup
1. Development/staging environment
2. Isolated database for testing
3. Mock external APIs where appropriate
4. Performance monitoring tools

### Test Reporting
1. Automated test execution reports
2. Manual test execution logs
3. Bug reports with detailed steps
4. Performance test results
5. Security test findings

### Continuous Testing
1. Automated unit tests on code commit
2. Integration tests on deployment
3. Performance tests on schedule
4. Security scans on regular basis 