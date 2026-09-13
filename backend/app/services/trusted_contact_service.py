"""Trusted Contact Service for Sanjeevni Phase 5."""
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.trusted_contact import TrustedContact
from app.schemas.trusted_contact import TrustedContactCreate, TrustedContactUpdate
from app.core.exceptions import SanjeevniException, ErrorCode


class TrustedContactService:
    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Optional[TrustedContact]:
        """Retrieves user's trusted contact or None."""
        return (
            db.query(TrustedContact)
            .filter(TrustedContact.user_id == user_id)
            .first()
        )

    @classmethod
    def create_or_update(
        cls, db: Session, user_id: int, data: TrustedContactCreate
    ) -> TrustedContact:
        """Creates or replaces the user's trusted contact."""
        existing = cls.get_by_user_id(db, user_id)
        if existing:
            existing.name = data.name
            existing.phone_number = data.phone_number
            existing.relationship = data.relationship
            existing.enabled = data.enabled
            existing.consent_given = data.consent_given
            existing.notification_level = data.notification_level.value
            db.commit()
            db.refresh(existing)
            return existing

        contact = TrustedContact(
            user_id=user_id,
            name=data.name,
            phone_number=data.phone_number,
            relationship=data.relationship,
            enabled=data.enabled,
            consent_given=data.consent_given,
            notification_level=data.notification_level.value,
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact

    @classmethod
    def update(
        cls, db: Session, user_id: int, data: TrustedContactUpdate
    ) -> TrustedContact:
        """Updates specific fields of user's trusted contact."""
        contact = cls.get_by_user_id(db, user_id)
        if not contact:
            raise SanjeevniException(
                status_code=404,
                error_code=ErrorCode.NOT_FOUND,
                message="No trusted contact configured for this user.",
            )

        if data.name is not None:
            contact.name = data.name
        if data.phone_number is not None:
            contact.phone_number = data.phone_number
        if data.relationship is not None:
            contact.relationship = data.relationship
        if data.enabled is not None:
            contact.enabled = data.enabled
        if data.consent_given is not None:
            if not data.consent_given and (data.enabled or contact.enabled):
                raise SanjeevniException(
                    status_code=422,
                    error_code=ErrorCode.VALIDATION_ERROR,
                    message="Cannot enable trusted contact without explicit consent.",
                )
            contact.consent_given = data.consent_given
        if data.notification_level is not None:
            contact.notification_level = data.notification_level.value

        db.commit()
        db.refresh(contact)
        return contact

    @classmethod
    def delete(cls, db: Session, user_id: int) -> bool:
        """Deletes user's trusted contact."""
        contact = cls.get_by_user_id(db, user_id)
        if not contact:
            raise SanjeevniException(
                status_code=404,
                error_code=ErrorCode.NOT_FOUND,
                message="No trusted contact configured for this user.",
            )
        db.delete(contact)
        db.commit()
        return True
