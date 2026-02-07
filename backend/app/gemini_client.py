"""
Gemini API Client with Model Fallback Strategy
Priority: gemini-3-pro-preview → gemini-3-flash-preview → gemini-2.5-flash
"""

import os
from pathlib import Path
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError
from typing import Optional
from dotenv import load_dotenv

# Load .env from backend directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Model priority chain (Newest -> Oldest)
# Gemini 3 first, then 2.5, then 2.0, then 1.5 as fallback
MODEL_PRIORITY = [
    "gemini-3-flash-preview",  # Newest Flash
    "gemini-3-pro-preview",    # Newest Pro
    "gemini-2.5-flash",        # 2.5 Flash
    "gemini-2.5-flash-lite",   # 2.5 Lite
    "gemini-2.0-flash",        # 2.0 Flash
    "gemini-1.5-pro",          # 1.5 Pro (Last Resort)
    "gemini-1.5-flash",        # 1.5 Flash (Last Resort)
]

class GeminiClient:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("[!] CRITICAL: GEMINI_API_KEY not found in environment! AI analysis will be SIMULATED (always returns Risk 0).")
            self.api_key = None
        else:
            print(f"[OK] GEMINI_API_KEY found (ends with ...{api_key[-4:]})")
            self.api_key = api_key
            genai.configure(api_key=api_key)
        
        self._initialized = True
    
    def _get_model(self, model_name: str):
        """Initialize a Gemini model instance."""
        return genai.GenerativeModel(model_name)
    
    async def analyze_image(
        self,
        prompt: str,
        image_bytes: bytes,
        mime_type: str = "image/png"
    ) -> dict:
        """
        Send image + prompt to Gemini with automatic fallback on rate limit.
        """
        if not self.api_key:
            # Simulated response for demo without API key
            return {
                "success": True,
                "model_used": "simulated",
                "response": '''{
                    "is_suspicious": false,
                    "confidence": 0.7,
                    "font_consistency_score": 85,
                    "alignment_score": 90,
                    "findings": [],
                    "explanation": "This is a simulated analysis. Configure GEMINI_API_KEY for real AI analysis."
                }''',
                "error": None
            }
        
        image_part = {
            "mime_type": mime_type,
            "data": image_bytes
        }
        
        last_error = None
        
        for model_name in MODEL_PRIORITY:
            try:
                print(f"[AI] Trying model: {model_name}...")
                model = self._get_model(model_name)
                response = model.generate_content(
                    [prompt, image_part],
                    generation_config={
                        "temperature": 0.2,
                        "max_output_tokens": 2048,
                    }
                )
                
                print(f"[OK] Success with {model_name}")
                return {
                    "success": True,
                    "model_used": model_name,
                    "response": response.text,
                    "error": None
                }
                
            except ResourceExhausted as e:
                print(f"[!] Rate limit hit on {model_name}, trying next...")
                last_error = str(e)
                continue
                
            except GoogleAPIError as e:
                print(f"[X] API error on {model_name}: {e}")
                last_error = str(e)
                continue
            
            except Exception as e:
                print(f"[X] Unexpected error on {model_name}: {e}")
                last_error = str(e)
                continue
        
        # All models failed
        return {
            "success": False,
            "model_used": None,
            "response": None,
            "error": f"All models failed. Last error: {last_error}"
        }
    
    async def analyze_text(self, prompt: str) -> dict:
        """Text-only analysis with fallback."""
        if not self.api_key:
            return {
                "success": True,
                "model_used": "simulated",
                "response": "Simulated text analysis response.",
                "error": None
            }
        
        last_error = None
        
        for model_name in MODEL_PRIORITY:
            try:
                model = self._get_model(model_name)
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.1,
                        "max_output_tokens": 1024,
                    }
                )
                
                return {
                    "success": True,
                    "model_used": model_name,
                    "response": response.text,
                    "error": None
                }
                
            except ResourceExhausted:
                print(f"[!] Rate limit hit on {model_name}, trying next...")
                continue
                
            except GoogleAPIError as e:
                last_error = str(e)
                continue
        
        return {
            "success": False,
            "model_used": None,
            "response": None,
            "error": f"All models failed. Last error: {last_error}"
        }


# Lazy singleton
gemini_client = GeminiClient()
