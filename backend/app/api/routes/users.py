import os
import uuid
import time
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.models.user import User
from app.api.dependencies import get_current_user
from app.core.config import settings

router = APIRouter(prefix="/users", tags=["Users"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.get("/me", response_model=UserResponse, summary="Get Current User")
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse, summary="Update Current User Profile")
def update_current_user(
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name.strip()
    if update_data.profile_image_url is not None:
        current_user.profile_image_url = update_data.profile_image_url
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/avatar", response_model=UserResponse, summary="Upload User Avatar")
async def upload_user_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image type '{file.content_type}'. Allowed types: jpeg, png, webp, gif.",
        )

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of 5MB.",
        )

    # Extract extension safely
    orig_ext = os.path.splitext(file.filename or "")[1].lower()
    if orig_ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
        }
        orig_ext = ext_map.get(file.content_type, ".jpg")

    safe_filename = f"avatar_{current_user.id}_{int(time.time())}_{uuid.uuid4().hex[:8]}{orig_ext}"
    file_path = os.path.join(settings.avatars_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    avatar_url = f"/uploads/avatars/{safe_filename}"
    current_user.profile_image_url = avatar_url
    db.commit()
    db.refresh(current_user)
    return current_user

