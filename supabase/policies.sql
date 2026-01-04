-- Home Library System RLS Policies
-- Run this after schema.sql in Supabase SQL Editor

-- Helper function to check if user is admin
create or replace function is_admin()
returns boolean as $$
  select exists (
    select 1 from profiles
    where id = auth.uid() and role = 'admin'
  );
$$ language sql security definer;

-- Helper function to check if user owns a branch
create or replace function owns_branch(branch_uuid uuid)
returns boolean as $$
  select exists (
    select 1 from branches
    where id = branch_uuid and owner_id = auth.uid()
  );
$$ language sql security definer;

-- ============ PROFILES ============

-- Anyone can read profiles (needed for displaying borrower names)
create policy "Public read profiles"
  on profiles for select
  using (true);

-- Users can update their own profile
create policy "Users update own profile"
  on profiles for update
  using (auth.uid() = id);

-- Admins can update any profile (for role changes)
create policy "Admins update any profile"
  on profiles for update
  using (is_admin());

-- ============ BRANCHES ============

-- Anyone can read branches
create policy "Public read branches"
  on branches for select
  using (true);

-- Admins can create branches
create policy "Admins create branches"
  on branches for insert
  with check (is_admin());

-- Branch owners and admins can update their branch
create policy "Owners update own branch"
  on branches for update
  using (owner_id = auth.uid() or is_admin());

-- Admins can delete branches
create policy "Admins delete branches"
  on branches for delete
  using (is_admin());

-- ============ BOOKS ============

-- Anyone can read books
create policy "Public read books"
  on books for select
  using (true);

-- Authenticated users can create books (when adding copies)
create policy "Authenticated create books"
  on books for insert
  with check (auth.uid() is not null);

-- Branch owners and admins can update books
create policy "Branch owners update books"
  on books for update
  using (
    is_admin() or
    exists (
      select 1 from branches where owner_id = auth.uid()
    )
  );

-- Admins can delete books
create policy "Admins delete books"
  on books for delete
  using (is_admin());

-- ============ COPIES ============

-- Anyone can read copies
create policy "Public read copies"
  on copies for select
  using (true);

-- Branch owners can create copies at their branch
create policy "Branch owners create copies"
  on copies for insert
  with check (owns_branch(branch_id) or is_admin());

-- Branch owners can update copies at their branch
create policy "Branch owners update copies"
  on copies for update
  using (owns_branch(branch_id) or is_admin());

-- Branch owners can delete copies at their branch
create policy "Branch owners delete copies"
  on copies for delete
  using (owns_branch(branch_id) or is_admin());

-- ============ LOANS ============

-- Borrowers can see their own loans
create policy "Borrowers read own loans"
  on loans for select
  using (borrower_id = auth.uid());

-- Branch owners can see loans for copies at their branch
create policy "Branch owners read branch loans"
  on loans for select
  using (
    exists (
      select 1 from copies c
      join branches b on c.branch_id = b.id
      where c.id = loans.copy_id and b.owner_id = auth.uid()
    )
  );

-- Admins can see all loans
create policy "Admins read all loans"
  on loans for select
  using (is_admin());

-- Branch owners can create loans for copies at their branch
create policy "Branch owners create loans"
  on loans for insert
  with check (
    exists (
      select 1 from copies c
      join branches b on c.branch_id = b.id
      where c.id = copy_id and b.owner_id = auth.uid()
    ) or is_admin()
  );

-- Branch owners can update loans (return) for copies at their branch
create policy "Branch owners update loans"
  on loans for update
  using (
    exists (
      select 1 from copies c
      join branches b on c.branch_id = b.id
      where c.id = loans.copy_id and b.owner_id = auth.uid()
    ) or is_admin()
  );

-- Branch owners can delete loans at their branch (admin use only)
create policy "Branch owners delete loans"
  on loans for delete
  using (is_admin());
