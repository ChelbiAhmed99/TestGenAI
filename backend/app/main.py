from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.api.router import router as api_router
from app.core.database import engine
from app.models import models, Base

# Create database tables
# This will now work correctly because models are imported above
Base.metadata.create_all(bind=engine)

# Seed initial project and unique admin if empty
from sqlalchemy.orm import Session
from app.core.security import get_password_hash

with Session(engine) as session:
    try:
        # Seed default project
        if not session.query(models.Project).first():
            default_project = models.Project(
                name="Default Project",
                description="Automated initial project for Devoteam Smart Test Accelerator"
            )
            session.add(default_project)
            session.commit()
            
        # Seed unique admin
        if not session.query(models.User).filter(models.User.username == "admin").first():
            admin_user = models.User(
                username="admin",
                email="admin@devoteam.com",
                hashed_password=get_password_hash("admin"),
                role=models.UserRole.ADMIN
            )
            session.add(admin_user)
            session.commit()
            print("✓ Admin seeded: username 'admin', password 'admin'")
            
    except Exception as e:
        print(f"⚠ Seeding skipped or failed: {e}")

app = FastAPI(
    title="Devoteam Smart Test Accelerator API",
    version="4.0.0",
    description="AI-Driven Quality Engineering Platform by Devoteam"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.auth import router as auth_router
from app.api.users import router as users_router

app.include_router(api_router, prefix="/api")
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/users", tags=["users"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Devoteam Smart Test Accelerator API",
        "status": "online",
        "version": "4.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "4.0.0",
        "ai_model": "gemini-2.0-flash",
        "platform": "Devoteam Smart Test Accelerator"
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
