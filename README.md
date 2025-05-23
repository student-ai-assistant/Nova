# Nova

A Flask-based web application designed to help students with their studies through intelligent AI assistance, document-based learning, personalized study plans, research assistance, and quiz generation.

## Overview

The Nova provides an intuitive platform for students to:

- Chat with an AI assistant for general academic support with ability to upload temporary file context
- Organize study materials by subject
- Upload and process subject-specific documents for persistent storage
- Get AI assistance tailored to specific subjects based on uploaded materials
- Benefit from persistent memory where the AI remembers key information from past conversations
- Generate personalized study timetables with multi-level AI agent system
- Create literature reviews on specified topics
- Generate and take interactive quizzes based on subject documents

The application leverages Azure AI services (including Azure OpenAI, Azure AI Document Intelligence, and potentially Azure AI Search) for intelligent features and MongoDB Atlas for persistent storage of metadata and memory journals, making the AI's responses more personalized and contextual over time.

## Features

### General Chat
- Interactive chat interface on the front page with a welcoming motivational message
- Upload temporary files for in-memory context (not stored persistently)
- AI responds considering both the conversation and uploaded file context

### Subject Management
- Create and organize subjects
- Upload documents for persistent storage associated with subjects
- View all uploaded materials for each subject

### Subject-Specific Chat
- Chat with AI about specific subjects
- AI uses Retrieval Augmented Generation (RAG) with your uploaded documents as context
- Subject-specific memory retention for more relevant responses

### Timetable Generation
- Three-level AI agent system analyzes documents and journal entries
- Creates personalized study schedules based on your commitments
- Highlights potential conflicts with existing commitments
- Download timetable in iCalendar (.ics) format

### Literature Review
- Generate comprehensive research reports
- Submit a query and get a Markdown-formatted literature review

### Quiz Generation
- Create multiple-choice quizzes based on your subject documents
- Specify topics for targeted assessment
- Take interactive quizzes and receive immediate scoring
- Review correct answers after completion

## Setup Instructions

### Prerequisites

- Python 3.10+
- Conda package manager
- MongoDB Atlas account
- Azure AI services:
  - Azure OpenAI service
  - Azure AI Document Intelligence (formerly Form Recognizer)
  - Azure AI Search (for RAG implementation)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd nova
   ```

2. Create and activate the Conda environment:
   ```
   conda env create -f nova/environment.yml
   conda activate nova
   ```

3. Set up environment variables:
   Create a `.env` file in the project root with the following variables:
   ```
   # Azure OpenAI Configuration
   AZURE_OPENAI_API_KEY=your_api_key_here
   AZURE_OPENAI_ENDPOINT=your_endpoint_here
   AZURE_OPENAI_API_VERSION=your_api_version_here
   AZURE_OPENAI_CHAT_DEPLOYMENT=your_deployment_name_here

   # Azure AI Document Intelligence
   AZURE_DOCUMENT_INTELLIGENCE_KEY=your_doc_intelligence_key_here
   AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=your_doc_intelligence_endpoint_here

   # Azure AI Search (for RAG)
   AZURE_SEARCH_ENDPOINT=your_search_endpoint_here
   AZURE_SEARCH_API_KEY=your_search_api_key_here
   AZURE_SEARCH_INDEX_NAME=your_index_name_here

   # MongoDB Atlas
   MONGODB_URI=your_mongodb_atlas_uri_here
   MONGODB_DB_NAME=your_database_name_here

   # Flask Configuration
   SECRET_KEY=your_flask_secret_key_here
   ```

### Running the Application

1. Start the Flask application:
   ```
   flask run
   ```

2. Access the application in your browser at `http://localhost:5000`

## Acknowledgments

- Built with Flask, MongoDB Atlas, and Azure AI services
- Uses Tailwind CSS for modern Material Design UI
- Built for [Q-Summit Hackathon](https://www.q-summit.com/hackathon) as part of the Microsoft challenge "Build AI Agents to Simplify Student Life"
