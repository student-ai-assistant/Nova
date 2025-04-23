# Copilot Instructions for Student AI Assistant Flask Application

This document provides guidelines and best practices for contributing to the development of the Student AI Assistant Flask application.

## Project Overview

The Student AI Assistant is a Flask-based web application designed to help students with their studies. It features a general chat interface powered by Azure AI and a subject-specific section where users can upload documents and chat with an AI agent that uses these documents as context. A key feature includes a **refined multi-level AI agent system (three agents)** to generate personalized study timetables, leveraging document content and user journal entries. The application utilizes MongoDB Atlas for persistent data storage. The user interface aims for a modern aesthetic using Tailwind CSS and Material Design principles.

## Technologies Used

* **Backend:** Flask (Python), pymongo (for MongoDB interaction), **icalendar (for .ics file generation)**
* **Database:** MongoDB Atlas
* **Frontend:** HTML, CSS, JavaScript, Tailwind CSS (with potential use of Material Tailwind components)
* **AI Services:** Azure AI (**Azure OpenAI Service**, **Azure AI Document Intelligence**, potentially Azure AI Agent Service or frameworks like Semantic Kernel/AutoGen for orchestration)
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
│   │   └── main.js         # Frontend JavaScript
│   └── src/                # Tailwind CSS source and config
│       ├── input.css       # Main Tailwind input file
│       └── tailwind.config.js
├── templates/
│   ├── index.html          # General chat page
│   ├── base.html           # Base template
│   ├── subjects.html       # Subject list page
│   ├── subject_detail.html # Specific subject page
│   └── timetable.html      # Timetable generation page
├── uploaded_documents/     # Directory for storing actual uploaded document files (or link to cloud storage)
├── app.py                  # Main Flask application instance (or use a package structure)
├── config.py               # Configuration for Azure keys, MongoDB URI, etc.
├── environment.yml         # Conda environment file (will include pymongo, Azure AI SDKs, icalendar)
└── .env                    # Environment variables (for sensitive keys and MongoDB URI)
```

* Consider using Flask Blueprints for larger applications to modularize different sections (e.g., `general_chat`, `subjects`, `timetable`, `api`).
* Keep frontend assets (CSS, JS, images) separate from backend logic.
* Store uploaded files in a dedicated and secure location on the server or a cloud storage service, storing the metadata and link/path in MongoDB Atlas.

## Best Practices

### Flask Backend

* **Modularity:** Use Flask Blueprints to organize routes and logic for different features (e.g., `/subjects`, `/timetable`, `/api/chat`).
* **Request Handling:** Validate and sanitize user input from forms and API requests.
* **Template Rendering:** Use Flask's `render_template` to serve HTML files. Pass necessary data to templates.
* **API Endpoints:** Design clear and consistent API endpoints for frontend communication (e.g., `/api/chat/general`, `/api/subjects`, `/api/subjects/<subject_id>/chat`, `/api/subjects/<subject_id>/upload`, `/api/timetable/generate`, **/api/timetable/download**). These endpoints will interact with MongoDB Atlas to save and retrieve data and coordinate calls to Azure AI services for chat and timetable generation, **and handle the generation and serving of the iCalendar file.**
* **Error Handling:** Implement proper error handling for routes and API calls (e.g., returning JSON error responses for API issues), including handling potential database errors and AI service errors.
* **Configuration:** Use a `config.py` file or environment variables (`.env`) for settings like Azure keys, storage paths, and MongoDB Atlas connection URI. Ensure all necessary Azure AI service keys (Azure OpenAI, Document Intelligence) are included. Never hardcode sensitive information.

### MongoDB Atlas

* **Connection Management:** Establish a secure connection to your MongoDB Atlas cluster using `pymongo` and the connection URI from configuration. Handle potential connection errors.
* **Data Models:** While MongoDB is schema-flexible, maintain a clear understanding of the document structures for:
    * Subjects (`name`, `user_id`/`session_id`)
    * Document Metadata (`filename`, `upload_timestamp`, `size`, `subject_id`, `user_id`/`session_id`, `storage_path`)
    * User Journals (`user_id`/`session_id`, `timestamp`, `content`)
    * Subject Journals (`user_id`/`session_id`, `subject_id`, `timestamp`, `content`)
* **Querying:** Write efficient queries using `pymongo` to retrieve subjects, document metadata, and relevant journal entries based on user/session and subject. The Timetable Generation feature will specifically query for document metadata (to access file content) and user journal entries.

### Frontend (HTML, CSS, JavaScript)

* **Tailwind CSS:** Utilize Tailwind's utility-first classes for styling.
* **Material Design:** Apply Material Design principles using Tailwind classes and potentially a library like Material Tailwind for components (buttons, cards, inputs). Follow consistent design patterns.
* **Responsiveness:** Ensure the UI is responsive and adapts well to different screen sizes using Tailwind's responsive utilities.
* **JavaScript:** Use plain JavaScript or a lightweight library if necessary for dynamic interactions (e.g., handling sidebar toggle, sending chat messages via AJAX, file upload progress, submitting timetable generation requests, displaying the generated timetable, **triggering the timetable download**). Avoid heavy frontend frameworks unless explicitly decided.
* **HTML Structure:** Use semantic HTML5 elements. Create a dedicated HTML template for the Timetable Generation section. **Ensure the timetable display clearly highlights conflicts.**

### Azure AI Integration

* **Secure Credentials:** Load Azure keys and endpoints from environment variables or a secure configuration file.
* **Chat Implementation:**
    * For the general chat, interact with a standard **Azure OpenAI Service** chat model, including user journal context from MongoDB Atlas.
    * For subject-specific chat, implement a Retrieval Augmented Generation (RAG) pattern using **Azure AI Search** for document chunks and **Azure OpenAI Service** for generation, incorporating subject journal context from MongoDB Atlas.
* **Timetable Generation Multi-Agent Workflow:**
    * **Agent 1 (Topic Extractor):** Will use **Azure AI Document Intelligence** (e.g., Layout/Read models) to extract text and structure from documents. It will then use **Azure OpenAI Service** to process this extracted text and identify/summarize key topics based on the user's input scope.
    * **Agent 3 (Journal Augmentation):** Will receive relevant user journal entries from MongoDB Atlas. It will use **Azure OpenAI Service** to analyze the natural language content, extract structured information about time commitments (date, time, duration, description), and pass this augmented data to Agent 2.
    * **Agent 2 (Timetable Generator):** Will use **Azure OpenAI Service** to process the topics from Agent 1, the augmented journal data from Agent 3, and the calculated study timeframe (starting from the day after the current date). It will generate a structured study timetable, considering and marking conflicts with identified commitments.
    * **Orchestration:** The backend Flask application will manage the flow of information between these steps and Azure services. Consider using **Azure AI Agent Service** or Python frameworks like **Semantic Kernel or AutoGen** to simplify the orchestration and management of this three-agent workflow.
* **Identifying Savable Information:** Implement logic (simple string matching, rule-based, or more advanced AI/NLP) to identify information from chat conversations that should be appended to the respective user or subject journals in MongoDB Atlas, along with a timestamp.
* **Asynchronous Operations:** Consider using asynchronous requests for AI calls and potentially database operations to prevent blocking the Flask application, especially if response times can be long.
* **API Versions:** Be mindful of the Azure AI service API versions being used.

### File Handling

* **Secure Uploads:** Implement secure file upload handling to prevent malicious uploads. Validate file types and sizes.
* **Storage:** Store uploaded files in a dedicated directory on the server (`uploaded_documents/`) or use a cloud storage service. Store the file metadata (filename, path/reference, etc.) in the `document_metadata` collection in MongoDB Atlas. The Timetable Generation feature will need to access the content of these stored files.
* **File Naming:** Sanitize uploaded filenames to prevent path traversal issues.

### Data Management

* **MongoDB Atlas:** This is the primary database for storing application data (subjects, document metadata, user journals, subject journals). Set up a cluster and obtain the connection URI.
* **Collections:** Ensure the `subjects`, `document_metadata`, `user_journals`, and `subject_journals` collections are properly structured and used.
* **Data Privacy:** Handle data, especially journal entries, securely. Implement appropriate access controls if user authentication is added later. Data should be clearly linked to users/sessions.
* **Journal Entry Logic:** Develop the rules or AI logic for determining what constitutes "savable" information for the journals and appending it with timestamps. Implement the logic in Agent 3 to extract structured commitments from journal entries.
* **Context Retrieval Logic:** Implement efficient methods for retrieving relevant journal entries for inclusion in AI prompts (for both general chat and the Timetable Generator Agent 2). Consider indexing strategies in MongoDB or using MongoDB Atlas Search.

### General

* **Conda Environments:** Always use a Conda environment to manage dependencies. Define dependencies (including `flask`, `pymongo`, `azure-ai-documentintelligence`, Azure OpenAI SDK, **`icalendar`**, and potentially `semantic-kernel` or `pyautogen`) in `environment.yml`.
* **Code Style:** Adhere to PEP 8 guidelines for Python code.
* **Comments:** Write clear and concise comments for complex logic, especially for database interactions, AI integration, multi-agent workflow, and file handling, **and iCalendar generation.**
* **Version Control:** Use Git for version control. Make frequent, small commits with descriptive messages. Use branches for new features or bug fixes.

## Development Workflow

1.  Clone the repository.
2.  Create the Conda environment from the `environment.yml` file (`conda env create -f environment.yml`). Ensure `pymongo`, `azure-ai-documentintelligence`, Azure OpenAI SDK, and `icalendar` are included.
3.  Activate the Conda environment (`conda activate <environment_name>`).
4.  Set up environment variables (e.g., create a `.env` file based on a `.env.example` containing your MongoDB Atlas connection URI, Azure AI service keys and endpoints, including Document Intelligence). You will need to set up your MongoDB Atlas cluster and Azure AI resources and get the necessary connection strings/keys.
5.  Install Tailwind CSS and related dependencies (`npm install` or `yarn install` in the `static/src` directory or project root, depending on setup).
6.  Compile Tailwind CSS (`npx tailwindcss -i ./static/src/input.css -o ./static/css/style.css --watch`). Run this command in a separate terminal or configure a build process.
7.  Run the Flask development server (`flask run` or `python app.py`).
8.  Develop features following the requirements and best practices outlined above. This will involve implementing MongoDB Atlas connections, data models, read/write operations, updating chat logic, implementing the new Timetable Generation routes and UI, **developing the backend logic for the three-agent workflow (Agent 1, Agent 3, Agent 2)**, integrating with Azure AI Document Intelligence and Azure OpenAI Service, **implementing the journal augmentation logic in Agent 3**, **implementing timetable generation with conflict handling in Agent 2, calculating the timeframe starting from the next day, and implementing the iCalendar generation and download functionality.**
9.  Test your changes thoroughly.
10. Commit your changes and push to the repository.