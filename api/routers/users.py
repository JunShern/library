from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import Optional
from pydantic import BaseModel

from auth import require_auth, require_admin, get_authenticated_client
from config import get_supabase_client

router = APIRouter(prefix="/users", tags=["users"])


class ProfileUpdate(BaseModel):
    name: Optional[str] = None


class RoleUpdate(BaseModel):
    role: str


@router.get("/me")
async def get_current_user_profile(user: dict = Depends(require_auth)):
    """Get the current user's profile."""
    supabase = get_supabase_client()

    response = supabase.table("profiles").select(
        "*, branches:branches(id, name)"
    ).eq("id", user["id"]).single().execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    return response.data


@router.put("/me")
async def update_current_user_profile(
    update: ProfileUpdate,
    user: dict = Depends(require_auth),
    authorization: Optional[str] = Header(None),
):
    """Update the current user's profile."""
    supabase = get_authenticated_client(authorization)

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    response = supabase.table("profiles").update(update_data).eq(
        "id", user["id"]
    ).execute()
    return response.data[0]


@router.get("")
async def list_users(
    user: dict = Depends(require_admin),
    role: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Search by name or email"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    """List all users. Admin only."""
    supabase = get_supabase_client()

    query = supabase.table("profiles").select("*")

    if role:
        query = query.eq("role", role)

    if q:
        query = query.or_(f"name.ilike.%{q}%")

    response = query.range(offset, offset + limit - 1).execute()
    return {"users": response.data, "count": len(response.data)}


@router.get("/{user_id}")
async def get_user(user_id: str, user: dict = Depends(require_admin)):
    """Get a user's profile. Admin only."""
    supabase = get_supabase_client()

    response = supabase.table("profiles").select(
        "*, branches:branches(id, name)"
    ).eq("id", user_id).single().execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")

    return response.data


@router.put("/{user_id}/role")
async def update_user_role(
    user_id: str,
    role_update: RoleUpdate,
    user: dict = Depends(require_admin),
    authorization: Optional[str] = Header(None),
):
    """Update a user's role. Admin only."""
    if role_update.role not in ("admin", "branch_owner", "borrower"):
        raise HTTPException(status_code=400, detail="Invalid role")

    supabase = get_authenticated_client(authorization)

    # Verify user exists
    existing = supabase.table("profiles").select("id").eq(
        "id", user_id
    ).execute()

    if not existing.data:
        raise HTTPException(status_code=404, detail="User not found")

    response = supabase.table("profiles").update(
        {"role": role_update.role}
    ).eq("id", user_id).execute()

    return response.data[0]
