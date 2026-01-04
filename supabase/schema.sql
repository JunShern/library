-- Home Library System Schema
-- Run this in Supabase SQL Editor

-- Profiles extends Supabase auth.users
create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text not null,
  role text not null default 'borrower' check (role in ('admin', 'branch_owner', 'borrower')),
  created_at timestamptz default now()
);

-- Auto-create profile on signup
create or replace function handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, name, role)
  values (new.id, coalesce(new.raw_user_meta_data->>'name', new.email), 'borrower');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function handle_new_user();

-- Branch = a physical location
create table branches (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  owner_id uuid references profiles(id) not null,
  address text,
  created_at timestamptz default now()
);

-- Book = bibliographic record (one per ISBN/title)
create table books (
  id uuid primary key default gen_random_uuid(),
  isbn text unique,
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
  book_id uuid references books(id) on delete cascade not null,
  branch_id uuid references branches(id) on delete cascade not null,
  condition text check (condition in ('excellent', 'good', 'fair', 'poor')),
  notes text,
  added_by uuid references profiles(id),
  added_at timestamptz default now()
);

-- Loans reference copies, not books
create table loans (
  id uuid primary key default gen_random_uuid(),
  copy_id uuid references copies(id) on delete cascade not null,
  borrower_id uuid references profiles(id) not null,
  borrowed_at timestamptz default now(),
  due_date date not null,
  returned_at timestamptz,
  notes text
);

-- Indexes for common queries
create index idx_copies_book_id on copies(book_id);
create index idx_copies_branch_id on copies(branch_id);
create index idx_loans_copy_id on loans(copy_id);
create index idx_loans_borrower_id on loans(borrower_id);
create index idx_loans_active on loans(copy_id) where returned_at is null;
create index idx_books_isbn on books(isbn) where isbn is not null;

-- Enable RLS on all tables
alter table profiles enable row level security;
alter table branches enable row level security;
alter table books enable row level security;
alter table copies enable row level security;
alter table loans enable row level security;
