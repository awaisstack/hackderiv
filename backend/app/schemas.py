from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class BankProvider(str, Enum):
    JAZZCASH = "jazzcash"
    EASYPAISA = "easypaisa"
    SADAPAY = "sadapay"
    NAYAPAY = "nayapay"
    UNKNOWN = "unknown"

class TransactionContext(BaseModel):
    claimed_amount: float
    claimed_sender: Optional[str] = None
    transaction_time: Optional[str] = None
    expected_bank: BankProvider

class ForensicFlag(BaseModel):
    layer: str = Field(..., description="Layer detecting error (Metadata, OCR, Visual)")
    severity: str = Field(..., description="HIGH, MEDIUM, LOW")
    description: str
    confidence: float

class AnalysisResult(BaseModel):
    risk_score: int = Field(..., ge=0, le=100)
    verdict: str = Field(..., description="APPROVE, REVIEW, REJECT")
    flags: List[ForensicFlag]
    
    # Metadata Details
    software_detected: Optional[str] = None
    hardware_detected: Optional[str] = None
    is_edited: bool = False
    
    # Visual Analysis Details
    amount_match: bool
    date_match: bool
    font_consistency_score: int
    alignment_score: int
    
    # Reasoning
    explanation: str
