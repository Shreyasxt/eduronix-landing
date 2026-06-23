import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
if not ENV_PATH.exists():
    ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Get these from your Supabase Project Settings > API
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY") 

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")

supabase: Client = create_client(url, key) 

# Temporary test
try:
    test_res = supabase.table("profiles").select("*").limit(1).execute()
    print("Connection Successful! Tables are reachable.")
except Exception as e:
    print(f"Connection Failed: {e}") 

from fastapi import Header, HTTPException, Depends

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    token = authorization.split(" ")[1]
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token user")
        return user_response.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

async def require_admin(user = Depends(get_current_user)):
    res = supabase.table("profiles").select("role").eq("id", user.id).execute()
    if not res.data or res.data[0].get("role") != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: Admin access required")
    return user

