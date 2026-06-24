from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models import models
from app.schemas import schemas

router = APIRouter()

@router.post("/upload", response_model=schemas.Requirement)
@router.post("/", response_model=schemas.Requirement)
async def upload_requirement(req: schemas.RequirementCreate, db: Session = Depends(get_db)):
    normalized_type = req.type.replace("-", "_").lower()
    db_req = models.Requirement(
        title=req.title,
        content=req.content,
        type=normalized_type,
        project_id=req.project_id
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req

@router.get("/", response_model=List[schemas.Requirement])
async def get_requirements(db: Session = Depends(get_db)):
    return db.query(models.Requirement).all()

@router.get("/{id}", response_model=schemas.Requirement)
async def get_requirement_by_id(id: int, db: Session = Depends(get_db)):
    req = db.query(models.Requirement).filter(models.Requirement.id == id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return req
