# Home Library System — Design Brief

## Overview

A web-based cataloging and lending system for a personal book collection, designed to eventually scale to a community/public library. Prioritizes simplicity now with clear extension points for the future.

## Goals

- Catalog books quickly via ISBN barcode scanning
- Track who has borrowed what and when it's due
- Simple user accounts for borrowers
- Owner can manage inventory; borrowers can browse and request
- Full data ownership (standard Postgres, exportable anytime)

## Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Database | Supabase (hosted Postgres) | Free tier, built-in auth, row-level security, easy migration path to self-hosted |
| API | FastAPI (Python) | Simple, fast, auto-docs, good async support |
| Frontend | Vanilla HTML/CSS/JS | No build step, easy to maintain, can add framework later |
| Hosting (API) | Railway or Render | Free tier, Git-based deploys |
| Hosting (Frontend) | Vercel, Netlify, or same as API | Static hosting, free |

## Database Schema

```sql
-- Supabase handles auth.users internally; this extends it
create table profiles (
  id uuid primary key references auth.users(id),
  name text not null,
  role text not null default 'borrower', -- 'admin' | 'branch_owner' | 'borrower'
  created_at timestamptz default now()
);

-- Branch = a physical location (your house, friend's house, etc.)
create table branches (
  id uuid primary key default gen_random_uuid(),
  name text not null,              -- "Jun's Home Library", "Sarah's Collection"
  owner_id uuid references profiles(id) not null,
  address text,                    -- optional, for pickup coordination
  created_at timestamptz default now()
);

-- Book = bibliographic record (one per ISBN/title)
create table books (
  id uuid primary key default gen_random_uuid(),
  isbn text unique,                -- unique constraint; null for books without ISBN
  title text not null,
  author text,
  cover_url text,
  publisher text,
  publish_year int,
  page_count int,
  description text,
  created_at timestamptz default now()
);

-- Copy = physical instance of a book at a specific branch
create table copies (
  id uuid primary key default gen_random_uuid(),
  book_id uuid references books(id) not null,
  branch_id uuid references branches(id) not null,
  condition text,                  -- 'excellent' | 'good' | 'fair' | 'poor'
  notes text,                      -- "has coffee stain on p.42", "signed by author"
  added_by uuid references profiles(id),
  added_at timestamptz default now()
);

-- Loans reference copies, not books
create table loans (
  id uuid primary key default gen_random_uuid(),
  copy_id uuid references copies(id) not null,
  borrower_id uuid references profiles(id) not null,
  borrowed_at timestamptz default now(),
  due_date date not null,
  returned_at timestamptz,
  notes text
);

-- Optional: for future "request a book" feature
create table holds (
  id uuid primary key default gen_random_uuid(),
  book_id uuid references books(id) not null,  -- hold on any copy of this book
  requester_id uuid references profiles(id) not null,
  preferred_branch_id uuid references branches(id),  -- optional preference
  requested_at timestamptz default now(),
  fulfilled_at timestamptz
);
```

### Key modeling decisions

- **Books vs Copies**: A `book` is a bibliographic record (one entry per ISBN). A `copy` is a physical book on a shelf. If you and your friend both own "Dune," that's one book record, two copy records.
- **Branches**: Each branch has an owner who can manage their own copies. An `admin` can manage everything; a `branch_owner` manages only their branch.
- **Loans**: Borrowers check out a specific copy, not an abstract book. This lets you track which physical item is where.

## API Endpoints

### Books (bibliographic records)
- `GET /books` — list all books (public, filterable by title/author search)
- `GET /books/{id}` — book details + all copies across branches + availability (public)
- `POST /books` — create book record (auto-created during copy add if ISBN not found)
- `POST /books/lookup?isbn={isbn}` — fetch metadata from Open Library, return without saving (public)

### Copies (physical instances)
- `GET /copies` — list copies (filterable by branch, available, book_id)
- `GET /copies/{id}` — single copy details + current loan status
- `POST /copies` — add a copy to a branch (branch_owner+ only)
- `PUT /copies/{id}` — edit copy (condition, notes) (branch_owner+ only)
- `DELETE /copies/{id}` — remove copy (branch_owner+ only)

### Branches
- `GET /branches` — list all branches (public)
- `GET /branches/{id}` — branch details + copy count
- `POST /branches` — create branch (admin only)
- `PUT /branches/{id}` — edit branch (branch_owner+ only)

### Loans
- `GET /loans` — list loans (filterable: current, overdue, history, by user, by branch)
- `POST /loans` — check out a copy to a user (branch_owner+ only)
- `PUT /loans/{id}/return` — mark returned (branch_owner+ only)

### Users
- `GET /users` — list borrowers (admin only)
- `GET /users/me` — current user profile
- `POST /auth/signup` — register (via Supabase auth)
- `POST /auth/login` — login (via Supabase auth)

## External APIs

### Open Library (primary)
- Endpoint: `https://openlibrary.org/isbn/{isbn}.json`
- Free, no auth required
- Returns: title, author, publisher, publish date, cover ID
- Cover images: `https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg`

### Google Books (fallback)
- Endpoint: `https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}`
- Free tier generous, optional API key
- Sometimes has better metadata for newer books

## Key User Flows

### 1. Cataloging a book (branch owner)
1. Open catalog page, click "Add Book"
2. Camera activates, scan barcode
3. ISBN extracted → hits `/books/lookup?isbn=...`
4. Preview metadata displayed
5. System checks if book record exists (by ISBN)
   - If yes: add a new copy linked to existing book
   - If no: create book record, then create copy
6. Owner can add copy-specific notes (condition, shelf location)
7. On confirm, `POST /copies` saves copy to their branch

### 2. Browsing (public, no login required)
1. View grid/list of all books
2. Filter by availability, search by title/author, filter by branch
3. Click book to see details: all copies across branches, which are available

### 3. Checking out (branch owner performs)
1. Owner opens copy detail, clicks "Check Out"
2. Selects borrower from dropdown (or invites new borrower by email)
3. Sets due date
4. `POST /loans` creates loan record for that specific copy

### 4. Returning (branch owner)
1. Owner opens copy or borrower's loan list
2. Clicks "Return"
3. `PUT /loans/{id}/return` sets returned_at

## Auth & Permissions

Using Supabase Auth with row-level security (RLS):

- **Public (no login)**: Browse books, view copies and availability, see branches
- **Borrower**: Above + view own loans, manage own profile
- **Branch Owner**: Above + full CRUD on copies at their branch, manage loans for their branch
- **Admin**: Full access to everything, can create branches, manage all users

RLS policies enforce this at the database level, so even if API has bugs, data access is protected.

### Public catalog
The browse experience requires no login. Visitors can search books, see which branches have copies, and check availability. They only need to log in to borrow or to see their loan history.

## Frontend Pages

### Public (no login)
1. **Home/Browse** — book grid with search/filter, branch filter
2. **Book Detail** — metadata, list of copies by branch, availability
3. **Branches** — list of participating libraries with descriptions

### Authenticated (borrower+)
4. **My Loans** — what I have checked out, due dates, history

### Branch Owner
5. **My Branch** — manage copies at my branch
6. **Add Book** — barcode scanner + manual entry form
7. **Branch Loans** — manage checkouts/returns for my branch

### Admin
8. **All Branches** — overview, create new branches
9. **All Users** — manage borrowers and branch owners

## Future Extensions (not in v1)

- Hold/request system (borrower can request unavailable book)
- Email notifications (due date reminders, hold available)
- Book reviews/ratings
- Export to CSV/standard library formats (MARC, etc.)
- Reading lists / curated collections
- Inter-branch transfers (request a book from another branch)

## Development Phases

### Phase 1: Foundation + catalog
- Supabase project setup, schema, RLS policies
- FastAPI skeleton with book/copy/branch CRUD
- ISBN lookup endpoint (Open Library, Google Books fallback)
- Two initial branches: Jun's home library, parents' home library
- Basic frontend: public browse, book detail with copies
- Add book with barcode scanner (using `html5-qrcode` library)
- Email/password auth via Supabase

### Phase 2: Lending
- Loans endpoints (checkout, return)
- Check out / return UI
- My Loans page for borrowers
- Branch Loans management for owners

### Phase 3: Polish
- Search and filtering (by branch, availability)
- Mobile-friendly responsive design
- Error handling, loading states
- Deploy to production

## Getting Started

1. Create Supabase project at supabase.com
2. Run schema SQL in Supabase SQL editor
3. Set up RLS policies (public read on books/copies/branches, authenticated write)
4. Create FastAPI project with supabase-py client
5. Implement `/books/lookup` endpoint first (instant gratification with barcode scanning)
6. Create your first branch (your home library)
7. Build up from there