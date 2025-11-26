"""Authentication endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import LoginRequest, RegisterRequest, Token, UserResponse
from app.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    get_current_active_user,
)
from app.database import get_db
import uuid
import secrets

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db=Depends(get_db)):
    """Register new organization and user"""
    # Check if email exists
    existing = await db.fetchval(
        "SELECT id FROM users WHERE email = $1", request.email
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create organization
    org_id = await db.fetchval(
        """
        INSERT INTO organizations (name, tier, api_key, api_secret)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        request.organization_name,
        "starter",
        f"ogt_{secrets.token_urlsafe(32)}",
        secrets.token_urlsafe(48),
    )

    # Create user
    user_id = await db.fetchval(
        """
        INSERT INTO users (organization_id, email, password_hash, full_name, role)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        org_id,
        request.email,
        get_password_hash(request.password),
        request.full_name,
        "owner",
    )

    user = await db.fetchrow(
        "SELECT id, email, full_name, role, active, created_at FROM users WHERE id = $1",
        user_id,
    )

    return UserResponse(**dict(user))


@router.post("/login", response_model=Token)
async def login(request: LoginRequest, db=Depends(get_db)):
    """Login and get access token"""
    user = await authenticate_user(request.email, request.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db=Depends(get_db)):
    """Refresh access token"""
    from jose import jwt, JWTError
    from app.config import settings

    try:
        payload = jwt.decode(
            refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if user_id is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Verify user still exists
        user = await db.fetchval("SELECT id FROM users WHERE id = $1 AND active = true", user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        # Create new tokens
        access_token = create_access_token(data={"sub": user_id})
        new_refresh_token = create_refresh_token(data={"sub": user_id})

        return Token(access_token=access_token, refresh_token=new_refresh_token)

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user=Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        active=current_user.active,
        created_at=None,  # Would need to fetch from DB
    )


@router.post("/logout")
async def logout():
    """Logout (client should discard tokens)"""
    return {"message": "Successfully logged out"}
