from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from database import supabase


router = APIRouter(tags=["Booking Requests"])


class BookingRequest(BaseModel):
    name: str
    phone: str
    email: EmailStr
    mentor_id: UUID
    slot_id: int


@router.post("/request-booking")
async def request_booking(payload: BookingRequest):
    try:
        insert_data = {
            "name": payload.name,
            "phone": payload.phone,
            "email": str(payload.email),
            "mentor_id": str(payload.mentor_id),
            "slot_id": payload.slot_id,
            "status": "pending",
        }

        res = supabase.table("booking_requests").insert(insert_data).execute()
        return {"status": "success", "booking_request": (res.data[0] if res.data else None)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/get-mentor-bookings/{mentor_id}")
async def get_mentor_bookings(mentor_id: UUID):
    try:
        res = (
            supabase.table("booking_requests")
            .select("*")
            .eq("mentor_id", str(mentor_id))
            .execute()
        )
        return {"status": "success", "bookings": res.data or []}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

