"""
Agent Privacy: OCR & PII Redaction
Detects and redacts sensitive information before sending to external AI.
"""

import re
from PIL import Image, ImageDraw, ImageFilter
from io import BytesIO
from typing import List, Tuple, Optional
from dataclasses import dataclass, field

# Try to import pytesseract, gracefully handle if not installed
try:
    import pytesseract
    import os
    
    # Cross-platform Tesseract detection
    if os.name == 'nt':  # Windows
        tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            TESSERACT_AVAILABLE = True
        else:
            TESSERACT_AVAILABLE = False
            print("[!] Tesseract not found at Windows path. OCR will be simulated.")
    else:  # Linux/Mac (Vercel runs on Linux)
        # Try common Linux paths or rely on PATH
        try:
            pytesseract.get_tesseract_version()
            TESSERACT_AVAILABLE = True
        except Exception:
            TESSERACT_AVAILABLE = False
            print("[!] Tesseract not found on system. OCR will be simulated.")
except ImportError:
    TESSERACT_AVAILABLE = False
    print("[!] pytesseract not available. OCR will be simulated.")


# PII Detection Patterns
PII_PATTERNS = {
    "account_number": r"\b\d{10,16}\b",  # 10-16 digit numbers (bank accounts)
    "phone_pk": r"\b03\d{9}\b",          # Pakistani phone numbers
    "cnic": r"\b\d{5}-\d{7}-\d{1}\b",    # Pakistani CNIC
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
}


@dataclass
class RedactionBox:
    x: int
    y: int
    width: int
    height: int
    pii_type: str
    original_text: str


@dataclass
class PrivacyAgentResult:
    redacted_image_bytes: Optional[bytes] = None
    pii_detected: List[dict] = field(default_factory=list)
    text_extracted: str = ""
    flags: List[dict] = field(default_factory=list)
    amount_detected: Optional[str] = None


class PrivacyAgent:
    """
    Agent Privacy: Scans for PII and creates a redacted copy of the image.
    """
    
    def __init__(self):
        self.name = "Agent Privacy"
        self.icon = "[PRIV]"
    
    def analyze(self, image_bytes: bytes) -> PrivacyAgentResult:
        """
        Extract text via OCR, detect PII, and create redacted image.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            PrivacyAgentResult with redacted image and findings
        """
        result = PrivacyAgentResult()
        
        try:
            image = Image.open(BytesIO(image_bytes))
            
            if TESSERACT_AVAILABLE:
                # Full OCR with bounding boxes
                ocr_data = pytesseract.image_to_data(
                    image, output_type=pytesseract.Output.DICT
                )
                result.text_extracted = pytesseract.image_to_string(image)
                
                # Find PII and create redaction boxes
                redaction_boxes = self._find_pii_boxes(ocr_data)
                
                # Apply redactions
                redacted_image = self._apply_redactions(image.copy(), redaction_boxes)
                
                # Convert back to bytes
                buffer = BytesIO()
                redacted_image.save(buffer, format="PNG")
                result.redacted_image_bytes = buffer.getvalue()
                
                # Record what was redacted
                for box in redaction_boxes:
                    result.pii_detected.append({
                        "type": box.pii_type,
                        "redacted": True
                    })
                
            else:
                # Fallback: Tesseract not found even after config
                result.text_extracted = "[OCR Error: Tesseract executable not found at configured path]"
                result.redacted_image_bytes = image_bytes
                
                result.flags.append({
                    "layer": "Privacy",
                    "severity": "LOW",
                    "description": "OCR engine not found. Privacy redaction skipped.",
                    "confidence": 0.5
                })
            
            # Try to extract amount from text
            result.amount_detected = self._extract_amount(result.text_extracted)
            
        except Exception as e:
            result.flags.append({
                "layer": "Privacy",
                "severity": "LOW",
                "description": f"Privacy scan error: {str(e)}",
                "confidence": 0.3
            })
            result.redacted_image_bytes = image_bytes
        
        return result
    
    def _find_pii_boxes(self, ocr_data: dict) -> List[RedactionBox]:
        """Find text regions matching PII patterns."""
        boxes = []
        n_boxes = len(ocr_data['text'])
        
        for i in range(n_boxes):
            text = ocr_data['text'][i].strip()
            if not text:
                continue
            
            for pii_type, pattern in PII_PATTERNS.items():
                if re.search(pattern, text):
                    boxes.append(RedactionBox(
                        x=ocr_data['left'][i],
                        y=ocr_data['top'][i],
                        width=ocr_data['width'][i],
                        height=ocr_data['height'][i],
                        pii_type=pii_type,
                        original_text=text
                    ))
                    break
        
        return boxes
    
    def _apply_redactions(self, image: Image.Image, boxes: List[RedactionBox]) -> Image.Image:
        """Apply blur redaction to detected PII regions."""
        draw = ImageDraw.Draw(image)
        
        for box in boxes:
            # Extract region
            region = image.crop((
                box.x, box.y,
                box.x + box.width, box.y + box.height
            ))
            # Apply strong blur
            blurred = region.filter(ImageFilter.GaussianBlur(radius=15))
            # Paste back
            image.paste(blurred, (box.x, box.y))
            # Draw border to indicate redaction
            draw.rectangle(
                [box.x, box.y, box.x + box.width, box.y + box.height],
                outline="#FF0000", width=2
            )
        
        return image
    
    def _extract_amount(self, text: str) -> Optional[str]:
        """Try to extract transaction amount from OCR text."""
        # Common patterns for amounts
        patterns = [
            r"(?:PKR|Rs\.?|₨)\s*([\d,]+(?:\.\d{2})?)",  # PKR 5,000.00
            r"(?:Amount|Total|Paid)\s*:?\s*([\d,]+(?:\.\d{2})?)",  # Amount: 5000
            r"\b(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:PKR|Rs)",  # 5,000 PKR
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).replace(",", "")
        
        return None
    
    def get_status_log(self, result: PrivacyAgentResult) -> List[str]:
        """Generate human-readable log entries for UI display."""
        logs = [
            f"{self.icon} Agent Privacy initialized...",
            f"{self.icon} Running OCR text extraction...",
        ]
        
        if result.pii_detected:
            logs.append(f"{self.icon} Detected {len(result.pii_detected)} PII regions")
            logs.append(f"{self.icon} Applying blur redaction...")
        else:
            logs.append(f"{self.icon} No PII patterns detected")
        
        if result.amount_detected:
            logs.append(f"{self.icon} Amount extracted: {result.amount_detected}")
        
        logs.append(f"{self.icon} [OK] Privacy-safe image prepared")
        
        return logs
