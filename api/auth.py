from fastapi import Depends, HTTPException, Header
from typing import Optional
from supabase import Client
from config import get_supabase_client


async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """
    Extract and validate user from Supabase JWT.
    Returns None if no token provided (allows public access).
    Raises 401 if token is invalid.
    """
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]
    supabase = get_supabase_client()

    try:
        response = supabase.auth.get_user(token)
        if response.user:
            # Fetch profile to get role
            profile = supabase.table("profiles").select("*").eq("id", response.user.id).single().execute()
            return {
                "id": response.user.id,
                "email": response.user.email,
                "role": profile.data.get("role", "borrower") if profile.data else "borrower",
                "name": profile.data.get("name") if profile.data else None,
            }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return None


async def require_auth(user: Optional[dict] = Depends(get_current_user)) -> dict:
    """Require authentication. Raises 401 if not authenticated."""
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def require_branch_owner(user: dict = Depends(require_auth)) -> dict:
    """Require branch_owner or admin role."""
    if user["role"] not in ("branch_owner", "admin"):
        raise HTTPException(status_code=403, detail="Branch owner access required")
    return user


async def require_admin(user: dict = Depends(require_auth)) -> dict:
    """Require admin role."""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def get_authenticated_client(authorization: Optional[str] = Header(None)) -> Client:
    """
    Get a Supabase client with the user's JWT set.
    This ensures RLS policies are applied based on the user.
    """
    supabase = get_supabase_client()
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        supabase.auth.set_session(token, token)  # Set both access and refresh
    return supabase
