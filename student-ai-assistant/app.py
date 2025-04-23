import os
import uuid
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from werkzeug.utils import secure_filename
import requests
import logging
import os.path

# Import our utility modules
from document_processor import extract_document_text, prepare_document_for_indexing
from search_utils import AzureSearchClient, get_relevant_context
from mongodb_utils import MongoDBClient
from journal_utils import JournalExtractor
from timetable_agent import TimetableAgentSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_pyfile('config.py')

# Configure session
app.secret_key = app.config['SECRET_KEY']
# Configure URL handling - this ensures routes work with or without trailing slashes
app.url_map.strict_slashes = False

# Ensure the upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Azure Search client (lazy initialization)
search_client = None
# Initialize MongoDB client (lazy initialization)
mongodb_client = None
# Initialize Timetable Agent System (lazy initialization)
timetable_agent_system = None

def get_search_client():
    """Get or initialize the Azure Search client"""
    global search_client
    if search_client is None:
        search_client = AzureSearchClient(
            endpoint=app.config['AZURE_SEARCH_ENDPOINT'],
            api_key=app.config['AZURE_SEARCH_API_KEY'],
            index_name=app.config['AZURE_SEARCH_INDEX_NAME']
        )
    return search_client

def get_mongodb_client():
    """Get or initialize the MongoDB client"""
    global mongodb_client
    if mongodb_client is None:
        mongodb_client = MongoDBClient(
            uri=app.config['MONGODB_URI'],
            db_name=app.config['MONGODB_DB_NAME']
        )
        # Try to establish connection
        mongodb_client.connect()
    return mongodb_client

def get_timetable_agent_system():
    """Get or initialize the Timetable Agent System"""
    global timetable_agent_system
    if timetable_agent_system is None:
        timetable_agent_system = TimetableAgentSystem(
            openai_endpoint=app.config['AZURE_OPENAI_ENDPOINT'],
            openai_api_key=app.config['AZURE_OPENAI_API_KEY'],
            openai_api_version=app.config['AZURE_OPENAI_API_VERSION'],
            openai_deployment=app.config['AZURE_OPENAI_CHAT_DEPLOYMENT'],
            document_intelligence_endpoint=app.config.get('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'),
            document_intelligence_key=app.config.get('AZURE_DOCUMENT_INTELLIGENCE_KEY')
        )
    return timetable_agent_system

# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Helper function to get or create a session ID
def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

# Routes
@app.route('/')
def index():
    """Render the general chat page (front page)"""
    return render_template('index.html')

@app.route('/api/chat/general', methods=['POST'])
def general_chat():
    """API endpoint for the general chat functionality"""
    try:
        session_id = get_session_id()
        user_message = request.json.get('message', '')
        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Retrieve memory journal entries for context
        mongo_client = get_mongodb_client()
        user_journal_entries = mongo_client.get_user_journal_entries(session_id)
        user_memory_context = JournalExtractor.get_memory_context(user_journal_entries)

        # Retrieve all subject journal entries for additional context
        subject_journal_entries = mongo_client.get_all_subject_journal_entries(session_id)
        subject_memory_context = JournalExtractor.get_memory_context(subject_journal_entries, max_entries=10)

        # Combine both contexts
        combined_context = ""
        if user_memory_context:
            combined_context += "User's General Memory:\n" + user_memory_context + "\n\n"
        if subject_memory_context:
            combined_context += "User's Subject-Specific Memory:\n" + subject_memory_context

        # Call Azure OpenAI API with combined memory context
        response = call_azure_openai(user_message, combined_context, is_subject_chat=False)

        # Extract and save important information from the user's message
        extracted_info = JournalExtractor.extract_important_information(user_message)
        for info in extracted_info:
            entry_data = JournalExtractor.prepare_journal_entry(info['content'], session_id)
            mongo_client.add_user_journal_entry(entry_data)

        # No longer saving AI responses to the journal

        return jsonify({"response": response})
    except Exception as e:
        logger.error(f"Error in general chat: {str(e)}")
        return jsonify({"error": "An error occurred processing your request"}), 500

def call_azure_openai(user_message, context=None, is_subject_chat=False):
    """Call Azure OpenAI API with user message and optional context"""
    try:
        endpoint = app.config['AZURE_OPENAI_ENDPOINT']
        api_key = app.config['AZURE_OPENAI_API_KEY']
        api_version = app.config['AZURE_OPENAI_API_VERSION']
        deployment = app.config['AZURE_OPENAI_CHAT_DEPLOYMENT']

        # Build API URL
        url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

        # Prepare the request payload
        messages = [{"role": "user", "content": user_message}]

        # Add context if provided
        if context:
            system_role = "You are a helpful AI assistant for students."

            if is_subject_chat:
                system_role += " Use the following information from documents and previous conversations to answer the student's question. If the answer is not in the provided context, say that you don't have that information."
            else:
                system_role += " Use the following information from previous conversations to provide personalized assistance."

            system_message = {
                "role": "system",
                "content": system_role
            }
            messages.insert(0, system_message)

            # Add context message
            context_message = {"role": "system", "content": f"Context information: {context}"}
            messages.insert(1, context_message)

        payload = {
            "messages": messages,
            "max_tokens": 800,
            "temperature": 0.7,
            "top_p": 0.95,
            "stream": False
        }

        # Send request to Azure OpenAI
        headers = {
            "Content-Type": "application/json",
            "api-key": api_key
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        ai_response = result['choices'][0]['message']['content']

        return ai_response

    except Exception as e:
        logger.error(f"Azure OpenAI API error: {str(e)}")
        raise

@app.route('/subjects')
def subjects_list():
    """Render the subjects page with a list of subjects"""
    session_id = get_session_id()

    # Get subjects from MongoDB
    mongo_client = get_mongodb_client()
    subjects = mongo_client.get_subjects(session_id)

    # Fetch documents for each subject to display accurate document counts
    for subject in subjects:
        documents = mongo_client.get_subject_documents(subject['_id'])
        subject['documents'] = documents

    return render_template('subjects.html', subjects=subjects)

@app.route('/subjects/add', methods=['POST'])
def add_subject():
    """Add a new subject"""
    session_id = get_session_id()
    subject_name = request.form.get('subject_name')

    if not subject_name:
        flash('Subject name is required', 'error')
        return redirect(url_for('subjects_list'))

    # Create a new subject in MongoDB
    mongo_client = get_mongodb_client()
    subject_data = {
        'name': subject_name,
        'session_id': session_id,
    }

    subject_id = mongo_client.create_subject(subject_data)

    if subject_id:
        flash(f'Subject "{subject_name}" added successfully', 'success')
    else:
        flash('Failed to add subject', 'error')

    return redirect(url_for('subjects_list'))

@app.route('/subjects/<subject_id>')
def subject_detail(subject_id):
    """Render the subject detail page"""
    session_id = get_session_id()

    # Get subject from MongoDB
    mongo_client = get_mongodb_client()
    subject = mongo_client.get_subject(subject_id)

    if subject is None:
        flash('Subject not found', 'error')
        return redirect(url_for('subjects_list'))

    # Get document metadata from MongoDB
    documents = mongo_client.get_subject_documents(subject_id)
    subject['documents'] = documents

    return render_template('subject_detail.html', subject=subject)

@app.route('/subjects/<subject_id>/upload', methods=['POST'])
def upload_document(subject_id):
    """Upload a document for a specific subject"""
    session_id = get_session_id()

    # Get subject from MongoDB
    mongo_client = get_mongodb_client()
    subject = mongo_client.get_subject(subject_id)

    if subject is None:
        return jsonify({"error": "Subject not found"}), 404

    # Check if a file was uploaded
    if 'document' not in request.files:
        return jsonify({"error": "No document part in the request"}), 400

    file = request.files['document']

    # Check if the file was actually selected
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Check if the file extension is allowed
    if not allowed_file(file.filename):
        return jsonify({"error": f"File type not allowed. Allowed types: {', '.join(app.config['ALLOWED_EXTENSIONS'])}"}), 400

    # Secure the filename and generate a unique filename
    filename = secure_filename(file.filename)
    unique_filename = f"{subject_id}_{str(uuid.uuid4())}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

    try:
        # Save the file
        file.save(file_path)

        # Add document metadata to MongoDB
        document_data = {
            'filename': filename,
            'storage_path': unique_filename,
            'subject_id': subject_id,
            'session_id': session_id,
            'size': os.path.getsize(file_path)
        }

        document_id = mongo_client.add_document_metadata(document_data)

        if document_id:
            document_data['_id'] = document_id

        # Process and index the document in Azure AI Search if available
        if app.config.get('AZURE_SEARCH_ENDPOINT') and app.config.get('AZURE_SEARCH_API_KEY'):
            try:
                # Prepare the document for indexing
                documents = prepare_document_for_indexing(
                    doc_info=document_data,
                    subject_name=subject['name'],
                    file_path=file_path
                )

                # Upload to Azure AI Search
                if documents:
                    search_client = get_search_client()
                    uploaded = search_client.upload_documents(documents)
                    logger.info(f"Indexed {uploaded} document chunks for '{filename}'")
            except Exception as e:
                logger.error(f"Error indexing document: {str(e)}")
                # Continue without failing if indexing fails

        return jsonify({"success": True, "message": "Document uploaded successfully", "document": document_data})

    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        return jsonify({"error": f"Error uploading document: {str(e)}"}), 500

@app.route('/api/subjects/<subject_id>/chat', methods=['POST'])
def subject_chat(subject_id):
    """API endpoint for subject-specific chat functionality"""
    try:
        session_id = get_session_id()

        # Verify subject exists in MongoDB
        mongo_client = get_mongodb_client()
        subject = mongo_client.get_subject(subject_id)

        if subject is None:
            return jsonify({"error": "Subject not found"}), 404

        user_message = request.json.get('message', '')
        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Use Azure AI Search to retrieve relevant document chunks as context
        document_context = retrieve_document_context(subject_id, user_message)

        # Retrieve subject journal entries for additional context
        journal_entries = mongo_client.get_subject_journal_entries(session_id, subject_id)
        journal_context = JournalExtractor.get_memory_context(journal_entries)

        # Combine document and journal context with better formatting
        combined_context = ""

        if document_context:
            combined_context += "### DOCUMENT INFORMATION ###\n" + document_context + "\n\n"

        if journal_context:
            combined_context += "### PREVIOUS CONVERSATION INFORMATION ###\n" + journal_context + "\n\n"

        # Add a instruction if both contexts are present
        if document_context and journal_context:
            combined_context += "Please use both document information and previous conversation context to provide a comprehensive answer.\n\n"
        # Add a title for empty context
        elif not combined_context:
            combined_context = "No relevant information found."

        # Call Azure OpenAI with the combined context
        response = call_azure_openai(user_message, combined_context, is_subject_chat=True)

        # Extract and save important information from user's message only
        extracted_info = JournalExtractor.extract_important_information(user_message)
        for info in extracted_info:
            entry_data = JournalExtractor.prepare_journal_entry(info['content'], session_id, subject_id)
            mongo_client.add_subject_journal_entry(entry_data)

        # No longer saving AI responses to the journal

        return jsonify({"response": response})

    except Exception as e:
        logger.error(f"Error in subject chat: {str(e)}")
        return jsonify({"error": "An error occurred processing your request"}), 500

def retrieve_document_context(subject_id, query):
    """
    Retrieve relevant document content from Azure AI Search based on the query
    """
    try:
        # Check if we have Azure Search credentials
        if app.config.get('AZURE_SEARCH_ENDPOINT') and app.config.get('AZURE_SEARCH_API_KEY'):
            search_client = get_search_client()
            return get_relevant_context(search_client, query, subject_id)

        # Fall back to basic context if no Azure Search
        mongo_client = get_mongodb_client()
        documents = mongo_client.get_subject_documents(subject_id)

        if not documents:
            return "No documents available for this subject yet."

        # Get a sample of content from the first document
        if documents:
            doc = documents[0]
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc['storage_path'])
            if os.path.exists(file_path):
                text = extract_document_text(file_path)
                if text:
                    # Return a sample of the text (first 500 characters)
                    sample = text[:500] + "..." if len(text) > 500 else text
                    return f"Sample from {doc['filename']}:\n\n{sample}\n\nNote: In a production environment, a more sophisticated document retrieval system would be used."

        return "Document content could not be retrieved. This is a development version without proper Azure AI Search integration."

    except Exception as e:
        logger.error(f"Error retrieving document context: {str(e)}")
        return f"Error retrieving document context: {str(e)}"

# New Timetable Generator Routes

@app.route('/timetable')
def timetable():
    """Render the timetable generation page"""
    session_id = get_session_id()

    # Get subjects from MongoDB to populate the subject dropdown
    mongo_client = get_mongodb_client()
    subjects = mongo_client.get_subjects(session_id)

    # Fetch documents for each subject to display accurate document counts
    for subject in subjects:
        documents = mongo_client.get_subject_documents(subject['_id'])
        subject['documents'] = documents

    return render_template('timetable.html', subjects=subjects)

@app.route('/api/timetable/extract_topics', methods=['POST'])
def extract_topics():
    """API endpoint for extracting topics from subject documents"""
    try:
        session_id = get_session_id()
        subject_id = request.json.get('subject_id')
        scope = request.json.get('scope', 'all topics')

        if not subject_id:
            return jsonify({"error": "Subject ID is required"}), 400

        # Get subject from MongoDB
        mongo_client = get_mongodb_client()
        subject = mongo_client.get_subject(subject_id)

        if subject is None:
            return jsonify({"error": "Subject not found"}), 404

        # Get document metadata from MongoDB
        documents = mongo_client.get_subject_documents(subject_id)

        if not documents:
            return jsonify({"error": "No documents found for this subject"}), 404

        # Initialize timetable agent system
        timetable_system = get_timetable_agent_system()

        # Extract topics from documents
        extraction_results = timetable_system.extract_topics_from_documents(
            documents=documents,
            upload_folder=app.config['UPLOAD_FOLDER'],
            scope=scope
        )

        return jsonify({
            "success": True,
            "subject": subject,
            "extraction_results": extraction_results
        })

    except Exception as e:
        logger.error(f"Error extracting topics: {str(e)}")
        return jsonify({"error": f"Error extracting topics: {str(e)}"}), 500

@app.route('/api/timetable/generate', methods=['POST'])
def generate_timetable():
    """API endpoint for generating a study timetable"""
    try:
        session_id = get_session_id()
        subject_id = request.json.get('subject_id')
        extracted_topics = request.json.get('extracted_topics')
        timeframe = request.json.get('timeframe')

        if not subject_id or not extracted_topics or not timeframe:
            return jsonify({"error": "Subject ID, extracted topics, and timeframe are required"}), 400

        # Get subject from MongoDB
        mongo_client = get_mongodb_client()
        subject = mongo_client.get_subject(subject_id)

        if subject is None:
            return jsonify({"error": "Subject not found"}), 404

        # Get user's journal entries for context
        user_journal_entries = mongo_client.get_user_journal_entries(session_id, limit=30)

        # Initialize timetable agent system
        timetable_system = get_timetable_agent_system()

        # Generate timetable
        timetable_results = timetable_system.generate_timetable(
            extracted_topics=extracted_topics,
            journal_entries=user_journal_entries,
            timeframe=timeframe
        )

        return jsonify({
            "success": True,
            "subject": subject,
            "timetable_results": timetable_results
        })

    except Exception as e:
        logger.error(f"Error generating timetable: {str(e)}")
        return jsonify({"error": f"Error generating timetable: {str(e)}"}), 500

# Clean up resources when app is shutting down
@app.teardown_appcontext
def close_connections(exception=None):
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])