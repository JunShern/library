import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")


def get_supabase_client() -> Client:
    """Get a Supabase client using the anon key (respects RLS)."""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def get_supabase_admin() -> Client:
    """Get a Supabase client using the service key (bypasses RLS)."""
    if not SUPABASE_SERVICE_KEY:
        raise ValueError("Missing SUPABASE_SERVICE_KEY for admin operations")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
