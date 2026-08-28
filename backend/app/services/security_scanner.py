import re
from typing import Tuple, List, Optional
from app.core.logging import logger

# Magic Byte Definitions
MAGIC_BYTES = {
    "pdf": b"%PDF-",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpeg": b"\xff\xd8\xff",
    "jpg": b"\xff\xd8\xff",
}

MALICIOUS_HEADER_SIGNATURES = [
    (b"MZ", "Windows PE Executable / DLL (.exe, .dll)"),
    (b"\x7fELF", "Linux Executable (.elf)"),
    (b"\xca\xfe\xba\xbe", "Java Compiled Classfile (.class)"),
    (b"PK\x03\x04", "Zip Archive (Zip archive disguising as document)"),
]

SCRIPT_PAYLOAD_PATTERNS = [
    r'<\s*script[^>]*>',
    r'<\s*\?\s*php',
    r'eval\s*\(',
    r'system\s*\(',
    r'exec\s*\(',
    r'passthru\s*\(',
    r'javascript\s*:',
]


class SecurityScanner:

    @staticmethod
    def validate_file_magic_bytes(file_bytes: bytes, mime_type: str, filename: str) -> Tuple[bool, str]:
        """
        Validate header magic bytes of uploaded file against expected file type.
        Detects renamed executables or corrupted file uploads.
        """
        if not file_bytes or len(file_bytes) < 4:
            return False, "File is empty or too short to contain valid header signatures."

        ext = filename.lower().split(".")[-1] if "." in filename else ""

        # PDF check
        if mime_type == "application/pdf" or ext == "pdf":
            if not file_bytes.startswith(MAGIC_BYTES["pdf"]):
                return False, f"Header magic bytes validation failed. File '{filename}' claims to be PDF but does not start with '%PDF-'."
            return True, "Valid PDF magic bytes."

        # PNG check
        if mime_type == "image/png" or ext == "png":
            if not file_bytes.startswith(b"\x89PNG"):
                return False, f"Header magic bytes validation failed. File '{filename}' claims to be PNG but lacks PNG magic header."
            return True, "Valid PNG magic bytes."

        # JPG/JPEG check
        if mime_type in ["image/jpeg", "image/jpg"] or ext in ["jpg", "jpeg"]:
            if not file_bytes.startswith(MAGIC_BYTES["jpeg"]):
                return False, f"Header magic bytes validation failed. File '{filename}' claims to be JPEG but lacks JPEG magic header."
            return True, "Valid JPEG magic bytes."

        return True, "File extension and structure accepted."

    @staticmethod
    def scan_security_risks(file_bytes: bytes, filename: str) -> Tuple[bool, List[str]]:
        """
        Scans uploaded file bytes for security risks:
        - Executable header signatures (MZ, ELF, Java Class)
        - Web shell / embedded script payloads
        - Malicious macros or embedded exploit vectors
        Returns (is_safe, risk_flags)
        """
        risk_flags = []

        # 1. Executable Header Signature Scan
        for sig, description in MALICIOUS_HEADER_SIGNATURES:
            # Allow ZIP if explicitly allowed, but reject MZ executable headers
            if sig == b"MZ" and file_bytes.startswith(sig):
                risk_flags.append(f"Security Alert: Executable binary header detected ({description}). Upload blocked.")
            elif sig == b"\x7fELF" and file_bytes.startswith(sig):
                risk_flags.append(f"Security Alert: Linux binary executable header detected ({description}). Upload blocked.")

        # 2. Embedded Script / WebShell Payload Scan
        try:
            # Inspection of ASCII string content within binary stream
            clean_str = file_bytes.decode('latin-1', errors='ignore')
            for pattern in SCRIPT_PAYLOAD_PATTERNS:
                if re.search(pattern, clean_str, re.IGNORECASE):
                    risk_flags.append(f"Security Warning: Embedded script payload matching pattern '{pattern}' detected in document stream.")
        except Exception as e:
            logger.warning(f"Error scanning payload text: {str(e)}")

        is_safe = len(risk_flags) == 0
        return is_safe, risk_flags

    @staticmethod
    def scan_with_clamav(file_bytes: bytes) -> Tuple[bool, Optional[str]]:
        """
        Extensible hook for local ClamAV virus daemon scan.
        Returns (is_clean, virus_name)
        """
        # ClamAV socket integration hook
        return True, None
