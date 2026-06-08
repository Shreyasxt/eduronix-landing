from fastapi import APIRouter, HTTPException
from database import supabase

router = APIRouter(prefix="/student", tags=["Student Dashboard"])

@router.get("/mentors")
async def get_all_mentors():

    #Fetches all mentors and their available time slots for the dashboard.
    try:
        # Fetch Mentor Details
        mentors_res = supabase.table("mentors").select("*").execute()
        
        # Fetch Availability Slots
        availability_res = supabase.table("mentor_availability").select("*").execute()
        
        mentors = mentors_res.data
        availability = availability_res.data
        
        # Merge availability into respective mentor dict
        for mentor in mentors:
            mentor["availability"] = [slot for slot in availability if slot["mentor_id"] == mentor["id"]]
            
        return {"status": "success", "mentors": mentors}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/bookings/{email}")
async def get_student_bookings(email: str):
    """
    Retrieves all booking requests associated with the student's email.
    """
    try:
        # Query booking_requests table for matching email
        res = supabase.table("booking_requests").select("*").eq("email", email).execute()
        return {"status": "success", "bookings": res.data}
    except Exception as e:
        return {"status": "error", "message": "Failed to fetch bookings", "detail": str(e)}

@router.get("/payments/{email}")
async def get_student_payments(email: str):
    """
    Returns specific payment columns for a student's past bookings.
    """
    try:
        res = supabase.table("booking_requests").select("id, course, payment_id, status").eq("email", email).execute()
        return {"status": "success", "payments": res.data}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
