import re
import io
import datetime
from typing import Dict, Any, Tuple, Optional
from app.core.logging import logger

# Try importing pypdf for PDF text extraction
try:
    import pypdf
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

# Try importing pytesseract / PIL for OCR
try:
    from PIL import Image
    import pytesseract
    HAS_PYTESSERACT = True
except Exception:
    HAS_PYTESSERACT = False


class OCRService:
    @staticmethod
    def extract_text_from_file(file_bytes: bytes, mime_type: str, file_name: str) -> str:
        """
        Extract raw text from PDF or Image file.
        Uses pypdf for PDFs, PIL/pytesseract for images, and smart fallback parsers.
        """
        extracted_text = ""
        
        # Case 1: PDF files
        if mime_type == "application/pdf" or file_name.lower().endswith(".pdf"):
            if HAS_PYPDF:
                try:
                    pdf_file = io.BytesIO(file_bytes)
                    reader = pypdf.PdfReader(pdf_file)
                    pages_text = []
                    for page in reader.pages:
                        t = page.extract_text()
                        if t:
                            pages_text.append(t)
                    extracted_text = "\n".join(pages_text)
                except Exception as e:
                    logger.warning(f"pypdf extraction failed: {str(e)}")

        # Case 2: Images (PNG / JPG / JPEG)
        elif mime_type in ["image/png", "image/jpeg", "image/jpg"] or any(
            file_name.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg"]
        ):
            if HAS_PYTESSERACT:
                try:
                    image = Image.open(io.BytesIO(file_bytes))
                    extracted_text = pytesseract.image_to_string(image)
                except Exception as e:
                    logger.warning(f"pytesseract OCR extraction failed: {str(e)}")

        # Fallback: Binary string scanning for text representations if standard extraction empty
        if not extracted_text or len(extracted_text.strip()) < 10:
            try:
                # Decodes plain ASCII/UTF-8 strings embedded in byte stream
                clean_chars = [chr(b) if 32 <= b <= 126 or b in (10, 13) else ' ' for b in file_bytes]
                raw_str = "".join(clean_chars)
                # Filter long whitespace
                extracted_text = re.sub(r'\s+', ' ', raw_str)
            except Exception:
                extracted_text = ""

        return extracted_text.strip()

    @staticmethod
    def classify_document(text: str, filename: str) -> Tuple[str, float]:
        """
        Classify document type using heuristic rules, regex, and keyword scores.
        Returns (document_type_code, confidence_score).
        """
        text_upper = text.upper()
        fn_upper = filename.upper()

        scores = {
            "PAN_CARD": 0.0,
            "GST_CERTIFICATE": 0.0,
            "RENT_AGREEMENT": 0.0,
            "FIRE_SAFETY_NOC": 0.0,
            "FSSAI_LICENSE": 0.0,
            "INCORPORATION_CERT": 0.0,
            "ELECTRICITY_BILL": 0.0,
            "POLLUTION_CONSENT": 0.0,
        }

        # Regex patterns
        pan_match = re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', text_upper)
        gstin_match = re.search(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b', text_upper)
        fssai_match = re.search(r'\b[0-9]{14}\b', text_upper)

        if pan_match:
            scores["PAN_CARD"] += 0.6
        if gstin_match:
            scores["GST_CERTIFICATE"] += 0.6

        # Keyword rules
        if "INCOME TAX DEPARTMENT" in text_upper or "PERMANENT ACCOUNT NUMBER" in text_upper or "PAN" in fn_upper:
            scores["PAN_CARD"] += 0.4
        if "GOODS AND SERVICES TAX" in text_upper or "GSTIN" in text_upper or "REGISTRATION CERTIFICATE" in text_upper or "GST" in fn_upper:
            scores["GST_CERTIFICATE"] += 0.4
        if "RENT AGREEMENT" in text_upper or "LEASE DEED" in text_upper or "LESSOR" in text_upper or "LESSEE" in text_upper or "RENT" in fn_upper:
            scores["RENT_AGREEMENT"] += 0.5
        if "FIRE NOC" in text_upper or "FIRE SAFETY" in text_upper or "NO OBJECTION CERTIFICATE" in text_upper or "FIRE" in fn_upper:
            scores["FIRE_SAFETY_NOC"] += 0.5
        if "FSSAI" in text_upper or "FOOD SAFETY" in text_upper or "LICENSE NUMBER" in text_upper or "FOOD" in fn_upper:
            scores["FSSAI_LICENSE"] += 0.5
        if "CERTIFICATE OF INCORPORATION" in text_upper or "REGISTRAR OF COMPANIES" in text_upper or "INC" in fn_upper:
            scores["INCORPORATION_CERT"] += 0.5
        if "ELECTRICITY" in text_upper or "DISCOM" in text_upper or "CONSUMER NUMBER" in text_upper or "BILL" in fn_upper:
            scores["ELECTRICITY_BILL"] += 0.5
        if "CONSENT TO OPERATE" in text_upper or "POLLUTION CONTROL BOARD" in text_upper or "CTO" in text_upper or "AIR ACT" in text_upper:
            scores["POLLUTION_CONSENT"] += 0.5

        # Pick best category
        best_cat = max(scores, key=scores.get)
        confidence = min(scores[best_cat], 0.99)

        if confidence < 0.2:
            # Fallback to filename-based inference if content is ambiguous
            if "PAN" in fn_upper:
                return "PAN_CARD", 0.70
            elif "GST" in fn_upper:
                return "GST_CERTIFICATE", 0.70
            elif "RENT" in fn_upper or "LEASE" in fn_upper:
                return "RENT_AGREEMENT", 0.70
            elif "FIRE" in fn_upper:
                return "FIRE_SAFETY_NOC", 0.70
            elif "FOOD" in fn_upper or "FSSAI" in fn_upper:
                return "FSSAI_LICENSE", 0.70
            elif "INC" in fn_upper or "INCORPORATION" in fn_upper:
                return "INCORPORATION_CERT", 0.70
            return "GENERAL_DOCUMENT", 0.50

        return best_cat, round(confidence, 2)

    @staticmethod
    def extract_metadata(text: str, document_type: str) -> Dict[str, Any]:
        """Extract key structured fields from OCR text based on document category."""
        text_upper = text.upper()
        extracted = {
            "document_number": None,
            "issue_date": None,
            "expiry_date": None,
            "entity_name": None,
            "address": None,
            "raw_text_snippet": text[:300] if text else ""
        }

        # 1. Extract Document Number
        pan_match = re.search(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b', text_upper)
        gstin_match = re.search(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b', text_upper)
        fssai_match = re.search(r'\b[0-9]{14}\b', text_upper)

        if document_type == "PAN_CARD" and pan_match:
            extracted["document_number"] = pan_match.group(0)
        elif document_type == "GST_CERTIFICATE" and gstin_match:
            extracted["document_number"] = gstin_match.group(0)
        elif document_type == "FSSAI_LICENSE" and fssai_match:
            extracted["document_number"] = fssai_match.group(0)
        elif pan_match:
            extracted["document_number"] = pan_match.group(0)
        elif gstin_match:
            extracted["document_number"] = gstin_match.group(0)

        # 2. Extract Dates (DD/MM/YYYY or YYYY-MM-DD or DD Month YYYY)
        dates = re.findall(r'\b\d{2}[/-]\d{2}[/-]\d{4}\b|\b\d{4}[/-]\d{2}[/-]\d{2}\b', text)
        if len(dates) >= 1:
            extracted["issue_date"] = dates[0]
        if len(dates) >= 2:
            extracted["expiry_date"] = dates[1]

        # Check for explicit expiry keywords like "VALID TILL 31/12/2028" or "EXPIRY: 2030-05-15"
        expiry_match = re.search(r'(?:VALID TILL|EXPIRY DATE|EXPIRES ON|VALID UPTO)[\s:]*(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})', text_upper)
        if expiry_match:
            extracted["expiry_date"] = expiry_match.group(1)

        # 3. Extract Name / Entity heuristic
        name_match = re.search(r'(?:NAME|ENTITY|BUSINESS|LEGAL NAME)[\s:]*([A-Z0-9\s.,]{3,50})', text_upper)
        if name_match:
            extracted["entity_name"] = name_match.group(1).strip()

        return extracted

    @staticmethod
    def parse_date_string(date_str: Optional[str]) -> Optional[datetime.datetime]:
        """Convert extracted date string to datetime object."""
        if not date_str:
            return None
        formats = [
            "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d",
            "%d/%m/%y", "%d-%m-%y"
        ]
        for fmt in formats:
            try:
                return datetime.datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        return None

    @classmethod
    def evaluate_verification(
        cls, extracted_data: Dict[str, Any], confidence: float, expiry_dt: Optional[datetime.datetime]
    ) -> Tuple[str, Optional[str]]:
        """
        Determine verification status (AUTO_VERIFIED, EXPIRED, or PENDING) and reason.
        """
        now = datetime.datetime.utcnow()
        if expiry_dt and expiry_dt < now:
            return "EXPIRED", f"Document expired on {expiry_dt.strftime('%Y-%m-%d')}."
        
        if confidence >= 0.70 and extracted_data.get("document_number"):
            doc_no = extracted_data.get("document_number")
            return "AUTO_VERIFIED", f"Automated OCR verified document number: {doc_no} (Confidence: {int(confidence * 100)}%)."

        return "PENDING", "Uploaded successfully. Awaiting manual officer verification."
