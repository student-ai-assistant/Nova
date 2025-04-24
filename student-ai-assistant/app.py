import os
import uuid
import json
import base64
import tempfile
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, send_file, Response
from werkzeug.utils import secure_filename
import requests
import logging
import os.path
import datetime
import io

# Import our utility modules
from document_processor import extract_document_text, prepare_document_for_indexing, extract_text_from_pdf
from search_utils import AzureSearchClient, get_relevant_context
from mongodb_utils import MongoDBClient
from journal_utils import JournalExtractor
from motivational_utils import motivational , get_values
from timetable_agent import TimetableAgentSystem
from agents.research_agent import run_lit_review
from agents.quiz_agent import QuizGenerator


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
# Initialize Quiz Generator (lazy initialization)
quiz_generator = None

def get_search_client():
    """Get or initialize the Azure Search client"""
    global search_client
    if (search_client is None):
        search_client = AzureSearchClient(endpoint=app.config['AZURE_SEARCH_ENDPOINT'], api_key=app.config['AZURE_SEARCH_API_KEY'], index_name=app.config['AZURE_SEARCH_INDEX_NAME'])
    return search_client

def get_mongodb_client():
    """Get or initialize the MongoDB client"""
    global mongodb_client
    if (mongodb_client is None):
        mongodb_client = MongoDBClient(uri=app.config['MONGODB_URI'], db_name=app.config['MONGODB_DB_NAME'])
        # Try to establish connection
        mongodb_client.connect()
    return mongodb_client

def get_timetable_agent_system():
    """Get or initialize the Timetable Agent System"""
    global timetable_agent_system
    if (timetable_agent_system is None):
        timetable_agent_system = TimetableAgentSystem(openai_endpoint=app.config['AZURE_OPENAI_ENDPOINT'], openai_api_key=app.config['AZURE_OPENAI_API_KEY'], openai_api_version=app.config['AZURE_OPENAI_API_VERSION'], openai_deployment=app.config['AZURE_OPENAI_CHAT_DEPLOYMENT'], document_intelligence_endpoint=app.config.get('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'), document_intelligence_key=app.config.get('AZURE_DOCUMENT_INTELLIGENCE_KEY'))
    return timetable_agent_system

def get_quiz_generator():
    """Get or initialize the Quiz Generator"""
    global quiz_generator
    if (quiz_generator is None):
        quiz_generator = QuizGenerator(
            openai_endpoint=app.config['AZURE_OPENAI_ENDPOINT'],
            openai_api_key=app.config['AZURE_OPENAI_API_KEY'],
            openai_api_version=app.config['AZURE_OPENAI_API_VERSION'],
            openai_deployment=app.config['AZURE_OPENAI_CHAT_DEPLOYMENT']
        )
    return quiz_generator

# Helper function to check if a file has an allowed extension
def allowed_file(filename):
    return ('.' in filename) and (filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS'])

# Helper function to get or create a session ID
def get_session_id():
    if ('session_id' not in session):
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def process_base64_file(base64_data, file_type, file_name):
    """
    Process a base64-encoded file and extract its content

    Args:
        base64_data: Base64-encoded file content
        file_type: MIME type of the file
        file_name: Name of the file

    Returns:
        Extracted text from the file or a message if extraction is not possible
    """
    try:
        # Remove the data URI prefix if present
        if base64_data.startswith('data:'):
            # Extract the base64 part after the comma
            base64_data = base64_data.split(',', 1)[1]

        # Decode the base64 data
        file_data = base64.b64decode(base64_data)

        # For PDFs, use our existing PDF extraction functionality
        if file_type == 'application/pdf' or file_name.lower().endswith('.pdf'):
            # We need to write the PDF to a temporary file to use pdfplumber
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(file_data)
                temp_path = temp_file.name

            # Extract text from the PDF
            text_content = extract_text_from_pdf(temp_path)

            # Remove the temporary file
            os.unlink(temp_path)

            # If we got text content, return it
            if text_content and not text_content.startswith("Error"):
                return f"Content extracted from PDF '{file_name}':\n\n{text_content}"
            else:
                return f"The PDF file '{file_name}' could not be processed properly. Please provide specific questions about it."

        # For text files
        elif file_type.startswith('text/'):
            return file_data.decode('utf-8', errors='replace')

        # For other file types
        else:
            return f"The file '{file_name}' of type '{file_type}' was uploaded but cannot be processed directly. Please provide specific questions about it."

    except Exception as e:
        logger.error(f"Error processing file {file_name}: {str(e)}")
        return f"Error processing file {file_name}: {str(e)}"

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

        # Check for uploaded file content (temporary, in-memory context)
        file_data = request.json.get('file')
        file_context = ""

        if file_data and isinstance(file_data, dict):
            file_name = file_data.get('name', 'uploaded file')
            file_content = file_data.get('content', '')
            file_type = file_data.get('type', '')

            # Process file content if available
            if file_content:
                # Use our helper function to process the file and extract its contents
                file_context = process_base64_file(file_content, file_type, file_name)
                logger.info(f"Processed file {file_name} of type {file_type}")

            # Append to the user message for context
            user_message += f"\n\nI've uploaded a file named '{file_name}' for context. Please consider it when responding."

        # Retrieve memory journal entries for context
        mongo_client = get_mongodb_client()
        user_journal_entries = mongo_client.get_user_journal_entries(session_id)
        user_memory_context = JournalExtractor.get_memory_context(user_journal_entries)

        # Retrieve all subject journal entries for additional context
        subject_journal_entries = mongo_client.get_all_subject_journal_entries(session_id)
        subject_memory_context = JournalExtractor.get_memory_context(subject_journal_entries, max_entries=10)

        # Combine all contexts
        combined_context = ""

        # Add file context first if available with strong emphasis
        if file_context:
            combined_context += "### UPLOADED FILE CONTEXT - IMPORTANT ###\n" + file_context + "\n\n"

        # Add memory contexts
        if user_memory_context:
            combined_context += "User's General Memory:\n" + user_memory_context + "\n\n"
        if subject_memory_context:
            combined_context += "User's Subject-Specific Memory:\n" + subject_memory_context

        # Call Azure OpenAI API with combined memory context
        response = call_azure_openai(user_message, combined_context, is_subject_chat=False, has_file_context=(file_context != ""))

        # Extract and save important information from the user's message
        extracted_info = JournalExtractor.extract_important_information(user_message)
        if extracted_info:
            # Extract unique content to avoid duplication
            unique_contents = set()
            for info in extracted_info:
                unique_contents.add(info['content'])

            # Only save if we have content
            if unique_contents:
                # Combine unique content into a single journal entry
                combined_content = "\n".join(unique_contents)
                entry_data = JournalExtractor.prepare_journal_entry(combined_content, session_id)
                mongo_client.add_user_journal_entry(entry_data)

        return jsonify({"response": response})
    except Exception as e:
        logger.error(f"Error in general chat: {str(e)}")
        return jsonify({"error": "An error occurred processing your request"}), 500

def call_azure_openai(user_message, context=None, is_subject_chat=False, has_file_context=False):
    """Call Azure OpenAI API with user message and optional context"""
    try:
        endpoint = app.config['AZURE_OPENAI_ENDPOINT']
        api_key = app.config['AZURE_OPENAI_API_KEY']
        api_version = app.config['AZURE_OPENAI_API_VERSION']
        deployment = app.config['AZURE_OPENAI_CHAT_DEPLOYMENT']
        # Build API URL
        url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
        # Prepare the request payload
        messages = [{'role': 'user', 'content': user_message}]
        # Add context if provided
        if context:
            system_role = 'You are a helpful AI assistant for students.'

            # Enhance system message for file context
            if has_file_context:
                system_role = 'You are a helpful AI assistant for students. You have been provided with a document for context. ' + \
                             'Pay close attention to the UPLOADED FILE CONTEXT section and use this information to provide a detailed and relevant response. ' + \
                             'If the document format makes it hard to interpret, acknowledge that and ask clarifying questions if needed.'

            # Add journal functionality information to the system message
            if is_subject_chat:
                system_role = 'You are a knowledgeable AI assistant for students. ' + \
                              'You have been provided with information from documents related to this subject. ' + \
                              'IMPORTANT: Thoroughly examine the DOCUMENT INFORMATION section below and use that content to provide detailed answers. ' + \
                              'Try your best to answer based on what is provided in the document information. ' + \
                              'Use your own knowledge to enhance your answers, but prioritize the provided document information. ' + \
                              'Only say you don\'t have information if the answer is completely absent from both the document context and your knowledge.'

                system_role += " I have the ability to remember important information you share with me. When you need me to remember something specific about this subject, please clearly state it with phrases like 'remember that...', 'note that...', or 'this is important:'. This information will be saved in your subject journal for future reference."
            else:
                system_role += ' Use the following information from previous conversations to provide personalized assistance.'
                system_role += " IMPORTANT: I have the ability to remember important information you share with me. When you need me to remember something specific, please clearly state it with phrases like 'remember that...', 'note that...', or 'this is important:'. This information will be saved in your journal for future reference."

            system_message = {'role': 'system', 'content': system_role}
            messages.insert(0, system_message)

            # Add context message with better formatting
            if has_file_context:
                # Place higher emphasis on file context by making it a separate message
                context_parts = context.split("### UPLOADED FILE CONTEXT - IMPORTANT ###")
                if len(context_parts) > 1:
                    file_context = context_parts[1].split("\n\n")[0].strip()
                    other_context = context_parts[0] + "\n\n" + "\n\n".join(context_parts[1].split("\n\n")[1:])

                    # Add file context as a separate system message
                    file_context_message = {'role': 'system', 'content': f"UPLOADED FILE CONTEXT:\n{file_context}"}
                    messages.insert(1, file_context_message)

                    # Add other context if it exists
                    if other_context.strip():
                        other_context_message = {'role': 'system', 'content': f'Additional context information:\n{other_context}'}
                        messages.insert(2, other_context_message)
                else:
                    # Fallback if splitting didn't work as expected
                    context_message = {'role': 'system', 'content': f'Context information:\n{context}'}
                    messages.insert(1, context_message)
            elif is_subject_chat and "### DOCUMENT INFORMATION ###" in context:
                # For subject chat, split document and conversation information for better context handling
                context_parts = context.split("### DOCUMENT INFORMATION ###")
                if len(context_parts) > 1:
                    doc_start = context_parts[1].find("\n") + 1  # Skip the header line
                    doc_context = context_parts[1][doc_start:].strip()

                    if "### PREVIOUS CONVERSATION INFORMATION ###" in doc_context:
                        doc_parts = doc_context.split("### PREVIOUS CONVERSATION INFORMATION ###")
                        doc_context = doc_parts[0].strip()
                        conv_context = doc_parts[1].strip()

                        # Add document context as a separate assistant message for better visibility
                        doc_context_message = {'role': 'assistant', 'content': f"DOCUMENT INFORMATION:\n{doc_context}"}
                        messages.insert(1, doc_context_message)

                        # Add conversation context if it exists
                        if conv_context:
                            conv_context_message = {'role': 'system', 'content': f'PREVIOUS CONVERSATION INFORMATION:\n{conv_context}'}
                            messages.insert(2, conv_context_message)
                    else:
                        # Only document context exists
                        doc_context_message = {'role': 'assistant', 'content': f"DOCUMENT INFORMATION:\n{doc_context}"}
                        messages.insert(1, doc_context_message)
                else:
                    # Fallback if splitting didn't work as expected
                    context_message = {'role': 'system', 'content': f'Context information:\n{context}'}
                    messages.insert(1, context_message)
            else:
                # Normal context handling
                context_message = {'role': 'system', 'content': f'Context information:\n{context}'}
                messages.insert(1, context_message)
        else:
            # Even without context, add information about journal functionality
            system_role = 'You are a helpful AI assistant for students.'
            if is_subject_chat:
                system_role += " IMPORTANT: I have the ability to remember important information you share with me. When you need me to remember something specific about this subject, please clearly state it with phrases like 'remember that...', 'note that...', or 'this is important:'. This information will be saved in your subject journal for future reference."
            else:
                system_role += " IMPORTANT: I have the ability to remember important information you share with me. When you need me to remember something specific, please clearly state it with phrases like 'remember that...', 'note that...', or 'this is important:'. This information will be saved in your journal for future reference."

            system_message = {'role': 'system', 'content': system_role}
            messages.insert(0, system_message)

        # Increase max tokens when file context is present to allow for longer responses
        max_tokens = 1000 if has_file_context else 800

        # For subject chat with document information, increase token limit for more comprehensive answers
        if is_subject_chat and context and "### DOCUMENT INFORMATION ###" in context:
            max_tokens = 1200

        payload = {
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': 0.7,
            'top_p': 0.95,
            'stream': False
        }

        # Send request to Azure OpenAI
        headers = {'Content-Type': 'application/json', 'api-key': api_key}
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
    subject_data = {'name': subject_name, 'session_id': session_id}
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
    if (subject is None):
        flash('Subject not found', 'error')
        return redirect(url_for('subjects_list'))
    # Get document metadata from MongoDB
    documents = mongo_client.get_subject_documents(subject_id)
    subject['documents'] = documents
    return render_template('subject_detail.html', subject=subject)

@app.route('/subjects/<subject_id>/upload', methods=['POST'])
def upload_document(subject_id):
    """Upload one or more documents for a specific subject"""
    session_id = get_session_id()
    # Get subject from MongoDB
    mongo_client = get_mongodb_client()
    subject = mongo_client.get_subject(subject_id)
    if (subject is None):
        return jsonify({'error': 'Subject not found'}), 404

    # Check if files were uploaded - support both single and multiple uploads
    if ('document' not in request.files and 'documents' not in request.files):
        return jsonify({'error': 'No document part in the request'}), 400

    # Handle multiple file uploads
    if 'documents' in request.files:
        files = request.files.getlist('documents')
        if not files or len(files) == 0 or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
    # Handle single file upload (backward compatibility)
    else:
        files = [request.files['document']]
        if files[0].filename == '':
            return jsonify({'error': 'No file selected'}), 400

    # Process all uploaded files
    uploaded_documents = []
    for file in files:
        # Check if the file extension is allowed
        if (not allowed_file(file.filename)):
            continue  # Skip this file but continue processing others

        # Secure the filename and generate a unique filename
        filename = secure_filename(file.filename)
        unique_filename = f'{subject_id}_{str(uuid.uuid4())}_{filename}'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        try:
            # Save the file
            file.save(file_path)
            # Add document metadata to MongoDB
            document_data = {'filename': filename, 'storage_path': unique_filename, 'subject_id': subject_id, 'session_id': session_id, 'size': os.path.getsize(file_path)}
            document_id = mongo_client.add_document_metadata(document_data)
            if document_id:
                document_data['_id'] = document_id

            uploaded_documents.append(document_data)

            # Process and index the document in Azure AI Search if available
            if app.config.get('AZURE_SEARCH_ENDPOINT') and app.config.get('AZURE_SEARCH_API_KEY'):
                try:
                    # Prepare the document for indexing
                    documents = prepare_document_for_indexing(doc_info=document_data, subject_name=subject['name'], file_path=file_path)
                    # Upload to Azure AI Search
                    if documents:
                        search_client = get_search_client()
                        uploaded = search_client.upload_documents(documents)
                        logger.info(f"Indexed {uploaded} document chunks for '{filename}'")
                except Exception as e:
                    logger.error(f"Error indexing document: {str(e)}")
                    # Continue without failing if indexing fails
        except Exception as e:
            logger.error(f"Error uploading document {filename}: {str(e)}")
            # Continue with other files

    if not uploaded_documents:
        return jsonify({'error': 'No valid documents were uploaded'}), 400

    # Return success with array of document data
    if len(uploaded_documents) == 1:
        return jsonify({'success': True, 'message': 'Document uploaded successfully', 'document': uploaded_documents[0]})
    else:
        return jsonify({'success': True, 'message': f'{len(uploaded_documents)} documents uploaded successfully', 'documents': uploaded_documents})

@app.route("/api/motivational")
def api_reading():
    message = "Please Generate a motivational quote depending on the users mode. Send only the quote in double quotation and the guy who said it afterwards -" \
    "+ dont add the following quotes and get new things" + str(get_values())
    response = call_azure_openai(message)
    x = motivational(response)
    return jsonify(value=x)

@app.route('/api/subjects/<subject_id>/chat', methods=['POST'])
def subject_chat(subject_id):
    """API endpoint for subject-specific chat functionality"""
    try:
        session_id = get_session_id()
        # Verify subject exists in MongoDB
        mongo_client = get_mongodb_client()
        subject = mongo_client.get_subject(subject_id)
        if (subject is None):
            return jsonify({'error': 'Subject not found'}), 404
        user_message = request.json.get('message', '')
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        # Use Azure AI Search to retrieve relevant document chunks as context
        document_context = retrieve_document_context(subject_id, user_message)
        # Retrieve subject journal entries for additional context
        journal_entries = mongo_client.get_subject_journal_entries(session_id, subject_id)
        journal_context = JournalExtractor.get_memory_context(journal_entries)
        # Combine document and journal context with better formatting
        combined_context = ''
        if document_context:
            combined_context += '### DOCUMENT INFORMATION ###\n' + document_context + '\n\n'
        if journal_context:
            combined_context += '### PREVIOUS CONVERSATION INFORMATION ###\n' + journal_context + '\n\n'
        # Add a instruction if both contexts are present
        if document_context and journal_context:
            combined_context += 'Please use both document information and previous conversation context to provide a comprehensive answer.\n\n'
        # Add a title for empty context
        elif (not combined_context):
            combined_context = 'No relevant information found.'
        # Call Azure OpenAI with the combined context
        response = call_azure_openai(user_message, combined_context, is_subject_chat=True)

        # Extract and save important information from user's message only
        extracted_info = JournalExtractor.extract_important_information(user_message)
        if extracted_info:
            # Extract unique content to avoid duplication
            unique_contents = set()
            for info in extracted_info:
                unique_contents.add(info['content'])

            # Only save if we have content
            if unique_contents:
                # Combine unique content into a single journal entry
                combined_content = "\n".join(unique_contents)
                entry_data = JournalExtractor.prepare_journal_entry(combined_content, session_id, subject_id)
                mongo_client.add_subject_journal_entry(entry_data)

        return jsonify({'response': response})
    except Exception as e:
        logger.error(f"Error in subject chat: {str(e)}")
        return jsonify({'error': 'An error occurred processing your request'}), 500

def retrieve_document_context(subject_id, query):
    """
    Retrieve relevant document content from Azure AI Search based on the query
    If Azure AI Search is not available, fall back to direct document extraction
    """
    try:
        # Log the incoming query for debugging
        logger.info(f"Searching for documents with query: '{query}' in subject_id: '{subject_id}'")

        if not query or query.strip() == "":
            logger.warning("Empty query provided to retrieve_document_context")
            return "No document context available - search query was empty."

        # Extract key terms from the query to improve search
        search_query = query
        if len(query) > 100:  # If query is long, extract key terms
            search_query = extract_search_terms(query)
            logger.info(f"Original query was long. Using extracted search terms: '{search_query}'")

        # Check if we have Azure Search credentials
        if app.config.get('AZURE_SEARCH_ENDPOINT') and app.config.get('AZURE_SEARCH_API_KEY'):
            search_client = get_search_client()

            # First try to use Azure AI Search
            if search_client.is_available:
                context = get_relevant_context(search_client, search_query, subject_id)
                # If we got a meaningful context, return it
                if context and not context.startswith("Error") and not context.startswith("Azure AI Search is not available"):
                    return context
                # Otherwise, log the issue and continue to fallback
                logger.warning(f"Azure AI Search retrieval failed for query: '{search_query}', falling back to direct document extraction")

        # Fall back to direct document extraction (either Azure Search is unavailable or failed)
        mongo_client = get_mongodb_client()
        documents = mongo_client.get_subject_documents(subject_id)

        if not documents:
            return 'No documents available for this subject yet.'

        # Prepare a more comprehensive context from available documents
        context_parts = []

        # Try to get content from multiple documents (up to 3)
        for idx, doc in enumerate(documents[:3]):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], doc['storage_path'])
            if os.path.exists(file_path):
                text = extract_document_text(file_path)
                if text:
                    # Extract a reasonable sample from the document (first 1000 characters)
                    sample = ((text[:1000] + '...') if (len(text) > 1000) else text)
                    context_parts.append(f"Document: {doc['filename']}\n\n{sample}")

                    # If we've already got a decent amount of content, stop here
                    if len('\n\n---\n\n'.join(context_parts)) > 3000:
                        break

        if context_parts:
            logger.info(f"Falling back to direct document extraction. Found {len(context_parts)} documents.")
            return '\n\n---\n\n'.join(context_parts)
        else:
            return 'Document content could not be retrieved. Please check that the uploaded documents are in a supported format.'

    except Exception as e:
        logger.error(f"Error retrieving document context: {str(e)}")
        return f"Error retrieving document context: {str(e)}"

def extract_search_terms(query, max_terms=5):
    """
    Extract key search terms from a long query to improve search results
    """
    try:
        # Remove common words and keep nouns and key terms
        words = query.lower().split()
        # Common English stop words to filter out
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
                      'be', 'been', 'being', 'to', 'of', 'for', 'with', 'about', 'against',
                      'between', 'into', 'through', 'during', 'before', 'after', 'above',
                      'below', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over',
                      'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
                      'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
                      'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
                      'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should',
                      'now', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those'}

        # Keep words that are not stop words and are at least 3 characters long
        filtered_words = [word for word in words if word not in stop_words and len(word) >= 3]

        # Get the most frequent terms (excluding very common words)
        from collections import Counter
        word_counts = Counter(filtered_words)
        top_terms = [word for word, count in word_counts.most_common(max_terms)]

        # Join the top terms back into a search query
        if top_terms:
            return ' '.join(top_terms)
        else:
            # If no good terms found, return the original query
            return query
    except Exception as e:
        logger.error(f"Error extracting search terms: {str(e)}")
        return query

# Timetable Generator Routes
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
    """API endpoint for extracting topics from subject documents (Agent 1)"""
    try:
        session_id = get_session_id()
        subject_id = request.json.get('subject_id')
        scope = request.json.get('scope', 'all topics')
        if not subject_id:
            return jsonify({"error": "Subject ID is required"}), 400
        # Get subject from MongoDB
        mongo_client = get_mongodb_client()
        subject = mongo_client.get_subject(subject_id)
        if (subject is None):
            return jsonify({"error": "Subject not found"}), 404
        # Get document metadata from MongoDB
        documents = mongo_client.get_subject_documents(subject_id)
        if (not documents):
            return jsonify({"error": "No documents found for this subject"}), 404
        # Initialize timetable agent system
        timetable_system = get_timetable_agent_system()
        # Extract topics from documents using Agent 1
        extraction_results = timetable_system.extract_topics_from_documents(documents=documents, upload_folder=app.config['UPLOAD_FOLDER'], scope=scope)
        return jsonify({'success': True, 'subject': subject, 'extraction_results': extraction_results})
    except Exception as e:
        logger.error(f"Error extracting topics: {str(e)}")
        return jsonify({'error': f"Error extracting topics: {str(e)}"}), 500

@app.route('/api/timetable/generate', methods=['POST'])
def generate_timetable():
    """API endpoint for generating a study timetable using the multi-agent workflow"""
    try:
        session_id = get_session_id()
        subject_id = request.json.get('subject_id')
        extracted_topics = request.json.get('extracted_topics')
        timeframe = request.json.get('timeframe')
        if (not subject_id) or (not extracted_topics) or (not timeframe):
            return jsonify({"error": "Subject ID, extracted topics, and timeframe are required"}), 400
        # Get subject from MongoDB
        mongo_client = get_mongodb_client()
        subject = mongo_client.get_subject(subject_id)
        if (subject is None):
            return jsonify({"error": "Subject not found"}), 404
        # Get user's journal entries for Agent 3
        user_journal_entries = mongo_client.get_user_journal_entries(session_id, limit=30)
        # Initialize timetable agent system
        timetable_system = get_timetable_agent_system()
        # Generate timetable using the multi-agent workflow
        timetable_results = timetable_system.generate_timetable(extracted_topics=extracted_topics, journal_entries=user_journal_entries, timeframe=timeframe)
        return jsonify({'success': True, 'subject': subject, 'timetable_results': timetable_results})
    except Exception as e:
        logger.error(f"Error generating timetable: {str(e)}")
        return jsonify({'error': f"Error generating timetable: {str(e)}"}), 500

@app.route('/api/timetable/download', methods=['POST'])
def download_timetable():
    """API endpoint for downloading timetable as iCalendar (.ics) file"""
    try:
        timetable_data = request.json.get('timetable_data')
        subject = request.json.get('subject', {})
        if not timetable_data:
            return jsonify({"error": "Timetable data is required"}), 400
        # Initialize timetable agent system
        timetable_system = get_timetable_agent_system()
        # Generate iCalendar file
        ics_data = timetable_system.generate_ics_calendar(timetable_data)
        # Create in-memory file
        ics_file = io.BytesIO(ics_data)
        # Prepare the filename
        subject_name = subject.get('name', 'Study')
        safe_subject_name = ''.join((c for c in subject_name if (c.isalnum() or (c in [' ', '_', '-'])))).strip()
        safe_subject_name = safe_subject_name.replace(' ', '_')
        date_str = datetime.datetime.now().strftime('%Y%m%d')
        filename = f'{safe_subject_name}_Timetable_{date_str}.ics'
        # Send the file
        return Response(ics_file.getvalue(), mimetype='text/calendar', headers={'Content-Disposition': f'attachment; filename="{filename}"', 'Content-Type': 'text/calendar; charset=utf-8'})
    except Exception as e:
        logger.error(f"Error downloading timetable: {str(e)}")
        return jsonify({'error': f"Error downloading timetable: {str(e)}"}), 500

# Research Assistant Routes
@app.route('/research-assistant/')
def research_assistant():
    """Render the research assistant page with literature review functionality"""
    return render_template('research_assistant.html')

@app.route('/api/research-assistant/generate', methods=['POST'])
def generate_literature_review():
    """API endpoint for generating a literature review using the run_lit_review function"""
    try:
        # Get the query from the request
        query = request.json.get('query', '')
        if not query:
            return jsonify({"error": "No query provided"}), 400

        # Call the run_lit_review function to generate the literature review
        logger.info(f"Generating literature review for query: {query}")
        report_path = run_lit_review(query)

        # Check if the report was generated successfully
        if not report_path or not os.path.exists(report_path):
            return jsonify({"error": "Failed to generate literature review report"}), 500

        # Read the report content
        with open(report_path, 'r') as f:
            report_content = f.read()

        return jsonify({"success": True, "report": report_content})
    except Exception as e:
        logger.error(f"Error generating literature review: {str(e)}")
        return jsonify({"error": f"Error generating literature review: {str(e)}"}), 500

# Quiz Generation Routes
@app.route('/quiz')
def quiz():
    """Render the quiz generation page with subject selection"""
    session_id = get_session_id()
    # Get subjects from MongoDB to populate the subject dropdown
    mongo_client = get_mongodb_client()
    subjects = mongo_client.get_subjects(session_id)
    # Fetch documents for each subject to display accurate document counts
    for subject in subjects:
        documents = mongo_client.get_subject_documents(subject['_id'])
        subject['documents'] = documents
    return render_template('quiz.html', subjects=subjects)

@app.route('/api/quiz/generate', methods=['POST'])
def generate_quiz():
    """API endpoint for generating a quiz based on subject documents and topic"""
    try:
        session_id = get_session_id()
        subject_id = request.json.get('subject_id')
        topic = request.json.get('topic')

        if not subject_id or not topic:
            return jsonify({"error": "Subject ID and topic are required"}), 400

        # Get subject from MongoDB
        mongo_client = get_mongodb_client()
        subject = mongo_client.get_subject(subject_id)
        if subject is None:
            return jsonify({"error": "Subject not found"}), 404

        # Get document metadata from MongoDB
        documents = mongo_client.get_subject_documents(subject_id)
        if not documents:
            return jsonify({"error": "No documents found for this subject"}), 404

        # Initialize quiz generator
        quiz_gen = get_quiz_generator()

        # Update the documents to include the upload folder path
        for doc in documents:
            # Store the upload folder temporarily for document content extraction
            doc['_upload_folder'] = app.config['UPLOAD_FOLDER']

        # Generate the quiz
        quiz_questions = quiz_gen.generate_quiz(
            documents=documents,
            topic=topic,
            num_questions=5,  # Default to 5 questions
            options_per_question=4  # Default to 4 options per question
        )

        if not quiz_questions:
            return jsonify({"error": "Failed to generate quiz questions. Please try a different topic or subject with more document content."}), 500

        # Store the generated quiz in the session for scoring later
        session['current_quiz'] = quiz_questions

        return jsonify({"success": True, "quiz": quiz_questions})

    except Exception as e:
        logger.error(f"Error generating quiz: {str(e)}")
        return jsonify({"error": f"Error generating quiz: {str(e)}"}), 500

@app.route('/api/quiz/submit', methods=['POST'])
def submit_quiz():
    """API endpoint for scoring a submitted quiz"""
    try:
        user_answers = request.json.get('user_answers')
        quiz_data = request.json.get('quiz_data')

        if not user_answers or not quiz_data:
            return jsonify({"error": "User answers and quiz data are required"}), 400

        # Initialize quiz generator
        quiz_gen = get_quiz_generator()

        # Score the quiz
        scoring_results = quiz_gen.score_quiz(user_answers, quiz_data)

        return jsonify({
            "success": True,
            "score": scoring_results['score'],
            "total": scoring_results['total'],
            "results": scoring_results['results']
        })

    except Exception as e:
        logger.error(f"Error scoring quiz: {str(e)}")
        return jsonify({"error": f"Error scoring quiz: {str(e)}"}), 500

@app.route('/api/subjects/<subject_id>/documents/<document_id>/delete', methods=['DELETE'])
def delete_document(subject_id, document_id):
    """API endpoint to delete a document and its metadata from MongoDB and storage"""
    try:
        session_id = get_session_id()

        # Get MongoDB client
        mongo_client = get_mongodb_client()

        # Check if subject exists
        subject = mongo_client.get_subject(subject_id)
        if subject is None:
            return jsonify({'error': 'Subject not found'}), 404

        # Get document metadata from MongoDB
        document = mongo_client.get_document(document_id)
        if document is None:
            return jsonify({'error': 'Document not found'}), 404

        # Verify that the document belongs to the specified subject
        if document.get('subject_id') != subject_id:
            return jsonify({'error': 'Document does not belong to the specified subject'}), 403

        # Get the file path from metadata
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], document.get('storage_path', ''))

        # Delete the actual document file from storage
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted document file: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting document file {file_path}: {str(e)}")
                return jsonify({'error': f"Error deleting document file: {str(e)}"}), 500
        else:
            logger.warning(f"Document file not found: {file_path}")

        # Delete document metadata from MongoDB
        deleted = mongo_client.delete_document_metadata(document_id)
        if not deleted:
            return jsonify({'error': 'Failed to delete document metadata'}), 500

        # If we have Azure Search configured, try to remove the document from the search index
        if app.config.get('AZURE_SEARCH_ENDPOINT') and app.config.get('AZURE_SEARCH_API_KEY'):
            try:
                search_client = get_search_client()
                if search_client.is_available:
                    # Delete by document ID filter - Note: This assumes a consistent ID format in the search index
                    filter_expression = f"metadata_storage_name eq '{document.get('storage_path')}'"
                    search_client.delete_documents_by_filter(filter_expression)
                    logger.info(f"Removed document from search index: {document.get('filename')}")
            except Exception as e:
                # Log the error but don't fail the entire operation if search index deletion fails
                logger.error(f"Error removing document from search index: {str(e)}")

        return jsonify({
            'success': True,
            'message': f"Document '{document.get('filename')}' deleted successfully"
        })

    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        return jsonify({'error': f"Error deleting document: {str(e)}"}), 500

# Clean up resources when app is shutting down
@app.teardown_appcontext
def close_connections(exception=None):
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()

if (__name__ == '__main__'):
    app.run(debug=app.config['DEBUG'])
