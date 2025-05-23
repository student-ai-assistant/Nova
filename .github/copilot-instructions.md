# Copilot Instructions for Student AI Assistant Flask Application

This document provides guidelines and best practices for contributing to the development of the Student AI Assistant Flask application.

## Project Overview

The Student AI Assistant is a Flask-based web application designed to help students with their studies. The application now features **user accounts with secure login/registration** and **data persistence tied to individual users**. The front page features a redesigned welcoming layout with a central motivational message and a general chat interface (with temporary file context upload). A subject-specific section allows logged-in users to upload documents for persistent storage (linked to their account) and chat with an AI agent using these documents as context, including an option to delete uploaded documents. A refined multi-level AI agent system generates personalized study timetables based on user documents and journal entries. A Literature Review feature allows users to generate research reports based on a query. A Quiz Generation feature enables students to create and take multiple-choice quizzes based on their subject documents. The application features an improved overall design with final touches and a dark mode toggle. The application utilizes MongoDB Atlas for persistent data storage (user accounts, subjects, document metadata, journals). The user interface aims for a modern aesthetic using Tailwind CSS and Material Design principles. **All user-specific data sections are now filtered to show only the logged-in user's data.**

## Technologies Used

* **Backend:** Flask (Python), pymongo (for MongoDB interaction), icalendar (for .ics file generation), **Flask-Login (or similar for authentication)**, **Werkzeug/passlib/bcrypt (for password hashing)**
* **Database:** MongoDB Atlas
* **Frontend:** HTML, CSS, JavaScript, Tailwind CSS (with potential use of Material Tailwind components)
* **AI Services:** Azure AI (Azure OpenAI Service, Azure AI Document Intelligence, potentially Azure AI Search for RAG, potentially Azure AI Agent Service or frameworks like Semantic Kernel/AutoGen for orchestration)
* **Package Management:** Conda
* **Frontend Build Tools:** npm or yarn (for Tailwind CSS compilation)
* **Version Control:** Git

## Code Structure

Maintain a clear and organized directory structure for the Flask application. A suggested structure is as follows:

```
student-ai-assistant/
├── conda_env/              # Conda environment files (or specify environment name)
├── static/
│   ├── css/
│   │   └── style.css       # Compiled Tailwind CSS output (includes light/dark mode styles)
│   ├── js/
│   │   └── main.js         # Frontend JavaScript for general interactions, front page, UI logic (dark mode, deletion, auth UI)
│   └── src/                # Tailwind CSS source and config
│       ├── input.css       # Main Tailwind input file
│       └── tailwind.config.js
├── templates/
│   ├── index.html          # Front page with general chat and motivational message
│   ├── base.html           # Base template (includes header/sidebar with Account section/button)
│   ├── subjects.html       # Subject list page (filtered by user)
│   ├── subject_detail.html # Specific subject page with chat and document listings (filtered by user)
│   ├── timetable.html      # Timetable generation page (uses user's data)
│   ├── research_assistant.html # Literature Review page
│   ├── quiz.html           # Quiz Generation page (uses user's data)
│   ├── login.html          # User login form
│   └── register.html       # User registration form
├── uploaded_documents/     # Directory for storing actual uploaded subject document files (persistent)
├── agents/                 # Directory for AI agent routines
│   └── research_agent.py   # Contains run_lit_review routine
├── auth/                   # Blueprint/module for authentication routes and logic
│   ├── init.py
│   └── routes.py
├── models.py               # Defines User model (potentially using Flask-Login's UserMixin)
├── app.py                  # Main Flask application instance (or use a factory pattern)
├── config.py               # Configuration for Azure keys, MongoDB URI, SECRET_KEY etc.
├── environment.yml         # Conda environment file (will include pymongo, Azure AI SDKs, icalendar, Flask-Login, bcrypt/passlib)
└── .env                    # Environment variables (for sensitive keys, MongoDB URI, Flask SECRET_KEY)
```

* Use Flask Blueprints to modularize different sections (e.g., `general_chat`, `subjects`, `timetable`, `research_assistant`, `quiz`, `api`, **`auth`**).
* Keep frontend assets (CSS, JS, images) separate from backend logic.
* Store **persistent** uploaded files (subject documents) in a dedicated and secure location on the server or a cloud storage service, storing the metadata and link/path in MongoDB Atlas. Files uploaded for general chat context are NOT stored here.
* Organize backend AI agent routines in a dedicated directory like `agents/`.
* Define user models (e.g., in `models.py`) potentially using `UserMixin` from Flask-Login.

## Best Practices

### Flask Backend

* **Modularity:** Use Flask Blueprints for features (**including `auth`**).
* **Authentication & Authorization:**
    * Implement user registration, login (verifying hashed passwords), and logout functionality using Flask-Login or similar extensions.
    * Securely hash passwords using `bcrypt` or `Argon2`. Never store plain text passwords.
    * Manage user sessions securely (e.g., using Flask's session handling with a strong `SECRET_KEY`).
    * Use the `@login_required` decorator (from Flask-Login) to protect routes/endpoints that require a logged-in user.
* **Request Handling:** Validate and sanitize user input (forms, API requests, login/registration data).
* **API Endpoints & Data Access:** Ensure all endpoints retrieving user-specific data (subjects, documents, journals) filter results based on the `current_user.id` (provided by Flask-Login). Update document deletion endpoint (`/api/subjects/<subject_id>/documents/<document_id>/delete`) to check user ownership before deletion.
* **Template Rendering:** Pass necessary data to templates, including user status (`current_user.is_authenticated`).
* **Error Handling:** Implement proper error handling for routes, API calls, database errors, AI service errors, file processing errors, **authentication failures (invalid login, registration errors)**, and document deletion errors.
* **Configuration:** Use `config.py` or `.env` for settings (Azure keys, MongoDB URI, **Flask `SECRET_KEY`**). Never hardcode sensitive information.

### MongoDB Atlas

* **Connection Management:** Establish a secure connection using `pymongo` and the connection URI.
* **Data Models / Collections:**
    * **`users`:** Store user information (`_id`, `username`/`email`, `password_hash`).
    * **`subjects`:** (`name`, `user_id`)
    * **`document_metadata`:** (`_id`, `filename`, `upload_timestamp`, `size`, `subject_id`, **`user_id`**, `storage_path`) - Ensure queries use `user_id`. **Deletion targets `_id` and checks `user_id`.**
    * **`user_journals`:** (`user_id`, `timestamp`, `content`)
    * **`subject_journals`:** (`user_id`, `subject_id`, `timestamp`, `content`)
* **Querying:** Write efficient queries using `pymongo`. **Crucially, filter all user-data queries by the `user_id` obtained from the authenticated session (`current_user.id`).** Index the `user_id` field in relevant collections.

### Frontend (HTML, CSS, JavaScript)

* **Tailwind CSS:** Utilize utility-first classes for styling, ensuring consistency. Apply classes for layouts, interactive elements, loading indicators, quiz/results display, front page redesign, dark mode, **login/registration forms, and account status indicators.** Implement dark mode styles. Apply design improvements.
* **Material Design:** Apply Material Design principles using Tailwind classes.
* **Responsiveness:** Ensure the UI is responsive.
* **JavaScript:** Use plain JavaScript for dynamic interactions.
    * Implement UI logic for chat, sidebar, subjects, timetable, literature review, quiz, dark mode toggle, and document deletion (confirmation dialog, API call).
    * **Implement UI logic for the Account section: potentially showing/hiding login/register/logout based on authentication status.**
    * **Handle form submissions for login and registration (client-side validation can be helpful).**
* **HTML Structure:** Use semantic HTML5 elements. Create new templates (`login.html`, `register.html`). **Add the Account button/link to the header/sidebar in `base.html`, potentially changing its text/target based on `current_user.is_authenticated`.** Add delete icons in `subject_detail.html`.

### Azure AI Integration

* **Secure Credentials:** Load keys/endpoints from configuration.
* **Context:** Ensure AI agents receive context relevant to the **logged-in user** (e.g., user's journal entries, user's subject documents).

### File Handling

* **Secure Uploads (Subject Documents):** Implement secure file upload handling (**linked to `user_id`**), validation, persistent storage, and metadata in MongoDB Atlas. **Implement secure deletion based on `user_id` authorization.**
* **Secure Uploads (General Chat):** Process in memory only.

### Data Management

* **MongoDB Atlas:** Primary database. Implement user collection and add `user_id` to all user-specific data collections. **Ensure delete operations check `user_id` authorization.**
* **Data Privacy:** Handle data securely. **Filter all data access by the logged-in user.** Ensure document deletion removes user data correctly.

### General

* **Conda Environments:** Use Conda (`environment.yml`) including **authentication/hashing libraries**.
* **Code Style:** Adhere to PEP 8.
* **Comments:** Write clear comments for complex logic, especially **authentication flows, password hashing, session management, user-specific data querying,** AI integration, file handling (upload/deletion), and UI logic.
* **Version Control:** Use Git with frequent, descriptive commits.

## Development Workflow

1.  Clone the repository.
2.  Create/update the Conda environment (`conda env create -f environment.yml` or `conda env update --file environment.yml --prune`). Ensure **Flask-Login, bcrypt/passlib** are included.
3.  Activate the Conda environment.
4.  Set up environment variables (`.env`), including MongoDB URI, Azure keys, and a strong **Flask `SECRET_KEY`**.
5.  Install/update frontend dependencies (`npm install` or `yarn install`).
6.  Compile Tailwind CSS (`npx tailwindcss ... --watch`). Define/implement dark mode styles.
7.  Run the Flask development server (`flask run` or `python app.py`).
8.  Develop features:
    * Implement all previously defined features.
    * **Implement User Authentication:** Set up Flask-Login, create user model, implement registration/login/logout routes and logic (including password hashing).
    * **Update Data Access:** Modify all database queries for subjects, documents, journals, etc., to filter by `current_user.id`.
    * **Protect Routes:** Add `@login_required` to necessary routes.
    * **Implement Frontend:** Create login/register pages, add Account section to header/sidebar, update UI to reflect login state.
    * Implement dark mode toggle, design improvements, and document deletion (checking user ownership).
9.  Test thoroughly, including **registration, login, logout, access control (trying to access data without login or as another user),** and all existing features with user context.
10. Commit changes and push.