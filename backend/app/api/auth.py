"""
Authentication API endpoints — Sign Up and Sign In.

POST /api/auth/signup  — Create new account, returns JWT
POST /api/auth/signin  — Login with email+password, returns JWT
GET  /api/auth/me      — Returns current user profile (requires auth)
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from app.database import get_db
from app.models.user import User
from app.services.auth_service import hash_password, verify_password, create_access_token
from app.api.deps import get_current_user

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────────────

class SignUpRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Endpoints ─────────────────────────────────────────────────────────

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(request: SignUpRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.
    Returns a JWT access token on success.
    """
    # Check if email is already registered
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=request.email,
        full_name=request.full_name,
        hashed_password=hash_password(request.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@router.post("/signin", response_model=TokenResponse)
def signin(request: SignInRequest, db: Session = Depends(get_db)):
    """
    Sign in with email and password.
    Returns a JWT access token on success.
    """
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled.",
        )

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the currently authenticated user's profile."""
    return UserOut.model_validate(current_user)
