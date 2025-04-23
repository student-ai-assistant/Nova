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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_pyfile('config.py')

# Ensure the upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Azure Search client (lazy initialization)
search_client = None

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

# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Initialize in-memory database for subjects (in a real app, use a proper database)
subjects = []

# Routes
@app.route('/')
def index():
    """Render the general chat page (front page)"""
    return render_template('index.html')

@app.route('/api/chat/general', methods=['POST'])
def general_chat():
    """API endpoint for the general chat functionality"""
    try:
        user_message = request.json.get('message', '')
        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Call Azure OpenAI API
        response = call_azure_openai(user_message)

        return jsonify({"response": response})
    except Exception as e:
        logger.error(f"Error in general chat: {str(e)}")
        return jsonify({"error": "An error occurred processing your request"}), 500

def call_azure_openai(user_message, context=None):
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

        # Add context if provided (for subject-specific chat)
        if context:
            system_message = {
                "role": "system",
                "content": "You are a helpful AI assistant for students. Use the following information to answer the student's question. If the answer is not in the provided context, say that you don't have that information."
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
    return render_template('subjects.html', subjects=subjects)

@app.route('/subjects/add', methods=['POST'])
def add_subject():
    """Add a new subject"""
    subject_name = request.form.get('subject_name')

    if not subject_name:
        flash('Subject name is required', 'error')
        return redirect(url_for('subjects_list'))

    # Generate a unique ID for the subject
    subject_id = str(uuid.uuid4())

    # Create a new subject
    subject = {
        'id': subject_id,
        'name': subject_name,
        'documents': []
    }

    subjects.append(subject)
    flash(f'Subject "{subject_name}" added successfully', 'success')

    return redirect(url_for('subjects_list'))

@app.route('/subjects/<subject_id>')
def subject_detail(subject_id):
    """Render the subject detail page"""
    subject = next((s for s in subjects if s['id'] == subject_id), None)

    if subject is None:
        flash('Subject not found', 'error')
        return redirect(url_for('subjects_list'))

    return render_template('subject_detail.html', subject=subject)

@app.route('/subjects/<subject_id>/upload', methods=['POST'])
def upload_document(subject_id):
    """Upload a document for a specific subject"""
    subject = next((s for s in subjects if s['id'] == subject_id), None)

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

        # Add document info to subject
        document_info = {
            'id': str(uuid.uuid4()),
            'name': filename,
            'path': unique_filename,
            'subject_id': subject_id
        }
        subject['documents'].append(document_info)

        # Process and index the document in Azure AI Search if available
        if app.config.get('AZURE_SEARCH_ENDPOINT') and app.config.get('AZURE_SEARCH_API_KEY'):
            try:
                # Prepare the document for indexing
                documents = prepare_document_for_indexing(
                    doc_info=document_info,
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

        return jsonify({"success": True, "message": "Document uploaded successfully", "document": document_info})

    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        return jsonify({"error": f"Error uploading document: {str(e)}"}), 500

@app.route('/api/subjects/<subject_id>/chat', methods=['POST'])
def subject_chat(subject_id):
    """API endpoint for subject-specific chat functionality"""
    try:
        subject = next((s for s in subjects if s['id'] == subject_id), None)

        if subject is None:
            return jsonify({"error": "Subject not found"}), 404

        user_message = request.json.get('message', '')
        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Use Azure AI Search to retrieve relevant document chunks as context
        context = retrieve_document_context(subject_id, user_message)

        # Call Azure OpenAI with the context
        response = call_azure_openai(user_message, context)

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
        subject = next((s for s in subjects if s['id'] == subject_id), None)
        if subject is None or not subject['documents']:
            return "No documents available for this subject yet."

        # Get a sample of content from the first document
        if subject['documents']:
            doc = subject['documents'][0]
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc['path'])
            if os.path.exists(file_path):
                text = extract_document_text(file_path)
                if text:
                    # Return a sample of the text (first 500 characters)
                    sample = text[:500] + "..." if len(text) > 500 else text
                    return f"Sample from {doc['name']}:\n\n{sample}\n\nNote: In a production environment, a more sophisticated document retrieval system would be used."

        return "Document content could not be retrieved. This is a development version without proper Azure AI Search integration."

    except Exception as e:
        logger.error(f"Error retrieving document context: {str(e)}")
        return f"Error retrieving document context: {str(e)}"

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])