"""
mongodb_utils.py - MongoDB Atlas integration module for Nova
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

    def get_subjects(self, session_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all subjects, optionally filtered by session ID

        Args:
            session_id: Optional session ID to filter by

        Returns:
            List of subject dictionaries
        """
        try:
            collection = self.get_collection('subjects')
            if collection is None:
                return []

            query = {'session_id': session_id} if session_id else {}

            # Get subjects and convert ObjectId to string
            subjects = list(collection.find(query))

            for subject in subjects:
                subject['_id'] = str(subject['_id'])

            return subjects

        except PyMongoError as e:
            logger.error(f"Failed to get subjects: {str(e)}")
            return []

    def get_subject(self, subject_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific subject by ID

        Args:
            subject_id: Subject ID

        Returns:
            Subject dictionary or None if not found
        """
        try:
            collection = self.get_collection('subjects')
            if collection is None:
                return None

            subject = collection.find_one({'_id': ObjectId(subject_id)})

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

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID

        Args:
            document_id: Document ID

        Returns:
            Document metadata dictionary or None if not found
        """
        try:
            collection = self.get_collection('documents')
            if collection is None:
                return None

            document = collection.find_one({'_id': ObjectId(document_id)})

            if document:
                document['_id'] = str(document['_id'])

            return document

        except PyMongoError as e:
            logger.error(f"Failed to get document {document_id}: {str(e)}")
            return None

    def delete_document_metadata(self, document_id: str) -> bool:
        """
        Delete document metadata by ID

        Args:
            document_id: Document ID to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            collection = self.get_collection('documents')
            if collection is None:
                return False

            result = collection.delete_one({'_id': ObjectId(document_id)})

            if result.deleted_count == 1:
                logger.info(f"Deleted document metadata: {document_id}")
                return True
            else:
                logger.warning(f"No document found with ID: {document_id}")
                return False

        except PyMongoError as e:
            logger.error(f"Failed to delete document metadata {document_id}: {str(e)}")
            return False

    def get_subject_documents(self, subject_id: str) -> List[Dict[str, Any]]:
        """
        Get documents for a specific subject

        Args:
            subject_id: Subject ID

        Returns:
            List of document metadata dictionaries
        """
        try:
            collection = self.get_collection('documents')
            if collection is None:
                return []

            documents = list(collection.find({'subject_id': subject_id}))

            # Convert ObjectId to string
            for doc in documents:
                doc['_id'] = str(doc['_id'])

            return documents

        except PyMongoError as e:
            logger.error(f"Failed to get documents for subject {subject_id}: {str(e)}")
            return []

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

    def get_user_journal_entries(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user journal entries

        Args:
            session_id: Session ID
            limit: Maximum number of entries to return (most recent first)

        Returns:
            List of journal entries
        """
        try:
            collection = self.get_collection('user_journals')
            if collection is None:
                return []

            entries = list(collection.find(
                {'session_id': session_id}
            ).sort('timestamp', -1).limit(limit))

            # Convert ObjectId to string
            for entry in entries:
                entry['_id'] = str(entry['_id'])

            return entries

        except PyMongoError as e:
            logger.error(f"Failed to get user journal entries: {str(e)}")
            return []

    def get_all_subject_journal_entries(self, session_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Get all subject journal entries for a session across all subjects

        Args:
            session_id: Session ID
            limit: Maximum number of entries to return (most recent first)

        Returns:
            List of journal entries from all subjects
        """
        try:
            collection = self.get_collection('subject_journals')
            if collection is None:
                return []

            entries = list(collection.find({
                'session_id': session_id
            }).sort('timestamp', -1).limit(limit))

            # Convert ObjectId to string
            for entry in entries:
                entry['_id'] = str(entry['_id'])

            return entries

        except PyMongoError as e:
            logger.error(f"Failed to get all subject journal entries: {str(e)}")
            return []

    def get_subject_journal_entries(self, session_id: str, subject_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get subject journal entries

        Args:
            session_id: Session ID
            subject_id: Subject ID
            limit: Maximum number of entries to return (most recent first)

        Returns:
            List of journal entries
        """
        try:
            collection = self.get_collection('subject_journals')
            if collection is None:
                return []

            entries = list(collection.find({
                'session_id': session_id,
                'subject_id': subject_id
            }).sort('timestamp', -1).limit(limit))

            # Convert ObjectId to string
            for entry in entries:
                entry['_id'] = str(entry['_id'])

            return entries

        except PyMongoError as e:
            logger.error(f"Failed to get subject journal entries: {str(e)}")
            return []