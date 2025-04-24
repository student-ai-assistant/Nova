# Copilot Instructions for Student AI Assistant Flask Application

This document provides guidelines and best practices for contributing to the development of the Student AI Assistant Flask application.

## Project Overview

The Student AI Assistant is a Flask-based web application designed to help students with their studies. The front page features a redesigned welcoming layout with a central motivational message and a general chat interface at the bottom, with the ability to upload a file for temporary, in-memory context. A subject-specific section allows users to upload documents for persistent storage and chat with an AI agent using these documents as context, **including an option to delete uploaded documents**. A refined multi-level AI agent system (three agents) generates personalized study timetables. A Literature Review feature allows users to generate research reports based on a query. A Quiz Generation feature enables students to create and take multiple-choice quizzes. The application features an **improved overall design with final touches and a dark mode toggle**. The application utilizes MongoDB Atlas for persistent data storage. The user interface aims for a modern aesthetic using Tailwind CSS and Material Design principles.

## Technologies Used

* **Backend:** Flask (Python), pymongo (for MongoDB interaction), icalendar (for .ics file generation)
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
│   │   └── main.js         # Frontend JavaScript for general interactions, front page, and UI logic (dark mode, deletion)
│   └── src/                # Tailwind CSS source and config
│       ├── input.css       # Main Tailwind input file
│       └── tailwind.config.js
├── templates/
│   ├── index.html          # Front page with general chat and motivational message
│   ├── base.html           # Base template (potentially includes dark mode toggle)
│   ├── subjects.html       # Subject list page
│   ├── subject_detail.html # Specific subject page with subject chat and document listings
│   ├── timetable.html      # Timetable generation page
│   ├── research_assistant.html # Literature Review page
│   └── quiz.html           # Quiz Generation page
├── uploaded_documents/     # Directory for storing actual uploaded subject document files (persistent)
├── agents/                 # Directory for AI agent routines
│   └── research_agent.py   # Contains run_lit_review routine
├── app.py                  # Main Flask application instance (or use a package structure)
├── config.py               # Configuration for Azure keys, MongoDB URI, etc.
├── environment.yml         # Conda environment file (will include pymongo, Azure AI SDKs, icalendar)
└── .env                    # Environment variables (for sensitive keys and MongoDB URI)
```

* Consider using Flask Blueprints for larger applications to modularize different sections (e.g., `general_chat`, `subjects`, `timetable`, `research_assistant`, `quiz`, `api`).
* Keep frontend assets (CSS, JS, images) separate from backend logic.
* Store **persistent** uploaded files (subject documents) in a dedicated and secure location on the server or a cloud storage service, storing the metadata and link/path in MongoDB Atlas. Files uploaded for general chat context are NOT stored here.
* Organize backend AI agent routines in a dedicated directory like `agents/`.

## Best Practices

### Flask Backend

* **Modularity:** Use Flask Blueprints to organize routes and logic for different features (e.g., `/subjects`, `/timetable`, `/research-assistant/`, `/quiz/`, `/api/chat`).
* **Request Handling:** Validate and sanitize user input from forms and API requests. The `/api/chat/general` endpoint must be capable of receiving text messages and potentially file content. The `/research-assistant/` endpoint will receive the literature review query. New endpoints are needed for the Quiz section (e.g., `/quiz/generate`, `/quiz/submit`). **A new endpoint is required for deleting subject documents (e.g., `/api/subjects/<subject_id>/documents/<document_id>/delete`).**
* **Template Rendering:** Use Flask's `render_template` to serve HTML files. Pass necessary data to templates. Ensure all template files are structured correctly.
* **API Endpoints:** Design clear and consistent API endpoints for frontend communication. These endpoints will interact with MongoDB Atlas to save and retrieve data and coordinate calls to Azure AI services.
* **Error Handling:** Implement proper error handling for routes and API calls, including handling potential database errors, AI service errors, issues with file processing, errors during literature review generation, quiz generation and scoring, **and document deletion errors**.
* **Configuration:** Use a `config.py` file or environment variables (`.env`) for settings like Azure keys, storage paths, and MongoDB Atlas connection URI. Ensure all necessary Azure AI service keys are included. Never hardcode sensitive information.

### MongoDB Atlas

* **Connection Management:** Establish a secure connection to your MongoDB Atlas cluster using `pymongo` and the connection URI from configuration. Handle potential connection errors.
* **Data Models:** While MongoDB is schema-flexible, maintain a clear understanding of the document structures for:
    * Subjects (`name`, `user_id`/`session_id`)
    * Document Metadata (`_id`, `filename`, `upload_timestamp`, `size`, `subject_id`, `user_id`/`session_id`, `storage_path`) - **ensure `_id` is used for targeting specific documents for deletion.**
    * User Journals (`user_id`/`session_id`, `timestamp`, `content`)
    * Subject Journals (`user_id`/`session_id`, `subject_id`, `timestamp`, `content`)
* **Querying:** Write efficient queries using `pymongo` to retrieve subjects, document metadata, and relevant journal entries. **Implement logic to delete specific document metadata entries from the `document_metadata` collection based on their `_id`.**

### Frontend (HTML, CSS, JavaScript)

* **Tailwind CSS:** Utilize Tailwind's utility-first classes for styling, ensuring consistency across all sections. Apply classes for layouts, interactive elements, loading indicators, displaying quiz questions/results, the front page redesign, the dark mode toggle, and **implementing the dark mode styles**. Apply additional classes for **overall design improvements and decorative elements**.
* **Material Design:** Apply Material Design principles using Tailwind classes and potentially a library like Material Tailwind for components. Follow consistent design patterns. Ensure the **dark mode design** is also consistent with Material Design.
* **Responsiveness:** Ensure the UI is responsive and adapts well to different screen sizes using Tailwind's responsive utilities.
* **JavaScript:** Use plain JavaScript or a lightweight library if necessary for dynamic interactions.
    * Implement general chat logic, sidebar navigation, subject section logic, timetable generation logic, and literature review logic as previously defined.
    * Implement quiz generation and scoring logic.
    * **Implement logic for the dark mode toggle: reading/saving preference (localStorage), adding/removing Tailwind dark mode classes to the `<html>` element or body.**
    * **Implement logic for document deletion in the subject detail view: displaying delete icons, showing a confirmation dialog, sending the DELETE or POST request to the backend delete endpoint, and updating the UI upon success.**
* **HTML Structure:** Use semantic HTML5 elements. Modify existing templates and create new ones as needed. **Add the dark mode toggle element to the base template or a suitable location in the layout.** Add delete icons next to document listings in `subject_detail.html`.

### Azure AI Integration

* **Secure Credentials:** Load Azure keys and endpoints from environment variables or a secure configuration file.
* **Chat Implementation (General):** Use **Azure OpenAI Service** with temporary document context.
* **Chat Implementation (Subject):** Use **Azure AI Search** and **Azure OpenAI Service** with subject journal context (RAG pattern).
* **Timetable Generation Multi-Agent Workflow:** Utilize **Azure AI Document Intelligence**, **Azure OpenAI Service**, and potentially **Azure AI Agent Service/frameworks**.
* **Literature Review Generation:** Call the `run_lit_review` routine which uses Azure AI services (likely **Azure OpenAI Service**, potentially **Azure AI Search**).
* **Quiz Generation:** Use **Azure OpenAI Service** and potentially **Azure AI Search** to generate questions from document content.
* **Identifying Savable Information:** Implement logic to identify information for journals.
* **Asynchronous Operations:** Consider using asynchronous requests for AI calls and potentially database operations.
* **API Versions:** Be mindful of the Azure AI service API versions being used.

### File Handling

* **Secure Uploads (Subject Documents):** Implement secure file upload handling for subject documents, including validation and **persistent storage** on the server or cloud, with metadata in MongoDB Atlas. Access content for AI tasks. **Implement logic to securely delete these files from storage based on the path/reference stored in MongoDB metadata when a document is deleted.**
* **Secure Uploads (General Chat):** Process these files in memory only. Do NOT save persistently.
* **File Naming:** Sanitize filenames for persistent subject document storage.

### Data Management

* **MongoDB Atlas:** This is the primary database. **Ensure delete operations on `document_metadata` are correctly implemented.**
* **Collections:** Ensure the `subjects`, `document_metadata`, `user_journals`, and `subject_journals` collections are properly structured and used.
* **Data Privacy:** Handle data securely. Ensure the document deletion process permanently removes sensitive document content.
* **Journal Entry Logic:** Develop the rules or AI logic for journal entries and augmentation.
* **Context Retrieval Logic:** Implement efficient methods for retrieving relevant data.

### General

* **Conda Environments:** Always use a Conda environment to manage dependencies. Define dependencies in `environment.yml`.
* **Code Style:** Adhere to PEP 8 guidelines for Python code.
* **Comments:** Write clear and concise comments for complex logic, especially for database interactions (including deletion), AI integration, multi-agent workflow, file handling (upload and **deletion**, temporary vs. persistent), iCalendar generation, literature review, quiz features, and **UI logic (dark mode, deletion confirmation)**.
* **Version Control:** Use Git for version control. Make frequent, small commits with descriptive messages. Use branches for new features or bug fixes.

## Development Workflow

1.  Clone the repository.
2.  Create the Conda environment from the `environment.yml` file (`conda env create -f environment.yml`). Ensure necessary libraries are included.
3.  Activate the Conda environment (`conda activate <environment_name>`).
4.  Set up environment variables (e.g., create a `.env` file based on a `.env.example` containing your MongoDB Atlas connection URI, Azure AI service keys and endpoints).
5.  Install Tailwind CSS and related dependencies (`npm install` or `yarn install` in the `static/src` directory or project root).
6.  Compile Tailwind CSS (`npx tailwindcss -i ./static/src/input.css -o ./static/css/style.css --watch`). Run this command in a separate terminal or configure a build process. **Define and implement dark mode styles in your CSS.**
7.  Run the Flask development server (`flask run` or `python app.py`).
8.  Develop features following the requirements and best practices. This includes implementing all previously defined features. **Additionally, implement the dark mode toggle (frontend HTML/JS/CSS), apply overall design improvements with Tailwind, and implement the document deletion feature (frontend UI/JS for delete icon/confirmation, and backend route/logic for deleting from MongoDB and storage).**
9.  Test your changes thoroughly.
10. Commit your changes and push to the repository.