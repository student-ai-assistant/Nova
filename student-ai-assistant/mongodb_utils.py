"""
mongodb_utils.py - MongoDB Atlas integration module for the Student AI Assistant
"""

import logging
import datetime
from typing import Dict, List, Any, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, PyMongoError
from bson.objectid import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBClient:
    """Client for MongoDB Atlas operations"""

    def __init__(self, uri: str, db_name: str):
        """
        Initialize MongoDB client

        Args:
            uri: MongoDB connection URI
            db_name: Database name
        """
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self.connected = False

    def connect(self) -> bool:
        """
        Connect to MongoDB Atlas

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            if not self.uri:
                logger.error("MongoDB URI is not provided")
                return False

            self.client = MongoClient(self.uri)

            # Verify connection
            self.client.admin.command('ping')

            # Access database
            self.db = self.client[self.db_name]
            self.connected = True

            logger.info(f"Connected to MongoDB Atlas: {self.db_name}")
            return True

        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {str(e)}")
            self.connected = False
            return False

    def get_collection(self, collection_name: str) -> Optional[Collection]:
        """
        Get a MongoDB collection

        Args:
            collection_name: Name of the collection

        Returns:
            MongoDB collection or None if not connected
        """
        if not self.connected:
            if not self.connect():
                return None

        return self.db[collection_name]

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("Closed MongoDB connection")

    # User operations

    def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new user

        Args:
            user_data: Dictionary containing user information (username, password_hash, email)

        Returns:
            ID of the inserted user or None if operation fails
        """
        try:
            collection = self.get_collection('users')
            if collection is None:
                return None

            # Add creation timestamp
            user_data['created_at'] = datetime.datetime.utcnow()

            result = collection.insert_one(user_data)
            user_id = str(result.inserted_id)

            logger.info(f"Created user: {user_id}")
            return user_id

        except PyMongoError as e:
            logger.error(f"Failed to create user: {str(e)}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by username

        Args:
            username: Username to look up

        Returns:
            User dictionary or None if not found
        """
        try:
            collection = self.get_collection('users')
            if collection is None:
                return None

            user = collection.find_one({'username': username})

            if user:
                user['_id'] = str(user['_id'])

            return user

        except PyMongoError as e:
            logger.error(f"Failed to get user by username {username}: {str(e)}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user by ID

        Args:
            user_id: User ID

        Returns:
            User dictionary or None if not found
        """
        try:
            collection = self.get_collection('users')
            if collection is None:
                return None

            user = collection.find_one({'_id': ObjectId(user_id)})

            if user:
                user['_id'] = str(user['_id'])

            return user

        except PyMongoError as e:
            logger.error(f"Failed to get user {user_id}: {str(e)}")
            return None

    def username_exists(self, username: str) -> bool:
        """
        Check if a username already exists

        Args:
            username: Username to check

        Returns:
            True if username exists, False otherwise
        """
        try:
            collection = self.get_collection('users')
            if collection is None:
                return False

            return collection.count_documents({'username': username}) > 0

        except PyMongoError as e:
            logger.error(f"Failed to check if username exists: {str(e)}")
            return False

    # Subject operations

    def create_subject(self, subject_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new subject

        Args:
            subject_data: Dictionary containing subject information

        Returns:
            ID of the inserted subject or None if operation fails
        """
        try:
            collection = self.get_collection('subjects')
            if collection is None:
                return None

            # Add creation timestamp
            subject_data['created_at'] = datetime.datetime.utcnow()

            result = collection.insert_one(subject_data)
            subject_id = str(result.inserted_id)

            logger.info(f"Created subject: {subject_id}")
            return subject_id

        except PyMongoError as e:
            logger.error(f"Failed to create subject: {str(e)}")
            return None

    def get_subjects(self, session_id: str = None, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all subjects, filtered by session ID or user ID

        Args:
            session_id: Optional session ID to filter by
            user_id: Optional user ID to filter by

        Returns:
            List of subject dictionaries
        """
        try:
            collection = self.get_collection('subjects')
            if collection is None:
                return []

            # Build query based on available IDs, prioritizing user_id if available
            if user_id:
                query = {'user_id': user_id}
            elif session_id:
                query = {'session_id': session_id}
            else:
                query = {}

            # Get subjects and convert ObjectId to string
            subjects = list(collection.find(query))

            for subject in subjects:
                subject['_id'] = str(subject['_id'])

            return subjects

        except PyMongoError as e:
            logger.error(f"Failed to get subjects: {str(e)}")
            return []

    def get_subject(self, subject_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Get a specific subject by ID, optionally checking if it belongs to a specific user

        Args:
            subject_id: Subject ID
            user_id: Optional user ID to verify ownership

        Returns:
            Subject dictionary or None if not found or not owned by specified user
        """
        try:
            collection = self.get_collection('subjects')
            if collection is None:
                return None

            # Build query based on whether we need to check user ownership
            query = {'_id': ObjectId(subject_id)}
            if user_id:
                query['user_id'] = user_id

            subject = collection.find_one(query)

            if subject:
                subject['_id'] = str(subject['_id'])

            return subject

        except PyMongoError as e:
            logger.error(f"Failed to get subject {subject_id}: {str(e)}")
            return None

    # Document metadata operations

    def add_document_metadata(self, document_data: Dict[str, Any]) -> Optional[str]:
        """
        Add metadata for an uploaded document

        Args:
            document_data: Dictionary containing document metadata

        Returns:
            ID of the inserted document metadata or None if operation fails
        """
        try:
            collection = self.get_collection('documents')
            if collection is None:
                return None

            # Add upload timestamp
            document_data['uploaded_at'] = datetime.datetime.utcnow()

            result = collection.insert_one(document_data)
            document_id = str(result.inserted_id)

            logger.info(f"Added document metadata: {document_id}")
            return document_id

        except PyMongoError as e:
            logger.error(f"Failed to add document metadata: {str(e)}")
            return None

    def get_subject_documents(self, subject_id: str, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Get documents for a specific subject, optionally filtered by user ID

        Args:
            subject_id: Subject ID
            user_id: Optional user ID to filter by

        Returns:
            List of document metadata dictionaries
        """
        try:
            collection = self.get_collection('documents')
            if collection is None:
                return []

            # Build query based on whether user_id is provided
            query = {'subject_id': subject_id}
            if user_id:
                query['user_id'] = user_id

            documents = list(collection.find(query))

            # Convert ObjectId to string
            for doc in documents:
                doc['_id'] = str(doc['_id'])

            return documents

        except PyMongoError as e:
            logger.error(f"Failed to get documents for subject {subject_id}: {str(e)}")
            return []

    def get_document_by_id(self, document_id: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID, optionally verifying user ownership

        Args:
            document_id: Document ID
            user_id: Optional user ID to verify ownership

        Returns:
            Document dictionary or None if not found or not owned by specified user
        """
        try:
            collection = self.get_collection('documents')
            if collection is None:
                return None

            # Build query based on whether we need to check user ownership
            query = {'_id': ObjectId(document_id)}
            if user_id:
                query['user_id'] = user_id

            document = collection.find_one(query)

            if document:
                document['_id'] = str(document['_id'])

            return document

        except PyMongoError as e:
            logger.error(f"Failed to get document {document_id}: {str(e)}")
            return None

    def delete_document(self, document_id: str, user_id: str) -> bool:
        """
        Delete a document by ID with user ownership verification

        Args:
            document_id: Document ID
            user_id: User ID for ownership verification

        Returns:
            True if document was deleted, False otherwise
        """
        try:
            collection = self.get_collection('documents')
            if collection is None:
                return False

            # Always verify user ownership when deleting
            result = collection.delete_one({
                '_id': ObjectId(document_id),
                'user_id': user_id
            })

            if result.deleted_count > 0:
                logger.info(f"Deleted document {document_id}")
                return True
            else:
                logger.warning(f"No document deleted for ID {document_id} - may not exist or belong to user {user_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            return False

    # Journal operations

    def add_user_journal_entry(self, entry_data: Dict[str, Any]) -> Optional[str]:
        """
        Add an entry to the user's journal

        Args:
            entry_data: Dictionary containing the journal entry

        Returns:
            ID of the inserted journal entry or None if operation fails
        """
        try:
            collection = self.get_collection('user_journals')
            if collection is None:
                return None

            # Add timestamp if not present
            if 'timestamp' not in entry_data:
                entry_data['timestamp'] = datetime.datetime.utcnow()

            result = collection.insert_one(entry_data)
            entry_id = str(result.inserted_id)

            logger.info(f"Added user journal entry: {entry_id}")
            return entry_id

        except PyMongoError as e:
            logger.error(f"Failed to add user journal entry: {str(e)}")
            return None

    def add_subject_journal_entry(self, entry_data: Dict[str, Any]) -> Optional[str]:
        """
        Add an entry to a subject journal

        Args:
            entry_data: Dictionary containing the journal entry

        Returns:
            ID of the inserted journal entry or None if operation fails
        """
        try:
            collection = self.get_collection('subject_journals')
            if collection is None:
                return None

            # Add timestamp if not present
            if 'timestamp' not in entry_data:
                entry_data['timestamp'] = datetime.datetime.utcnow()

            result = collection.insert_one(entry_data)
            entry_id = str(result.inserted_id)

            logger.info(f"Added subject journal entry: {entry_id}")
            return entry_id

        except PyMongoError as e:
            logger.error(f"Failed to add subject journal entry: {str(e)}")
            return None

    def get_user_journal_entries(self, session_id: str = None, user_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user journal entries

        Args:
            session_id: Optional session ID (deprecated, kept for backward compatibility)
            user_id: Optional user ID (preferred method for identifying user)
            limit: Maximum number of entries to return (most recent first)

        Returns:
            List of journal entries
        """
        try:
            collection = self.get_collection('user_journals')
            if collection is None:
                return []

            # Build query based on available IDs, prioritizing user_id if available
            if user_id:
                query = {'user_id': user_id}
            elif session_id:
                query = {'session_id': session_id}
            else:
                query = {}

            entries = list(collection.find(query).sort('timestamp', -1).limit(limit))

            # Convert ObjectId to string
            for entry in entries:
                entry['_id'] = str(entry['_id'])

            return entries

        except PyMongoError as e:
            logger.error(f"Failed to get user journal entries: {str(e)}")
            return []

    def get_all_subject_journal_entries(self, session_id: str = None, user_id: str = None, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Get all subject journal entries for a session or user across all subjects

        Args:
            session_id: Optional session ID (deprecated, kept for backward compatibility)
            user_id: Optional user ID (preferred method for identifying user)
            limit: Maximum number of entries to return (most recent first)

        Returns:
            List of journal entries from all subjects
        """
        try:
            collection = self.get_collection('subject_journals')
            if collection is None:
                return []

            # Build query based on available IDs, prioritizing user_id if available
            if user_id:
                query = {'user_id': user_id}
            elif session_id:
                query = {'session_id': session_id}
            else:
                query = {}

            entries = list(collection.find(query).sort('timestamp', -1).limit(limit))

            # Convert ObjectId to string
            for entry in entries:
                entry['_id'] = str(entry['_id'])

            return entries

        except PyMongoError as e:
            logger.error(f"Failed to get all subject journal entries: {str(e)}")
            return []

    def get_subject_journal_entries(self, session_id: str = None, subject_id: str = None, user_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get subject journal entries

        Args:
            session_id: Optional session ID (deprecated, kept for backward compatibility)
            subject_id: Subject ID
            user_id: Optional user ID (preferred method for identifying user)
            limit: Maximum number of entries to return (most recent first)

        Returns:
            List of journal entries
        """
        try:
            collection = self.get_collection('subject_journals')
            if collection is None:
                return []

            # Build query based on available parameters
            query = {}
            if subject_id:
                query['subject_id'] = subject_id

            # Add user identification, prioritizing user_id if available
            if user_id:
                query['user_id'] = user_id
            elif session_id:
                query['session_id'] = session_id

            entries = list(collection.find(query).sort('timestamp', -1).limit(limit))

            # Convert ObjectId to string
            for entry in entries:
                entry['_id'] = str(entry['_id'])

            return entries

        except PyMongoError as e:
            logger.error(f"Failed to get subject journal entries: {str(e)}")
            return []