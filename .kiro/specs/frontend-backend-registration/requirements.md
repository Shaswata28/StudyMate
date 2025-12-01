# Requirements Document

## Introduction

This document specifies the requirements for integrating the frontend registration flow with the Python backend authentication system. The system enables users to create accounts through a two-step registration process: first providing security credentials (email/password), then completing their academic profile. The integration ensures seamless communication between the React frontend and FastAPI backend using JWT-based authentication.

## Glossary

- **Frontend**: The React-based client application that provides the user interface
- **Backend**: The Python FastAPI server that handles authentication and data persistence
- **JWT Token**: JSON Web Token used for authenticating API requests
- **Academic Profile**: User's educational information including grade, semester type, semester number, and subjects
- **Registration Flow**: The two-step process of account creation (security + academic profile)
- **Auth Service**: The frontend service class that manages authentication operations
- **Supabase**: The backend authentication and database provider
- **Access Token**: Short-lived JWT token for authenticating API requests
- **Refresh Token**: Long-lived token for obtaining new access tokens

## Requirements

### Requirement 1

**User Story:** As a new user, I want to register with my email and password, so that I can create an account and access the application.

#### Acceptance Criteria

1. WHEN a user submits valid email and password on step 1 THEN the Frontend SHALL send a POST request to `/api/auth/signup` with the credentials
2. WHEN the Backend receives a signup request with valid credentials THEN the Backend SHALL create a new user account and return access token, refresh token, and user information
3. WHEN the Backend receives a signup request with an email that already exists THEN the Backend SHALL return a 400 error with message "A user with this email already exists"
4. WHEN the Frontend receives a successful signup response THEN the Frontend SHALL store the access token, refresh token, and user information in localStorage
5. WHEN the Frontend receives an error response from signup THEN the Frontend SHALL display the error message to the user

### Requirement 2

**User Story:** As a new user completing registration, I want to provide my academic information, so that the system can personalize my learning experience.

#### Acceptance Criteria

1. WHEN a user completes step 1 successfully THEN the Frontend SHALL display step 2 with academic profile fields
2. WHEN a user submits academic profile information THEN the Frontend SHALL send a POST request to `/api/academic` with the access token in the Authorization header
3. WHEN the Backend receives an academic profile request with valid authentication THEN the Backend SHALL create the academic profile record linked to the user
4. WHEN the Backend receives an academic profile request without valid authentication THEN the Backend SHALL return a 401 error
5. WHEN the Frontend receives a successful academic profile response THEN the Frontend SHALL navigate the user to the onboarding page

### Requirement 3

**User Story:** As a user, I want my authentication tokens to be managed automatically, so that I can have a seamless experience without manual token handling.

#### Acceptance Criteria

1. WHEN the Frontend makes an authenticated API request THEN the Frontend SHALL include the access token in the Authorization header as "Bearer {token}"
2. WHEN the Backend receives a request with an expired access token THEN the Backend SHALL return a 401 error
3. WHEN the Frontend receives a 401 error on an authenticated request THEN the Frontend SHALL attempt to refresh the access token using the refresh token
4. WHEN the Frontend successfully refreshes the access token THEN the Frontend SHALL retry the original request with the new token
5. WHEN the Frontend fails to refresh the access token THEN the Frontend SHALL clear all tokens and redirect to login

### Requirement 4

**User Story:** As a developer, I want comprehensive error handling throughout the registration flow, so that users receive clear feedback when issues occur.

#### Acceptance Criteria

1. WHEN the Backend encounters a validation error THEN the Backend SHALL return a 400 error with a descriptive error message
2. WHEN the Backend encounters an authentication error THEN the Backend SHALL return a 401 error with message "Invalid or expired authentication token"
3. WHEN the Backend encounters a server error THEN the Backend SHALL return a 500 error with message "An unexpected error occurred"
4. WHEN the Frontend receives an error response THEN the Frontend SHALL extract the error message from the response detail field
5. WHEN the Frontend displays an error THEN the Frontend SHALL show the error using the toast notification system

### Requirement 5

**User Story:** As a user, I want my registration to complete atomically, so that I don't end up with a partial account if something fails.

#### Acceptance Criteria

1. WHEN step 1 (signup) fails THEN the Frontend SHALL not proceed to step 2
2. WHEN step 2 (academic profile) fails THEN the Frontend SHALL display an error but keep the user authenticated
3. WHEN the user closes the browser during registration THEN the Frontend SHALL preserve authentication state in localStorage
4. WHEN an authenticated user returns to the signup page THEN the Frontend SHALL redirect them to the appropriate page based on their profile completion status
5. WHEN the Backend creates an academic profile THEN the Backend SHALL verify the user is authenticated before creating the record

### Requirement 6

**User Story:** As a system administrator, I want all API communication to follow RESTful conventions, so that the system is maintainable and predictable.

#### Acceptance Criteria

1. WHEN the Frontend sends a signup request THEN the Frontend SHALL use POST method with Content-Type "application/json"
2. WHEN the Backend returns a successful signup THEN the Backend SHALL return HTTP status 201 (Created)
3. WHEN the Backend returns a successful academic profile creation THEN the Backend SHALL return HTTP status 201 (Created)
4. WHEN the Backend returns an error THEN the Backend SHALL use appropriate HTTP status codes (400 for validation, 401 for auth, 500 for server errors)
5. WHEN the Frontend makes any API request THEN the Frontend SHALL use the configured API_BASE_URL from environment variables

### Requirement 7

**User Story:** As a user, I want my password to be validated before submission, so that I create a secure account.

#### Acceptance Criteria

1. WHEN a user enters a password THEN the Frontend SHALL display a password strength indicator
2. WHEN a user submits step 1 with a password shorter than 8 characters THEN the Frontend SHALL display an error "Password must be at least 8 characters"
3. WHEN a user submits step 1 with mismatched passwords THEN the Frontend SHALL display an error "Passwords do not match"
4. WHEN the Backend receives a password shorter than 8 characters THEN the Backend SHALL return a 400 error
5. WHEN a user enters a valid password THEN the Frontend SHALL enable the submit button

### Requirement 8

**User Story:** As a user, I want my academic profile data to be validated, so that I provide complete and correct information.

#### Acceptance Criteria

1. WHEN a user submits step 2 without selecting a grade THEN the Frontend SHALL display an error "Grade is required"
2. WHEN a user submits step 2 without selecting a semester type THEN the Frontend SHALL display an error "Semester type is required"
3. WHEN a user submits step 2 without selecting a semester number THEN the Frontend SHALL display an error "Semester is required"
4. WHEN a user submits step 2 without selecting a subject THEN the Frontend SHALL display an error "Subject is required"
5. WHEN the Backend receives an academic profile with missing required fields THEN the Backend SHALL return a 400 error with details of missing fields

### Requirement 9

**User Story:** As a new user completing registration, I want to set my learning preferences after providing my academic information, so that the system can tailor content to my learning style.

#### Acceptance Criteria

1. WHEN a user successfully completes academic profile submission THEN the Frontend SHALL navigate to the preferences/onboarding page
2. WHEN a user submits learning preferences THEN the Frontend SHALL send a POST request to `/api/preferences` with the access token in the Authorization header
3. WHEN the Backend receives a preferences request with valid authentication THEN the Backend SHALL create or update the preferences record linked to the user
4. WHEN the Backend receives a preferences request without valid authentication THEN the Backend SHALL return a 401 error
5. WHEN the Frontend receives a successful preferences response THEN the Frontend SHALL navigate the user to the dashboard or main application
