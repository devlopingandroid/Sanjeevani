"""API Endpoints for Phase 5 Trusted Contact and Consent."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.api.dependencies import get_current_user
from app.schemas.trusted_contact import (
    TrustedContactCreate,
    TrustedContactUpdate,
    TrustedContactResponse,
)
from app.services.trusted_contact_service import TrustedContactService

router = APIRouter(prefix="/trusted-contact", tags=["Trusted Contact & Consent"])


@router.get(
    "",
    response_model=TrustedContactResponse,
    summary="Get user's trusted contact",
)
def get_trusted_contact(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves the authenticated user's trusted contact."""
    contact = TrustedContactService.get_by_user_id(db, user_id=current_user.id)
    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No trusted contact configured for this user.",
        )
    return contact


@router.post(
    "",
    response_model=TrustedContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Configure/set user's trusted contact",
)
def create_trusted_contact(
    data: TrustedContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Configures or replaces the authenticated user's trusted contact with explicit consent."""
    return TrustedContactService.create_or_update(
        db=db, user_id=current_user.id, data=data
    )


@router.patch(
    "",
    response_model=TrustedContactResponse,
    summary="Update user's trusted contact",
)
def update_trusted_contact(
    data: TrustedContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Updates specific fields of the authenticated user's trusted contact."""
    return TrustedContactService.update(
        db=db, user_id=current_user.id, data=data
    )


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
    summary="Delete user's trusted contact",
)
def delete_trusted_contact(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deletes the authenticated user's trusted contact record."""
    TrustedContactService.delete(db=db, user_id=current_user.id)
    return {"message": "Trusted contact successfully deleted.", "success": True}
