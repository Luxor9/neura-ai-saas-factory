"""
Unit tests for shared utilities
"""

import pytest
from unittest.mock import patch
from packages.shared.utils import (
    generate_api_key,
    hash_password,
    verify_password,
    sanitize_filename,
    format_file_size,
    validate_email,
    validate_api_key,
    truncate_string,
    calculate_similarity
)

class TestApiKey:
    """Test API key functions"""
    
    def test_generate_api_key_default_prefix(self):
        """Test API key generation with default prefix"""
        key = generate_api_key()
        assert key.startswith("neura_")
        assert len(key) > 10
    
    def test_generate_api_key_custom_prefix(self):
        """Test API key generation with custom prefix"""
        key = generate_api_key("test")
        assert key.startswith("test_")
    
    def test_validate_api_key_valid(self):
        """Test validation of valid API key"""
        key = generate_api_key()
        assert validate_api_key(key) is True
    
    def test_validate_api_key_invalid(self):
        """Test validation of invalid API keys"""
        invalid_keys = [
            "",
            "invalid",
            "invalid_short",
            "toolong_" + "x" * 50,
            "wrong_format_no_underscore"
        ]
        
        for key in invalid_keys:
            assert validate_api_key(key) is False

class TestPasswordHandling:
    """Test password hashing and verification"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) == 64  # SHA-256 hex length
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False

class TestFileUtilities:
    """Test file-related utilities"""
    
    def test_sanitize_filename_safe(self):
        """Test sanitizing safe filename"""
        filename = "safe_filename.txt"
        sanitized = sanitize_filename(filename)
        assert sanitized == filename
    
    def test_sanitize_filename_unsafe_chars(self):
        """Test sanitizing filename with unsafe characters"""
        filename = "unsafe<>:\"/\\|?*filename.txt"
        sanitized = sanitize_filename(filename)
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized
    
    def test_sanitize_filename_empty(self):
        """Test sanitizing empty filename"""
        sanitized = sanitize_filename("")
        assert sanitized.startswith("file_")
    
    def test_format_file_size_bytes(self):
        """Test file size formatting for bytes"""
        assert format_file_size(0) == "0 B"
        assert format_file_size(500) == "500.0 B"
    
    def test_format_file_size_kb(self):
        """Test file size formatting for kilobytes"""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"
    
    def test_format_file_size_mb(self):
        """Test file size formatting for megabytes"""
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 1.5) == "1.5 MB"

class TestValidation:
    """Test validation functions"""
    
    def test_validate_email_valid(self):
        """Test email validation with valid emails"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@example.com"
        ]
        
        for email in valid_emails:
            assert validate_email(email) is True
    
    def test_validate_email_invalid(self):
        """Test email validation with invalid emails"""
        invalid_emails = [
            "",
            "invalid",
            "@example.com",
            "test@",
            "test@@example.com",
            "test..test@example.com"
        ]
        
        for email in invalid_emails:
            assert validate_email(email) is False

class TestStringUtilities:
    """Test string manipulation utilities"""
    
    def test_truncate_string_short(self):
        """Test truncating string shorter than max length"""
        text = "Short text"
        truncated = truncate_string(text, 20)
        assert truncated == text
    
    def test_truncate_string_long(self):
        """Test truncating long string"""
        text = "This is a very long text that needs to be truncated"
        truncated = truncate_string(text, 20)
        assert len(truncated) == 20
        assert truncated.endswith("...")
    
    def test_calculate_similarity_identical(self):
        """Test similarity calculation for identical texts"""
        text1 = "hello world"
        text2 = "hello world"
        similarity = calculate_similarity(text1, text2)
        assert similarity == 1.0
    
    def test_calculate_similarity_different(self):
        """Test similarity calculation for different texts"""
        text1 = "hello world"
        text2 = "goodbye earth"
        similarity = calculate_similarity(text1, text2)
        assert 0.0 <= similarity <= 1.0
        assert similarity < 1.0
    
    def test_calculate_similarity_empty(self):
        """Test similarity calculation with empty strings"""
        similarity = calculate_similarity("", "hello")
        assert similarity == 0.0
        
        similarity = calculate_similarity("hello", "")
        assert similarity == 0.0
        
        similarity = calculate_similarity("", "")
        assert similarity == 0.0