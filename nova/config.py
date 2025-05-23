import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# General application configuration
# Set DEBUG mode based on FLASK_ENV. Defaults to False (production) if FLASK_ENV is not 'development'.
DEBUG = os.getenv('FLASK_ENV') == 'development'
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01')
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT', 'gpt-35-turbo')

# Azure AI Search configuration
AZURE_SEARCH_ENDPOINT = os.getenv('AZURE_SEARCH_ENDPOINT')
AZURE_SEARCH_API_KEY = os.getenv('AZURE_SEARCH_API_KEY')
AZURE_SEARCH_INDEX_NAME = os.getenv('AZURE_SEARCH_INDEX_NAME', 'student-documents')

# Azure Document Intelligence configuration
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
AZURE_DOCUMENT_INTELLIGENCE_KEY = os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')

# MongoDB Atlas configuration
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'student_ai_assistant')
MONGODB_SUBJECTS_COLLECTION = os.getenv('MONGODB_SUBJECTS_COLLECTION', 'subjects')
MONGODB_DOCUMENTS_COLLECTION = os.getenv('MONGODB_DOCUMENTS_COLLECTION', 'documents')
MONGODB_USER_JOURNALS_COLLECTION = os.getenv('MONGODB_USER_JOURNALS_COLLECTION', 'user_journals')
MONGODB_SUBJECT_JOURNALS_COLLECTION = os.getenv('MONGODB_SUBJECT_JOURNALS_COLLECTION', 'subject_journals')

# File upload configuration
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB max upload size
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'subject_documents'))
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'md'}