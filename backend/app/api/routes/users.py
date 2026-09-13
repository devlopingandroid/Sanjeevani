"""User management routes."""
from fastapi import APIRouter, Depends
from app.schemas.user import UserResponse
from app.models.user import User
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse, summary="Get Current User")
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
