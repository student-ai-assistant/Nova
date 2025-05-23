"""
auth/__init__.py - Authentication blueprint for Student AI Assistant
"""

from flask import Blueprint

# Create a Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# Import routes at the end to avoid circular imports
from auth.routes import *