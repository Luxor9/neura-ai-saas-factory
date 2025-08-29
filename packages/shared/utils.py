"""
NEURA AI SaaS Factory - Shared Utilities
Common utility functions used across all packages
"""

import os
import json
import hashlib
import secrets
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import asyncio
import logging

logger = logging.getLogger(__name__)

def generate_api_key(prefix: str = "neura") -> str:
    """Generate a secure API key with prefix"""
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}_{random_part}"

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == hashed

def generate_user_id() -> str:
    """Generate a unique user ID"""
    timestamp = str(int(time.time()))
    random_part = secrets.token_hex(8)
    return f"user_{timestamp}_{random_part}"

def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe storage"""
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length and remove leading/trailing spaces
    filename = filename.strip()[:100]
    
    # Ensure it's not empty or just dots
    if not filename or filename.replace('.', '').strip() == '':
        filename = f"file_{int(time.time())}"
    
    return filename

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat()

def parse_timestamp(timestamp: str) -> datetime:
    """Parse ISO timestamp string to datetime object"""
    try:
        return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except ValueError:
        logger.warning(f"Invalid timestamp format: {timestamp}")
        return datetime.now(timezone.utc)

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely load JSON string with fallback"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Failed to parse JSON: {json_str[:100]}...")
        return default

def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely dump object to JSON string with fallback"""
    try:
        return json.dumps(obj, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        logger.warning(f"Failed to serialize to JSON: {type(obj)}")
        return default

def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if it doesn't"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def cleanup_old_files(directory: Union[str, Path], max_age_days: int = 30) -> int:
    """Clean up files older than specified days"""
    directory = Path(directory)
    if not directory.exists():
        return 0
    
    cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
    cleaned_count = 0
    
    for file_path in directory.rglob('*'):
        if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
            try:
                file_path.unlink()
                cleaned_count += 1
                logger.info(f"Cleaned up old file: {file_path}")
            except OSError as e:
                logger.warning(f"Failed to delete {file_path}: {e}")
    
    return cleaned_count

def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_api_key(api_key: str) -> bool:
    """Validate API key format"""
    if not api_key:
        return False
    
    # Check if it matches our format: prefix_base64urlsafe
    parts = api_key.split('_', 1)
    if len(parts) != 2:
        return False
    
    prefix, key_part = parts
    
    # Check prefix
    if prefix not in ['neura', 'test']:
        return False
    
    # Check key part length (should be 43 chars for 32 bytes base64url)
    if len(key_part) != 43:
        return False
    
    return True

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to max length with suffix"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def retry_async(max_attempts: int = 3, delay: float = 1.0):
    """Decorator for retrying async functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed. Last error: {e}")
            
            raise last_exception
        
        return wrapper
    return decorator

def get_system_info() -> Dict[str, Any]:
    """Get basic system information"""
    import platform
    import psutil
    
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total": psutil.virtual_memory().total,
        "memory_available": psutil.virtual_memory().available,
        "disk_usage": {
            "total": psutil.disk_usage('/').total,
            "free": psutil.disk_usage('/').free,
            "used": psutil.disk_usage('/').used,
        } if os.name != 'nt' else None
    }

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts (simple implementation)"""
    if not text1 or not text2:
        return 0.0
    
    # Convert to lowercase and split into words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0

def batch_process(items: List[Any], batch_size: int = 100, process_func=None):
    """Process items in batches"""
    if not process_func:
        process_func = lambda x: x
    
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = []
        
        for item in batch:
            try:
                result = process_func(item)
                batch_results.append(result)
            except Exception as e:
                logger.warning(f"Failed to process item {item}: {e}")
                batch_results.append(None)
        
        results.extend(batch_results)
        logger.info(f"Processed batch {i // batch_size + 1}/{(len(items) - 1) // batch_size + 1}")
    
    return results

# Performance monitoring utilities
class Timer:
    """Simple timer context manager"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.info(f"{self.name} completed in {duration:.2f} seconds")
    
    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None