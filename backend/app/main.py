"""
Deriv P2P Sentinel - FastAPI Backend
AI-Powered Receipt Fraud Detection
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import base64
import os

from .schemas import TransactionContext, BankProvider, AnalysisResult
from .orchestrator import Orchestrator

load_dotenv()

app = FastAPI(
    title="Deriv P2P Sentinel",
    description="AI-Powered Receipt Fraud Detection for P2P Trading",
    version="1.0.0",
    # Vercel Serverless environment detection
    # AWS_LAMBDA_FUNCTION_NAME is present in Vercel System Env
    root_path="/api/py" if (os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")) else ""
)

# CORS setup for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = Orchestrator()


@app.api_route("/", methods=["GET", "POST"])
async def health_check(request: Request):
    """
    Health check & Debug endpoint.
    Accepts POST to catch 405 errors caused by path stripping.
    """
    return {
        "status": "online",
        "service": "Deriv P2P Sentinel",
        "version": "1.0.0",
        "agents": ["Agent Meta", "Agent Privacy", "Agent Vision"],
        "debug": {
            "received_method": request.method,
            "received_path": request.url.path,
            "raw_path": request.scope.get("path"),
            "root_path": request.scope.get("root_path"),
            "full_scope_path": request.scope.get("path")
        }
    }


@app.post("/scan", response_model=dict)
async def scan_receipt(
    image: UploadFile = File(...),
    claimed_amount: float = Form(...),
    expected_bank: str = Form("unknown"),
    claimed_sender: str = Form(None),
    transaction_time: str = Form(None)
):
    """
    Analyze a P2P receipt image for fraud indicators.
    
    Args:
        image: The receipt image (PNG, JPG)
        claimed_amount: The amount the buyer claims to have sent
        expected_bank: The expected bank/wallet (jazzcash, easypaisa, sadapay, nayapay)
        claimed_sender: Optional sender name
        transaction_time: Optional ISO timestamp of claimed transaction
    
    Returns:
        Analysis result with risk score, verdict, and forensic flags
    """
    # Supported image formats
    SUPPORTED_FORMATS = [
        "image/png", 
        "image/jpeg", 
        "image/jpg",
        "image/webp",
        "image/gif",
        "image/bmp",
        "image/tiff",
        "image/heic",
        "image/heif"
    ]
    
    # Validate file type
    if image.content_type not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{image.content_type}'. Supported: PNG, JPEG, WebP, GIF, BMP, TIFF, HEIC"
        )
    
    # Read image bytes
    image_bytes = await image.read()
    
    if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(
            status_code=400,
            detail="Image too large. Maximum size is 10MB."
        )
    
    # Parse bank provider
    try:
        bank = BankProvider(expected_bank.lower())
    except ValueError:
        bank = BankProvider.UNKNOWN
    
    # Build context
    context = TransactionContext(
        claimed_amount=claimed_amount,
        claimed_sender=claimed_sender,
        transaction_time=transaction_time,
        expected_bank=bank
    )
    
    # Run the multi-agent pipeline
    try:
        result = await orchestrator.analyze(image_bytes, context)
        
        return {
            "success": True,
            "analysis": result.analysis.model_dump(),
            "agents": [
                {
                    "name": status.name,
                    "icon": status.icon,
                    "status": status.status,
                    "logs": status.logs
                }
                for status in result.agent_statuses
            ],
            "logs": result.all_logs
        }
        
    except Exception as e:
        import traceback
        print(f"ERROR ANALYZING RECEIPT: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@app.post("/scan/base64", response_model=dict)
async def scan_receipt_base64(
    image_base64: str = Form(...),
    claimed_amount: float = Form(...),
    expected_bank: str = Form("unknown"),
    claimed_sender: str = Form(None),
    transaction_time: str = Form(None)
):
    """
    Alternative endpoint accepting base64-encoded image.
    Useful for frontend integrations.
    """
    try:
        # Decode base64
        if "base64," in image_base64:
            image_base64 = image_base64.split("base64,")[1]
        
        image_bytes = base64.b64decode(image_base64)
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid base64 image: {str(e)}"
        )
    
    # Parse bank provider
    try:
        bank = BankProvider(expected_bank.lower())
    except ValueError:
        bank = BankProvider.UNKNOWN
    
    context = TransactionContext(
        claimed_amount=claimed_amount,
        claimed_sender=claimed_sender,
        transaction_time=transaction_time,
        expected_bank=bank
    )
    
    try:
        result = await orchestrator.analyze(image_bytes, context)
        
        return {
            "success": True,
            "analysis": result.analysis.model_dump(),
            "agents": [
                {
                    "name": status.name,
                    "icon": status.icon,
                    "status": status.status,
                    "logs": status.logs
                }
                for status in result.agent_statuses
            ],
            "logs": result.all_logs
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request

# ... (rest of imports)

# ... (at the end of file, before if __name__ == "__main__":)

@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def catch_all(request: Request, path_name: str):
    """
    Debug endpoint to catch path mismatches.
    """
    return {
        "status": "debug_catch_all",
        "message": "Route not found in standard routes, caught by fallback.",
        "received_method": request.method,
        "received_path": request.url.path,
        "raw_path": request.scope.get("path"),
        "root_path": request.scope.get("root_path"),
        "path_param": path_name
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
