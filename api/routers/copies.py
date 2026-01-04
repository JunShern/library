from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import Optional
from pydantic import BaseModel

from auth import require_branch_owner, get_authenticated_client
from config import get_supabase_client
from services.isbn_lookup import lookup_isbn

router = APIRouter(prefix="/copies", tags=["copies"])


class CopyCreate(BaseModel):
    book_id: Optional[str] = None  # If provided, links to existing book
    branch_id: str
    isbn: Optional[str] = None  # If provided without book_id, creates/finds book
    condition: Optional[str] = None
    notes: Optional[str] = None


class CopyUpdate(BaseModel):
    condition: Optional[str] = None
    notes: Optional[str] = None


@router.get("")
async def list_copies(
    book_id: Optional[str] = Query(None),
    branch_id: Optional[str] = Query(None),
    available: Optional[bool] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    """List copies with optional filters. Public endpoint."""
    supabase = get_supabase_client()

    query = supabase.table("copies").select(
        "*, book:books(*), branch:branches(id, name), loans(id, returned_at)"
    )

    if book_id:
        query = query.eq("book_id", book_id)
    if branch_id:
        query = query.eq("branch_id", branch_id)

    response = query.range(offset, offset + limit - 1).execute()
    copies = response.data

    # Post-process for availability
    for copy in copies:
        active_loan = next(
            (loan for loan in copy.get("loans", []) if loan["returned_at"] is None),
            None
        )
        copy["is_available"] = active_loan is None

    if available is not None:
        copies = [c for c in copies if c["is_available"] == available]

    return {"copies": copies, "count": len(copies)}


@router.get("/{copy_id}")
async def get_copy(copy_id: str):
    """Get a single copy with loan status. Public endpoint."""
    supabase = get_supabase_client()

    response = supabase.table("copies").select(
        "*, book:books(*), branch:branches(*), "
        "loans(*, borrower:profiles(id, name))"
    ).eq("id", copy_id).single().execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Copy not found")

    copy = response.data
    active_loan = next(
        (loan for loan in copy.get("loans", []) if loan["returned_at"] is None),
        None
    )
    copy["is_available"] = active_loan is None
    copy["current_loan"] = active_loan

    return copy


@router.post("")
async def create_copy(
    copy: CopyCreate,
    user: dict = Depends(require_branch_owner),
    authorization: Optional[str] = Header(None),
):
    """
    Add a copy to a branch.
    If isbn provided without book_id, will create or find the book record.
    Requires branch_owner role.
    """
    supabase = get_authenticated_client(authorization)

    book_id = copy.book_id

    # If no book_id but ISBN provided, find or create book
    if not book_id and copy.isbn:
        # Check if book exists
        existing = supabase.table("books").select("id").eq(
            "isbn", copy.isbn
        ).execute()

        if existing.data:
            book_id = existing.data[0]["id"]
        else:
            # Look up metadata and create book
            metadata = await lookup_isbn(copy.isbn)
            if not metadata:
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not find metadata for ISBN {copy.isbn}. "
                    "Please create the book manually."
                )

            book_response = supabase.table("books").insert(metadata).execute()
            book_id = book_response.data[0]["id"]

    if not book_id:
        raise HTTPException(
            status_code=400,
            detail="Either book_id or isbn must be provided"
        )

    # Verify user owns this branch
    branch_response = supabase.table("branches").select("owner_id").eq(
        "id", copy.branch_id
    ).single().execute()

    if not branch_response.data:
        raise HTTPException(status_code=404, detail="Branch not found")

    if branch_response.data["owner_id"] != user["id"] and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="You don't own this branch")

    # Create the copy
    copy_data = {
        "book_id": book_id,
        "branch_id": copy.branch_id,
        "condition": copy.condition,
        "notes": copy.notes,
        "added_by": user["id"],
    }

    response = supabase.table("copies").insert(copy_data).execute()
    return response.data[0]


@router.put("/{copy_id}")
async def update_copy(
    copy_id: str,
    update: CopyUpdate,
    user: dict = Depends(require_branch_owner),
    authorization: Optional[str] = Header(None),
):
    """Update a copy (condition, notes). Requires branch_owner role."""
    supabase = get_authenticated_client(authorization)

    # Verify copy exists and user owns the branch
    copy_response = supabase.table("copies").select(
        "branch_id, branch:branches(owner_id)"
    ).eq("id", copy_id).single().execute()

    if not copy_response.data:
        raise HTTPException(status_code=404, detail="Copy not found")

    owner_id = copy_response.data["branch"]["owner_id"]
    if owner_id != user["id"] and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="You don't own this branch")

    # Update
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    response = supabase.table("copies").update(update_data).eq(
        "id", copy_id
    ).execute()
    return response.data[0]


@router.delete("/{copy_id}")
async def delete_copy(
    copy_id: str,
    user: dict = Depends(require_branch_owner),
    authorization: Optional[str] = Header(None),
):
    """Delete a copy. Requires branch_owner role."""
    supabase = get_authenticated_client(authorization)

    # Verify copy exists and user owns the branch
    copy_response = supabase.table("copies").select(
        "branch_id, branch:branches(owner_id)"
    ).eq("id", copy_id).single().execute()

    if not copy_response.data:
        raise HTTPException(status_code=404, detail="Copy not found")

    owner_id = copy_response.data["branch"]["owner_id"]
    if owner_id != user["id"] and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="You don't own this branch")

    supabase.table("copies").delete().eq("id", copy_id).execute()
    return {"status": "deleted"}
