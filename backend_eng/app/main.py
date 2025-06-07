from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Import the routers
from app.api import projects, inspections, photos

# Create necessary directories first
os.makedirs("app/data", exist_ok=True)
os.makedirs("app/static/uploads/pdfs", exist_ok=True)
os.makedirs("app/static/uploads/photos", exist_ok=True)

# Import database components for initialization
from app.db.database import create_tables

# Initialize database tables
create_tables()

# Create the FastAPI app
app = FastAPI(
    title="Construction Inspection API",
    description="API for managing construction inspections and photos",
    version="1.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
os.makedirs("app/static", exist_ok=True)
app.mount("/app/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(inspections.router, prefix="/api", tags=["inspections"])
app.include_router(photos.router, prefix="/api", tags=["photos"])

@app.get("/")
async def root():
    return {"message": "Welcome to Construction Inspection API"}
