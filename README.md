# Home Library System

A web-based cataloging and lending system for personal book collections.

## Quick Start

### 1. Supabase Setup

1. Create a free project at [supabase.com](https://supabase.com)
2. Go to SQL Editor and run `supabase/schema.sql`
3. Then run `supabase/policies.sql`
4. Go to Project Settings > API Keys and note your:
   - **Project URL** (from Data API section)
   - **Publishable key** (`sb_publishable_...`) - for frontend
   - **Secret key** (`sb_secret_...`) - for backend

### 2. Backend Setup

```bash
cd api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your Supabase credentials:
#   SUPABASE_URL=https://your-project-id.supabase.co
#   SUPABASE_ANON_KEY=sb_publishable_...
#   SUPABASE_SERVICE_KEY=sb_secret_...

# Run the server
python -m uvicorn main:app --reload
```

API runs at http://localhost:8000 (docs at /docs)

### 3. Frontend Setup

1. Edit `docs/js/config.js` with your Supabase credentials:
```javascript
const CONFIG = {
  API_URL: 'http://localhost:8000',
  SUPABASE_URL: 'https://your-project-id.supabase.co',
  SUPABASE_ANON_KEY: 'sb_publishable_...',  // Your publishable key
};
```

2. Serve the frontend (any static server works):
```bash
cd docs
python -m http.server 5500
# Or use VS Code Live Server, npx serve, etc.
```

Frontend runs at http://localhost:5500

### 4. Initial Setup

1. Sign up for an account
2. In Supabase Table Editor, set your profile's `role` to `admin`
3. Create branches for your libraries
4. Start scanning books!

## Deployment

### Backend → Railway

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) and create a new project
3. Select "Deploy from GitHub repo" → choose your repo
4. Set the root directory:
   - Click on the service (purple box)
   - Go to **Settings** → **Source** → **Root Directory**
   - Set to `api`
5. Add environment variables:
   - Go to **Variables** tab
   - Add these:
   ```
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=sb_publishable_...
   SUPABASE_SERVICE_KEY=sb_secret_...
   ```
6. Generate your public URL:
   - Go to **Settings** → **Networking**
   - Click **Generate Domain**
   - When prompted for port, enter `8080`
   - Note your app URL (e.g., `https://library-api-production.up.railway.app`)

### Frontend → GitHub Pages

1. Update `docs/js/config.js` with your production API URL:
   ```javascript
   const CONFIG = {
     API_URL: 'https://library-api.up.railway.app',  // Your Railway URL
     SUPABASE_URL: 'https://your-project-id.supabase.co',
     SUPABASE_ANON_KEY: 'sb_publishable_...',
   };
   ```

2. In your GitHub repo, go to **Settings → Pages**
3. Set source to your branch and folder `/docs`
4. Your site will be live at `https://username.github.io/repo-name/`

### Update CORS

After deploying, update `api/main.py` to allow your GitHub Pages domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "https://username.github.io",  # Add your GitHub Pages domain
    ],
    ...
)
```

Redeploy the API after this change.

## Project Structure

```
library/
├── api/                 # FastAPI backend
│   ├── routers/         # API endpoints
│   ├── services/        # ISBN lookup
│   └── main.py          # App entry
├── docs/                # Frontend (Vanilla HTML/CSS/JS)
│   ├── css/
│   ├── js/
│   └── *.html           # Pages
├── supabase/            # Database setup
│   ├── schema.sql
│   └── policies.sql
├── brief.md             # Design document
└── user_instructions.md # End-user guide
```

## Features

- **ISBN Barcode Scanning**: Add books quickly with camera
- **Multi-Branch Support**: Track books across locations
- **Loan Management**: Check out and return books
- **Public Catalog**: Browse without login
- **Role-Based Access**: Admin, Branch Owner, Borrower

## Tech Stack

- **Database**: Supabase (Postgres + Auth + RLS)
- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla HTML/CSS/JS
- **Barcode Scanning**: html5-qrcode
