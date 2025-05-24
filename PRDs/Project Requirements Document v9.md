---
title: "Project Requirements Document: Nova"
---

# Project Requirements Document: Nova

### 1. Introduction (Supplement)

This document outlines the requirements for implementing user accounts and authentication within the Student AI Assistant. This feature will allow users to create persistent accounts, log in, and manage their sessions. Data previously associated with temporary sessions (like uploaded documents, subjects, and journal entries) will be linked to individual user accounts, ensuring data privacy and persistence across sessions.

### 2. Goals and Objectives (Supplement)

* Implement a secure user account system (registration, login, logout).
* Associate all user-specific data (subjects, documents, journals, etc.) with a unique user ID instead of a temporary session ID.
* Ensure users can only access their own data after logging in.
* Store user credentials securely, including hashing passwords.
* Provide a clear user interface for account management.
* Integrate the authentication system seamlessly with the existing Flask application and MongoDB Atlas database.

### 3. User Stories (Supplement)

* As a student, I want to create a personal account so my subjects, documents, and chat history are saved permanently.
* As a student, I want to log in securely with a user ID (or email) and password.
* As a student, I want to be able to log out of my account easily.
* As a student, I want to be sure that only I can see my uploaded documents, subjects, and journal entries after I log in.
* As a student, I want an easily accessible section in the application to manage my account (log in, register, log out).

### 4. Functional Requirements (Supplement)

**4.1. User Account Creation (Registration)**

* **REQ-FUN-4.1.1:** Users shall be able to register for a new account.
* **REQ-FUN-4.1.2:** Registration shall require a unique user identifier (e.g., username or email address) and a password.
* **REQ-FUN-4.1.3:** Passwords entered during registration shall be securely hashed before being stored.
* **REQ-FUN-4.1.4:** The application shall validate registration input (e.g., check for unique username/email, password complexity if desired).
* **REQ-FUN-4.1.5:** Upon successful registration, a new user account record shall be created in the database.

**4.2. User Login**

* **REQ-FUN-4.2.1:** Registered users shall be able to log in using their user identifier and password.
* **REQ-FUN-4.2.2:** The application shall verify the provided credentials against the stored user data (comparing the hash of the provided password with the stored hash).
* **REQ-FUN-4.2.3:** Upon successful login, a user session shall be established, linking subsequent actions to the logged-in user's ID.

**4.3. User Logout**

* **REQ-FUN-4.3.1:** Logged-in users shall be able to log out of their accounts.
* **REQ-FUN-4.3.2:** Logging out shall terminate the current user session.

**4.4. Account Management UI**

* **REQ-FUN-4.4.1:** A dedicated "Account" section or button shall be added to the application's header or sidebar navigation.
* **REQ-FUN-4.4.2:** This section shall provide options/forms for user registration, login, and logout.

**4.5. Data Association and Privacy**

* **REQ-FUN-4.5.1:** All data currently associated with a `session_id` (e.g., subjects, document metadata, user journals, subject journals) shall now be associated with the `user_id` of the logged-in user.
* **REQ-FUN-4.5.2:** Existing data structures in MongoDB Atlas (subjects, document metadata, journal entries) shall be updated to include a mandatory `user_id` field.
* **REQ-FUN-4.5.3:** All application sections (Subjects, Timetable Generation, Quiz Generation, etc.) shall filter data to display only the information belonging to the currently logged-in user. Anonymous or non-logged-in users should not be able to access user-specific data.
* **REQ-FUN-4.5.4:** Data retrieval queries across the application must be modified to include a filter based on the `user_id` from the current session.

### 5. Technical Requirements (Supplement)

* **TECH-REQ-5.1:** Implement user authentication logic within the Flask application. Consider using established Flask extensions like Flask-Login or Flask-Security.
* **TECH-REQ-5.2:** Implement secure password hashing using a strong algorithm (e.g., bcrypt, Argon2) via libraries like `werkzeug.security` or `passlib`.
* **TECH-REQ-5.3:** Create a new MongoDB Atlas collection (e.g., `users`) to store user account information (`user_id`, `username`/`email`, `password_hash`).
* **TECH-REQ-5.4:** Modify existing MongoDB Atlas collections (`subjects`, `document_metadata`, `user_journals`, `subject_journals`) to include a `user_id` field and ensure it's indexed for efficient querying.
* **TECH-REQ-5.5:** Implement session management (e.g., using secure server-side sessions provided by Flask).
* **TECH-REQ-5.6:** Update all backend routes and database query logic to require user login where necessary and to filter data based on the logged-in `user_id`.
* **TECH-REQ-5.7:** Implement new Flask routes for handling registration, login, and logout requests.
* **TECH-REQ-5.8:** Ensure secure handling of user credentials and session data.

### 6. UI/UX Requirements (Supplement)

* **UI-UX-6.1:** Design clear and user-friendly forms for registration and login.
* **UI-UX-6.2:** Integrate the Account button/section seamlessly into the existing header or sidebar navigation.
* **UI-UX-6.3:** Provide clear feedback to the user upon successful/failed registration, login, and logout attempts.
* **UI-UX-6.4:** Ensure the application clearly indicates the logged-in state (e.g., displaying username, changing Account button text to "Logout").

### 7. Data Management (Supplement)

* **DATA-7.1:** A new `users` collection will be created in MongoDB Atlas.
* **DATA-7.2:** Existing collections (`subjects`, `document_metadata`, `user_journals`, `subject_journals`) must be modified to include a `user_id` field. Consider data migration strategies if existing session-based data needs to be associated with newly created user accounts (though this might be out of scope initially).
* **DATA-7.3:** Password hashes must be stored securely; plaintext passwords must never be stored.

### 8. Future Considerations (Supplement)

* Password recovery mechanism (e.g., "Forgot Password" email link).
* User profile management (e.g., changing password, updating email).
* Role-based access control (if different user types are needed later).
* Integration with third-party authentication providers (e.g., Google, GitHub).