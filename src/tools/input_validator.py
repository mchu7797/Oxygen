"""
Input validation utility module.
Standardizes validation for all user inputs.
"""

import re
from typing import Tuple


class InputValidator:
    """Input validation class."""

    @staticmethod
    def validate_nickname(nickname: str) -> Tuple[bool, str]:
        """Validate nickname."""
        if not nickname or not nickname.strip():
            return False, "Nickname cannot be empty."

        # Remove whitespace and validate
        nickname = nickname.strip()

        # Length validation (UTF-8 byte basis)
        if len(nickname.encode("utf-8")) < 3:
            return False, "Nickname must be at least 3 characters long."

        if len(nickname.encode("utf-8")) > 20:
            return False, "Nickname must be at most 20 characters long."

        # Forbidden character validation
        # Prevent SQL injection, XSS, control characters
        forbidden_chars = r"[<>\"'&;{}()\[\]\\|`~!@#$%^*+=/?]"
        if re.search(forbidden_chars, nickname):
            return False, "Nickname contains forbidden characters."

        # Control character and non-printable character validation
        if re.search(r"[\x00-\x1f\x7f-\x9f]", nickname):
            return False, "Nickname contains invalid control characters."

        # Prevent consecutive spaces
        if re.search(r"\s{2,}", nickname):
            return False, "Nickname cannot contain consecutive spaces."

        # Forbidden word patterns
        forbidden_patterns = [
            r"admin",
            r"administrator",
            r"moderator",
            r"system",
            r"null",
            r"undefined",
            r"delete",
            r"drop",
            r"select",
        ]
        for pattern in forbidden_patterns:
            if re.search(pattern, nickname, re.IGNORECASE):
                return False, "Nickname contains forbidden words."

        return True, "Valid nickname."

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """Validate password strength."""
        if not password:
            return False, "Password cannot be empty."

        if len(password) < 9:
            return False, "Password must be at least 9 characters long."

        if len(password) > 128:
            return False, "Password is too long."

        # Password complexity validation
        has_upper = bool(re.search(r"[A-Z]", password))
        has_lower = bool(re.search(r"[a-z]", password))
        has_digit = bool(re.search(r"\d", password))
        has_special = bool(
            re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/|`~]', password)
        )

        complexity_score = sum([has_upper, has_lower, has_digit, has_special])

        if complexity_score < 3:
            return (
                False,
                "Password must contain at least 3 of: uppercase, lowercase, digit, special character.",
            )

        # Consecutive character validation
        if re.search(r"(.)\1{2,}", password):
            return (
                False,
                "Password cannot contain 3 or more consecutive identical characters.",
            )

        return True, "Valid password."

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email address."""
        if not email or not email.strip():
            return False, "Email cannot be empty."

        email = email.strip().lower()

        # Length validation
        if len(email) > 254:
            return False, "Email address is too long."

        # Basic email format validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            return False, "Invalid email format."

        # Dangerous character validation
        if re.search(r'[<>"\']', email):
            return False, "Email contains forbidden characters."

        return True, "Valid email."

    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """Validate username."""
        if not username or not username.strip():
            return False, "Username cannot be empty."

        username = username.strip()

        # Length validation
        if len(username) < 3:
            return False, "Username must be at least 3 characters long."

        if len(username) > 20:
            return False, "Username must be at most 20 characters long."

        # Only allowed characters (alphanumeric, hyphens, underscores)
        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            return (
                False,
                "Username can only contain letters, numbers, hyphens, and underscores.",
            )

        # Start/end character validation
        if username.startswith("-") or username.endswith("-"):
            return False, "Username cannot start or end with hyphen."

        return True, "Valid username."

    @staticmethod
    def sanitize_search_input(search_input: str) -> str:
        """Sanitize search input."""
        if not search_input:
            return ""

        # Remove dangerous SQL characters
        dangerous_chars = ["'", '"', ";", "\\", "/", "*"]
        for char in dangerous_chars:
            search_input = search_input.replace(char, "")

        # Length limit
        return search_input.strip()[:100]

    @staticmethod
    def validate_numeric_id(value: str, field_name: str = "ID") -> Tuple[bool, str]:
        """Validate numeric ID."""
        if not value or not str(value).strip():
            return False, f"{field_name} cannot be empty."

        try:
            num_value = int(value)
            if num_value <= 0:
                return False, f"{field_name} must be a positive number."
            if num_value > 2147483647:  # INT max value
                return False, f"{field_name} is too large."
            return True, "Valid ID."
        except (ValueError, TypeError):
            return False, f"{field_name} must be a valid number."
