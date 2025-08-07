"""
입력 검증 유틸리티 모듈
모든 사용자 입력에 대한 검증을 표준화합니다.
"""
import re
from typing import Tuple


class InputValidator:
    """입력 검증 클래스"""
    
    @staticmethod
    def validate_nickname(nickname: str) -> Tuple[bool, str]:
        """닉네임 검증"""
        if not nickname or not nickname.strip():
            return False, "Nickname cannot be empty."
        
        # 공백 제거 후 검증
        nickname = nickname.strip()
        
        # 길이 검증 (UTF-8 바이트 기준)
        if len(nickname.encode('utf-8')) < 3:
            return False, "Nickname must be at least 3 characters long."
        
        if len(nickname.encode('utf-8')) > 20:
            return False, "Nickname must be at most 20 characters long."
        
        # 허용되지 않는 문자 검증
        # SQL 인젝션, XSS, 제어문자 방지
        forbidden_chars = r"[<>\"'&;{}()\[\]\\|`~!@#$%^*+=/?]"
        if re.search(forbidden_chars, nickname):
            return False, "Nickname contains forbidden characters."
        
        # 제어문자 및 비출력 문자 검증
        if re.search(r'[\x00-\x1f\x7f-\x9f]', nickname):
            return False, "Nickname contains invalid control characters."
        
        # 연속된 공백 방지
        if re.search(r'\s{2,}', nickname):
            return False, "Nickname cannot contain consecutive spaces."
        
        # 금지된 단어 패턴
        forbidden_patterns = [
            r'admin', r'administrator', r'moderator', r'system',
            r'null', r'undefined', r'delete', r'drop', r'select'
        ]
        for pattern in forbidden_patterns:
            if re.search(pattern, nickname, re.IGNORECASE):
                return False, "Nickname contains forbidden words."
        
        return True, "Valid nickname."
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """패스워드 강도 검증"""
        if not password:
            return False, "Password cannot be empty."
        
        if len(password) < 9:
            return False, "Password must be at least 9 characters long."
        
        if len(password) > 128:
            return False, "Password is too long."
        
        # 패스워드 복잡성 검증
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/|`~]', password))
        
        complexity_score = sum([has_upper, has_lower, has_digit, has_special])
        
        if complexity_score < 3:
            return False, "Password must contain at least 3 of: uppercase, lowercase, digit, special character."
        
        # 연속된 문자 검증
        if re.search(r'(.)\1{2,}', password):
            return False, "Password cannot contain 3 or more consecutive identical characters."
        
        return True, "Valid password."
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """이메일 검증"""
        if not email or not email.strip():
            return False, "Email cannot be empty."
        
        email = email.strip().lower()
        
        # 길이 검증
        if len(email) > 254:
            return False, "Email address is too long."
        
        # 기본 이메일 형식 검증
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email format."
        
        # 위험한 문자 검증
        if re.search(r'[<>"\']', email):
            return False, "Email contains forbidden characters."
        
        return True, "Valid email."
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """사용자명 검증"""
        if not username or not username.strip():
            return False, "Username cannot be empty."
        
        username = username.strip()
        
        # 길이 검증
        if len(username) < 3:
            return False, "Username must be at least 3 characters long."
        
        if len(username) > 20:
            return False, "Username must be at most 20 characters long."
        
        # 허용되는 문자만 (영숫자, 하이픈, 언더스코어)
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username can only contain letters, numbers, hyphens, and underscores."
        
        # 시작/끝 문자 검증
        if username.startswith('-') or username.endswith('-'):
            return False, "Username cannot start or end with hyphen."
        
        return True, "Valid username."
    
    @staticmethod
    def sanitize_search_input(search_input: str) -> str:
        """검색 입력 정화"""
        if not search_input:
            return ""
        
        # 위험한 SQL 문자 제거
        dangerous_chars = ['\'', '"', ';', '\\', '/', '*']
        for char in dangerous_chars:
            search_input = search_input.replace(char, '')
        
        # 길이 제한
        return search_input.strip()[:100]
    
    @staticmethod
    def validate_numeric_id(value: str, field_name: str = "ID") -> Tuple[bool, str]:
        """숫자 ID 검증"""
        if not value or not str(value).strip():
            return False, f"{field_name} cannot be empty."
        
        try:
            num_value = int(value)
            if num_value <= 0:
                return False, f"{field_name} must be a positive number."
            if num_value > 2147483647:  # INT 최대값
                return False, f"{field_name} is too large."
            return True, "Valid ID."
        except (ValueError, TypeError):
            return False, f"{field_name} must be a valid number."