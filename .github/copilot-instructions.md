# Copilot Instructions for Student AI Assistant Flask Application

This document provides guidelines and best practices for contributing to the development of the Student AI Assistant Flask application.

## Project Overview

The Student AI Assistant is a Flask-based web application designed to help students with their studies. It features a general chat interface powered by Azure AI and a subject-specific section where users can upload documents and chat with an AI agent that uses these documents as context. The application aims for a modern user interface using Tailwind CSS and Material Design principles.

## Technologies Used

* **Backend:** Flask (Python)
* **Frontend:** HTML, CSS, JavaScript, Tailwind CSS (with potential use of Material Tailwind components)
* **AI Services:** Azure AI (specifically Azure OpenAI for chat models and Azure AI Search for document indexing and retrieval)
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
│   └── subject_detail.html # Specific subject page
├── subject_documents/      # Directory for uploaded subject documents (consider secure storage)
├── app.py                  # Main Flask application instance (or use a package structure)
├── config.py               # Configuration for Azure keys, etc. 1
├── environment.yml         # Conda environment file
└── .env                    # Environment variables (for sensitive keys)
```

* Consider using Flask Blueprints for larger applications to modularize different sections (e.g., `general_chat`, `subjects`).
* Keep frontend assets (CSS, JS, images) separate from backend logic.
* Store uploaded files in a dedicated and secure location on the server.

## Best Practices

### Flask Backend

* **Modularity:** Use Flask Blueprints to organize routes and logic for different features (e.g., `/subjects`, `/api/chat`).
* **Request Handling:** Validate and sanitize user input from forms and API requests.
* **Template Rendering:** Use Flask's `render_template` to serve HTML files. Pass necessary data to templates.
* **API Endpoints:** Design clear and consistent API endpoints for frontend communication (e.g., `/api/chat/general`, `/api/subjects`, `/api/subjects/<subject_id>/chat`, `/api/subjects/<subject_id>/upload`).
* **Error Handling:** Implement proper error handling for routes and API calls (e.g., returning JSON error responses for API issues).
* **Configuration:** Use a `config.py` file or environment variables (`.env`) for settings like Azure keys, storage paths, etc. **Never hardcode sensitive information.**

### Frontend (HTML, CSS, JavaScript)

* **Tailwind CSS:** Utilize Tailwind's utility-first classes for styling.
* **Material Design:** Apply Material Design principles using Tailwind classes and potentially a library like Material Tailwind for components (buttons, cards, inputs). Follow consistent design patterns.
* **Responsiveness:** Ensure the UI is responsive and adapts well to different screen sizes using Tailwind's responsive utilities.
* **JavaScript:** Use plain JavaScript or a lightweight library if necessary for dynamic interactions (e.g., handling sidebar toggle, sending chat messages via AJAX, file upload progress). Avoid heavy frontend frameworks unless explicitly decided.
* **HTML Structure:** Use semantic HTML5 elements.

### Azure AI Integration

* **Secure Credentials:** Load Azure keys and endpoints from environment variables or a secure configuration file.
* **Chat Implementation:**
    * For the general chat, interact with a standard Azure OpenAI chat model.
    * For subject-specific chat, implement a Retrieval Augmented Generation (RAG) pattern. This involves:
        * Using Azure AI Search to index the content of the uploaded subject documents.
        * When a user asks a question in the subject chat, query the Azure AI Search index to retrieve relevant document chunks.
        * Include these retrieved document chunks as context in the prompt sent to the Azure OpenAI model.
* **Asynchronous Operations:** Consider using asynchronous requests for AI calls to prevent blocking the Flask application, especially if response times can be long.
* **API Versions:** Be mindful of the Azure AI service API versions being used.

### File Handling

* **Secure Uploads:** Implement secure file upload handling to prevent malicious uploads. Validate file types and sizes.
* **Storage:** Store uploaded files in a dedicated directory outside of the application's source code if possible, or within a designated static folder with appropriate security measures. Organize files logically (e.g., by user ID and subject ID).
* **File Naming:** Sanitize uploaded filenames to prevent path traversal issues.

### General

* **Conda Environments:** Always use a Conda environment to manage dependencies. Define dependencies in `environment.yml`.
* **Code Style:** Adhere to PEP 8 guidelines for Python code.
* **Comments:** Write clear and concise comments for complex logic, especially for AI integration and file handling.
* **Version Control:** Use Git for version control. Make frequent, small commits with descriptive messages. Use branches for new features or bug fixes.

## Development Workflow

1.  Clone the repository.
2.  Create the Conda environment from the `environment.yml` file (`conda env create -f environment.yml`).
3.  Activate the Conda environment (`conda activate <environment_name>`).
4.  Set up environment variables (e.g., create a `.env` file based on a `.env.example`).
5.  Install Tailwind CSS and related dependencies (`npm install` or `yarn install` in the `static/src` directory or project root, depending on setup).
6.  Compile Tailwind CSS (`npx tailwindcss -i ./static/src/input.css -o ./static/css/style.css --watch`). Run this command in a separate terminal or configure a build process.
7.  Run the Flask development server (`flask run` or `python app.py`).
8.  Develop features following the requirements and best practices outlined above.
9.  Test your changes thoroughly.
10. Commit your changes and push to the repository.
