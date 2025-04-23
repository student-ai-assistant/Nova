# Student AI Assistant

A Flask-based web application designed to help students with their studies through intelligent AI assistance and document-based learning.

## Overview

The Student AI Assistant provides an intuitive platform for students to:

- Chat with an AI assistant for general academic support
- Organize study materials by subject
- Upload and process subject-specific documents
- Get AI assistance tailored to specific subjects based on uploaded materials
- Benefit from persistent memory where the AI remembers key information from past conversations

The application leverages Azure OpenAI for the chat functionality and MongoDB Atlas for storing metadata and memory journals, making the AI's responses more personalized and contextual over time.

## Setup Instructions

### Prerequisites

- Python 3.10+
- Conda package manager
- MongoDB Atlas account
- Azure OpenAI service access
- Azure AI Search service

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd student-ai-assistant
   ```

2. Create and activate the Conda environment:
   ```
   conda env create -f student-ai-assistant/environment.yml
   conda activate student-ai-assistant
   ```

3. Set up environment variables:
   Create a `.env` file in the project root with the following variables:
   ```
   AZURE_OPENAI_API_KEY=your_api_key_here
   AZURE_OPENAI_ENDPOINT=your_endpoint_here
   AZURE_OPENAI_API_VERSION=your_api_version_here
   AZURE_OPENAI_CHAT_DEPLOYMENT=your_deployment_name_here
   AZURE_SEARCH_ENDPOINT=your_search_endpoint_here
   AZURE_SEARCH_API_KEY=your_search_api_key_here
   AZURE_SEARCH_INDEX_NAME=your_index_name_here
   MONGODB_URI=your_mongodb_atlas_uri_here
   MONGODB_DB_NAME=your_database_name_here
   SECRET_KEY=your_flask_secret_key_here
   ```

### Running the Application

1. Start the Flask application:
   ```
   flask run
   ```

2. Access the application in your browser at `http://localhost:5000`

## Basic Usage

- **General Chat**: Available on the home page for asking any academic questions
- **Subjects**: Create subjects and upload study materials via the Subjects section
- **Subject-Specific Chat**: Ask questions related to your uploaded materials within each subject page

The AI assistant will remember important information from your conversations across sessions to provide more personalized assistance over time.
