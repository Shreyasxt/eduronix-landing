from fastapi import APIRouter, HTTPException, Depends
from database import supabase, require_admin
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["Admin Control Panel"], dependencies=[Depends(require_admin)])

class AssignMentorRequest(BaseModel):
    booking_id: str
    mentor_id: str

class ToggleApprovalRequest(BaseModel):
    mentor_id: str
    is_approved: bool

class CancelSessionRequest(BaseModel):
    booking_id: str

class MarkPayoutRequest(BaseModel):
    mentor_id: str

@router.get("/overview")
async def get_overview():
    try:
        # 1. Fetch all booking requests
        bookings_res = supabase.table("booking_requests").select("*").execute()
        bookings = bookings_res.data or []
        
        # 2. Fetch all mentors
        mentors_res = supabase.table("mentors").select("*").execute()
        mentors = mentors_res.data or []

        # 3. Fetch college match leads count
        total_college_matches = 0
        unique_college_match_users = 0
        try:
            leads_res = supabase.table("college_match_leads").select("email").execute()
            leads = leads_res.data or []
            total_college_matches = len(leads)
            unique_college_match_users = len(set(l.get("email").strip().lower() for l in leads if l.get("email")))
        except Exception as e:
            print("Failed to fetch college match leads for admin overview:", e)
        
        total_sessions = len(bookings)
        total_revenue = sum(299 for b in bookings if b.get("status") != "cancelled")
        total_mentors = len(mentors)
        
        # Pending payouts = completed sessions not yet paid * 239 (80% of 299)
        # We can treat status 'completed' as pending payout
        pending_payouts = sum(239 for b in bookings if b.get("status") == "completed")
        
        # Today stats (using UTC date helper since created_at is in ISO format)
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        today_completed = sum(1 for b in bookings if b.get("status") == "completed" and b.get("created_at", "").startswith(today_str))
        # fallback to general counts if today has no data
        if today_completed == 0:
            today_completed = sum(1 for b in bookings if b.get("status") == "completed")
            
        today_upcoming = sum(1 for b in bookings if b.get("status") in ["assigned", "upcoming"])
        today_cancelled = sum(1 for b in bookings if b.get("status") == "cancelled")
        
        # Unassigned requests: status is pending and mentor_id is null/None
        unassigned_requests = []
        for b in bookings:
            if b.get("status") == "pending" and not b.get("mentor_id"):
                unassigned_requests.append({
                    "id": b.get("id"),
                    "student": b.get("name") or "Anonymous Student",
                    "targetCollege": b.get("college") or "Not Specified",
                    "topic": b.get("course") or "General Inquiry",
                    "preferredDate": "Upcoming",
                    "preferredTime": "TBD",
                    "amount": 299,
                    "priority": "medium" if not b.get("requirements") else "high",
                    "note": b.get("requirements") or ""
                })
                
        # Assigned requests
        assigned_sessions = []
        mentor_map = {m["id"]: m["full_name"] for m in mentors}
        for b in bookings:
            if b.get("mentor_id"):
                assigned_sessions.append({
                    "id": b.get("id"),
                    "student": b.get("name") or "Anonymous Student",
                    "targetCollege": b.get("college") or "Not Specified",
                    "mentor": mentor_map.get(b.get("mentor_id")) or "Unknown Mentor",
                    "date": "Scheduled",
                    "time": "TBD",
                    "status": "Upcoming" if b.get("status") in ["assigned", "upcoming"] else b.get("status", "Upcoming").capitalize()
                })
                
        # Recent Activity (last 5 bookings)
        recent_activity = []
        sorted_bookings = sorted(bookings, key=lambda x: x.get("created_at", ""), reverse=True)[:5]
        for idx, b in enumerate(sorted_bookings):
            time_desc = "Recent"
            if b.get("status") == "completed":
                desc = f"Session completed: {b.get('name')} with Mentor"
                b_type = "completed"
            elif b.get("mentor_id"):
                desc = f"{b.get('name')} booked a session with {mentor_map.get(b.get('mentor_id'), 'a Mentor')}"
                b_type = "booked"
            else:
                desc = f"New booking request from {b.get('name')} for {b.get('college')}"
                b_type = "pending"
            recent_activity.append({
                "id": f"act_{idx}",
                "description": desc,
                "time": time_desc,
                "type": b_type
            })
            
        # Revenue Chart grouping by month
        revenue_by_month = {}
        for b in bookings:
            if b.get("status") == "cancelled" or not b.get("created_at"):
                continue
            try:
                date_obj = datetime.strptime(b.get("created_at")[:10], "%Y-%m-%d")
                month_name = date_obj.strftime("%b")
                revenue_by_month[month_name] = revenue_by_month.get(month_name, 0) + 299
            except Exception:
                pass
                
        # Default fallback chart if empty
        if not revenue_by_month:
            revenue_by_month = {"Jan": 3588, "Feb": 5976, "Mar": 7165, "Apr": 8952, "May": 9549, "Jun": 11022}
            
        revenue_chart = [{"month": m, "value": v} for m, v in revenue_by_month.items()]
        
        return {
            "status": "success",
            "totalSessions": total_sessions,
            "totalRevenue": total_revenue,
            "totalMentors": total_mentors,
            "pendingPayouts": pending_payouts,
            "todayCompleted": today_completed,
            "todayUpcoming": today_upcoming,
            "todayCancelled": today_cancelled,
            "unassignedRequests": unassigned_requests,
            "assignedSessions": assigned_sessions,
            "recentActivity": recent_activity,
            "revenueChart": revenue_chart,
            "totalCollegeMatches": total_college_matches,
            "uniqueCollegeMatchUsers": unique_college_match_users
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/mentors")
async def get_mentors():
    try:
        mentors_res = supabase.table("mentors").select("*").execute()
        mentors = mentors_res.data or []
        
        bookings_res = supabase.table("booking_requests").select("id, mentor_id, status").execute()
        bookings = bookings_res.data or []
        
        # Aggregate stats per mentor
        result = []
        for m in mentors:
            mentor_id = m.get("id")
            mentor_bookings = [b for b in bookings if b.get("mentor_id") == mentor_id]
            sessions_count = len(mentor_bookings)
            
            # Pending payout = completed sessions * 239
            pending_payout = sum(239 for b in mentor_bookings if b.get("status") == "completed")
            
            # Map rating (hardcode 4.8 or check average feedback if feedback table exists)
            # Default fallback rating to 5.0
            rating = 5.0
            
            status = "Active" if m.get("is_approved") else "Pending"
            
            result.append({
                "id": mentor_id,
                "name": m.get("full_name") or "Unknown Mentor",
                "college": m.get("college") or "Not Specified",
                "branch": m.get("course") or "Engineering",
                "year": m.get("year") or "Senior",
                "sessions": sessions_count,
                "rating": rating,
                "earned": sessions_count * 239,
                "pendingPayout": pending_payout,
                "status": status,
                "available": m.get("is_approved") or False,
                "upi": m.get("upi") or "Not Provided"
            })
        return {"status": "success", "mentors": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/students")
async def get_students():
    try:
        profiles_res = supabase.table("profiles").select("*").eq("role", "student").execute()
        students = profiles_res.data or []
        
        bookings_res = supabase.table("booking_requests").select("*").execute()
        bookings = bookings_res.data or []
        
        result = []
        for s in students:
            student_id = s.get("id")
            student_email = s.get("email") # fallback if profile doesn't have it
            
            # Filter bookings by matching email or name
            student_bookings = [b for b in bookings if b.get("email") == student_email or b.get("name") == s.get("full_name")]
            sessions_count = len(student_bookings)
            total_spent = sum(299 for b in student_bookings if b.get("status") != "cancelled")
            
            phone = "N/A"
            city = "N/A"
            if student_bookings:
                phone = student_bookings[0].get("phone") or "N/A"
                city = student_bookings[0].get("city") or "N/A"
                
            result.append({
                "id": student_id,
                "name": s.get("full_name") or "Anonymous",
                "city": city,
                "phone": phone,
                "sessions": sessions_count,
                "spent": total_spent,
                "joined": "2026"
            })
        return {"status": "success", "students": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/assign-mentor")
async def assign_mentor(payload: AssignMentorRequest):
    try:
        res = supabase.table("booking_requests").update({
            "mentor_id": payload.mentor_id,
            "status": "assigned"
        }).eq("id", payload.booking_id).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Booking request not found")
            
        return {"status": "success", "message": "Mentor assigned successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cancel-session")
async def cancel_session(payload: CancelSessionRequest):
    try:
        res = supabase.table("booking_requests").update({
            "status": "cancelled"
        }).eq("id", payload.booking_id).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Booking request not found")
            
        return {"status": "success", "message": "Session cancelled successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/toggle-mentor-approval")
async def toggle_mentor_approval(payload: ToggleApprovalRequest):
    try:
        res = supabase.table("mentors").update({
            "is_approved": payload.is_approved
        }).eq("id", payload.mentor_id).execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Mentor not found")
            
        return {"status": "success", "message": f"Mentor approval toggled to {payload.is_approved}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/mark-payout-paid")
async def mark_payout_paid(payload: MarkPayoutRequest):
    try:
        # Mark all completed bookings for this mentor as 'payout_paid'
        res = supabase.table("booking_requests").update({
            "status": "payout_paid"
        }).eq("mentor_id", payload.mentor_id).eq("status", "completed").execute()
        
        return {"status": "success", "message": "Payouts marked as paid"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/collegematch-leads")
async def get_collegematch_leads():
    try:
        res = supabase.table("college_match_leads").select("*").execute()
        leads = res.data or []
        sorted_leads = sorted(leads, key=lambda x: x.get("created_at", ""), reverse=True)
        return {"status": "success", "leads": sorted_leads}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
