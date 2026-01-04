import httpx
from typing import Optional


async def lookup_isbn(isbn: str) -> Optional[dict]:
    """
    Look up book metadata by ISBN.
    Tries Open Library first, falls back to Google Books.
    Returns normalized book data or None if not found.
    """
    # Clean ISBN (remove hyphens, spaces)
    isbn = isbn.replace("-", "").replace(" ", "").strip()

    # Try Open Library first
    result = await _lookup_open_library(isbn)
    if result:
        return result

    # Fall back to Google Books
    result = await _lookup_google_books(isbn)
    if result:
        return result

    return None


async def _lookup_open_library(isbn: str) -> Optional[dict]:
    """Fetch from Open Library API."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get book data
            response = await client.get(f"https://openlibrary.org/isbn/{isbn}.json")
            if response.status_code != 200:
                return None

            data = response.json()

            # Get author name if author key exists
            author = None
            if "authors" in data and data["authors"]:
                author_key = data["authors"][0].get("key")
                if author_key:
                    author_response = await client.get(f"https://openlibrary.org{author_key}.json")
                    if author_response.status_code == 200:
                        author_data = author_response.json()
                        author = author_data.get("name")

            # Build cover URL
            cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"

            # Extract publish year from publish_date
            publish_year = None
            if "publish_date" in data:
                # Try to extract 4-digit year
                import re
                match = re.search(r"\b(19|20)\d{2}\b", data["publish_date"])
                if match:
                    publish_year = int(match.group())

            return {
                "isbn": isbn,
                "title": data.get("title"),
                "author": author,
                "cover_url": cover_url,
                "publisher": data.get("publishers", [None])[0] if "publishers" in data else None,
                "publish_year": publish_year,
                "page_count": data.get("number_of_pages"),
                "description": _extract_description(data.get("description")),
            }
    except Exception:
        return None


async def _lookup_google_books(isbn: str) -> Optional[dict]:
    """Fetch from Google Books API."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://www.googleapis.com/books/v1/volumes",
                params={"q": f"isbn:{isbn}"}
            )
            if response.status_code != 200:
                return None

            data = response.json()
            if data.get("totalItems", 0) == 0:
                return None

            volume = data["items"][0]["volumeInfo"]

            # Prefer Open Library cover (more reliable than Google Books)
            # Open Library often has covers even when they lack metadata
            cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"

            return {
                "isbn": isbn,
                "title": volume.get("title"),
                "author": ", ".join(volume.get("authors", [])) or None,
                "cover_url": cover_url,
                "publisher": volume.get("publisher"),
                "publish_year": _parse_year(volume.get("publishedDate")),
                "page_count": volume.get("pageCount"),
                "description": volume.get("description"),
            }
    except Exception:
        return None


def _extract_description(desc) -> Optional[str]:
    """Handle Open Library description which can be string or dict."""
    if desc is None:
        return None
    if isinstance(desc, str):
        return desc
    if isinstance(desc, dict):
        return desc.get("value")
    return None


def _parse_year(date_str: Optional[str]) -> Optional[int]:
    """Extract year from date string like '2020-01-15' or '2020'."""
    if not date_str:
        return None
    try:
        return int(date_str[:4])
    except (ValueError, IndexError):
        return None
