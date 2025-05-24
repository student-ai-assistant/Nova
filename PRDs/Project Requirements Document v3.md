# Project Requirements Document: Nova

## 1. Introduction

Nova is a Flask-based web application designed to help students with their studies. Leveraging the power of AI, Nova provides personalized assistance in various aspects of learning, including but not limited to, resource discovery, query resolution, and study planning. The application aims to integrate seamlessly into the student's academic life, offering support that is both intelligent and intuitive.

This document details the requirements for adding a new "Timetable Generation" feature to Nova. This feature will utilize a multi-level AI agent architecture powered by Azure AI to create personalized study plans based on user-specified study goals, uploaded subject documents, and existing user journal entries stored in MongoDB Atlas.

### 2. Goals and Objectives (Supplement)

* Introduce a dedicated section for generating study timetables.
* Enable users to specify study goals (subject/document and target timeframe).
* Implement a multi-level AI agent workflow to process study materials and user context.
* Generate personalized study timetables that consider subject content and user commitments from their journal.
* Present the generated timetable to the user in an understandable format.
* Integrate the new feature seamlessly with the existing Flask application, leveraging MongoDB Atlas and Azure AI.

### 3. User Stories (Supplement)

* As a student, I want a dedicated tool to help me plan my study schedule.
* As a student, I want to easily select a subject or provide materials I need to study for the timetable.
* As a student, I want to tell the AI what I need to study and by when.
* As a student, I want the AI to understand the key topics from my study materials.
* As a student, I want the AI to consider my existing commitments (from my journal) when creating a study plan.
* As a student, I want the AI to provide me with a clear study timetable.

### 4. Functional Requirements (Supplement)

**4.1. Timetable Generation Section**

* **REQ-FUN-4.1.1:** A new section for "Timetable Generation" shall be added to the application.
* **REQ-FUN-4.1.2:** A link or icon for the Timetable Generation section shall be added to the foldable sidebar navigation.

**4.2. Study Goal Input**

* **REQ-FUN-4.2.1:** Within the Timetable Generation section, the user shall be able to specify the subject matter for which they need a timetable. This should allow selecting an existing subject from their saved subjects. An option to upload a new, temporary document specifically for this timetable generation task could also be considered, though prioritizing existing subject documents is key.
* **REQ-FUN-4.2.2:** The user shall be able to input the specific topics or scope they want to cover within the selected subject/document. A text input field is required for this.
* **REQ-FUN-4.2.3:** The user shall be able to specify a target date or timeframe for completing the study plan (e.g., "study for the exam in two weeks", "cover these topics by Friday").

**4.3. Multi-Level Agentic Workflow**

* **REQ-FUN-4.3.1:** Upon user submission of study goals, the application shall initiate a multi-level AI agent process.
* **REQ-FUN-4.3.2:** **Agent 1 (Topic Extractor):**
    * This agent shall receive the selected subject's uploaded documents (retrieved via metadata from MongoDB Atlas and content access) or the content of a newly uploaded document.
    * It shall analyze the document content to identify and extract the main topics, chapters, or key concepts relevant to the user's specified scope if possible, or provide a general outline if no specific scope is given.
    * The extracted topics/summary shall be passed to Agent 2.
    * This agent will utilize **Azure AI services such as Azure AI Document Intelligence (for text and structure extraction) and Azure OpenAI Service (for processing the extracted text to identify and summarize topics)**.
* **REQ-FUN-4.3.3:** **Agent 2 (Timetable Generator):**
    * This agent shall receive the extracted topics/summary from Agent 1.
    * It shall retrieve relevant entries from the user's general memory journal stored in MongoDB Atlas to understand existing commitments, appointments, or preferred study times. The method for identifying "relevant" journal entries is important here (e.g., filtering by date, keywords like "meeting", "class", "work").
    * Using the extracted topics, the target timeframe, and the user's journal information, this agent shall generate a structured study plan or timetable.
    * The timetable should ideally break down the study goals into actionable steps or sessions allocated within the specified timeframe, considering the user's availability as indicated in their journal.
    * This agent will also utilize **Azure AI services, primarily Azure OpenAI Service, to process the combined context (topics, journal entries, timeframe) and generate the structured timetable. Azure AI Agent Service could potentially be used to orchestrate the workflow between Agent 1 and Agent 2.**

**4.4. Timetable Output**

* **REQ-FUN-4.4.1:** The generated study plan/timetable from Agent 2 shall be presented to the user in a clear and readable format within the Timetable Generation section.
* **REQ-FUN-4.4.2:** The format could be a simple list, a table, or a visual representation of a calendar or schedule.
* **REQ-FUN-4.4.3:** The user should be able to view the complete generated timetable.

### 5. Technical Requirements (Supplement)

* **TECH-REQ-5.1:** Implement new Flask routes and backend logic for the Timetable Generation section.
* **TECH-REQ-5.2:** Develop the backend logic to manage the interaction and data passing between the two AI agents. This might involve sequential API calls to different Azure AI model deployments or different prompts to a single, more capable model instructed to perform steps sequentially. **Consider using Azure AI Agent Service or frameworks like Semantic Kernel or AutoGen for orchestrating this multi-agent workflow.**
* **TECH-REQ-5.3:** Integrate with MongoDB Atlas to:
    * Retrieve document metadata for the selected subject.
    * Access the actual document content based on the storage path/reference.
    * Retrieve relevant entries from the user's general memory journal.
* **TECH-REQ-5.4:** Utilize **Azure AI Document Intelligence (Layout/Read models) for initial document text and structure extraction.**
* **TECH-REQ-5.5:** Utilize **Azure OpenAI Service (e.g., GPT-4, GPT-4o) for the core logic of both Agent 1 (processing extracted text for topics/summaries) and Agent 2 (generating the timetable based on topics, journal context, and timeframe).**
* **TECH-REQ-5.6:** Implement logic to select or filter relevant journal entries for Agent 2.
* **TECH-REQ-5.7:** Design the data flow between the frontend, Flask backend, MongoDB Atlas, and the Azure AI agents.
* **TECH-REQ-5.8:** Consider the potential latency of multi-step AI processes and provide appropriate loading indicators or feedback to the user.
* **TECH-REQ-5.9:** Securely manage Azure AI service keys and endpoints.

### 6. UI/UX Requirements (Supplement)

* **UI-UX-6.1:** Design a user-friendly interface for the Timetable Generation section, consistent with the overall Material Design theme using Tailwind CSS.
* **UI-UX-6.2:** Provide clear input fields for selecting a subject/document, specifying study scope, and setting a target timeframe.
* **UI-UX-6.3:** Display the generated timetable in an easy-to-read and well-formatted manner.
* **UI-UX-6.4:** Include visual feedback during the timetable generation process (e.g., "Analyzing documents...", "Extracting topics...", "Consulting your journal...", "Creating your study plan...").

### 7. Data Management (Supplement)

* **DATA-7.1:** Leverage existing data in MongoDB Atlas:
    * Subject information.
    * Document metadata to access document content.
    * User memory journal entries.
* **DATA-7.2:** No new persistent data storage in MongoDB Atlas is strictly required by this feature, but it relies heavily on the existing stored data.

### 8. Future Considerations (Supplement)

* Allowing users to edit or refine the generated timetable.
* Integrating with external calendar applications.
* Providing options for different study plan formats or granularities.
* Using subject-specific journal entries in Agent 2's context as well.
* Implementing feedback mechanisms for users to rate the quality of the generated timetables, which could potentially be used to fine-tune the AI prompts or logic.
* **Exploring more advanced orchestration patterns using Azure AI Agent Service or frameworks like Semantic Kernel/AutoGen as the application grows.**