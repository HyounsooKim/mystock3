"""
Input sanitization utilities for user-generated content.
Prevents XSS attacks and ensures data integrity.
"""

import re
import html
from typing import Optional


class InputSanitizer:
    """
    Sanitize user input to prevent security vulnerabilities.
    
    Features:
    - HTML escape for display
    - Strip dangerous characters
    - Validate length constraints
    - Remove control characters
    """
    
    # Maximum lengths for different field types
    MAX_MEMO_LENGTH = 500
    MAX_SYMBOL_LENGTH = 10
    MAX_EMAIL_LENGTH = 254
    MAX_CATEGORY_LENGTH = 50
    
    # Dangerous patterns
    SCRIPT_PATTERN = re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL)
    HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
    CONTROL_CHARS_PATTERN = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')
    
    @staticmethod
    def sanitize_memo(memo: Optional[str]) -> Optional[str]:
        """
        Sanitize portfolio/watchlist memo field.
        
        Args:
            memo: User-provided memo text
        
        Returns:
            Sanitized memo or None if input is None/empty
        """
        if not memo:
            return None
        
        # Strip whitespace
        memo = memo.strip()
        
        if not memo:
            return None
        
        # Remove control characters
        memo = InputSanitizer.CONTROL_CHARS_PATTERN.sub('', memo)
        
        # Remove script tags
        memo = InputSanitizer.SCRIPT_PATTERN.sub('', memo)
        
        # Remove other HTML tags
        memo = InputSanitizer.HTML_TAG_PATTERN.sub('', memo)
        
        # HTML escape remaining content
        memo = html.escape(memo)
        
        # Enforce length limit
        if len(memo) > InputSanitizer.MAX_MEMO_LENGTH:
            memo = memo[:InputSanitizer.MAX_MEMO_LENGTH]
        
        return memo
    
    @staticmethod
    def sanitize_symbol(symbol: str) -> str:
        """
        Sanitize stock symbol input.
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Sanitized symbol (uppercase, alphanumeric only)
        
        Raises:
            ValueError: If symbol is invalid
        """
        if not symbol:
            raise ValueError("Symbol cannot be empty")
        
        # Remove whitespace
        symbol = symbol.strip().upper()
        
        # Only allow alphanumeric characters and dots (for some ETFs)
        if not re.match(r'^[A-Z0-9.]+$', symbol):
            raise ValueError(
                f"Invalid symbol format: {symbol}. "
                "Only alphanumeric characters and dots allowed."
            )
        
        # Enforce length limit
        if len(symbol) > InputSanitizer.MAX_SYMBOL_LENGTH:
            raise ValueError(
                f"Symbol too long: {symbol}. "
                f"Maximum {InputSanitizer.MAX_SYMBOL_LENGTH} characters."
            )
        
        return symbol
    
    @staticmethod
    def sanitize_category(category: Optional[str]) -> Optional[str]:
        """
        Sanitize portfolio category field.
        
        Args:
            category: Portfolio category
        
        Returns:
            Sanitized category or None
        """
        if not category:
            return None
        
        # Strip whitespace
        category = category.strip()
        
        if not category:
            return None
        
        # Remove control characters
        category = InputSanitizer.CONTROL_CHARS_PATTERN.sub('', category)
        
        # HTML escape
        category = html.escape(category)
        
        # Enforce length limit
        if len(category) > InputSanitizer.MAX_CATEGORY_LENGTH:
            category = category[:InputSanitizer.MAX_CATEGORY_LENGTH]
        
        return category
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """
        Sanitize email address.
        
        Args:
            email: Email address
        
        Returns:
            Sanitized email (lowercase, stripped)
        
        Raises:
            ValueError: If email format is invalid
        """
        if not email:
            raise ValueError("Email cannot be empty")
        
        # Strip and lowercase
        email = email.strip().lower()
        
        # Basic email format validation
        email_pattern = re.compile(
            r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$',
            re.IGNORECASE
        )
        
        if not email_pattern.match(email):
            raise ValueError(f"Invalid email format: {email}")
        
        # Enforce length limit
        if len(email) > InputSanitizer.MAX_EMAIL_LENGTH:
            raise ValueError(
                f"Email too long. Maximum {InputSanitizer.MAX_EMAIL_LENGTH} characters."
            )
        
        return email
    
    @staticmethod
    def sanitize_generic_text(
        text: str,
        max_length: int = 200,
        allow_html: bool = False
    ) -> str:
        """
        Sanitize generic text input.
        
        Args:
            text: Input text
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML (escaped)
        
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Strip whitespace
        text = text.strip()
        
        # Remove control characters
        text = InputSanitizer.CONTROL_CHARS_PATTERN.sub('', text)
        
        if not allow_html:
            # Remove all HTML
            text = InputSanitizer.SCRIPT_PATTERN.sub('', text)
            text = InputSanitizer.HTML_TAG_PATTERN.sub('', text)
        
        # HTML escape
        text = html.escape(text)
        
        # Enforce length limit
        if len(text) > max_length:
            text = text[:max_length]
        
        return text


def sanitize_input(value: any, field_type: str) -> any:
    """
    Convenience function to sanitize input based on field type.
    
    Args:
        value: Input value
        field_type: Type of field (memo, symbol, email, category, text)
    
    Returns:
        Sanitized value
    
    Raises:
        ValueError: If field_type is unknown or validation fails
    """
    if value is None:
        return None
    
    field_type = field_type.lower()
    
    if field_type == "memo":
        return InputSanitizer.sanitize_memo(value)
    elif field_type == "symbol":
        return InputSanitizer.sanitize_symbol(value)
    elif field_type == "email":
        return InputSanitizer.sanitize_email(value)
    elif field_type == "category":
        return InputSanitizer.sanitize_category(value)
    elif field_type == "text":
        return InputSanitizer.sanitize_generic_text(value)
    else:
        raise ValueError(f"Unknown field type: {field_type}")
