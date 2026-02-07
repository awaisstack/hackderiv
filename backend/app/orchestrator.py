"""
Orchestrator: Coordinates the multi-agent forensic pipeline.
Runs Agent Meta → Agent Privacy → Agent Vision in sequence.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from .agents import MetaAgent, PrivacyAgent, VisionAgent
from .schemas import AnalysisResult, ForensicFlag, TransactionContext


@dataclass
class AgentStatus:
    name: str
    icon: str
    status: str  # "pending", "running", "complete", "error"
    logs: List[str] = field(default_factory=list)


@dataclass
class OrchestratorResult:
    analysis: AnalysisResult
    agent_statuses: List[AgentStatus]
    all_logs: List[str]


class Orchestrator:
    """
    Runs the three-agent forensic pipeline and aggregates results.
    """
    
    def __init__(self):
        self.meta_agent = MetaAgent()
        self.privacy_agent = PrivacyAgent()
        self.vision_agent = VisionAgent()
    
    async def analyze(
        self,
        image_bytes: bytes,
        context: TransactionContext
    ) -> OrchestratorResult:
        """
        Run the full forensic pipeline.
        
        Args:
            image_bytes: Raw uploaded image
            context: Transaction context (claimed amount, bank, etc.)
            
        Returns:
            OrchestratorResult with final risk score and all agent outputs
        """
        all_flags: List[ForensicFlag] = []
        all_logs: List[str] = []
        agent_statuses: List[AgentStatus] = []
        
        # ===== STAGE 1: Agent Meta =====
        meta_status = AgentStatus(
            name=self.meta_agent.name,
            icon=self.meta_agent.icon,
            status="running"
        )
        
        meta_result = self.meta_agent.analyze(image_bytes)
        meta_status.status = "complete"
        meta_status.logs = self.meta_agent.get_status_log(meta_result)
        agent_statuses.append(meta_status)
        all_logs.extend(meta_status.logs)
        
        # Convert meta flags
        for flag in meta_result.flags:
            all_flags.append(ForensicFlag(**flag))
        
        # ===== STAGE 2: Agent Privacy =====
        privacy_status = AgentStatus(
            name=self.privacy_agent.name,
            icon=self.privacy_agent.icon,
            status="running"
        )
        
        privacy_result = self.privacy_agent.analyze(image_bytes)
        privacy_status.status = "complete"
        privacy_status.logs = self.privacy_agent.get_status_log(privacy_result)
        agent_statuses.append(privacy_status)
        all_logs.extend(privacy_status.logs)
        
        for flag in privacy_result.flags:
            all_flags.append(ForensicFlag(**flag))
        
        # ===== STAGE 3: Agent Vision =====
        vision_status = AgentStatus(
            name=self.vision_agent.name,
            icon=self.vision_agent.icon,
            status="running"
        )
        
        # Use redacted image for vision analysis
        vision_image = privacy_result.redacted_image_bytes or image_bytes
        vision_context = {
            "claimed_amount": context.claimed_amount,
            "expected_bank": context.expected_bank.value,
            "transaction_time": context.transaction_time
        }
        
        vision_result = await self.vision_agent.analyze(vision_image, vision_context)
        vision_status.status = "complete"
        vision_status.logs = self.vision_agent.get_status_log(vision_result)
        agent_statuses.append(vision_status)
        all_logs.extend(vision_status.logs)
        
        for flag in vision_result.flags:
            all_flags.append(ForensicFlag(**flag))
        
        # ===== RISK SCORING =====
        risk_score = self._calculate_risk_score(
            meta_result=meta_result,
            privacy_result=privacy_result,
            vision_result=vision_result,
            context=context
        )
        
        verdict = self._get_verdict(risk_score)
        
        # Amount match check
        amount_match = True
        if privacy_result.amount_detected:
            try:
                detected = float(privacy_result.amount_detected)
                claimed = float(context.claimed_amount)
                amount_match = abs(detected - claimed) < 1.0  # Allow $1 tolerance
            except (ValueError, TypeError):
                amount_match = True  # Can't verify, assume match
        
        # Build final result
        analysis = AnalysisResult(
            risk_score=risk_score,
            verdict=verdict,
            flags=all_flags,
            software_detected=meta_result.software_detected,
            hardware_detected=meta_result.hardware_detected,
            is_edited=meta_result.is_edited,
            amount_match=amount_match,
            date_match=True,  # TODO: Implement date logic
            font_consistency_score=vision_result.font_consistency_score,
            alignment_score=vision_result.alignment_score,
            explanation=vision_result.explanation or "Analysis complete."
        )
        
        return OrchestratorResult(
            analysis=analysis,
            agent_statuses=agent_statuses,
            all_logs=all_logs
        )
    
    def _calculate_risk_score(
        self,
        meta_result,
        privacy_result,
        vision_result,
        context
    ) -> int:
        """
        Calculate overall risk score (0-100).
        
        Scoring V2 (Stricter):
        - Base: 0
        - Editing software detected: +100 (Immediate Fail)
        - Vision flagged suspicious: +50
        - Non-receipt detected (0% scores): +100 (Immediate Fail)
        - Amount mismatch: +30
        - Font/Alignment issues: +20 each
        - Each HIGH severity flag: +20 (No Cap)
        """
        score = 0
        
        # 1. Critical Failures (Immediate 100)
        if meta_result.is_edited:
            return 100
            
        # If forensic scores are near zero, it's either not a receipt or completely unreadable
        if vision_result.font_consistency_score < 10 and vision_result.alignment_score < 10:
            return 100

        if vision_result.is_suspicious and vision_result.font_consistency_score == 0:
            return 100
        
        # 2. Vision Signals
        if vision_result.is_suspicious:
            score += 50
        
        # 3. Amount Mismatch
        if privacy_result.amount_detected:
            try:
                detected = float(privacy_result.amount_detected)
                claimed = float(context.claimed_amount)
                if abs(detected - claimed) > 1.0:
                    score += 30
            except (ValueError, TypeError):
                pass
        
        # 4. Forensic Signals
        if vision_result.font_consistency_score < 80:
            score += 20
        if vision_result.alignment_score < 80:
            score += 20
        
        # 5. Severity Accumulator (No Cap)
        high_flags = sum(
            1 for f in vision_result.flags
            if f.get("severity") == "HIGH"
        )
        score += (high_flags * 20)
        
        return min(score, 100)  # Cap at 100
    
    def _get_verdict(self, score: int) -> str:
        """Determine verdict based on risk score."""
        if score <= 20:
            return "APPROVE"
        elif score <= 75:
            return "REVIEW"
        else:
            return "REJECT"
