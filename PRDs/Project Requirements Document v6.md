# Project Requirements Document: Nova

## 1. Introduction

Nova is a Flask-based web application designed to help students with their studies. This document outlines the requirements for a redesign of Nova's front page. The goal is to create a more visually appealing and inviting initial experience for the user, while also adding the capability to provide document context to the general chat for the current session.

### 2. Goals and Objectives (Supplement)

* Enhance the visual appeal and welcoming nature of the front page.
* Prominently display a motivational message upon initial load.
* Allow users to upload files as temporary context for the general chat AI.
* Dynamically manage the visibility of the motivational message based on user interaction.
* Ensure the front page adheres to modern Material Design principles using Tailwind CSS.

### 3. User Stories (Supplement)

* As a student, I want the front page to feel welcoming and encouraging.
* As a student, I want to be able to provide a document for the general AI to consider when answering my questions in the current chat session.
* As a student, I don't want the motivational message to clutter the screen once I start chatting.

### 4. Functional Requirements (Supplement)

**4.1. Front Page Layout and Motivational Message**

* **REQ-FUN-4.1.1:** The front page shall prominently display a motivational message when the user first arrives.
* **REQ-FUN-4.1.2:** The motivational message shall be visually centered on the page to draw attention and create a welcoming feel.
* **REQ-FUN-4.1.3:** The motivational message shall disappear or be hidden from view once the user initiates a conversation in the general chat (sends their first message).

**4.2. General Chat with Temporary File Upload**

* **REQ-FUN-4.2.1 (Modification of REQ-FUN-4.1.1):** The front page shall have a chat interface for general interaction with an AI agent.
* **REQ-FUN-4.2.2 (Modification of REQ-FUN-4.1.2):** Users shall be able to type messages into a text input area within the chat interface.
* **REQ-FUN-4.2.3:** A button or icon for uploading a file shall be present within or near the chat input area, preferably as a small icon beside the send button.
* **REQ-FUN-4.2.4:** Users shall be able to select a file from their local machine for upload via the upload icon.
* **REQ-FUN-4.2.5:** Upon selecting a file, the application shall process the file content in memory. **The uploaded file and its content shall NOT be saved persistently in the backend file system or the MongoDB Atlas database.**
* **REQ-FUN-4.2.6:** The content of the uploaded file shall be used as additional context for the general AI agent for subsequent messages within the current chat session. The method for incorporating this context might involve techniques like sending the document content or a summary/embeddings along with each user message in that session.
* **REQ-FUN-4.2.7 (Modification of REQ-FUN-4.1.3):** The application shall send user messages, **potentially augmented with the in-memory document context**, to a general-purpose AI agent hosted on Azure.
* **REQ-FUN-4.2.8 (Modification of REQ-FUN-4.1.4):** The AI agent's responses shall be displayed in the chat interface, reflecting the added context when provided.
* **REQ-FUN-4.2.9 (Modification of REQ-FUN-4.1.5):** The chat interface shall maintain a history of the current conversation during a session, including acknowledging when a document has been provided for context. The in-memory document context should persist only for the duration of that specific chat session (e.g., until the page is refreshed or the session ends).

### 5. Technical Requirements (Supplement)

* **TECH-REQ-5.1:** Modify the Flask route for the front page to handle rendering the updated template.
* **TECH-REQ-5.2:** Implement frontend JavaScript to handle:
    * Displaying and centering the motivational message.
    * Handling the file selection via the upload icon.
    * Reading the file content into memory using JavaScript's File API.
    * Sending the file content (or a processed version) along with chat messages to the backend.
    * Dynamically hiding the motivational message when the user sends their first chat message.
* **TECH-REQ-5.3:** Modify the backend Flask route that handles general chat messages to:
    * Accept potentially larger payloads that include file content.
    * Process the file content received from the frontend in memory.
    * Incorporate the in-memory document content as context when making calls to the Azure AI agent. This might involve using Azure AI capabilities that support temporary context via API calls or including the content directly in the prompt for that session.
* **TECH-REQ-5.4:** Ensure the backend *does not* write the uploaded file content to disk or store it persistently in the database for the general chat upload.
* **TECH-REQ-5.5:** The general AI agent on Azure (Azure OpenAI Service) needs to be able to process and utilize the provided document context effectively for generating responses.

### 6. UI/UX Requirements (Supplement)

* **UI-UX-6.1:** Redesign the front page layout to create a pleasant and inviting initial view, with the motivational message as a focal point.
* **UI-UX-6.2:** The motivational message should use appealing typography and potentially subtle visual elements to enhance its impact.
* **UI-UX-6.3:** The general chat interface should remain at the bottom but be seamlessly integrated into the redesigned front page layout.
* **UI-UX-6.4:** The file upload icon beside the send button in the general chat should be small, visually intuitive (e.g., a paperclip or document icon), and fit within the overall Material Design aesthetic.
* **UI-UX-6.5:** Provide visual feedback when a file has been selected for upload (e.g., displaying the filename, a small indicator).
* **UI-UX-6.6:** The transition of the motivational message disappearing should be smooth and non-disruptive.
* **UI-UX-6.7:** Consider adding other subtle visual elements (e.g., a background image, gentle animations) to make the front page more inviting, while ensuring they align with Material Design and do not distract from the main content or chat interface. Use Tailwind CSS classes for styling.

### 7. Data Management (Supplement)

* **DATA-7.1:** No persistent storage of the documents uploaded in the general chat is required or allowed by this feature. Document content for the general chat is processed and held only in temporary memory for the duration of the session.

### 8. Future Considerations (Supplement)

* Providing feedback on the processing status of the uploaded file for context in the general chat.
* Limiting the size and type of files that can be uploaded for general chat context.
* Allowing the user to remove the temporary document context during a session without refreshing the page.