from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from auth import get_current_user, require_auth, require_admin, get_authenticated_client
from config import get_supabase_client
from services.isbn_lookup import lookup_isbn

router = APIRouter(prefix="/books", tags=["books"])


class BookCreate(BaseModel):
    isbn: Optional[str] = None
    title: str
    author: Optional[str] = None
    cover_url: Optional[str] = None
    publisher: Optional[str] = None
    publish_year: Optional[int] = None
    page_count: Optional[int] = None
    description: Optional[str] = None


@router.get("")
async def list_books(
    q: Optional[str] = Query(None, description="Search title or author"),
    branch: Optional[str] = Query(None, description="Filter by branch ID"),
    available: Optional[bool] = Query(None, description="Filter by availability"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
):
    """
    List all books with optional filters.
    Public endpoint - no auth required.
    """
    supabase = get_supabase_client()

    # Start with books query
    query = supabase.table("books").select(
        "*, copies(id, branch_id, condition, loans(id, returned_at))"
    )

    # Apply search filter
    if q:
        query = query.or_(f"title.ilike.%{q}%,author.ilike.%{q}%")

    # Execute query
    response = query.range(offset, offset + limit - 1).execute()
    books = response.data

    # Post-process for branch and availability filters
    if branch or available is not None:
        filtered_books = []
        for book in books:
            copies = book.get("copies", [])

            # Filter by branch
            if branch:
                copies = [c for c in copies if c["branch_id"] == branch]

            # Filter by availability
            if available is not None:
                if available:
                    # Book is available if any copy has no active loan
                    copies = [
                        c for c in copies
                        if not any(
                            loan["returned_at"] is None
                            for loan in c.get("loans", [])
                        )
                    ]
                else:
                    # Book is unavailable if all copies are on loan
                    copies = [
                        c for c in copies
                        if any(
                            loan["returned_at"] is None
                            for loan in c.get("loans", [])
                        )
                    ]

            if copies or not (branch or available):
                book["copies"] = copies
                filtered_books.append(book)

        books = filtered_books

    return {"books": books, "count": len(books)}


@router.get("/lookup")
async def lookup_book_by_isbn(isbn: str = Query(..., description="ISBN to look up")):
    """
    Look up book metadata by ISBN from external APIs.
    Returns data without saving to database.
    Public endpoint - useful for previewing before adding.
    """
    result = await lookup_isbn(isbn)
    if not result:
        raise HTTPException(status_code=404, detail="Book not found for this ISBN")
    return result


@router.get("/{book_id}")
async def get_book(book_id: str):
    """
    Get a single book with all copies and availability.
    Public endpoint.
    """
    supabase = get_supabase_client()

    response = supabase.table("books").select(
        "*, copies(*, branch:branches(id, name), loans(id, borrower_id, due_date, returned_at))"
    ).eq("id", book_id).single().execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Book not found")

    book = response.data

    # Annotate each copy with availability
    for copy in book.get("copies", []):
        active_loan = next(
            (loan for loan in copy.get("loans", []) if loan["returned_at"] is None),
            None
        )
        copy["is_available"] = active_loan is None
        copy["current_loan"] = active_loan

    return book


@router.post("")
async def create_book(book: BookCreate, user: dict = Depends(require_auth)):
    """
    Create a new book record.
    Requires authentication (typically called when adding a copy).
    """
    supabase = get_supabase_client()

    # Check if ISBN already exists
    if book.isbn:
        existing = supabase.table("books").select("id").eq(
            "isbn", book.isbn
        ).execute()
        if existing.data:
            raise HTTPException(
                status_code=409,
                detail=f"Book with ISBN {book.isbn} already exists",
                headers={"X-Existing-Book-Id": existing.data[0]["id"]}
            )

    response = supabase.table("books").insert(book.model_dump()).execute()
    return response.data[0]


@router.delete("/{book_id}")
async def delete_book(book_id: str, user: dict = Depends(require_admin)):
    """
    Delete a book and all its copies.
    Requires admin role.
    """
    supabase = get_supabase_client()

    # Check if book exists
    existing = supabase.table("books").select("id").eq("id", book_id).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Book not found")

    # Delete book (copies will cascade via FK)
    supabase.table("books").delete().eq("id", book_id).execute()

    return {"message": "Book deleted successfully"}
