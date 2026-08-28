import os
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from jose import JWTError, jwt
from app.core.config import settings
from app.core.logging import logger

SIGNED_TOKEN_ALGORITHM = "HS256"


class StorageService:
    @staticmethod
    def compute_hash(file_bytes: bytes) -> str:
        """Compute SHA-256 hash of file contents."""
        return hashlib.sha256(file_bytes).hexdigest()

    @staticmethod
    def generate_storage_key(business_id: uuid.UUID, document_type: str, version: int, filename: str) -> str:
        """
        Generate a secure, structured object storage key.
        Example: businesses/123e4567-e89b-12d3-a456-426614174000/PAN_CARD/v1_8a7f9b2c.pdf
        """
        ext = os.path.splitext(filename)[1].lower() or ".bin"
        unique_suffix = uuid.uuid4().hex[:8]
        safe_type = document_type.upper().replace(" ", "_")
        return f"businesses/{business_id}/{safe_type}/v{version}_{unique_suffix}{ext}"

    @staticmethod
    def save_file(file_bytes: bytes, storage_key: str) -> str:
        """
        Save file bytes to local object storage directory.
        Returns the absolute local path written.
        """
        full_path = os.path.join(settings.UPLOAD_DIR, storage_key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(file_bytes)
        logger.info(f"File stored successfully at key: {storage_key}")
        return full_path

    @staticmethod
    def read_file(storage_key: str) -> bytes:
        """Read file bytes from object storage."""
        full_path = os.path.join(settings.UPLOAD_DIR, storage_key)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Storage key {storage_key} not found on disk.")
        with open(full_path, "rb") as f:
            return f.read()

    @staticmethod
    def delete_file(storage_key: str) -> bool:
        """Delete file from object storage if exists."""
        full_path = os.path.join(settings.UPLOAD_DIR, storage_key)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    @staticmethod
    def generate_signed_token(document_id: uuid.UUID, user_id: uuid.UUID, expires_in_seconds: int = 300) -> Tuple[str, datetime]:
        """
        Generate a secure HMAC-signed JWT token for single-use / short-lived document download access.
        Default expiration is 5 minutes (300 seconds).
        """
        expire_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
        payload = {
            "sub": str(document_id),
            "user_id": str(user_id),
            "type": "signed_document_download",
            "exp": expire_at
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=SIGNED_TOKEN_ALGORITHM)
        return token, expire_at

    @staticmethod
    def verify_signed_token(token: str) -> Dict[str, Any]:
        """
        Verify and decode signed document token.
        Returns payload dict with document_id and user_id if valid.
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[SIGNED_TOKEN_ALGORITHM])
            if payload.get("type") != "signed_document_download":
                raise ValueError("Invalid token scope for document access")
            return payload
        except JWTError as e:
            raise ValueError(f"Signed URL token expired or invalid: {str(e)}")
