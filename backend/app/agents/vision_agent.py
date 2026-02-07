"""
Agent Vision: Gemini-Powered Visual Analysis
Analyzes redacted images for forensic inconsistencies.
"""

import json
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field
from ..gemini_client import gemini_client


VISION_PROMPT = """You are a senior Forensic Document Examiner for a P2P crypto exchange. Your job is to approve or reject transaction receipts with EXTREME SKEPTICISM.

Your Goal: Detect any sign of digital tampering, no matter how subtle.

1. **Analyze the Image Structure:**
   - **Font Consistency:** Are all fonts the same size, weight, and family? (Look for mismatched numbers in amount or time).
   - **Alignment:** Does text "float" or looked pasted on? (Look for misaligned labels vs values).
   - **Artifacts:** visual noise or "halos" around text (signs of copy-paste).
   - **Pixelation:** Is text sharper or blurrier than the background logo?

2. **Verdict Rules:**
   - If ANY text looks edited, different font, or pasted -> **VERDICT: FRAUD**
   - If numbers (Amount/Time) look different from labels -> **VERDICT: FRAUD**
   - If the receipt looks indistinguishable from a genuine banking app screenshot -> **VERDICT: AUTHENTIC**

3. **Respond in JSON:**
{
    "is_suspicious": true/false,
    "confidence": 0.0-1.0 (1.0 = absolute certainty),
    "font_consistency_score": 0-100 (Lower = likely fake),
    "alignment_score": 0-100 (Lower = likely fake),
    "findings": [
        {"issue": "Brief description of defect", "severity": "HIGH/MEDIUM"}
    ],
    "explanation": "Professional forensic conclusion. Be direct."
}

**CRITICAL:** If you are unsure, err on the side of caution and mark as SUSPICIOUS. Better to reject a valid receipt than approve a fake one.
"""


@dataclass
class VisionAgentResult:
    is_suspicious: bool = False
    confidence: float = 0.0
    font_consistency_score: int = 100
    alignment_score: int = 100
    findings: List[dict] = field(default_factory=list)
    explanation: str = ""
    model_used: Optional[str] = None
    flags: List[dict] = field(default_factory=list)
    raw_response: str = ""


class VisionAgent:
    """
    Agent Vision: Uses Gemini Vision to detect visual inconsistencies.
    """
    
    def __init__(self):
        self.name = "Agent Vision"
        self.icon = "[VISION]"
    
    async def analyze(self, image_bytes: bytes, context: Optional[dict] = None) -> VisionAgentResult:
        """
        Send redacted image to Gemini for visual forensic analysis.
        
        Args:
            image_bytes: Redacted image bytes
            context: Optional transaction context (claimed amount, etc.)
            
        Returns:
            VisionAgentResult with Gemini's analysis
        """
        result = VisionAgentResult()
        
        # Build prompt with context if available
        prompt = VISION_PROMPT
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt += f"\n\nCURRENT SYSTEM TIME: {current_time}\n"
        
        if context:
            prompt += f"ADDITIONAL CONTEXT:\n"
            prompt += f"- Claimed Amount: {context.get('claimed_amount', 'Unknown')}\n"
            prompt += f"- Expected Bank: {context.get('expected_bank', 'Unknown')}\n"
            prompt += f"- Transaction Time: {context.get('transaction_time', 'Unknown')}\n"
        
        # Call Gemini with fallback
        gemini_result = await gemini_client.analyze_image(
            prompt=prompt,
            image_bytes=image_bytes,
            mime_type="image/png"
        )
        
        if not gemini_result["success"]:
            result.flags.append({
                "layer": "Vision",
                "severity": "HIGH",
                "description": f"AI analysis failed: {gemini_result['error']}",
                "confidence": 0.0
            })
            result.explanation = "AI analysis could not be completed."
            return result
        
        result.model_used = gemini_result["model_used"]
        result.raw_response = gemini_result["response"]
        
        # Parse the JSON response - Robust JSON extraction
        try:
            # Find the first '{' and last '}'
            start_idx = gemini_result["response"].find('{')
            end_idx = gemini_result["response"].rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = gemini_result["response"][start_idx:end_idx+1]
                analysis = json.loads(json_str)
            else:
                raise ValueError("No JSON object found in response")
        
            result.is_suspicious = analysis.get("is_suspicious", False)
            result.confidence = analysis.get("confidence", 0.5)
            result.font_consistency_score = analysis.get("font_consistency_score", 100)
            result.alignment_score = analysis.get("alignment_score", 100)
            result.explanation = analysis.get("explanation", "")
            
            # Convert findings to flags
            for finding in analysis.get("findings", []):
                result.flags.append({
                    "layer": "Vision",
                    "severity": finding.get("severity", "MEDIUM"),
                    "description": finding.get("issue", "Unknown issue"),
                    "confidence": result.confidence
                })
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback: Treat raw response as explanation but MARK AS FAILED
            print(f"[VISION] JSON Parse Error: {str(e)}")
            print(f"[VISION] Raw Response: {gemini_result['response']}")
            
            result.explanation = "AI Analysis Error: Could not parse response."
            result.flags.append({
                "layer": "Vision",
                "severity": "LOW",
                "description": "Could not parse structured AI response",
                "confidence": 0.3
            })
        
        return result
    
    def get_status_log(self, result: VisionAgentResult) -> List[str]:
        """Generate human-readable log entries for UI display."""
        logs = [
            f"{self.icon} Agent Vision initialized...",
            f"{self.icon} Sending to Gemini ({result.model_used or 'pending'})...",
            f"{self.icon} Analyzing font consistency...",
            f"{self.icon} Checking alignment patterns...",
            f"{self.icon} Scanning for visual artifacts...",
        ]
        
        if result.is_suspicious:
            logs.append(f"{self.icon} [!] SUSPICIOUS PATTERNS DETECTED")
        else:
            logs.append(f"{self.icon} [OK] No obvious forgery indicators")
        
        return logs
