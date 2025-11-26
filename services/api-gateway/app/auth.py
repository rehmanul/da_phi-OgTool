"""Authentication and authorization"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import structlog

from app.config import settings
from app.database import get_db
from app.models import User, TokenData

logger = structlog.get_logger()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token authentication
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db),
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "access":
            raise credentials_exception

        token_data = TokenData(user_id=user_id)

    except JWTError as e:
        logger.warning("JWT validation failed", error=str(e))
        raise credentials_exception

    # Fetch user from database
    user = await db.fetchrow(
        """
        SELECT u.id, u.organization_id, u.email, u.full_name, u.role, u.active,
               o.tier, o.api_key
        FROM users u
        JOIN organizations o ON u.organization_id = o.id
        WHERE u.id = $1 AND u.active = true
        """,
        user_id,
    )

    if user is None:
        raise credentials_exception

    return User(**dict(user))


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user"""
    if not current_user.active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return current_user


def require_role(required_role: str):
    """Dependency to require specific role"""

    async def role_checker(current_user: User = Depends(get_current_active_user)):
        role_hierarchy = {"viewer": 0, "member": 1, "admin": 2, "owner": 3}

        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 999)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role or higher",
            )

        return current_user

    return role_checker


async def authenticate_user(email: str, password: str, db) -> Optional[User]:
    """Authenticate user by email and password"""
    user = await db.fetchrow(
        """
        SELECT u.id, u.organization_id, u.email, u.password_hash, u.full_name,
               u.role, u.active, o.tier, o.api_key
        FROM users u
        JOIN organizations o ON u.organization_id = o.id
        WHERE u.email = $1 AND u.active = true
        """,
        email,
    )

    if not user:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    # Update last login
    await db.execute(
        "UPDATE users SET last_login = NOW() WHERE id = $1", user["id"]
    )

    return User(**dict(user))
