"""
Agent Meta: Metadata Forensics
Extracts and analyzes EXIF data from images to detect editing software.
"""

from PIL import Image
from PIL.ExifTags import TAGS
from io import BytesIO
from typing import Optional
from dataclasses import dataclass, field
from typing import List

# Known editing software signatures
EDITING_SOFTWARE = [
    "photoshop", "gimp", "canva", "pixlr", "snapseed",
    "lightroom", "affinity", "paint.net", "pixelmator",
    "adobe", "edit", "modified"
]

@dataclass
class MetaAgentResult:
    is_edited: bool = False
    software_detected: Optional[str] = None
    hardware_detected: Optional[str] = None
    flags: List[dict] = field(default_factory=list)
    raw_exif: dict = field(default_factory=dict)


class MetaAgent:
    """
    Agent Meta: Analyzes image metadata for signs of tampering.
    """
    
    def __init__(self):
        self.name = "Agent Meta"
        self.icon = "[META]"
    
    def analyze(self, image_bytes: bytes) -> MetaAgentResult:
        """
        Extract and analyze EXIF metadata from image.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            MetaAgentResult with findings
        """
        result = MetaAgentResult()
        
        try:
            image = Image.open(BytesIO(image_bytes))
            exif_data = image._getexif()
            
            if exif_data is None:
                # No EXIF is common for screenshots or web images
                result.flags.append({
                    "layer": "Metadata",
                    "severity": "LOW",
                    "description": "No EXIF data (Common in screenshots/digital wallets)",
                    "confidence": 0.5
                })
                return result
            
            # Parse EXIF tags
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                result.raw_exif[tag_name] = str(value)
                
                # Check for Software tag
                if tag_name == "Software":
                    software_str = str(value).lower()
                    result.software_detected = value
                    
                    for editor in EDITING_SOFTWARE:
                        if editor in software_str:
                            result.is_edited = True
                            result.flags.append({
                                "layer": "Metadata",
                                "severity": "HIGH",
                                "description": f"Editing software detected: {value}",
                                "confidence": 0.95
                            })
                            break
                
                # Check for Make/Model (device info)
                if tag_name == "Make":
                    result.hardware_detected = str(value)
                if tag_name == "Model" and result.hardware_detected:
                    result.hardware_detected += f" {value}"
            
            # Additional check: ImageDescription often contains editing traces
            if "ImageDescription" in result.raw_exif:
                desc = result.raw_exif["ImageDescription"].lower()
                for editor in EDITING_SOFTWARE:
                    if editor in desc:
                        result.is_edited = True
                        result.flags.append({
                            "layer": "Metadata",
                            "severity": "MEDIUM",
                            "description": f"Editing trace in ImageDescription",
                            "confidence": 0.7
                        })
                        break
            
        except Exception as e:
            result.flags.append({
                "layer": "Metadata",
                "severity": "LOW",
                "description": f"Could not parse image metadata: {str(e)}",
                "confidence": 0.2
            })
        
        return result
    
    def get_status_log(self, result: MetaAgentResult) -> List[str]:
        """Generate human-readable log entries for UI display."""
        logs = [
            f"{self.icon} Agent Meta initialized...",
            f"{self.icon} Extracting EXIF metadata...",
        ]
        
        if result.software_detected:
            logs.append(f"{self.icon} Software tag found: {result.software_detected}")
        if result.hardware_detected:
            logs.append(f"{self.icon} Device: {result.hardware_detected}")
        if result.is_edited:
            logs.append(f"{self.icon} [!] EDITING SOFTWARE DETECTED")
        else:
            logs.append(f"{self.icon} [OK] No obvious editing markers")
        
        return logs
