# Project Requirements Document: Nova

## 1. Introduction

Nova is a Flask-based web application designed to help students with their studies. This document supplements the initial requirements by outlining features for persistent data storage and enhanced conversational memory within Nova. Leveraging MongoDB Atlas, the application will store uploaded subject documents and maintain user-specific and subject-specific journal files to provide richer context for the AI agents.

### 2. Goals and Objectives (Supplement)

* Ensure permanent storage of user-uploaded subject documents.
* Implement a user-specific memory journal to retain conversational context for the general AI.
* Develop subject-specific memory journals to enhance the context of the subject-specific AI.
* Utilize MongoDB Atlas API for efficient and scalable online database storage for document metadata and journal entries.
* Enable AI agents to leverage stored memory journals and documents for more personalized and informed responses.

### 3. User Stories (Supplement)

* As a student, I want the documents I upload for a subject to be saved permanently so I don't have to re-upload them.
* As a student, I want the general AI to remember previous important information I've shared across different sessions.
* As a student, I want the subject-specific AI to remember details from our past conversations about that subject.
* As a student, I want key information from my chats to be automatically saved to a personal journal.
* As a student, I want key information from my subject chats to be automatically saved to a subject-specific journal.

### 4. Functional Requirements (Supplement)

**4.1. Permanent Document Storage**

* **REQ-FUN-4.1.1:** Uploaded subject documents shall be stored permanently. While the files themselves might be stored in a file system or cloud storage (like Azure Blob Storage) for efficiency with large files, their metadata (filename, upload date, associated subject, storage path/reference) shall be stored in MongoDB Atlas.
* **REQ-FUN-4.1.2:** The application shall maintain a record in MongoDB Atlas linking uploaded document metadata to the specific subject and user (assuming user authentication in a later phase, otherwise linked to a session or a simple identifier).
* **REQ-FUN-4.1.3:** When a user accesses a subject, the application shall retrieve the metadata of previously uploaded documents for that subject from MongoDB Atlas.

**4.2. User Memory Journal**

* **REQ-FUN-4.2.1:** A persistent memory journal shall be created and maintained for each user (or session, in the absence of user authentication).
* **REQ-FUN-4.2.2:** This journal shall be stored, likely as a collection of dated entries, within MongoDB Atlas.
* **REQ-FUN-4.2.3:** The application, potentially with AI assistance in identifying relevant information, shall append significant information from the general chat to the user's memory journal.
* **REQ-FUN-4.2.4:** Each entry in the memory journal shall include a timestamp indicating when the information was recorded.

**4.3. Appending to User Journal**

* **REQ-FUN-4.3.1:** During general chat interactions, the application shall analyze the conversation for information deemed important or memorable (e.g., user preferences, goals, previous questions asked).
* **REQ-FUN-4.3.2:** Identified key information shall be formatted and appended as a new entry to the user's memory journal in MongoDB Atlas.
* **REQ-FUN-4.3.3:** The process of identifying and saving information should be relatively unobtrusive to the user experience.

**4.4. General Chat Context from Journal**

* **REQ-FUN-4.4.1:** Before generating a response in the general chat, the application shall retrieve relevant entries from the user's memory journal stored in MongoDB Atlas.
* **REQ-FUN-4.4.2:** These retrieved journal entries shall be included as part of the context provided to the Azure AI agent for generating a more personalized and context-aware response. The method of selecting "relevant" entries might involve keyword matching, vector similarity search on journal content, or other AI-driven techniques.

**4.5. Subject Specific Memory Journal**

* **REQ-FUN-4.5.1:** A persistent memory journal shall be created and maintained for each subject for each user (or session/identifier).
* **REQ-FUN-4.5.2:** These subject journals shall be stored within MongoDB Atlas, linked to the specific subject and user.
* **REQ-FUN-4.5.3:** Significant information from the subject-specific chat shall be appended to the corresponding subject's memory journal in MongoDB Atlas.
* **REQ-FUN-4.5.4:** Each entry in the subject memory journal shall include a timestamp.

**4.6. Subject Chat Context from Documents and Journal**

* **REQ-FUN-4.6.1:** Before generating a response in the subject-specific chat, the application shall retrieve relevant entries from both the subject's memory journal and relevant chunks from the uploaded subject documents (via the RAG pattern using Azure AI Search).
* **REQ-FUN-4.6.2:** Both the retrieved journal entries and the document chunks shall be included as context for the Azure AI agent to generate a response that is informed by both the subject material and the user's past conversations about that subject.

### 5. Technical Requirements (Supplement)

* **TECH-REQ-5.1:** MongoDB Atlas shall be used as the online database store.
* **TECH-REQ-5.2:** The Flask application shall interact with MongoDB Atlas using a suitable Python driver (e.g., `pymongo`).
* **TECH-REQ-5.3:** Secure connection string management for MongoDB Atlas is required (using environment variables).
* **TECH-REQ-5.4:** Data models for storing document metadata and journal entries in MongoDB collections shall be defined.
    * Document Metadata: Should include fields like filename, upload timestamp, size, associated user/session ID, subject ID, and potentially a path or reference to the file storage location.
    * Journal Entries: Should include fields like timestamp, content (the saved piece of information), associated user/session ID, and for subject journals, the subject ID.
* **TECH-REQ-5.5:** Logic shall be implemented to identify "savable" information from chat conversations. This might involve simple keyword rules or more advanced Natural Language Processing (NLP) techniques.
* **TECH-REQ-5.6:** Retrieval mechanisms for fetching relevant journal entries based on the current chat context need to be developed. This could involve querying MongoDB based on keywords or using vector embeddings of journal entries and the current query if MongoDB Atlas Search or a separate vector database is integrated.
* **TECH-REQ-5.7:** The RAG implementation for subject chat will need to be enhanced to include retrieved subject journal entries in the context sent to the Azure AI model, alongside document chunks.
* **TECH-REQ-5.8:** Consider potential scaling implications for MongoDB Atlas as the number of users, documents, and journal entries grows.

### 6. Data Management (Supplement)

* **DATA-6.1:** MongoDB Atlas shall host the primary database for storing application data, excluding potentially large raw document files.
* **DATA-6.2:** Separate collections within the MongoDB Atlas database should be used for:
    * User/Session information (if applicable)
    * Subject information
    * Document metadata
    * User Memory Journal entries
    * Subject Memory Journal entries
* **DATA-6.3:** Data privacy and security for stored journal entries must be a priority. Data should be linked to individual users/sessions and access controlled.
* **DATA-6.4:** A strategy for storing the actual uploaded files needs to be determined. Options include storing them on the server's file system (simpler for initial development) or using a cloud storage service like Azure Blob Storage (more scalable and robust). The choice impacts the "storage path/reference" field in the document metadata stored in MongoDB.

### 7. Future Considerations (Supplement)

* Implementing user authentication to associate data permanently with individual users.
* Refining the logic for identifying and saving relevant journal entries using more sophisticated AI techniques.
* Implementing search and retrieval features for users to browse their saved journal entries.
* Exploring different strategies for managing and querying large volumes of journal data for AI context.
* Integrating with Azure Blob Storage for scalable and cost-effective storage of the raw document files.