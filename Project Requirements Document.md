# Project Requirements Document: Student AI Assistant Flask Application

## 1. Introduction

This document outlines the requirements for a Flask-based web application designed to assist students with their studies. The application will provide a platform for general AI interaction and subject-specific support, including answering questions based on uploaded documents. Azure AI services will be utilized for the AI capabilities, and the user interface will feature a modern Material Design aesthetic implemented with Tailwind CSS.

## 2. Goals and Objectives

* Provide a central platform for students to interact with an AI assistant.
* Offer general AI assistance for a wide range of student queries.
* Enable students to organize subject-specific materials and receive AI-powered help based on those materials.
* Implement a user-friendly and aesthetically pleasing interface using modern web technologies.
* Leverage Azure AI services for scalable and intelligent conversational agents.

## 3. User Stories

* As a student, I want a central place to ask general questions about my studies to an AI.
* As a student, I want to easily navigate between different sections of the application, such as the general chat and my subjects.
* As a student, I want to have a dedicated section to manage information related to each subject I am studying.
* As a student, I want to be able to add new subjects to my personalized list.
* As a student, for a specific subject, I want to upload documents (like lecture notes or textbooks) to provide context for the AI.
* As a student, I want to chat with an AI agent that can answer questions specifically based on the documents I've uploaded for a subject.

## 4. Functional Requirements

**4.1. General Chat (Front Page)**

* **REQ-FUN-4.1.1:** The front page of the application shall display a prominent chat interface.
* **REQ-FUN-4.1.2:** Users shall be able to type messages into a text input area within the chat interface.
* **REQ-FUN-4.1.3:** The application shall send user messages to a general-purpose AI agent hosted on Azure.
* **REQ-FUN-4.1.4:** The AI agent's responses shall be displayed in the chat interface in a clear and readable format.
* **REQ-FUN-4.1.5:** The chat interface shall maintain a history of the current conversation during a session.

**4.2. Foldable Sidebar Navigation**

* **REQ-FUN-4.2.1:** The application shall include a sidebar on the left side of the interface for navigation.
* **REQ-FUN-4.2.2:** The sidebar shall be foldable, allowing users to expand or collapse it to save screen space.
* **REQ-FUN-4.2.3:** The sidebar shall contain links or icons to navigate to different sections of the application (at a minimum, the General Chat and Subjects sections).

**4.3. Subject Specific Information Section**

* **REQ-FUN-4.3.1:** The application shall have a dedicated section for managing subject-specific information.
* **REQ-FUN-4.3.2:** This section shall display a collection of interactive cards, with each card representing a subject.
* **REQ-FUN-4.3.3:** Each subject card shall clearly display the name of the subject.
* **REQ-FUN-4.3.4:** There shall be a clearly visible button or element for adding a new subject.
* **REQ-FUN-4.3.5:** Clicking on a subject card shall navigate the user to a detailed view for that specific subject.

**4.4. Adding New Subjects**

* **REQ-FUN-4.4.1:** Clicking the "Add New Subject" button shall trigger a mechanism to create a new subject.
* **REQ-FUN-4.4.2:** The user shall be prompted to enter a name for the new subject.
* **REQ-FUN-4.4.3:** The new subject shall be added to the list of subject cards in the Subject Specific Information section.

**4.5. Subject Document Upload**

* **REQ-FUN-4.5.1:** Within the detailed view of a specific subject, there shall be an option to upload documents.
* **REQ-FUN-4.5.2:** This option should be prominently located, preferably near the top of the subject's detailed view.
* **REQ-FUN-4.5.3:** Users shall be able to select one or more files from their local machine for upload.
* **REQ-FUN-4.5.4:** Uploaded documents shall be securely stored in a designated folder on the backend server, organized by subject.
* **REQ-FUN-4.5.5:** The application shall provide feedback to the user on the status of the document upload (e.g., progress bar, success/failure message).
* **REQ-FUN-4.5.6:** The application should support common document formats relevant to academic study (e.g., PDF, DOCX, TXT).

**4.6. Subject Specific Chat**

* **REQ-FUN-4.6.1:** The detailed view of a specific subject shall include a chat box at the bottom of the page.
* **REQ-FUN-4.6.2:** Users shall be able to type messages into this subject-specific chat box.
* **REQ-FUN-4.6.3:** The application shall send user messages to a specialized AI agent on Azure.
* **REQ-FUN-4.6.4:** This specialized AI agent shall use the documents uploaded for the current subject as context for generating responses. This will likely involve a Retrieval Augmented Generation (RAG) pattern, where relevant document chunks are retrieved and provided to the AI model along with the user's query.
* **REQ-FUN-4.6.5:** The AI agent's responses, informed by the subject documents, shall be displayed in the subject-specific chat interface.
* **REQ-FUN-4.6.6:** The subject-specific chat shall maintain a history of the conversation for that subject during a session.

### 5. Technical Requirements

* **TECH-REQ-5.1:** The application shall be built using the Flask web framework in Python.
* **TECH-REQ-5.2:** The frontend shall utilize HTML, CSS, and JavaScript.
* **TECH-REQ-5.3:** Tailwind CSS shall be used for implementing the user interface styling, adhering to modern Material Design principles. Libraries like Material Tailwind can be explored for pre-built components.
* **TECH-REQ-5.4:** Azure AI services shall be used for the AI chatbot functionalities. This will involve:
    * **TECH-REQ-5.4.1:** Integration with Azure OpenAI or Azure AI Language service for conversational AI.
    * **TECH-REQ-5.4.2:** Utilizing Azure AI Search or similar services for indexing and retrieving information from uploaded subject documents to provide context to the AI.
    * **TECH-REQ-5.4.3:** Securely managing Azure API keys and endpoints within the Flask application (e.g., using environment variables).
* **TECH-REQ-5.5:** File uploads shall be handled securely on the backend, with appropriate validation and storage mechanisms. The uploaded documents should be stored in a structured manner, likely within the Flask application's directory or a configured storage location, organized by user and subject.
* **TECH-REQ-5.6:** The application should handle potential errors gracefully, including issues with AI service communication, file uploads, and invalid user input.
* **TECH-REQ-5.7:** The application should be designed with scalability in mind, particularly regarding the Azure AI services and document storage as the number of users and documents grows.

### 6. UI/UX Requirements

* **UI-UX-6.1:** The application shall have a clean and intuitive user interface.
* **UI-UX-6.2:** The design shall follow modern Material Design principles, utilizing Tailwind CSS for implementation. This includes consistent use of spacing, typography, color palettes, and interactive elements like ripple effects (potentially via Material Tailwind).
* **UI-UX-6.3:** The foldable sidebar shall be visually distinct and easy to operate.
* **UI-UX-6.4:** Subject cards shall be visually appealing and clearly display subject names.
* **UI-UX-6.5:** The document upload interface shall be user-friendly, with clear instructions and feedback.
* **UI-UX-6.6:** Chat interfaces shall be easy to read and use, with clear distinctions between user messages and AI responses.
* **UI-UX-6.7:** The application should be responsive and work well on different screen sizes (desktop, tablet, mobile).

### 7. Data Management

* **DATA-7.1:** Subject information (names, associated document paths) shall be stored persistently on the backend. A simple database (like SQLite for smaller deployments or PostgreSQL/MySQL for larger ones) or structured files could be used initially.
* **DATA-7.2:** Uploaded subject documents shall be stored in a file system accessible by the backend. The storage location should be configurable.
* **DATA-7.3:** User data (if user authentication is implemented in the future) should be handled securely and in compliance with relevant privacy regulations.

### 8. Future Considerations (Out of Scope for Initial Version)

* User authentication and personalized subject lists.
* Integration with other academic tools or calendars for scheduling assistance.
* More advanced AI features (e.g., summarization of documents, quiz generation).
* Collaboration features for students.
* Deployment to a production environment (e.g., Azure App Service).