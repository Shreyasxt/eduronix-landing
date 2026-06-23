from fastapi import APIRouter, HTTPException, Depends
from database import supabase, get_current_user

router = APIRouter(prefix="/student", tags=["Student Dashboard"], dependencies=[Depends(get_current_user)])

@router.get("/mentors")
async def get_all_mentors():
    """
    Fetches all approved mentors and their available time slots for the dashboard in a single query.
    """
    try:
        # Fetch Mentor Details with availability embedded in one single query, filtering by approved status
        res = supabase.table("mentors").select("*, mentor_availability(*)").eq("is_approved", True).execute()
        
        mentors = res.data or []
        for mentor in mentors:
            # Map the database relation name to the key expected by the frontend
            mentor["availability"] = mentor.pop("mentor_availability", [])
            
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
