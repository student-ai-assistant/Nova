"""
models.py - Database models for the Student AI Assistant
"""

from flask_login import UserMixin
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    """User model implementing Flask-Login's UserMixin"""

    def __init__(self, user_data):
        self.id = str(user_data.get('_id'))
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.password_hash = user_data.get('password_hash')
        # Add any other fields as needed

    def get_id(self):
        """Return the user ID as a string, as required by Flask-Login"""
        return self.id

    @staticmethod
    def get(user_id, mongo_client):
        """Get a user by ID"""
        if not user_id:
            return None

        # Use the proper MongoDB client method
        try:
            user_data = mongo_client.get_user_by_id(user_id)
            if user_data:
                return User(user_data)
        except Exception as e:
            print(f"Error retrieving user: {str(e)}")
        return None

    @staticmethod
    def get_by_username(username, mongo_client):
        """Get a user by username"""
        if not username:
            return None

        # Use the proper MongoDB client method
        user_data = mongo_client.get_user_by_username(username)
        if user_data:
            return User(user_data)
        return None

    @staticmethod
    def create(username, password, email=None, mongo_client=None):
        """Create a new user with a hashed password"""
        if not mongo_client:
            raise ValueError("MongoDB client is required")

        # Check if username already exists using client method
        if mongo_client.username_exists(username):
            return None, "Username already exists"

        # Check if email already exists if provided
        # For now, just check if any user has this email (implement in mongo_client if needed)
        if email:
            # Use get_collection properly to ensure connection is active
            users_collection = mongo_client.get_collection('users')
            if users_collection and users_collection.count_documents({'email': email}) > 0:
                return None, "Email already exists"

        # Create new user document
        user_data = {
            'username': username,
            'password_hash': generate_password_hash(password),
            'email': email
        }

        try:
            # Use the proper MongoDB client method to create user
            user_id = mongo_client.create_user(user_data)
            if user_id:
                user_data['_id'] = user_id
                return User(user_data), None
            else:
                return None, "Failed to create user"
        except Exception as e:
            return None, f"Database error: {str(e)}"

    def verify_password(self, password):
        """Verify the password against the stored hash"""
        return check_password_hash(self.password_hash, password)

    def transfer_session_data(self, session_id, mongo_client):
        """Transfer all data associated with a session ID to this user"""
        if not session_id or not mongo_client:
            return False

        try:
            # Use collections via get_collection to ensure connection is active
            subjects_collection = mongo_client.get_collection('subjects')
            documents_collection = mongo_client.get_collection('documents')
            user_journals_collection = mongo_client.get_collection('user_journals')
            subject_journals_collection = mongo_client.get_collection('subject_journals')

            if subjects_collection:
                # Update all subjects
                subjects_collection.update_many(
                    {'session_id': session_id},
                    {'$set': {'user_id': self.id, 'session_id': None}}
                )

            if documents_collection:
                # Update all document metadata
                documents_collection.update_many(
                    {'session_id': session_id},
                    {'$set': {'user_id': self.id, 'session_id': None}}
                )

            if user_journals_collection:
                # Update user journal entries
                user_journals_collection.update_many(
                    {'session_id': session_id},
                    {'$set': {'user_id': self.id, 'session_id': None}}
                )

            if subject_journals_collection:
                # Update subject journal entries
                subject_journals_collection.update_many(
                    {'session_id': session_id},
                    {'$set': {'user_id': self.id, 'session_id': None}}
                )

            return True
        except Exception as e:
            print(f"Error transferring session data: {str(e)}")
            return False