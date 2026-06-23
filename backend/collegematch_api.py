import os
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database import supabase
from google import genai
from google.genai import types
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
if not ENV_PATH.exists():
    ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

router = APIRouter(prefix="/api", tags=["CollegeMatch"])

# Input validation schema
class CollegeMatchRequest(BaseModel):
    full_name: str
    whatsapp_number: str
    email: str
    stream: str
    exams: List[str]
    board_percentage: int
    budget_per_year: int
    scholarship_reservation: str
    career_goal: str
    preferred_locations: List[str]
    college_priority: List[str]
    living_preference: str
    pressure_handling: str
    biggest_fear: str
    target_colleges: Optional[str] = None
    decision_maker: str

# Enforcement schema for Gemini's response structure
class CollegeData(BaseModel):
    name: str
    location: str
    type: str
    fee: str
    placement_rate: str
    match_score: int
    tags: List[str]
    description: str

class CollegeMatchResponse(BaseModel):
    status: str
    matches_found: int
    data: List[CollegeData]

def get_gemini_client() -> genai.Client:
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key is missing. Set GEMINI_API_KEY in eduronix-landing/.env.",
        )
    return genai.Client(api_key=api_key)

@router.post("/college-match")
async def process_college_match(payload: CollegeMatchRequest):
    try:
        client = get_gemini_client()

        # 1. Log incoming data to Supabase
        lead_data = payload.dict()
        supabase.table("college_match_leads").insert(lead_data).execute()

        # 2. Setup System Guidelines
        system_instruction = (
            "You are the Eduronix AI College Predictor. Analyze the student's profile "
            "and suggest the top 5 engineering or mainstream colleges in India that match their "
            "stream, budget, and location preferences. Provide a realistic match_score (0-100) and "
            "write an empathetic explanation for each college mapping to their goals. "
            "Set 'status' to 'success' and 'matches_found' to 5."
        )
        
        user_profile = f"Analyze this student profile: {json.dumps(lead_data)}"

        # 3. Call the API
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_profile,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=CollegeMatchResponse,
            ),
        )

        return json.loads(response.text) 

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}") 
