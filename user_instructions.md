# Home Library System - User Instructions

## For Library Guests (Public Visitors & Borrowers)

### Browsing the Catalog (No Login Required)
1. **Home page**: See all books across all branches in a grid view
2. **Search**: Type in the search bar to filter by title or author
3. **Filter by branch**: Click a branch name to see only books at that location
4. **Book details**: Click any book to see:
   - Full metadata (author, publisher, description, etc.)
   - Which branches have copies
   - Whether each copy is available or currently on loan

### As a Borrower (Logged In)
1. **Sign up**: Click "Sign Up", enter your email and password
2. **Log in**: Use your email/password to access borrower features
3. **My Loans**: View your current checkouts and due dates
4. **Loan history**: See what you've borrowed in the past
5. **Returning a book**: Bring the physical book back to the branch you borrowed it from. The branch owner will mark it returned in the system.

Note: You cannot check out books yourself online. Borrowing happens in person - you arrange with the branch owner, and they record the loan.

---

## For Library Admins & Branch Owners

### Initial Setup (Admin)
1. Create your Supabase project and run the schema
2. Create your admin account (first user, manually set role to 'admin' in profiles table)
3. Create branches for each physical location (e.g., "Jun's Home Library", "Parents' Library")
4. Assign branch owners (yourself or family members)

### Adding Books (Branch Owner)
1. **Navigate to "Add Book"** from your branch dashboard
2. **Scan the barcode**:
   - Allow camera access when prompted
   - Point camera at the book's ISBN barcode
   - Wait for the beep/confirmation
3. **Review the metadata**: Title, author, cover image pulled automatically from Open Library
4. **Add copy details** (optional):
   - Condition: excellent, good, fair, poor
   - Notes: "Signed by author", "Missing dust jacket", etc.
5. **Confirm**: The book is added to your branch's inventory

For books without barcodes:
1. Click "Manual Entry"
2. Fill in title, author, and other details
3. Save to add the copy

### Managing Loans (Branch Owner)
**Checking out a book:**
1. Go to "Branch Loans" or find the specific copy
2. Click "Check Out"
3. Select the borrower from the dropdown (or invite them by email if new)
4. Set the due date
5. Confirm - hand them the physical book

**Processing a return:**
1. When the borrower brings the book back
2. Find the loan in "Branch Loans" or the copy's detail page
3. Click "Return"
4. The copy is now available for others

### Viewing Reports (Branch Owner)
- **Current loans**: Who has what from your branch
- **Overdue**: Books past their due date
- **Loan history**: Complete record of past checkouts

### Managing Users (Admin Only)
- View all registered borrowers
- Promote users to branch_owner role
- Create new branches and assign owners

---

## Quick Reference

| Task | Who Can Do It | Where |
|------|---------------|-------|
| Browse books | Anyone | Home page |
| View book details | Anyone | Click any book |
| Sign up / Log in | Anyone | Login page |
| View my loans | Logged-in borrower | My Loans |
| Add a book | Branch owner | Add Book |
| Check out a copy | Branch owner | Branch Loans |
| Return a copy | Branch owner | Branch Loans |
| Create branches | Admin | Admin panel |
| Manage users | Admin | Admin panel |
