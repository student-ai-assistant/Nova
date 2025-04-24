# Project Requirements Document: Student AI Assistant - Quiz Generation Feature

### 1. Introduction (Supplement)

This document details the requirements for adding a "Quiz Generation" feature to the Student AI Assistant. This feature will enable students to create and take multiple-choice quizzes based on the documents associated with their saved subjects and specific topics within those subjects, utilizing AI to generate questions and score the results.

### 2. Goals and Objectives (Supplement)

* Introduce a dedicated section for generating and taking quizzes.
* Allow users to select a subject and specify a topic for a quiz.
* Utilize AI to generate multiple-choice questions based on the content of subject documents related to the chosen topic.
* Provide an interactive interface for users to take the generated quiz.
* Implement functionality to score the quiz upon submission and display the results, including correct answers.
* Integrate the quiz feature with existing subject and document data stored in MongoDB Atlas and leverage Azure AI services.

### 3. User Stories (Supplement)

* As a student, I want to be able to test my knowledge on a specific topic within one of my subjects.
* As a student, I want the quiz questions to be generated from the documents I have uploaded for that subject.
* As a student, I want to take an interactive quiz in the application.
* As a student, I want to see my score after completing the quiz.
* As a student, I want to know which answers were correct after the quiz is scored so I can learn.

### 4. Functional Requirements (Supplement)

**4.1. Quiz Generation Section**

* **REQ-FUN-4.1.1:** A new section for "Quiz Generation" shall be added to the application.
* **REQ-FUN-4.1.2:** A link or icon for the Quiz Generation section shall be added to the foldable sidebar navigation.

**4.2. Quiz Topic Selection**

* **REQ-FUN-4.2.1:** Within the Quiz Generation section, the user shall first be prompted to select one of their saved subjects. A dropdown or list of existing subjects (retrieved from MongoDB Atlas) shall be displayed.
* **REQ-FUN-4.2.2:** After selecting a subject, the user shall be prompted to enter a specific topic within that subject for which they want to generate a quiz. A text input field shall be provided.

**4.3. Quiz Generation Agent**

* **REQ-FUN-4.3.1:** Upon user submission of the subject and topic, an AI agent shall be initiated to generate the quiz.
* **REQ-FUN-4.3.2:** The agent shall access the documents associated with the selected subject (retrieved via metadata from MongoDB Atlas and content access).
* **REQ-FUN-4.3.3:** The agent shall process the content of these documents, focusing specifically on information related to the user-provided topic. This may involve techniques similar to those used in the subject-specific chat and timetable generation (e.g., leveraging Azure AI Search for relevant document chunks).
* **REQ-FUN-4.3.4:** The agent shall generate a set of multiple-choice questions based on the processed document content and the specified topic. Each question shall have a clear question stem and multiple answer options, with one correct answer. The number of questions and options per question should be reasonable (e.g., 5-10 questions, 3-4 options per question).
* **REQ-FUN-4.3.5:** The generated quiz data (questions, options, correct answers) shall be structured and passed to the frontend for display.
* **REQ-FUN-4.3.6:** The quiz generation process shall utilize Azure AI capabilities, likely leveraging **Azure OpenAI Service** for understanding the documents and generating questions/answers.

**4.4. Interactive Quiz Display**

* **REQ-FUN-4.4.1:** The generated multiple-choice quiz shall be displayed to the user in an interactive format on the frontend.
* **REQ-FUN-4.4.2:** Each question shall be clearly presented, followed by its answer options.
* **REQ-FUN-4.4.3:** Users shall be able to select one option for each question (e.g., using radio buttons).
* **REQ-FUN-4.4.4:** A "Submit Quiz" button shall be prominently displayed at the end of the quiz.

**4.5. Quiz Scoring and Results Display**

* **REQ-FUN-4.5.1:** Upon clicking the "Submit Quiz" button, the application shall process the user's selected answers.
* **REQ-FUN-4.5.2:** The user's answers shall be compared against the correct answers (originally provided by the AI agent).
* **REQ-FUN-4.5.3:** A score shall be calculated (e.g., number of correct answers or a percentage).
* **REQ-FUN-4.5.4:** The final score shall be clearly displayed to the user in the Quiz Generation section.
* **REQ-FUN-4.5.5:** For each question, the application shall indicate whether the user's answer was correct or incorrect.
* **REQ-FUN-4.5.6:** For each question, the application shall clearly show which option was the correct answer.

**4.6. Loading Indicator**

* **REQ-FUN-4.6.1:** The application shall display a loading animation or message while the AI agent is generating the quiz.

### 5. Technical Requirements (Supplement)

* **TECH-REQ-5.1:** Implement new Flask routes and backend logic for the Quiz Generation section. This includes routes for selecting a subject/topic, initiating quiz generation, and submitting answers for scoring.
* **TECH-REQ-5.2:** Develop backend logic to:
    * Retrieve subject and document metadata from MongoDB Atlas.
    * Access and process the content of relevant subject documents.
    * Interact with the Azure AI service (likely Azure OpenAI) to generate the quiz questions, options, and correct answers based on the document content and topic.
    * Store the generated quiz data temporarily on the backend (e.g., in session or a temporary cache) to allow for scoring upon submission.
    * Receive user answers from the frontend.
    * Score the quiz by comparing user answers to the correct answers.
    * Send the score and correct answers back to the frontend.
* **TECH-REQ-5.3:** Implement frontend JavaScript to:
    * Handle subject and topic selection input.
    * Display the loading indicator during quiz generation.
    * Receive and dynamically render the quiz questions and options in an interactive format.
    * Capture user selections for each question.
    * Send user answers to the backend upon submission.
    * Receive and display the quiz score and the correct answers.
* **TECH-REQ-5.4:** Utilize **Azure OpenAI Service** for the AI agent responsible for generating quiz questions and answers based on document content. This may involve careful prompt engineering to instruct the model on creating multiple-choice questions with a single correct answer from provided text.
* **TECH-REQ-5.5:** Integrate with existing document retrieval mechanisms (potentially leveraging Azure AI Search as used in RAG) to provide relevant document content to the quiz generation agent.
* **TECH-REQ-5.6:** Design the data flow between the frontend, Flask backend, MongoDB Atlas, and the Azure AI agent for quiz generation and scoring.
* **TECH-REQ-5.7:** Consider the potential latency of AI-based quiz generation and ensure the loading indicator is effective.
* **TECH-REQ-5.8:** Securely manage Azure AI service keys and endpoints.

### 6. UI/UX Requirements (Supplement)

* **UI-UX-6.1:** Design a user-friendly interface for the Quiz Generation section, consistent with the overall Material Design theme using Tailwind CSS.
* **UI-UX-6.2:** Provide clear steps for selecting a subject and entering a topic.
* **UI-UX-6.3:** Display the generated quiz questions and answer options in a clean, readable, and interactive format. Use radio buttons or similar controls for answer selection.
* **UI-UX-6.4:** Include a prominent "Submit Quiz" button.
* **UI-UX-6.5:** Display the score and results clearly and understandably.
* **UI-UX-6.6:** Clearly indicate which options were correct after scoring, potentially using visual cues like color (e.g., green for correct, red for incorrect user answer) and marking the correct option.
* **UI-UX-6.7:** Include a clear visual indicator (loading animation, message) during the quiz generation process.

### 7. Data Management (Supplement)

* **DATA-7.1:** This feature relies on existing subject and document data stored in MongoDB Atlas.
* **DATA-7.2:** The generated quiz questions, options, and correct answers can be stored temporarily on the backend (e.g., in the user's session) for the purpose of scoring. Persistent storage of quiz attempts or generated quizzes is not required in this initial version but could be a future consideration.

### 8. Future Considerations (Supplement)

* Allowing users to specify the number of questions or difficulty level.
* Generating different question types (e.g., true/false, fill-in-the-blank).
* Providing explanations for correct/incorrect answers.
* Storing quiz history and user performance.
* Allowing users to save or share quizzes.
* Incorporating a wider range of document types or even web content for quiz generation.