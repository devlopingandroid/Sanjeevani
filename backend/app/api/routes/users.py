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
from app.services.cloudinary_service import cloudinary_service

router = APIRouter(prefix="/users", tags=["Users"])

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/heic",
    "image/heif",
    "application/octet-stream",
}
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}
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
    content_type = (file.content_type or "").lower()
    orig_ext = os.path.splitext(file.filename or "")[1].lower()

    # If generic binary stream, strictly enforce valid image file extension
    if content_type == "application/octet-stream":
        if orig_ext not in VALID_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension '{orig_ext}' for image upload.",
            )
    elif content_type not in ALLOWED_IMAGE_TYPES and orig_ext not in VALID_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image type '{file.content_type}'. Allowed types: jpeg, png, webp, gif.",
        )

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum limit of 5MB.",
        )

    # Server-side upload to Cloudinary
    secure_url, public_id = cloudinary_service.upload_profile_avatar(
        file_bytes=content,
        user_id=current_user.id,
        old_public_id=current_user.profile_image_public_id,
    )

    current_user.profile_image_url = secure_url
    current_user.profile_image_public_id = public_id
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me/emotional-data", summary="Delete User Emotional Wellness Data")
def delete_user_emotional_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deletes emotional assessments, risk events, and notification audit records for the authenticated user.

    Preserves raw conversation logs (conversations & chat_messages) unless full account deletion is requested.
    """
    from app.models.emotional_assessment import EmotionalAssessment
    from app.models.risk_event import RiskEvent
    from app.models.notification_event import NotificationEvent

    deleted_assessments = (
        db.query(EmotionalAssessment)
        .filter(EmotionalAssessment.user_id == current_user.id)
        .delete(synchronize_session=False)
    )
    deleted_risk_events = (
        db.query(RiskEvent)
        .filter(RiskEvent.user_id == current_user.id)
        .delete(synchronize_session=False)
    )
    deleted_notifications = (
        db.query(NotificationEvent)
        .filter(NotificationEvent.user_id == current_user.id)
        .delete(synchronize_session=False)
    )

    db.commit()

    return {
        "success": True,
        "message": "Emotional wellness data successfully deleted.",
        "deleted_assessments_count": deleted_assessments,
        "deleted_risk_events_count": deleted_risk_events,
        "deleted_notification_events_count": deleted_notifications,
    }



