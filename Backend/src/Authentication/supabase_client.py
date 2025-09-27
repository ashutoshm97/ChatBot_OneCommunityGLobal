import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()  # load .env variables

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# For regular (public) operations
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# For admin operations (secure, server-side only)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
