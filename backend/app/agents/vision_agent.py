"""
Agent Vision: Gemini-Powered Visual Analysis
Analyzes redacted images for forensic inconsistencies.
"""

import json
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field
from ..gemini_client import gemini_client


VISION_PROMPT = """You are a senior Security Officer for a P2P crypto exchange. Your job is to approve or reject transaction receipts.

BE CONCISE. DO NOT EXPLAIN "AS SUCH". BE DECISIVE.

1. **If the image is a valid receipt:**
   - Verify: consistent fonts, proper alignment, no pixelation around text.
   - Verdict: "Authentic Document."

2. **If the image is FAKE/EDITED:**
   - Spot: Mismatched fonts, blurry text edges, impossible dates.
   - Verdict: "Fraud Detected: [Specific Reason]."

3. **If the image is IRRELEVANT (Partially or completely):**
   - Example: A selfie, a car, a landscape.
   - Verdict: "Invalid Document: Uploaded file is not a banking transaction receipt."

Respond in this exact JSON format:
{
    "is_suspicious": true/false,
    "confidence": 0.0-1.0,
    "font_consistency_score": 0-100,
    "alignment_score": 0-100,
    "findings": [
        {"issue": "Short, punchy description of defect", "severity": "HIGH/MEDIUM/LOW"}
    ],
    "explanation": "Security Officer's Conclusion. Max 2 sentences. Direct and professional."
}
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
        
        # Parse the JSON response
        try:
            # Try to extract JSON from the response
            response_text = gemini_result["response"]
            
            # Handle markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            analysis = json.loads(response_text.strip())
            
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
            
        except json.JSONDecodeError as e:
            # Fallback: Treat raw response as explanation
            result.explanation = gemini_result["response"][:500]
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
