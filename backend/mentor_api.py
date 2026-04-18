from fastapi import APIRouter, HTTPException
from database import supabase
from pydantic import BaseModel
from typing import List

# Use APIRouter instead of FastAPI() so it can be "plugged into" main.py
router = APIRouter(prefix="/mentor", tags=["Mentor Dashboard"])

class MentorProfile(BaseModel):
    user_id: str
    full_name: str
    bio: str
    expertise: List[str]
    linkedin_url: str

@router.post("/setup-profile")
async def setup_profile(profile: MentorProfile):
    try:
        # Update Central Profile
        supabase.table("profiles").update({
            "full_name": profile.full_name,
            "role": "mentor"
        }).eq("id", profile.user_id).execute()

        # Update Mentor Details
        res = supabase.table("mentors").upsert({
            "id": profile.user_id,
            "bio": profile.bio,
            "expertise": profile.expertise,
            "linkedin_url": profile.linkedin_url
        }).execute()

        return {"status": "success", "message": "Mentor profile updated!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 