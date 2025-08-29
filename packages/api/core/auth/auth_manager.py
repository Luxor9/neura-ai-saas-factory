
import secrets
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sqlite3
import os

class APIKeyManager:
    def __init__(self, db_path: str = "neura_saas.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                plan TEXT DEFAULT 'free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # API Keys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                key_hash TEXT UNIQUE NOT NULL,
                key_prefix TEXT NOT NULL,
                name TEXT,
                usage_count INTEGER DEFAULT 0,
                rate_limit INTEGER DEFAULT 1000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Usage tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key_id INTEGER,
                endpoint TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_time REAL,
                status_code INTEGER,
                FOREIGN KEY (api_key_id) REFERENCES api_keys (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_api_key(self, user_id: int, name: str = "Default") -> Dict:
        """Generate a new API key for a user"""
        # Generate a secure random key
        key = f"neura_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(32))}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        key_prefix = key[:12] + "..."
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_keys (user_id, key_hash, key_prefix, name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, key_hash, key_prefix, name))
        
        api_key_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "api_key": key,
            "key_id": api_key_id,
            "prefix": key_prefix,
            "name": name,
            "created_at": datetime.now().isoformat()
        }
    
    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """Validate an API key and return user info"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ak.id, ak.user_id, ak.usage_count, ak.rate_limit, u.email, u.plan
            FROM api_keys ak
            JOIN users u ON ak.user_id = u.id
            WHERE ak.key_hash = ? AND ak.is_active = TRUE AND u.is_active = TRUE
        ''', (key_hash,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "key_id": result[0],
                "user_id": result[1],
                "usage_count": result[2],
                "rate_limit": result[3],
                "email": result[4],
                "plan": result[5]
            }
        return None
    
    def track_usage(self, api_key_id: int, endpoint: str, response_time: float, status_code: int):
        """Track API usage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert usage record
        cursor.execute('''
            INSERT INTO api_usage (api_key_id, endpoint, response_time, status_code)
            VALUES (?, ?, ?, ?)
        ''', (api_key_id, endpoint, response_time, status_code))
        
        # Update usage count and last used
        cursor.execute('''
            UPDATE api_keys 
            SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (api_key_id,))
        
        conn.commit()
        conn.close()
    
    def get_user_usage(self, user_id: int) -> Dict:
        """Get usage statistics for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_requests,
                AVG(response_time) as avg_response_time,
                COUNT(DISTINCT endpoint) as unique_endpoints
            FROM api_usage au
            JOIN api_keys ak ON au.api_key_id = ak.id
            WHERE ak.user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            "total_requests": result[0] or 0,
            "avg_response_time": round(result[1] or 0, 3),
            "unique_endpoints": result[2] or 0
        }

class AuthManager:
    def __init__(self):
        self.api_key_manager = APIKeyManager()
        self.security = HTTPBearer()
        self.JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-this")
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Dependency to get current user from API key"""
        token = credentials.credentials
        
        # Check if it's an API key
        if token.startswith("neura_"):
            user_info = self.api_key_manager.validate_api_key(token)
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key"
                )
            return user_info
        
        # Check if it's a JWT token
        try:
            payload = jwt.decode(token, self.JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("user_id")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            return {"user_id": user_id}
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def create_user(self, email: str, password: str) -> Dict:
        """Create a new user"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = sqlite3.connect(self.api_key_manager.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (email, password_hash)
                VALUES (?, ?)
            ''', (email, password_hash))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            # Generate initial API key
            api_key_info = self.api_key_manager.generate_api_key(user_id, "Initial Key")
            
            return {
                "user_id": user_id,
                "email": email,
                "api_key": api_key_info["api_key"],
                "created_at": datetime.now().isoformat()
            }
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        finally:
            conn.close()
