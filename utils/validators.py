"""Input validation utilities."""
import re
from typing import Tuple

class Validators:
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        if not username:
            return False, "Username is required"
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        if len(username) > 50:
            return False, "Username must be less than 50 characters"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        return True, ""
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        if not password:
            return False, "Password is required"
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        if len(password) > 100:
            return False, "Password must be less than 100 characters"
        return True, ""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        if not email:
            return False, "Email is required"
        if len(email) > 100:
            return False, "Email must be less than 100 characters"
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email format"
        return True, ""
    
    @staticmethod
    def validate_product_name(name: str) -> Tuple[bool, str]:
        if not name or not name.strip():
            return False, "Product name is required"
        if len(name.strip()) < 2:
            return False, "Product name must be at least 2 characters"
        if len(name) > 200:
            return False, "Product name must be less than 200 characters"
        return True, ""
