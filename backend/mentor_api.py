from fastapi import APIRouter, HTTPException
from database import supabase
from pydantic import BaseModel, Field
from typing import List

# Use APIRouter instead of FastAPI() so it can be "plugged into" main.py
router = APIRouter(prefix="/mentor", tags=["Mentor Dashboard"])

class AvailabilitySlot(BaseModel):
    day_of_week: str = Field(..., description="Day of week for this slot (e.g. monday)")
    start_time: str = Field(..., description="Start time (e.g. 09:00 or 09:00:00)")
    end_time: str = Field(..., description="End time (e.g. 17:00 or 17:00:00)")


class SetAvailabilityRequest(BaseModel):
    user_id: str 
    slots: List[AvailabilitySlot]


class MentorProfile(BaseModel):
    user_id: str
    full_name: str
    bio: str
    expertise: List[str]
    linkedin: str
    upi: str
    year: str
    city: str
    state: str

@router.post("/setup-profile")
async def setup_profile(profile: MentorProfile):
    try:
        # Update Central Profile
        supabase.table("profiles").update({
            "full_name": profile.full_name,
            "role": "mentor"
        }).eq("id", profile.user_id).execute()

        # Keys must match `mentors` columns exactly
        mentor_data = {
            "id": profile.user_id,
            "full_name": profile.full_name,
            "bio": profile.bio,
            "expertise": profile.expertise,
            "linkedin": profile.linkedin,
            "upi": profile.upi,
            "year": profile.year,
            "city": profile.city,
            "state": profile.state,
        }
        supabase.table("mentors").upsert(mentor_data).execute()

        return {"status": "success", "message": "Mentor profile updated!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/set-availability")
async def set_availability(payload: SetAvailabilityRequest):
    """
    Replace all availability slots for the mentor: removes existing rows for
    `user_id`, then inserts the provided slots into `mentor_availability`.
    """
    try:
        supabase.table("mentor_availability").delete().eq(
            "mentor_id", payload.user_id 
        ).execute()

        if not payload.slots:
            return {
                "status": "success",
                "message": "Availability cleared (no slots provided).",
                "count": 0,
            }

        rows = [
            {
                "mentor_id": payload.user_id,
                "day_of_week": slot.day_of_week, 
                "start_time": slot.start_time,
                "end_time": slot.end_time,
            } 
            for slot in payload.slots
        ]

        supabase.table("mentor_availability").insert(rows).execute()

        return {
            "status": "success",
            "message": "Availability saved.",
            "count": len(rows),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/get-availability/{mentor_id}")
async def get_availability(mentor_id: str):
    """
    Fetch all availability slots for a mentor from `mentor_availability`.
    """
    try:
        res = (
            supabase.table("mentor_availability")
            .select("day_of_week,start_time,end_time")
            .eq("mentor_id", mentor_id)
            .execute()
        )

        # supabase-py returns a response object with `.data` as a list (or None).
        return res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))