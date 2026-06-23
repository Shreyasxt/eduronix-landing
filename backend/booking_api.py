from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel, EmailStr

from database import supabase, get_current_user


router = APIRouter(tags=["Booking Requests"], dependencies=[Depends(get_current_user)])


class BookingRequest(BaseModel): 
    name: str
    phone: str
    email: EmailStr
    mentor_id: UUID
    slot_id: int
    whatsapp_number: str
    target_college: str
    special_requirements: str
    session_type: Optional[Literal["solo", "buddy"]] = None
    buddy_name: Optional[str] = None
    buddy_whatsapp: Optional[str] = None
    buddy_email: Optional[EmailStr] = None
    buddy_city: Optional[str] = None


class UpdateBookingStatusRequest(BaseModel):
    booking_id: UUID
    new_status: str


@router.post("/request-booking")
async def request_booking(
    payload: BookingRequest, user = Depends(get_current_user)
):
    try:
        insert_data = {
            "name": payload.name,
            "phone": payload.phone,
            "email": str(payload.email),
            "mentor_id": str(payload.mentor_id),
            "slot_id": payload.slot_id,
            "whatsapp_number": payload.whatsapp_number,
            "target_college": payload.target_college,
            "special_requirements": payload.special_requirements,
            "session_type": payload.session_type,
            "buddy_name": payload.buddy_name,
            "buddy_whatsapp": payload.buddy_whatsapp,
            "buddy_email": str(payload.buddy_email) if payload.buddy_email else None,
            "buddy_city": payload.buddy_city,
            "status": "pending",
        }

        supabase.table("booking_requests").insert(insert_data).execute()

        return {
            "status": "success",
            "message": "Booking request submitted.",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/update-booking-status")
async def update_booking_status(payload: UpdateBookingStatusRequest):
    try:
        res = (
            supabase.table("booking_requests")
            .update({"status": payload.new_status})
            .eq("id", str(payload.booking_id))
            .execute()
        )

        updated = res.data[0] if res.data else None
        if not updated:
            raise HTTPException(status_code=404, detail="Booking request not found")

        return {
            "status": "success",
            "message": "Booking status updated",
            "booking_request": updated,
        }
    except HTTPException:
        raise
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
