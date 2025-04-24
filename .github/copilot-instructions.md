# Copilot Instructions for Nova Flask Application

This document provides guidelines and best practices for contributing to the development of the Nova Flask application.

## Project Overview

Nova is a Flask-based web application designed to help students with their studies. The front page features a redesigned welcoming layout with a central motivational message and a general chat interface at the bottom, with the ability to upload a file for temporary, in-memory context. A subject-specific section allows users to upload documents for persistent storage and chat with an AI agent that uses these documents as context. A refined multi-level AI agent system (three agents) generates personalized study timetables. A Literature Review feature allows users to generate research reports based on a query. **A new Quiz Generation feature enables students to create and take multiple-choice quizzes based on their subject documents and specified topics.** The application utilizes MongoDB Atlas for persistent data storage. The user interface aims for a modern aesthetic using Tailwind CSS and Material Design principles.

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
│   │   └── style.css       # Compiled Tailwind CSS output
│   ├── js/
│   │   └── main.js         # Frontend JavaScript for general interactions and front page logic
│   └── src/                # Tailwind CSS source and config
│       ├── input.css       # Main Tailwind input file
│       └── tailwind.config.js
├── templates/
│   ├── index.html          # Front page with general chat and motivational message
│   ├── base.html           # Base template
│   ├── subjects.html       # Subject list page
│   ├── subject_detail.html # Specific subject page with subject chat
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
* **Request Handling:** Validate and sanitize user input from forms and API requests. The `/api/chat/general` endpoint must be capable of receiving text messages and potentially file content. The `/research-assistant/` endpoint will receive the literature review query. **New endpoints are needed for the Quiz section (e.g., `/quiz/generate`, `/quiz/submit`).**
* **Template Rendering:** Use Flask's `render_template` to serve HTML files. Pass necessary data to templates. Ensure all template files (`index.html`, `subjects.html`, `subject_detail.html`, `timetable.html`, `research_assistant.html`, **`quiz.html`**) are structured correctly.
* **API Endpoints:** Design clear and consistent API endpoints for frontend communication (e.g., `/api/chat/general`, `/api/subjects`, `/api/subjects/<subject_id>/chat`, `/api/subjects/<subject_id>/upload`, `/api/timetable/generate`, `/api/timetable/download`, `/api/research-assistant/generate-report`, **/api/quiz/generate**, **/api/quiz/submit**). These endpoints will interact with MongoDB Atlas to save and retrieve data and coordinate calls to Azure AI services.
* **Error Handling:** Implement proper error handling for routes and API calls, including handling potential database errors, AI service errors, issues with file processing, errors during literature review generation, **and errors during quiz generation and scoring**.
* **Configuration:** Use a `config.py` file or environment variables (`.env`) for settings like Azure keys, storage paths, and MongoDB Atlas connection URI. Ensure all necessary Azure AI service keys (Azure OpenAI, Document Intelligence, potentially Azure AI Search) are included. Never hardcode sensitive information.

### MongoDB Atlas

* **Connection Management:** Establish a secure connection to your MongoDB Atlas cluster using `pymongo` and the connection URI from configuration. Handle potential connection errors.
* **Data Models:** While MongoDB is schema-flexible, maintain a clear understanding of the document structures for:
    * Subjects (`name`, `user_id`/`session_id`)
    * Document Metadata (`filename`, `upload_timestamp`, `size`, `subject_id`, `user_id`/`session_id`, `storage_path`)
    * User Journals (`user_id`/`session_id`, `timestamp`, `content`)
    * Subject Journals (`user_id`/`session_id`, `subject_id`, `timestamp`, `content`)
* **Querying:** Write efficient queries using `pymongo` to retrieve subjects, document metadata, and relevant journal entries based on user/session and subject. The Timetable Generation feature will specifically query for document metadata (to access file content) and user journal entries. **The Quiz Generation feature will query for subject and document metadata to access document content.**

### Frontend (HTML, CSS, JavaScript)

* **Tailwind CSS:** Utilize Tailwind's utility-first classes for styling, ensuring consistency across all sections, including the new Quiz page. Apply classes for layouts, interactive elements, loading indicators, and displaying quiz questions/results.
* **Material Design:** Apply Material Design principles using Tailwind classes and potentially a library like Material Tailwind for components. Follow consistent design patterns.
* **Responsiveness:** Ensure the UI is responsive and adapts well to different screen sizes using Tailwind's responsive utilities.
* **JavaScript:** Use plain JavaScript or a lightweight library if necessary for dynamic interactions.
    * Implement logic for the general chat interface, including capturing user input, sending messages, handling temporary file uploads, and controlling the motivational message visibility.
    * Handle sidebar toggle navigation.
    * Implement logic for the Subject section (adding subjects, navigating to subject details, file uploads).
    * Implement logic for the Timetable Generation section (submitting goals, displaying loading state, rendering the timetable with conflict highlighting, triggering download).
    * Implement logic for the Literature Review section (submitting query, displaying loading state, receiving and rendering the Markdown report content).
    * **Implement logic for the Quiz Generation section: handling subject and topic selection, displaying the loading indicator during generation, receiving and rendering the interactive quiz, capturing user answers, submitting answers for scoring, and displaying the score and correct answers after submission.**
* **HTML Structure:** Use semantic HTML5 elements. Modify existing templates and create `quiz.html` for the required layouts and elements.

### Azure AI Integration

* **Secure Credentials:** Load Azure keys and endpoints from environment variables or a secure configuration file.
* **Chat Implementation (General):** The `/api/chat/general` endpoint will forward user messages and the in-memory document content (if provided) to an **Azure OpenAI Service** chat model.
* **Chat Implementation (Subject):** Implement a Retrieval Augmented Generation (RAG) pattern using **Azure AI Search** for document chunks and **Azure OpenAI Service** for generation, incorporating subject journal context from MongoDB Atlas.
* **Timetable Generation Multi-Agent Workflow:** Utilize **Azure AI Document Intelligence** (Agent 1), **Azure OpenAI Service** (Agents 1, 3, 2), and potentially **Azure AI Agent Service/frameworks** for orchestration.
* **Literature Review Generation:** The backend calls the `run_lit_review` routine (in `agents/research_agent.py`), which interacts with Azure AI services (likely **Azure OpenAI Service**, potentially **Azure AI Search**).
* **Quiz Generation:** Implement an AI agent within the backend logic for the Quiz section. This agent will retrieve relevant document content (potentially via Azure AI Search or direct text extraction and processing) and use **Azure OpenAI Service** to generate multiple-choice questions, options, and identify the correct answers based on the user's specified subject and topic.
* **Identifying Savable Information:** Implement logic to identify information from chat conversations that should be appended to the respective user or subject journals in MongoDB Atlas.
* **Asynchronous Operations:** Consider using asynchronous requests for AI calls (chat, timetable agents, literature review routine, **quiz generation**) and potentially database operations. Quiz generation might take some time, so asynchronous handling and frontend loading states are important.
* **API Versions:** Be mindful of the Azure AI service API versions being used.

### File Handling

* **Secure Uploads (Subject Documents):** Implement secure file upload handling for subject documents, including validation and **persistent storage** on the server or cloud, with metadata in MongoDB Atlas. Access content for subject chat, timetable generation, and **quiz generation**.
* **Secure Uploads (General Chat):** Implement secure handling for files uploaded in the general chat. **Process these files in memory only. Do NOT save the file content or metadata persistently to disk or the database.** Validate file types and sizes to prevent abuse.
* **File Naming:** Sanitize filenames for persistent subject document storage.

### Data Management

* **MongoDB Atlas:** This is the primary database for storing application data (subjects, document metadata, user journals, subject journals). Documents uploaded in the general chat are NOT stored here. Generated literature review reports and **generated quiz questions/answers for scoring are handled temporarily (e.g., in session)**.
* **Collections:** Ensure the `subjects`, `document_metadata`, `user_journals`, and `subject_journals` collections are properly structured and used.
* **Data Privacy:** Handle data securely. Journal entries and subject document metadata should be linked to users/sessions. Temporary data for general chat and quizzes should be handled with care and not logged or stored beyond the session.
* **Journal Entry Logic:** Develop the rules or AI logic for determining what constitutes "savable" information for the journals and appending it with timestamps. Implement the logic in Agent 3 to extract structured commitments from journal entries.
* **Context Retrieval Logic:** Implement efficient methods for retrieving relevant journal entries and document content/chunks for AI prompts.

### General

* **Conda Environments:** Always use a Conda environment to manage dependencies. Define dependencies (including `flask`, `pymongo`, `azure-ai-documentintelligence`, Azure OpenAI SDK, `icalendar`, and potentially orchestration libraries or libraries needed by the research agent) in `environment.yml`.
* **Code Style:** Adhere to PEP 8 guidelines for Python code.
* **Comments:** Write clear and concise comments for complex logic, especially for database interactions, AI integration, multi-agent workflow, file handling (distinguishing temporary vs. persistent), iCalendar generation, literature review report generation, **and quiz generation/scoring**.
* **Version Control:** Use Git for version control. Make frequent, small commits with descriptive messages. Use branches for new features or bug fixes.

## Development Workflow

1.  Clone the repository.
2.  Create the Conda environment from the `environment.yml` file (`conda env create -f environment.yml`). Ensure necessary libraries are included.
3.  Activate the Conda environment (`conda activate <environment_name>`).
4.  Set up environment variables (e.g., create a `.env` file based on a `.env.example` containing your MongoDB Atlas connection URI, Azure AI service keys and endpoints). You will need to set up your MongoDB Atlas cluster and Azure AI resources.
5.  Install Tailwind CSS and related dependencies (`npm install` or `yarn install` in the `static/src` directory or project root).
6.  Compile Tailwind CSS (`npx tailwindcss -i ./static/src/input.css -o ./static/css/style.css --watch`). Run this command in a separate terminal or configure a build process.
7.  Run the Flask development server (`flask run` or `python app.py`).
8.  Develop features following the requirements and best practices. This includes implementing the front page redesign and temporary file upload, updating chat logic, implementing subject/journal/timetable/literature review features, **and implementing the Quiz Generation feature (new route `/quiz/`, new UI template `quiz.html`, frontend JS for subject/topic selection, quiz display, answer capture, submission, and results display, backend logic for quiz generation via AI, temporary storage of quiz data, and scoring).**
9.  Test your changes thoroughly.
10. Commit your changes and push to the repository.