import os
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database import supabase
from groq import Groq
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
    exam_scores: dict = {}
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

# Enforcement schema for Groq's response structure
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

def get_groq_client() -> Groq:
    api_key = (os.getenv("GROQ_API_KEY") or "").strip().strip('"').strip("'")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Groq API key is missing. Set GROQ_API_KEY in backend/.env.",
        )
    return Groq(api_key=api_key)

@router.get("/college-match/check-email")
async def check_email(email: str):
    try:
        existing = supabase.table("college_match_leads").select("id").ilike("email", email.strip()).execute()
        if existing.data and len(existing.data) >= 2:
            return {"exists": True}
        return {"exists": False}
    except Exception as db_err:
        print("Database check failed:", db_err)
        return {"exists": False}

@router.post("/college-match")
async def process_college_match(payload: CollegeMatchRequest):
    try:
        # Check if user has already taken the test (limit 2 per user email)
        try:
            existing = supabase.table("college_match_leads").select("id").ilike("email", payload.email.strip()).execute()
            if existing.data and len(existing.data) >= 2:
                raise HTTPException(
                    status_code=400,
                    detail="You have already taken the college match test 2 times. Limit is two tests per user."
                )
        except HTTPException:
            raise
        except Exception as db_err:
            print("Database check failed:", db_err)

        client = get_groq_client()

        # 1. Log incoming data to Supabase (cleaning up exam_scores to match schema)
        lead_data = payload.model_dump()
        db_data = lead_data.copy()
        db_data.pop("exam_scores", None)

        if payload.exam_scores:
            formatted_exams = []
            for exam in payload.exams:
                score = payload.exam_scores.get(exam)
                if score:
                    formatted_exams.append(f"{exam} ({score})")
                else:
                    formatted_exams.append(exam)
            db_data["exams"] = formatted_exams

        supabase.table("college_match_leads").insert(db_data).execute()

        # 2. Setup System Prompt & Schema Description
        system_instruction = (
            "You are the Eduronix AI College Predictor. Analyze the student's profile "
            "and suggest the top 5 engineering or mainstream colleges in India that match their "
            "stream, budget, location preferences, and entrance exam scores/percentiles (e.g. JEE, MHT-CET, NEET, CAT, CLAT etc.). "
            "Provide a realistic match_score (0-100) taking into account their exam percentiles or marks relative to typical cutoffs. "
            "Write an empathetic explanation for each college mapping to their goals. "
            "You must return a valid JSON object matching this schema:\n"
            "{\n"
            "  \"status\": \"success\",\n"
            "  \"matches_found\": 5,\n"
            "  \"data\": [\n"
            "    {\n"
            "      \"name\": \"College Name\",\n"
            "      \"location\": \"Location\",\n"
            "      \"type\": \"Type (e.g. Government, Private)\",\n"
            "      \"fee\": \"Fee (e.g. INR 1,00,000 per year)\",\n"
            "      \"placement_rate\": \"Placement rate (e.g. 85%+)\",\n"
            "      \"match_score\": 90,\n"
            "      \"tags\": [\"Tag1\", \"Tag2\"],\n"
            "      \"description\": \"Empathetic mapping explanation...\"\n"
            "    }\n"
            "  ]\n"
            "}"
        )
        
        user_profile = f"Analyze this student profile: {json.dumps(lead_data)}"

        # 3. Call Groq API with JSON mode
        chat_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_profile}
            ],
            response_format={"type": "json_object"}
        )

        response_text = chat_completion.choices[0].message.content
        response_json = json.loads(response_text)

        # Validate with pydantic to ensure correctness
        validated_response = CollegeMatchResponse(**response_json)
        return validated_response.dict()

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")
