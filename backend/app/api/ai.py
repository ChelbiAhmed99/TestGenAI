from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.services.ai_service import ai_service

router = APIRouter()

class GenerateGherkinRequest(schemas.BaseModel):
    requirement: str

@router.post("/analyze-requirement")
async def analyze_requirement(requirement_id: int, db: Session = Depends(get_db)):
    requirement = db.query(models.Requirement).filter(models.Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    gherkin = await ai_service.generate_gherkin(requirement.content)
    
    scenario = models.Scenario(
        requirement_id=requirement_id,
        title=f"AI Generated for {requirement.title}",
        gherkin_content=gherkin
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    
    return {"status": "success", "scenario_id": scenario.id}

@router.post("/generate-gherkin")
async def api_generate_gherkin(req: GenerateGherkinRequest):
    gherkin = await ai_service.generate_gherkin(req.requirement)
    return {"gherkin": gherkin}

class GenerateTestStrategyRequest(schemas.BaseModel):
    requirement: str

@router.post("/generate-test-strategy")
async def generate_test_strategy(req: GenerateTestStrategyRequest):
    return {
        "strategy": {
            "type": "E2E UI Testing",
            "priority": "High",
            "framework": "Playwright",
            "coverage": ["Positive Path", "Negative Path", "Edge Cases"]
        }
    }
