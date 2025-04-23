# Project Requirements Document: Student AI Assistant - Enhanced Timetable Generation Feature

### 1. Introduction (Supplement)

This document details the requirements for enhancing the "Timetable Generation" feature within the Student AI Assistant. A refined multi-level AI agent architecture will be implemented using Azure AI to create more personalized and practical study plans. This includes a new agent dedicated to processing user journal entries to better understand time commitments, leveraging data from uploaded subject documents and journal entries stored in MongoDB Atlas.

### 2. Goals and Objectives (Supplement)

* Refine the multi-level AI agent workflow for improved timetable accuracy.
* Introduce a dedicated agent to extract and structure time commitment information from user journal entries.
* Generate personalized study timetables that accurately reflect subject content and user availability based on augmented journal data.
* Visually highlight conflicts between the proposed study plan and user commitments.
* Enable users to download the generated timetable in a calendar-compatible format.
* Ensure the timetable generation considers the user's specified timeframe starting from the next day relative to the current date.

### 3. User Stories (Supplement)

* As a student, I want the AI to understand my existing appointments and activities from my journal when creating a study plan.
* As a student, I want the study timetable to clearly show me where study times clash with my commitments.
* As a student, I want to download the generated timetable to add it to my personal calendar.
* As a student, I want the timetable to start planning from tomorrow, not today.

### 4. Functional Requirements (Supplement)

**4.1. Timetable Generation Section (No Change)**

* **REQ-FUN-4.1.1:** A new section for "Timetable Generation" shall be added to the application.
* **REQ-FUN-4.1.2:** A link or icon for the Timetable Generation section shall be added to the foldable sidebar navigation.

**4.2. Study Goal Input (Refinement)**

* **REQ-FUN-4.2.1:** Within the Timetable Generation section, the user shall be able to specify the subject matter for which they need a timetable. This should allow selecting an existing subject from their saved subjects. An option to upload a new, temporary document specifically for this timetable generation task could also be considered, though prioritizing existing subject documents is key.
* **REQ-FUN-4.2.2:** The user shall be able to input the specific topics or scope they want to cover within the selected subject/document. A text input field is required for this.
* **REQ-FUN-4.2.3:** The user shall be able to specify a target date or timeframe for completing the study plan (e.g., "study for the exam in two weeks", "cover these topics by Friday"). **The application shall calculate the actual end date based on the current date and the user's specified timeframe, and the timetable will commence from the day immediately following the current date.**

**4.3. Multi-Level Agentic Workflow (Updated)**

* **REQ-FUN-4.3.1:** Upon user submission of study goals, the application shall initiate a multi-level AI agent process with the following flow: User Input -> Agent 1 (Topic Extraction) -> **Agent 3 (Journal Augmentation)** -> Agent 2 (Timetable Generation).
* **REQ-FUN-4.3.2:** **Agent 1 (Topic Extractor):**
    * This agent shall receive the selected subject's uploaded documents (retrieved via metadata from MongoDB Atlas and content access) or the content of a newly uploaded document.
    * It shall analyze the document content to identify and extract the main topics, chapters, or key concepts relevant to the user's specified scope if possible, or provide a general outline if no specific scope is given.
    * The extracted topics/summary shall be passed to Agent 3.
    * This agent will utilize **Azure AI services such as Azure AI Document Intelligence (for text and structure extraction) and Azure OpenAI Service (for processing the extracted text to identify and summarize topics)**.
* **REQ-FUN-4.3.3:** **Agent 3 (Journal Augmentation):**
    * This agent shall receive relevant entries from the user's general memory journal stored in MongoDB Atlas (each with its original timestamp and content).
    * It shall analyze the natural language content of these journal entries to identify specific time-related commitments, appointments, or blocks of unavailability.
    * It shall extract structured information from these entries, such as the date, time, duration, and a brief description of the commitment.
    * The output of this agent shall be a structured list of user commitments with associated date/time and duration information, which shall be passed to Agent 2.
    * This agent will primarily utilize **Azure OpenAI Service for its natural language understanding and data extraction capabilities.**
* **REQ-FUN-4.3.4:** **Agent 2 (Timetable Generator):**
    * This agent shall receive the extracted topics/summary from Agent 1.
    * It shall receive the **augmented, structured list of user commitments from Agent 3**.
    * Using the extracted topics, the calculated study period (starting from the day after the current date), and the structured user commitments, this agent shall generate a structured study plan or timetable.
    * The timetable should break down the study goals into actionable steps or sessions allocated within the specified timeframe, **explicitly avoiding or marking conflicts with the user's identified commitments.**
    * This agent will primarily utilize **Azure OpenAI Service to process the combined context and generate the structured timetable. Azure AI Agent Service or frameworks like Semantic Kernel/AutoGen could potentially be used to orchestrate the entire three-agent workflow.**

**4.4. Timetable Output (Updated)**

* **REQ-FUN-4.4.1:** The generated study plan/timetable from Agent 2 shall be presented to the user in a clear and readable format within the Timetable Generation section.
* **REQ-FUN-4.4.2:** The timetable shall **visually indicate any instances where a proposed study slot overlaps with a user commitment identified by Agent 3. This highlighting should be clear and easily distinguishable.**
* **REQ-FUN-4.4.3:** The user should be able to view the complete generated timetable.
* **REQ-FUN-4.4.4:** A button or link shall be provided to allow the user to download the generated timetable.
* **REQ-FUN-4.4.5:** The timetable download shall be in a standard calendar format, such as iCalendar (.ics), containing the study sessions as events.

### 5. Technical Requirements (Supplement)

* **TECH-REQ-5.1:** Implement new Flask routes and backend logic for the Timetable Generation section.
* **TECH-REQ-5.2:** Develop the backend logic to manage the interaction and data passing between the three AI agents (Agent 1 -> Agent 3 -> Agent 2). This requires orchestrating sequential calls to different Azure AI model deployments or carefully structured prompts to a single model. **Consider using Azure AI Agent Service or frameworks like Semantic Kernel or AutoGen for orchestrating this multi-agent workflow.**
* **TECH-REQ-5.3:** Integrate with MongoDB Atlas to:
    * Retrieve document metadata for the selected subject.
    * Access the actual document content based on the storage path/reference.
    * Retrieve relevant entries from the user's general memory journal for Agent 3.
* **TECH-REQ-5.4:** Utilize **Azure AI Document Intelligence (Layout/Read models) for initial document text and structure extraction (for Agent 1).**
* **TECH-REQ-5.5:** Utilize **Azure OpenAI Service (e.g., GPT-4, GPT-4o) for the core logic of Agent 1 (topic identification), Agent 3 (journal augmentation), and Agent 2 (timetable generation).** Careful prompt engineering is required for each agent's specific task.
* **TECH-REQ-5.6:** Implement logic to select or filter relevant journal entries for Agent 3.
* **TECH-REQ-5.7:** Implement backend logic to calculate the study timeframe based on the current date and user input, **ensuring the start date is the day after the current date.**
* **TECH-REQ-5.8:** Implement backend logic to generate an iCalendar (.ics) file from the structured timetable output of Agent 2, including incorporating commitment information for potential display in calendar apps.
* **TECH-REQ-5.9:** Design the data flow between the frontend, Flask backend, MongoDB Atlas, and the Azure AI agents.
* **TECH-REQ-5.10:** Implement error handling for the multi-step AI process and file generation.
* **TECH-REQ-5.11:** Consider the potential latency of multi-step AI processes and provide appropriate loading indicators or feedback to the user.
* **TECH-REQ-5.12:** Securely manage Azure AI service keys and endpoints.

### 6. UI/UX Requirements (Supplement)

* **UI-UX-6.1:** Design a user-friendly interface for the Timetable Generation section, consistent with the overall Material Design theme using Tailwind CSS.
* **UI-UX-6.2:** Provide clear input fields for selecting a subject/document, specifying study scope, and setting a target timeframe.
* **UI-UX-6.3:** Display the generated timetable in an easy-to-read and well-formatted manner. **Visually distinguish or highlight study slots that conflict with detected user commitments.**
* **UI-UX-6.4:** Include visual feedback during the timetable generation process, indicating the progress through the different agent steps (e.g., "Analyzing documents...", "Extracting topics...", "Analyzing your journal for commitments...", "Creating your study plan...", "Highlighting conflicts...").
* **UI-UX-6.5:** Provide a clear and easily accessible button for downloading the timetable as an iCalendar file.

### 7. Data Management (Supplement)

* **DATA-7.1:** Leverage existing data in MongoDB Atlas:
    * Subject information.
    * Document metadata to access document content.
    * User memory journal entries (used as input for Agent 3).
* **DATA-7.2:** The augmented journal data produced by Agent 3 is a temporary output used by Agent 2 and does not necessarily need to be persistently stored in MongoDB Atlas, although this could be a future consideration.

### 8. Future Considerations (Supplement)

* Allowing users to edit or refine the generated timetable within the application.
* **More sophisticated conflict resolution strategies beyond just highlighting, potentially offering alternative study slots.**
* Integrating directly with external calendar applications for two-way sync (requires handling authentication and API integrations).
* Providing options for different study plan formats or granularities.
* Using subject-specific journal entries in Agent 3/Agent 2's context as well.
* Implementing feedback mechanisms for users to rate the quality of the generated timetables.
* Exploring more advanced orchestration patterns using Azure AI Agent Service or frameworks like Semantic Kernel/AutoGen as the application grows.