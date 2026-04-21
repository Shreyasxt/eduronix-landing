import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env')) 

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