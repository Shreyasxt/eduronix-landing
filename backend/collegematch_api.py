from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database import supabase  # Importing your existing Supabase client instance

router = APIRouter(prefix="/api", tags=["CollegeMatch"])

# 1. Define Request Payload Schema
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

# 2. Hardcoded College Dataset for Engine Evaluation
COLLEGE_DATABASE = [
    {
        "name": "COEP Technological University",
        "location": "Pune, Maharashtra",
        "type": "Government",
        "fee": 120000,
        "placement_rate": "94%",
        "match_score": 96,
        "tags": ["Active Campus", "3 Mentors Available"],
        "stream": "Science",
        "description": "Your MHT-CET score range, budget, and Pune preference align perfectly with COEP. Strong alumni network."
    },
    {
        "name": "VJTI Mumbai",
        "location": "Mumbai, Maharashtra",
        "type": "Autonomous",
        "fee": 150000,
        "placement_rate": "91%",
        "match_score": 91,
        "tags": ["Industry Connections", "2 Mentors Available"],
        "stream": "Science",
        "description": "Strong placement record in Mumbai's tech ecosystem. Slightly higher fees but excellent ROI."
    },
    {
        "name": "VIT Vellore",
        "location": "Vellore, Tamil Nadu",
        "type": "Private",
        "fee": 450000,
        "placement_rate": "89%",
        "match_score": 84,
        "tags": ["Vibrant Fest Culture", "5 Mentors Available"],
        "stream": "Science",
        "description": "Excellent infrastructure and widespread industry brand recognition across states."
    }
]

# 3. The API Processing Endpoint
@router.post("/college-match")
async def process_college_match(payload: CollegeMatchRequest):
    try:
        # A. Log the complete data bundle into Supabase
        lead_data = {
            "full_name": payload.full_name,
            "whatsapp_number": payload.whatsapp_number,
            "email": payload.email,
            "stream": payload.stream,
            "exams": payload.exams,
            "board_percentage": payload.board_percentage,
            "budget_per_year": payload.budget_per_year,
            "scholarship_reservation": payload.scholarship_reservation,
            "career_goal": payload.career_goal,
            "preferred_locations": payload.preferred_locations,
            "college_priority": payload.college_priority,
            "living_preference": payload.living_preference,
            "pressure_handling": payload.pressure_handling,
            "biggest_fear": payload.biggest_fear,
            "target_colleges": payload.target_colleges,
            "decision_maker": payload.decision_maker
        }
        
        supabase.table("college_match_leads").insert(lead_data).execute()
        
        # B. Matching Filter Algorithm Loop
        matches = []
        for college in COLLEGE_DATABASE:
            # Drop college if it massively breaks their explicit budget cap
            if college["fee"] > (payload.budget_per_year + 50000):
                continue
            
            # Simple sorting weights if user priority matches structural college strengths
            final_score = college["match_score"]
            if "Best placements" in payload.college_priority and int(college["placement_rate"].replace('%','')) > 90:
                final_score += 2
                
            matched_item = college.copy()
            matched_item["match_score"] = min(final_score, 99) # Cap at 99%
            matches.append(matched_item)
            
        # Sort output matches based on engine alignment score descending
        matches = sorted(matches, key=lambda x: x["match_score"], reverse=True)
        
        return {
            "status": "success",
            "matches_found": len(matches),
            "data": matches[:10] # Return the top matching items array
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database pipeline failure: {str(e)}") 