"""
Cloudinary Persistent Profile Image Storage Service.

Provides secure server-side profile photo uploading, replacement, and deletion
using official Cloudinary Python SDK.
Enforces user-isolated public ID strategy so users cannot overwrite another user's image.
"""
from typing import Tuple, Optional
import cloudinary
import cloudinary.uploader
from app.core.config import settings
from app.core.exceptions import SanjeevniException


class CloudinaryService:
    """Service wrapper around Cloudinary SDK for user profile photo management."""

    def __init__(self):
        self._is_configured = False

    def _ensure_configured(self) -> None:
        """Configures Cloudinary SDK if credentials exist; otherwise raises error."""
        if not settings.is_cloudinary_configured:
            raise SanjeevniException(
                message="Profile photo service is currently unavailable.",
                status_code=503,
                error_code="CLOUDINARY_UNCONFIGURED",
            )

        if not self._is_configured:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET,
                secure=True,
            )
            self._is_configured = True

    def upload_profile_avatar(
        self,
        file_bytes: bytes,
        user_id: int,
        old_public_id: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Uploads or replaces a profile photo in Cloudinary using user-isolated public_id strategy.

        Args:
            file_bytes: Raw binary image payload.
            user_id: Authenticated backend user ID.
            old_public_id: Optional previous public_id for safe deletion.

        Returns:
            Tuple of (secure_url, public_id).
        """
        self._ensure_configured()

        # Deterministic user-specific public ID under sanjeevni/profile-avatars/
        public_id = f"{settings.CLOUDINARY_FOLDER}/user_{user_id}_avatar"

        # If previous public ID exists and differs from current format, destroy old asset
        if old_public_id and old_public_id != public_id:
            try:
                cloudinary.uploader.destroy(old_public_id, invalidate=True)
            except Exception:
                # Non-fatal if old image deletion fails
                pass

        # Perform server-side upload with overwrite & CDN invalidation
        response = cloudinary.uploader.upload(
            file_bytes,
            public_id=public_id,
            overwrite=True,
            invalidate=True,
            resource_type="image",
        )

        secure_url = response.get("secure_url") or response.get("url")
        returned_public_id = response.get("public_id") or public_id

        if not secure_url:
            raise SanjeevniException(
                message="Unable to update profile photo. Cloudinary did not return a valid URL.",
                status_code=500,
                error_code="CLOUDINARY_UPLOAD_FAILED",
            )

        return secure_url, returned_public_id

    def delete_profile_avatar(self, public_id: str) -> bool:
        """Deletes an avatar asset from Cloudinary cleanly."""
        if not public_id:
            return False
        try:
            self._ensure_configured()
            res = cloudinary.uploader.destroy(public_id, invalidate=True)
            return res.get("result") == "ok"
        except Exception:
            return False


cloudinary_service = CloudinaryService()
