"""Authentication endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import Token, LoginRequest
from app.schemas.user import UserCreate, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.core.exceptions import SanjeevniException, ErrorCode

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise SanjeevniException(
            status_code=status.HTTP_409_CONFLICT,
            error_code=ErrorCode.VALIDATION_ERROR,
            message="An account with this email already exists",
        )

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="User Login",
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise SanjeevniException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=ErrorCode.UNAUTHORIZED,
            message="Incorrect email or password",
        )

    access_token = create_access_token(subject=user.id)
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
