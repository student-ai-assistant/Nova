# Project Requirements Document: Student AI Assistant - UI Enhancements and Document Management

### 1. Introduction (Supplement)

This document details requirements for further enhancing the user interface and adding document management functionality to the Student AI Assistant. This includes implementing a dark mode toggle, adding final design touches, and enabling the deletion of uploaded subject documents.

### 2. Goals and Objectives (Supplement)

* Provide users with the option to switch between light and dark color schemes.
* Enhance the overall visual appeal of the application with refined design elements.
* Allow users to manage their uploaded subject documents by providing a delete option.
* Maintain a consistent and modern user interface using Tailwind CSS and Material Design principles.

### 3. User Stories (Supplement)

* As a student, I want to be able to use the app in dark mode to reduce eye strain.
* As a student, I want the app to look polished and visually appealing.
* As a student, I want to be able to remove subject documents that I no longer need.

### 4. Functional Requirements (Supplement)

**4.1. Dark Mode Toggle**

* **REQ-FUN-4.1.1:** The application shall include a user interface element (e.g., a toggle switch, button, or menu option) to enable or disable dark mode.
* **REQ-FUN-4.1.2:** When dark mode is enabled, the application's color scheme shall switch to a darker palette for backgrounds, text, and UI elements.
* **REQ-FUN-4.1.3:** When dark mode is disabled (or light mode is active), the application shall use a lighter color scheme.
* **REQ-FUN-4.1.4:** The user's preference for light or dark mode shall be saved (e.g., in a cookie or local storage) so that the preference persists across sessions.

**4.2. Overall Design Improvements**

* **REQ-FUN-4.2.1:** Implement final design touches and refinements across all sections of the application to enhance the overall aesthetic.
* **REQ-FUN-4.2.2:** Add small, non-distracting decorative elements (e.g., subtle icons, illustrations, background patterns, improved spacing and typography details) to make the design more appealing and inviting, while adhering to Material Design principles.

**4.3. Document Deletion**

* **REQ-FUN-4.3.1:** Within the detailed view of a specific subject, there shall be an option to delete each previously uploaded document. This could be an icon (e.g., trash can) displayed next to each document listing.
* **REQ-FUN-4.3.2:** Clicking the delete option for a document shall initiate the document deletion process.
* **REQ-FUN-4.3.3:** The user shall be prompted with a confirmation dialog before a document is permanently deleted to prevent accidental deletion.
* **REQ-FUN-4.3.4:** Upon confirmation, the application shall remove the document's metadata from MongoDB Atlas.
* **REQ-FUN-4.3.5:** The application shall also delete the actual document file from the backend storage location (file system or cloud storage).
* **REQ-FUN-4.3.6:** The document listing for the subject shall update automatically after a document is successfully deleted.

### 5. Technical Requirements (Supplement)

* **TECH-REQ-5.1:** Implement frontend logic (JavaScript) to handle the state of the dark mode toggle and apply the appropriate CSS classes (provided by Tailwind CSS) to the relevant HTML elements based on the selected mode.
* **TECH-REQ-5.2:** Utilize Tailwind CSS's built-in dark mode support or custom classes to define the different styles for light and dark themes.
* **TECH-REQ-5.3:** Implement frontend JavaScript to save and retrieve the dark mode preference using browser storage (e.g., `localStorage`).
* **TECH-REQ-5.4:** Implement the design improvements by adding/modifying HTML structures and applying additional Tailwind CSS classes and potentially custom CSS for decorative elements.
* **TECH-REQ-5.5:** Implement a new Flask route on the backend to handle document deletion requests (e.g., `/api/subjects/<subject_id>/documents/<document_id>/delete`).
* **TECH-REQ-5.6:** Develop backend logic for the document deletion route to:
    * Receive the subject ID and document ID to be deleted.
    * Authenticate/authorize the request (if user authentication is implemented later).
    * Retrieve the document's metadata from MongoDB Atlas using the document ID.
    * Using the storage path/reference from the metadata, delete the actual file from the backend file system or cloud storage. Implement error handling for file deletion.
    * Delete the document's metadata from the `document_metadata` collection in MongoDB Atlas. Implement error handling for database deletion.
    * Return a success or failure response to the frontend.
* **TECH-REQ-5.7:** Implement frontend JavaScript to:
    * Display the delete option for each document in the subject detail view.
    * Trigger a confirmation dialog when the delete option is clicked.
    * Send an AJAX request to the backend delete route upon user confirmation, including the subject and document IDs.
    * Update the UI (remove the document from the list) upon receiving a successful response.
* **TECH-REQ-5.8:** Ensure proper error handling is displayed to the user if document deletion fails on the backend.

### 6. UI/UX Requirements (Supplement)

* **UI-UX-6.1:** The dark mode toggle shall be easily accessible within the application interface (e.g., in the sidebar or a header/footer).
* **UI-UX-6.2:** The visual transition between light and dark mode should be smooth.
* **UI-UX-6.3:** The dark mode color scheme shall be aesthetically pleasing and provide good contrast for readability.
* **UI-UX-6.4:** The design improvements and decorative elements should enhance the user experience without being distracting or cluttering the interface. They should align with the Material Design principles.
* **UI-UX-6.5:** The delete option for documents should be visually clear (e.g., a trash icon) but also placed carefully to avoid accidental clicks.
* **UI-UX-6.6:** The confirmation dialog for document deletion should be clear and concise, explaining the action and requiring explicit user confirmation.
* **UI-UX-6.7:** Provide clear visual feedback on the success or failure of a document deletion operation.

### 7. Data Management (Supplement)

* **DATA-7.1:** The document deletion feature requires deleting data from two locations: the `document_metadata` collection in MongoDB Atlas and the actual file from backend storage.
* **DATA-7.2:** Ensure data consistency: if metadata is deleted from MongoDB, the corresponding file should also be deleted, and vice versa, to avoid orphaned files or broken database references. Implement logic to handle potential failures in either step.

### 8. Future Considerations (Supplement)

* Implementing bulk document deletion.
* Adding an "undo" option for recently deleted documents (requires temporary storage or a "soft delete" mechanism).
* Providing a visual indicator of storage space used per subject or in total.