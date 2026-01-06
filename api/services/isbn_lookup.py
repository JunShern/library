import httpx
from typing import Optional

# Open Library returns a tiny 1x1 image (43 bytes) when no cover exists
OPEN_LIBRARY_BLANK_SIZE = 43


async def _check_cover_valid(client: httpx.AsyncClient, url: str) -> bool:
    """Check if a cover URL returns a valid image (not a blank placeholder)."""
    try:
        response = await client.head(url, follow_redirects=True)
        if response.status_code != 200:
            return False
        # Open Library's blank image is 43 bytes
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) <= OPEN_LIBRARY_BLANK_SIZE:
            return False
        return True
    except Exception:
        return False


async def _get_google_books_cover(client: httpx.AsyncClient, isbn: str) -> Optional[str]:
    """Get cover URL from Google Books if available."""
    try:
        response = await client.get(
            "https://www.googleapis.com/books/v1/volumes",
            params={"q": f"isbn:{isbn}"}
        )
        if response.status_code != 200:
            return None
        data = response.json()
        if data.get("totalItems", 0) == 0:
            return None
        volume = data["items"][0].get("volumeInfo", {})
        image_links = volume.get("imageLinks", {})
        cover_url = image_links.get("thumbnail") or image_links.get("smallThumbnail")
        if cover_url:
            # Upgrade to HTTPS and larger size
            return cover_url.replace("http://", "https://").replace("zoom=1", "zoom=2")
        return None
    except Exception:
        return None


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

            # Check Open Library cover, fall back to Google Books if invalid
            ol_cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
            cover_url = None
            if await _check_cover_valid(client, ol_cover_url):
                cover_url = ol_cover_url
            else:
                # Try Google Books cover as fallback
                cover_url = await _get_google_books_cover(client, isbn)

            # Extract publish year from publish_date
            publish_year = None
            if "publish_date" in data:
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

            # Try Open Library cover first, then Google Books
            ol_cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"
            cover_url = None
            if await _check_cover_valid(client, ol_cover_url):
                cover_url = ol_cover_url
            else:
                cover_url = await _get_google_books_cover(client, isbn)

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
