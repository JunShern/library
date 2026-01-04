from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import Optional
from datetime import date, timedelta
from pydantic import BaseModel

from auth import require_auth, require_branch_owner, get_authenticated_client
from config import get_supabase_client

router = APIRouter(prefix="/loans", tags=["loans"])


class LoanCreate(BaseModel):
    copy_id: str
    borrower_id: str
    due_date: date
    notes: Optional[str] = None


class LoanReturn(BaseModel):
    notes: Optional[str] = None


@router.get("")
async def list_loans(
    user: dict = Depends(require_auth),
    borrower_id: Optional[str] = Query(None),
    branch_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, regex="^(active|overdue|returned)$"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    authorization: Optional[str] = Header(None),
):
    """
    List loans with filters.
    - Borrowers see only their own loans
    - Branch owners see loans at their branch
    - Admins see all
    """
    supabase = get_authenticated_client(authorization)

    query = supabase.table("loans").select(
        "*, copy:copies(*, book:books(id, title, author, cover_url), "
        "branch:branches(id, name, owner_id)), borrower:profiles(id, name)"
    )

    # Apply filters based on role
    if user["role"] == "borrower":
        # Borrowers can only see their own loans
        query = query.eq("borrower_id", user["id"])
    elif user["role"] == "branch_owner":
        # Branch owners see their branch loans (filtered after fetch)
        if borrower_id:
            query = query.eq("borrower_id", borrower_id)
    else:  # admin
        if borrower_id:
            query = query.eq("borrower_id", borrower_id)

    response = query.order("borrowed_at", desc=True).range(
        offset, offset + limit - 1
    ).execute()

    loans = response.data

    # Filter by branch for branch owners
    if user["role"] == "branch_owner" and not user.get("role") == "admin":
        loans = [
            loan for loan in loans
            if loan["copy"]["branch"]["owner_id"] == user["id"]
        ]

    # Filter by branch_id if specified
    if branch_id:
        loans = [
            loan for loan in loans
            if loan["copy"]["branch"]["id"] == branch_id
        ]

    # Filter by status
    today = date.today()
    if status == "active":
        loans = [l for l in loans if l["returned_at"] is None]
    elif status == "overdue":
        loans = [
            l for l in loans
            if l["returned_at"] is None and l["due_date"] < str(today)
        ]
    elif status == "returned":
        loans = [l for l in loans if l["returned_at"] is not None]

    return {"loans": loans, "count": len(loans)}


@router.get("/{loan_id}")
async def get_loan(
    loan_id: str,
    user: dict = Depends(require_auth),
    authorization: Optional[str] = Header(None),
):
    """Get a single loan. User must be borrower, branch owner, or admin."""
    supabase = get_authenticated_client(authorization)

    response = supabase.table("loans").select(
        "*, copy:copies(*, book:books(*), branch:branches(*)), "
        "borrower:profiles(*)"
    ).eq("id", loan_id).single().execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Loan not found")

    loan = response.data

    # Check access
    is_borrower = loan["borrower_id"] == user["id"]
    is_branch_owner = loan["copy"]["branch"]["owner_id"] == user["id"]
    is_admin = user["role"] == "admin"

    if not (is_borrower or is_branch_owner or is_admin):
        raise HTTPException(status_code=403, detail="Access denied")

    return loan


@router.post("")
async def create_loan(
    loan: LoanCreate,
    user: dict = Depends(require_branch_owner),
    authorization: Optional[str] = Header(None),
):
    """
    Check out a copy to a borrower.
    Requires branch_owner role for the copy's branch.
    """
    supabase = get_authenticated_client(authorization)

    # Verify copy exists and get branch info
    copy_response = supabase.table("copies").select(
        "id, branch:branches(id, owner_id)"
    ).eq("id", loan.copy_id).single().execute()

    if not copy_response.data:
        raise HTTPException(status_code=404, detail="Copy not found")

    # Verify user owns the branch
    owner_id = copy_response.data["branch"]["owner_id"]
    if owner_id != user["id"] and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="You don't own this branch")

    # Check if copy is already on loan
    active_loan = supabase.table("loans").select("id").eq(
        "copy_id", loan.copy_id
    ).is_("returned_at", "null").execute()

    if active_loan.data:
        raise HTTPException(
            status_code=409,
            detail="This copy is already on loan"
        )

    # Verify borrower exists
    borrower = supabase.table("profiles").select("id").eq(
        "id", loan.borrower_id
    ).execute()

    if not borrower.data:
        raise HTTPException(status_code=404, detail="Borrower not found")

    # Create the loan
    loan_data = {
        "copy_id": loan.copy_id,
        "borrower_id": loan.borrower_id,
        "due_date": str(loan.due_date),
        "notes": loan.notes,
    }

    response = supabase.table("loans").insert(loan_data).execute()
    return response.data[0]


@router.put("/{loan_id}/return")
async def return_loan(
    loan_id: str,
    return_data: LoanReturn = LoanReturn(),
    user: dict = Depends(require_branch_owner),
    authorization: Optional[str] = Header(None),
):
    """
    Mark a loan as returned.
    Requires branch_owner role for the copy's branch.
    """
    supabase = get_authenticated_client(authorization)

    # Get loan with branch info
    loan_response = supabase.table("loans").select(
        "id, returned_at, copy:copies(branch:branches(owner_id))"
    ).eq("id", loan_id).single().execute()

    if not loan_response.data:
        raise HTTPException(status_code=404, detail="Loan not found")

    loan = loan_response.data

    if loan["returned_at"]:
        raise HTTPException(status_code=400, detail="Loan already returned")

    # Verify user owns the branch
    owner_id = loan["copy"]["branch"]["owner_id"]
    if owner_id != user["id"] and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="You don't own this branch")

    # Mark as returned
    from datetime import datetime
    update_data = {"returned_at": datetime.utcnow().isoformat()}
    if return_data.notes:
        update_data["notes"] = return_data.notes

    response = supabase.table("loans").update(update_data).eq(
        "id", loan_id
    ).execute()
    return response.data[0]
