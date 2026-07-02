from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.core.dependencies import require_admin, get_current_user
from app.core.security import get_password_hash

router = APIRouter()

@router.get("/", response_model=List[schemas.User])
def get_users(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """All authenticated users can view the user list (read-only consultation)."""
    return db.query(models.User).all()

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_username = db.query(models.User).filter(models.User.username == user.username).first()
    if db_username:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user.password)
    
    # Map role string to enum
    role_enum = models.UserRole.QA_DEVELOPER
    try:
        if user.role:
            role_enum = models.UserRole(user.role.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role specified")

    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=role_enum
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user_update.role:
        try:
            db_user.role = models.UserRole(user_update.role.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role specified")
            
    if user_update.email:
        db_user.email = user_update.email
    if user_update.username:
        db_user.username = user_update.username

    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
        
    db.delete(db_user)
    db.commit()
    return {"status": "deleted", "id": user_id}
