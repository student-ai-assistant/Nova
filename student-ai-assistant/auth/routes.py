"""
auth/routes.py - Authentication routes for Student AI Assistant
"""

import logging
from flask import (
    render_template, redirect, url_for, flash,
    request, current_app, session
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from bson.objectid import ObjectId

from . import auth_bp
from models import User

# Configure logging
logger = logging.getLogger(__name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Log in an existing user"""
    # If user is already logged in, redirect to home
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('index'))

    # Handle form submission
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False) == 'on'

        # Basic validation
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('login.html')

        # Get MongoDB client from the app
        mongo_client = current_app.config['get_mongodb_client']()

        # Get user from database
        user = User.get_by_username(username, mongo_client)

        # Check if user exists and password is correct
        if not user or not user.verify_password(password):
            flash('Invalid username or password.', 'error')
            return render_template('login.html')

        # Store the current session ID to transfer data after login
        session_id = session.get('session_id')

        # Log the user in
        login_user(user, remember=remember)
        flash('Login successful!', 'success')

        # Transfer any existing session data to the user account
        if session_id:
            user.transfer_session_data(session_id, mongo_client)

        # Redirect to home page or next page
        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))

    # GET request - show login form
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user"""
    # If user is already logged in, redirect to home
    if current_user.is_authenticated:
        flash('You are already logged in.', 'info')
        return redirect(url_for('index'))

    # Handle form submission
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Basic validation
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        # Get MongoDB client from the app
        mongo_client = current_app.config['get_mongodb_client']()

        # Create new user
        user, error = User.create(username=username, password=password, email=email, mongo_client=mongo_client)

        if error:
            flash(f'Registration error: {error}', 'error')
            return render_template('register.html')

        if user:
            # Store the current session ID to transfer data after login
            session_id = session.get('session_id')

            # Log the user in
            login_user(user)
            flash('Registration successful! You are now logged in.', 'success')

            # Transfer any existing session data to the new user account
            if session_id:
                user.transfer_session_data(session_id, mongo_client)

            # Redirect to home page or next page
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))

    # GET request - show registration form
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Display user profile page"""
    return render_template('profile.html')

def transfer_session_data(mongo_client, session_id, user_id):
    """
    Transfer data from anonymous session to user account

    Args:
        mongo_client: MongoDB client instance
        session_id: Anonymous session ID
        user_id: User ID to transfer data to

    Note:
        This function transfers subjects, documents, and journal entries
        from an anonymous session to a user account.
    """
    if not session_id:
        return

    try:
        # Get all subjects for the session using client methods
        subjects = mongo_client.get_subjects(session_id=session_id)

        for subject in subjects:
            subject_id = subject['_id']

            # Update the subject to belong to the user - use get_collection to ensure connection is active
            subject_collection = mongo_client.get_collection('subjects')
            if subject_collection:
                subject_collection.update_one(
                    {'_id': ObjectId(subject_id)},
                    {'$set': {'user_id': user_id, 'session_id': None}}
                )

            # Update all documents for this subject
            document_collection = mongo_client.get_collection('documents')
            if document_collection:
                document_collection.update_many(
                    {'subject_id': subject_id, 'session_id': session_id},
                    {'$set': {'user_id': user_id, 'session_id': None}}
                )

            # Update all subject journal entries
            subject_journal_collection = mongo_client.get_collection('subject_journals')
            if subject_journal_collection:
                subject_journal_collection.update_many(
                    {'subject_id': subject_id, 'session_id': session_id},
                    {'$set': {'user_id': user_id, 'session_id': None}}
                )

        # Update all user journal entries
        user_journal_collection = mongo_client.get_collection('user_journals')
        if user_journal_collection:
            user_journal_collection.update_many(
                {'session_id': session_id},
                {'$set': {'user_id': user_id, 'session_id': None}}
            )

        logger.info(f"Transferred session data from {session_id} to user {user_id}")

    except Exception as e:
        logger.error(f"Error transferring session data: {str(e)}")