from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from pydantic import BaseModel

from auth import require_admin, require_branch_owner, get_authenticated_client
from config import get_supabase_client

router = APIRouter(prefix="/branches", tags=["branches"])


class BranchCreate(BaseModel):
    name: str
    owner_id: str
    address: Optional[str] = None


class BranchUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None


@router.get("")
async def list_branches():
    """List all branches with copy counts. Public endpoint."""
    supabase = get_supabase_client()

    response = supabase.table("branches").select(
        "*, owner:profiles(id, name), copies(id)"
    ).execute()

    branches = response.data
    for branch in branches:
        branch["copy_count"] = len(branch.get("copies", []))
        del branch["copies"]  # Don't return full copy list

    return {"branches": branches}


@router.get("/{branch_id}")
async def get_branch(branch_id: str):
    """Get a single branch with stats. Public endpoint."""
    supabase = get_supabase_client()

    response = supabase.table("branches").select(
        "*, owner:profiles(id, name), copies(id, loans(id, returned_at))"
    ).eq("id", branch_id).single().execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Branch not found")

    branch = response.data

    # Calculate stats
    copies = branch.get("copies", [])
    total_copies = len(copies)
    available_copies = sum(
        1 for c in copies
        if not any(loan["returned_at"] is None for loan in c.get("loans", []))
    )
    on_loan = total_copies - available_copies

    branch["stats"] = {
        "total_copies": total_copies,
        "available": available_copies,
        "on_loan": on_loan,
    }
    del branch["copies"]

    return branch


@router.post("")
async def create_branch(
    branch: BranchCreate,
    user: dict = Depends(require_admin),
    authorization: Optional[str] = Header(None),
):
    """Create a new branch. Admin only."""
    supabase = get_authenticated_client(authorization)

    response = supabase.table("branches").insert(branch.model_dump()).execute()
    return response.data[0]


@router.put("/{branch_id}")
async def update_branch(
    branch_id: str,
    update: BranchUpdate,
    user: dict = Depends(require_branch_owner),
    authorization: Optional[str] = Header(None),
):
    """Update a branch. Branch owner or admin only."""
    supabase = get_authenticated_client(authorization)

    # Verify branch exists and user has permission
    branch_response = supabase.table("branches").select("owner_id").eq(
        "id", branch_id
    ).single().execute()

    if not branch_response.data:
        raise HTTPException(status_code=404, detail="Branch not found")

    if branch_response.data["owner_id"] != user["id"] and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="You don't own this branch")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    response = supabase.table("branches").update(update_data).eq(
        "id", branch_id
    ).execute()
    return response.data[0]
