import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# General application configuration
DEBUG = True
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

# File upload configuration
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'subject_documents'))
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'md'}