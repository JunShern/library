from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import books, copies, branches, loans, users

app = FastAPI(
    title="Home Library API",
    description="API for the Home Library System",
    version="1.0.0",
)

# CORS - allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(books.router)
app.include_router(copies.router)
app.include_router(branches.router)
app.include_router(loans.router)
app.include_router(users.router)


@app.get("/")
async def root():
    return {
        "name": "Home Library API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
