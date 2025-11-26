"""
Production Authentication System
JWT-based authentication with refresh tokens
"""
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import structlog

logger = structlog.get_logger()

# Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", secrets.token_urlsafe(32))
REFRESH_SECRET_KEY = os.environ.get("JWT_REFRESH_SECRET", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
VERIFICATION_TOKEN_EXPIRE_HOURS = 24
PASSWORD_RESET_TOKEN_EXPIRE_HOURS = 2

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer
security = HTTPBearer()

class AuthService:
    """Production authentication service"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: Dict[str, Any]) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow()
        })
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow()
        })
        return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode a JWT token"""
        try:
            if token_type == "access":
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            else:
                payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    @staticmethod
    def create_verification_token(email: str) -> str:
        """Create an email verification token"""
        data = {
            "email": email,
            "purpose": "email_verification",
            "created": datetime.utcnow().isoformat()
        }
        expire = datetime.utcnow() + timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
        data["exp"] = expire
        return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_reset_token(email: str) -> str:
        """Create a password reset token"""
        data = {
            "email": email,
            "purpose": "password_reset",
            "created": datetime.utcnow().isoformat()
        }
        expire = datetime.utcnow() + timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
        data["exp"] = expire
        return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        return f"ogtool_{secrets.token_urlsafe(32)}"

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()

class AuthMiddleware:
    """Authentication middleware for FastAPI"""

    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get the current authenticated user from JWT token"""
        from database.connection import get_db
        from database.models import User

        token = credentials.credentials
        payload = AuthService.verify_token(token, "access")

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is disabled"
                )
            return user

    async def get_current_active_user(self, user = Depends(get_current_user)):
        """Ensure user is active and verified"""
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified"
            )
        return user

    async def require_admin(self, user = Depends(get_current_active_user)):
        """Require admin role"""
        if user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return user

    async def require_organization(self, user = Depends(get_current_active_user)):
        """Require user to belong to an organization"""
        if not user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization membership required"
            )
        return user

# Singleton instances
auth_service = AuthService()
auth_middleware = AuthMiddleware()

# Dependency shortcuts
get_current_user = auth_middleware.get_current_user
get_current_active_user = auth_middleware.get_current_active_user
require_admin = auth_middleware.require_admin
require_organization = auth_middleware.require_organization

class RateLimiter:
    """Rate limiting for API endpoints"""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = {}

    async def check_rate_limit(self, user_id: int) -> bool:
        """Check if user has exceeded rate limit"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)

        # Clean old requests
        if user_id in self.requests:
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if req_time > minute_ago
            ]
        else:
            self.requests[user_id] = []

        # Check limit
        if len(self.requests[user_id]) >= self.requests_per_minute:
            return False

        # Add current request
        self.requests[user_id].append(now)
        return True

# Global rate limiter
rate_limiter = RateLimiter()

async def check_api_key(api_key: str) -> Optional[Dict]:
    """Validate API key and return user info"""
    from database.connection import get_db
    from database.models import ApiKey, User

    if not api_key or not api_key.startswith("ogtool_"):
        return None

    key_hash = AuthService.hash_api_key(api_key)

    with get_db() as db:
        api_key_record = db.query(ApiKey).filter(
            ApiKey.key == key_hash,
            ApiKey.is_active == True
        ).first()

        if not api_key_record:
            return None

        # Check expiration
        if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
            return None

        # Update last used
        api_key_record.last_used = datetime.utcnow()
        db.commit()

        # Get user
        user = db.query(User).filter(User.id == api_key_record.user_id).first()
        if not user or not user.is_active:
            return None

        return {
            "user_id": user.id,
            "permissions": api_key_record.permissions,
            "rate_limit": api_key_record.rate_limit
        }