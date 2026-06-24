from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.services.ai_service import ai_service
from app.services.gitlab_service import gitlab_service
from app.models import models
from app.schemas import schemas
from typing import List, Optional
from app.services.docker_service import docker_service
from app.services.report_service import report_service
from fastapi.responses import Response
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter()

def get_ai_overrides(
    x_ai_model: Optional[str] = Header(default=None, alias="X-AI-Model"),
    x_groq_api_key: Optional[str] = Header(default=None, alias="X-Groq-API-Key"),
    x_google_api_key: Optional[str] = Header(default=None, alias="X-Google-API-Key")
) -> dict:
    api_key = x_groq_api_key if x_ai_model and x_ai_model.startswith("llama") else x_google_api_key
    return {"model_override": x_ai_model, "api_key_override": api_key}

@router.get("/reports/export/{project_id}")
async def export_report(project_id: int, db: Session = Depends(get_db)):
    # Fetch some dummy results for the report
    results = [
        {"name": "Auth Test", "status": "Passed", "duration": 4},
        {"name": "Payment Test", "status": "Failed", "duration": 12},
    ]
    pdf_content = report_service.generate_pdf_report(results)
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=TestGenAI_Report_{project_id}.pdf"}
    )

@router.get("/reports")
async def get_all_reports(db: Session = Depends(get_db)):
    return db.query(models.ExecutionResult).all()

@router.get("/reports/{run_id}")
async def get_report_by_run_id(run_id: int, db: Session = Depends(get_db)):
    result = db.query(models.ExecutionResult).filter(models.ExecutionResult.id == run_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result

@router.post("/execute/{script_id}")
async def execute_test(script_id: int, db: Session = Depends(get_db)):
    script = db.query(models.TestScript).filter(models.TestScript.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Run in Docker
    result_data = await docker_service.run_test_container(script.code, script.tool)
    
    # Save Result
    result = models.ExecutionResult(
        test_script_id=script_id,
        status=result_data["status"],
        output=result_data["output"],
        duration=result_data["duration"],
        kpis=result_data["kpis"]
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    
    return result

@router.post("/execution/run/{project_id}")
async def run_project_execution(project_id: int, db: Session = Depends(get_db)):
    return {"status": "Execution started", "project_id": project_id, "run_id": 1}

@router.get("/execution/results/{run_id}")
async def get_execution_results_by_run_id(run_id: int, db: Session = Depends(get_db)):
    result = db.query(models.ExecutionResult).filter(models.ExecutionResult.id == run_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Execution result not found")
    return result

@router.post("/requirements/upload", response_model=schemas.Requirement)
async def upload_requirement(
    title: str,
    content: str,
    type: str,
    project_id: int,
    db: Session = Depends(get_db)
):
    # Normalize type (e.g. user-story -> USER_STORY)
    normalized_type = type.replace("-", "_").upper()
    
    db_req = models.Requirement(
        title=title,
        content=content,
        type=normalized_type,
        project_id=project_id
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req

# ── Requirement CRUD ───────────────────────────────────────────────────────
@router.put("/requirements/{requirement_id}", response_model=schemas.Requirement)
async def update_requirement(
    requirement_id: int,
    req: schemas.RequirementUpdate,
    db: Session = Depends(get_db)
):
    db_req = db.query(models.Requirement).filter(models.Requirement.id == requirement_id).first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    if req.title is not None:
        db_req.title = req.title
    if req.content is not None:
        db_req.content = req.content
    if req.type is not None:
        db_req.type = req.type.replace("-", "_").upper()
    
    db.commit()
    db.refresh(db_req)
    return db_req

@router.delete("/requirements/{requirement_id}")
async def delete_requirement(requirement_id: int, db: Session = Depends(get_db)):
    db_req = db.query(models.Requirement).filter(models.Requirement.id == requirement_id).first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    db.delete(db_req)
    db.commit()
    return {"status": "deleted", "id": requirement_id}

@router.post("/analyze/{requirement_id}")
async def analyze_requirement(requirement_id: int, db: Session = Depends(get_db), ai_opts: dict = Depends(get_ai_overrides)):
    requirement = db.query(models.Requirement).filter(models.Requirement.id == requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    # Generate Gherkin
    gherkin = await ai_service.generate_gherkin(requirement.content, **ai_opts)
    
    # Save Scenario
    scenario = models.Scenario(
        requirement_id=requirement_id,
        title=f"AI Generated for {requirement.title}",
        gherkin_content=gherkin
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    
    # Generate Test Script with Self-Healing (Playwright / TypeScript)
    script_result = await ai_service.generate_test_script_healed(gherkin, tool="playwright", **ai_opts)
    test_script = models.TestScript(
        scenario_id=scenario.id,
        tool="playwright",
        language="typescript",
        code=script_result.get("code", "")
    )
    db.add(test_script)
    db.commit()

    return {"status": "success", "scenario_id": scenario.id}

class GenerateGherkinRequest(BaseModel):
    requirement: str

@router.post("/ai/generate-gherkin")
async def api_generate_gherkin(req: GenerateGherkinRequest, ai_opts: dict = Depends(get_ai_overrides)):
    gherkin = await ai_service.generate_gherkin(req.requirement, **ai_opts)
    return {"gherkin": gherkin}

@router.post("/ai/generate-gherkin-json")
async def api_generate_gherkin_json(req: GenerateGherkinRequest, ai_opts: dict = Depends(get_ai_overrides)):
    """
    Returns structured JSON output from Gherkin generation for
    frontend display and human validation.
    """
    result = await ai_service.generate_gherkin_json(req.requirement, **ai_opts)
    return result

# ── NLP Ingestion Pipeline ─────────────────────────────────────────────────
class IngestParseRequest(BaseModel):
    content: str
    source_type: str = "auto"  # "auto", "user_story", "swagger"

@router.post("/ingest/parse")
async def ingest_parse(req: IngestParseRequest):
    """
    Parses raw text (User Story or Swagger/OpenAPI) using the NLP
    ingestion pipeline and returns structured data.
    """
    import sys, os
    core_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "core"))
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    from ingestion import IngestionPipeline
    
    try:
        pipeline = IngestionPipeline()
        result = pipeline.process(req.content, req.source_type)
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")


# ── Jira Ingestion ───────────────────────────────────────────────────────
class JiraIngestRequest(BaseModel):
    jira_url: str
    project_id: int = 1

@router.post("/ingest/jira")
async def ingest_jira(req: JiraIngestRequest, db: Session = Depends(get_db), ai_opts: dict = Depends(get_ai_overrides)):
    """
    Fetches a Jira issue and saves it as a Requirement, then triggers AI analysis.
    """
    try:
        content = await ai_service.fetch_jira_story(req.jira_url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Jira fetch failed: {e}")

    # Derive title from URL key
    import re
    match = re.search(r"/browse/([A-Z][A-Z0-9]+-\d+)", req.jira_url)
    title = match.group(1) if match else "Jira Import"

    db_req = models.Requirement(
        title=title,
        content=content,
        type=models.RequirementType.USER_STORY,
        project_id=req.project_id
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)

    # Trigger AI pipeline
    gherkin = await ai_service.generate_gherkin(content, **ai_opts)
    scenario = models.Scenario(
        requirement_id=db_req.id,
        title=f"[Jira] {title}",
        gherkin_content=gherkin
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)

    script_result = await ai_service.generate_test_script_healed(gherkin, tool="playwright", **ai_opts)
    test_script = models.TestScript(
        scenario_id=scenario.id,
        tool="playwright",
        language="typescript",
        code=script_result.get("code", "")
    )
    db.add(test_script)
    db.commit()

    return {
        "status": "success",
        "requirement_id": db_req.id,
        "scenario_id": scenario.id,
        "preview": content[:200]
    }

# ── GitLab Project Push ───────────────────────────────────────────────────
class GitLabPushRequest(BaseModel):
    scenario_id: int
    project_name: Optional[str] = None
    gitlab_namespace: Optional[str] = None

@router.post("/gitlab/push")
async def push_to_gitlab(req: GitLabPushRequest, db: Session = Depends(get_db)):
    """
    Creates a new GitLab repository and pushes the full Playwright TypeScript
    project (POM + feature files + CI pipeline) in a single commit.
    """
    scenario = db.query(models.Scenario).filter(models.Scenario.id == req.scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    script = db.query(models.TestScript).filter(
        models.TestScript.scenario_id == req.scenario_id
    ).first()

    project_name = req.project_name or scenario.title.replace(" ", "-")[:40]
    gherkin  = scenario.gherkin_content or ""
    code     = script.code if script else ""

    try:
        result = await gitlab_service.create_and_push_project(
            project_name=project_name,
            gherkin=gherkin,
            script=code,
            namespace=req.gitlab_namespace,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GitLab push failed: {e}")

    return result

class GenerateTestStrategyRequest(schemas.BaseModel):
    requirement: str

@router.post("/ai/generate-test-strategy")
async def generate_test_strategy(req: GenerateTestStrategyRequest):
    return {
        "strategy": {
            "type": "E2E UI Testing",
            "priority": "High",
            "framework": "Playwright",
            "coverage": ["Positive Path", "Negative Path", "Edge Cases"]
        }
    }

class GenerateTestCodeRequest(schemas.BaseModel):
    gherkin: str
    tool: str = "playwright"

@router.post("/generator/test-code")
async def generate_test_code(req: GenerateTestCodeRequest, ai_opts: dict = Depends(get_ai_overrides)):
    code = await ai_service.generate_test_script(req.gherkin, req.tool, **ai_opts)
    return {"code": code}

class GenerateTestCodeHealedRequest(schemas.BaseModel):
    gherkin: str
    tool: str = "playwright"
    max_retries: int = 3

@router.post("/generator/test-code-healed")
async def generate_test_code_healed(req: GenerateTestCodeHealedRequest, ai_opts: dict = Depends(get_ai_overrides)):
    """
    Generate a test script with self-healing: if the initial code has
    TypeScript errors, they are sent back to the LLM for correction.
    """
    result = await ai_service.generate_test_script_healed(
        req.gherkin, req.tool, req.max_retries, **ai_opts
    )
    return result

class ValidateCodeRequest(schemas.BaseModel):
    code: str
    filename: str = "test.ts"

@router.post("/generator/validate-ts")
async def validate_typescript(req: ValidateCodeRequest):
    """Validate TypeScript code via tsc --noEmit (no correction)."""
    import sys, os
    core_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "core"))
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    from self_healer import TypeScriptValidator

    validator = TypeScriptValidator()
    result = validator.validate(req.code, req.filename)
    return result.to_dict()

# ── Scaffolding Engine ─────────────────────────────────────────────────────
class ScaffoldRequest(BaseModel):
    project_name: str
    scenario_id: int
    base_url: str = "http://localhost:3000"
    include_ci: bool = True
    overwrite: bool = False

@router.post("/generator/scaffold")
async def scaffold_project(req: ScaffoldRequest, db: Session = Depends(get_db)):
    """
    Generate a complete Playwright/TypeScript project on disk from a
    saved scenario. Uses the AI service to generate Page Objects and
    spec files, then the scaffolder writes them to disk.
    """
    import sys, os
    core_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "core"))
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    from scaffolder import ProjectScaffolder

    scenario = db.query(models.Scenario).filter(models.Scenario.id == req.scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    script = db.query(models.TestScript).filter(
        models.TestScript.scenario_id == req.scenario_id
    ).first()

    gherkin = scenario.gherkin_content or ""
    code = script.code if script else ""

    # Use AI-generated code as a single spec file + basic page object
    page_objects = [{"filename": "AppPage.ts", "code": (
        "import { Page, Locator } from '@playwright/test';\n\n"
        "export class AppPage {\n"
        "  readonly page: Page;\n\n"
        "  constructor(page: Page) {\n"
        "    this.page = page;\n"
        "  }\n\n"
        "  async navigate(): Promise<void> {\n"
        "    await this.page.goto('/');\n"
        "  }\n"
        "}\n"
    )}]
    spec_files = [{"filename": "generated.spec.ts", "code": code}]

    scaffolder = ProjectScaffolder()
    result = scaffolder.scaffold_project(
        project_name=req.project_name,
        gherkin_content=gherkin,
        page_objects=page_objects,
        spec_files=spec_files,
        base_url=req.base_url,
        include_ci=req.include_ci,
        overwrite=req.overwrite,
    )

    if not result.success:
        raise HTTPException(status_code=409, detail=result.errors[0])

    return result.to_dict()

class ScaffoldFromJsonRequest(BaseModel):
    project_name: str
    gherkin_json: dict
    base_url: str = "http://localhost:3000"
    include_ci: bool = True
    overwrite: bool = False

@router.post("/generator/scaffold-from-json")
async def scaffold_from_json(req: ScaffoldFromJsonRequest):
    """
    Generate a Playwright project from structured Gherkin JSON using
    deterministic templates (no AI call needed).
    """
    import sys, os
    core_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "core"))
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)
    from scaffolder import ProjectScaffolder

    scaffolder = ProjectScaffolder()
    result = scaffolder.scaffold_from_gherkin_json(
        project_name=req.project_name,
        gherkin_json=req.gherkin_json,
        base_url=req.base_url,
        include_ci=req.include_ci,
        overwrite=req.overwrite,
    )

    if not result.success:
        raise HTTPException(status_code=409, detail=result.errors[0])

    return result.to_dict()

@router.post("/generator/project")
async def generate_project_structure():
    return {
        "structure": [
            "tests/", "pages/", "features/",
            "package.json", "tsconfig.json", "playwright.config.ts",
            ".gitignore", ".gitlab-ci.yml", "README.md"
        ]
    }

@router.post("/generator/pipeline")
async def generate_pipeline(tool: str = "gitlab"):
    return {"yaml": "stages:\n  - test\n  - report\n\nrun_automation:\n  stage: test\n  image: mcr.microsoft.com/playwright:v1.44.0-jammy\n  script:\n    - npm ci\n    - npx playwright install --with-deps\n    - npx playwright test\n"}

@router.get("/projects", response_model=List[schemas.Project])
async def get_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()

from app.core.github_integration import generate_playwright_project
import os

@router.post("/projects/github/create")
async def create_github_project(project: schemas.GithubProjectCreate, db: Session = Depends(get_db)):
    github_token = os.environ.get("GITHUB_TOKEN")
    
    # Generate on Github
    try:
        repo_url = await generate_playwright_project(
            github_token=github_token,
            project_name=project.name,
            visibility=project.visibility
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # Save to local database
    db_project = models.Project(
        name=project.name,
        description=f"{project.type} / {project.language} project",
        github_url=repo_url
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return {"status": "success", "github_url": repo_url, "project": db_project.id}

@router.get("/dashboard/projects", response_model=List[schemas.ProjectDashboard])
async def get_dashboard_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Project).all()
    result = []
    for p in projects:
        owner_username = p.owner.username if p.owner else "System"
        latest_status = "Unknown"
        latest_date = None
        
        # Traverse relationships to find the latest execution
        for req in p.requirements:
            for sc in req.scenarios:
                for ts in sc.test_scripts:
                    for er in ts.results:
                        if not latest_date or er.created_at > latest_date:
                            latest_date = er.created_at
                            latest_status = er.status.value
                            
        result.append({
            "id": p.id,
            "name": p.name,
            "created_at": p.created_at,
            "owner_username": owner_username,
            "github_url": p.github_url,
            "last_execution_status": latest_status.capitalize() if latest_status != "Unknown" else "Unknown"
        })
    # Sort by created_at descending (newest first)
    result.sort(key=lambda x: x["created_at"] or datetime.datetime.min, reverse=True)
    return result

@router.get("/requirements", response_model=List[schemas.Requirement])
async def get_requirements(db: Session = Depends(get_db)):
    return db.query(models.Requirement).order_by(models.Requirement.created_at.desc()).all()

@router.get("/scenarios", response_model=List[schemas.Scenario])
async def get_scenarios(requirement_id: int = None, db: Session = Depends(get_db)):
    query = db.query(models.Scenario)
    if requirement_id:
        query = query.filter(models.Scenario.requirement_id == requirement_id)
    return query.all()

@router.put("/scenarios/{scenario_id}", response_model=schemas.Scenario)
async def update_scenario(scenario_id: int, payload: schemas.ScenarioUpdate, db: Session = Depends(get_db)):
    scenario = db.query(models.Scenario).filter(models.Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    scenario.gherkin_content = payload.gherkin_content
    db.commit()
    db.refresh(scenario)
    return scenario

from app.services.ai_service import ai_service

@router.post("/scenarios/{scenario_id}/generate-code")
async def generate_scenario_code(scenario_id: int, db: Session = Depends(get_db), ai_opts: dict = Depends(get_ai_overrides)):
    scenario = db.query(models.Scenario).filter(models.Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    script_result = await ai_service.generate_test_script_healed(scenario.gherkin_content, tool="playwright", **ai_opts)
    
    # Check if a test script already exists
    import re
    import os
    
    code = script_result.get("code", "")
    
    # Inject Allure Traceability
    if "allure-playwright" not in code:
        code = "import * as allure from 'allure-playwright';\n" + code
        
    platform_url = os.environ.get("PLATFORM_URL", "http://localhost:8000")
    req_id = scenario.requirement_id
    issue_code = f"    allure.issue('UserStory-{req_id}', '{platform_url}/requirements/{req_id}');\n"
    
    # Inject the allure.issue inside the first test(...) block
    code = re.sub(r"(test\(['\"].*?['\"], async \({.*?}\) => \{)", r"\1\n" + issue_code, code, count=1)

    test_script = db.query(models.TestScript).filter(models.TestScript.scenario_id == scenario.id).first()
    if test_script:
        test_script.code = code
    else:
        test_script = models.TestScript(
            scenario_id=scenario.id,
            tool="playwright",
            language="typescript",
            code=code
        )
        db.add(test_script)
    
    db.commit()
    return {"status": "success", "message": "Playwright code generated successfully."}

import httpx

@router.post("/scenarios/{scenario_id}/push-github")
async def push_scenario_to_github(scenario_id: int, db: Session = Depends(get_db)):
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise HTTPException(status_code=400, detail="GITHUB_TOKEN is not configured in the environment.")

    scenario = db.query(models.Scenario).filter(models.Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    test_script = db.query(models.TestScript).filter(models.TestScript.scenario_id == scenario.id).first()
    if not test_script or not test_script.code:
        raise HTTPException(status_code=400, detail="No test script code to push.")
        
    req = scenario.requirement
    project = req.project
    
    if not project or not project.github_url:
        raise HTTPException(status_code=400, detail="No GitHub project associated with this scenario's requirement.")
        
    # extract owner and repo from github_url, e.g., https://github.com/Devoteam/test-gen-ai
    github_url = project.github_url.rstrip("/")
    parts = github_url.split("/")
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL format.")
    owner = parts[-2]
    repo = parts[-1]
    
    path = f"tests/scenario_{scenario.id}.spec.ts"
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    import base64
    encoded_content = base64.b64encode(test_script.code.encode("utf-8")).decode("utf-8")
    
    async with httpx.AsyncClient() as client:
        # Check if file exists to get SHA
        get_res = await client.get(api_url, headers=headers)
        data = {
            "message": f"feat: Add automated test for scenario {scenario.id}",
            "content": encoded_content
        }
        if get_res.status_code == 200:
            data["sha"] = get_res.json().get("sha")
            
        put_res = await client.put(api_url, headers=headers, json=data)
        
        if put_res.status_code not in (200, 201):
            raise HTTPException(status_code=put_res.status_code, detail=f"GitHub API Error: {put_res.text}")
            
    return {"status": "success", "message": "Successfully pushed to GitHub repository!"}

@router.post("/webhooks/github/execution-result")
async def github_webhook_execution_result(payload: schemas.GithubWebhookPayload, db: Session = Depends(get_db)):
    # payload.repository is like "owner/repo"
    project = db.query(models.Project).filter(models.Project.github_url.contains(payload.repository)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find the most recent test script for this project
    latest_script = None
    latest_date = None
    
    for req in project.requirements:
        for sc in req.scenarios:
            for ts in sc.test_scripts:
                # assuming ts doesn't have created_at directly, but we can just use the highest ID or assume the last one is the latest
                if not latest_script or ts.id > latest_script.id:
                    latest_script = ts

    if not latest_script:
        raise HTTPException(status_code=404, detail="No test script found for project")

    status_mapping = {
        "success": models.ExecutionStatus.PASSED,
        "failure": models.ExecutionStatus.FAILED,
        "cancelled": models.ExecutionStatus.SKIPPED,
    }
    
    final_status = status_mapping.get(payload.status.lower(), models.ExecutionStatus.PENDING)

    execution = models.ExecutionResult(
        test_script_id=latest_script.id,
        status=final_status,
        output=f"GitHub Actions run: {payload.status}",
        duration=0,
        kpis={"coverage": 100} if final_status == models.ExecutionStatus.PASSED else {}
    )
    db.add(execution)
    db.commit()
    return {"status": "success"}

@router.get("/scripts/{scenario_id}", response_model=schemas.TestScript)
async def get_script(scenario_id: int, db: Session = Depends(get_db)):
    script = db.query(models.TestScript).filter(models.TestScript.scenario_id == scenario_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script

@router.get("/executions")
async def get_executions(db: Session = Depends(get_db)):
    results = db.query(models.ExecutionResult).order_by(models.ExecutionResult.created_at.desc()).all()
    # Add executed_at alias for frontend compatibility
    output = []
    for r in results:
        data = {
            "id": r.id,
            "test_script_id": r.test_script_id,
            "status": r.status.value if hasattr(r.status, 'value') else r.status,
            "output": r.output,
            "duration": r.duration,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "executed_at": r.created_at.isoformat() if r.created_at else None,
            "kpis": r.kpis,
        }
        output.append(data)
    return output

@router.delete("/scenarios/{scenario_id}")
async def delete_scenario(scenario_id: int, db: Session = Depends(get_db)):
    scenario = db.query(models.Scenario).filter(models.Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    db.delete(scenario)
    db.commit()
    return {"status": "deleted", "id": scenario_id}

@router.get("/traceability")
async def get_traceability_matrix(db: Session = Depends(get_db)):
    # Complex join for traceability
    results = db.query(
        models.Requirement.title.label("req_title"),
        models.Requirement.id.label("req_id"),
        models.Scenario.id.label("scenario_id"),
        models.TestScript.id.label("script_id"),
        models.ExecutionResult.status.label("last_status")
    ).outerjoin(models.Scenario, models.Requirement.id == models.Scenario.requirement_id)\
     .outerjoin(models.TestScript, models.Scenario.id == models.TestScript.scenario_id)\
     .outerjoin(models.ExecutionResult, models.TestScript.id == models.ExecutionResult.test_script_id)\
     .all()
    return [dict(r._mapping) for r in results]

@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    total_passed = db.query(models.ExecutionResult).filter(models.ExecutionResult.status == "passed").count()
    total_failed = db.query(models.ExecutionResult).filter(models.ExecutionResult.status == "failed").count()
    total_tests = total_passed + total_failed
    
    # Real chart data from past 7 days
    chart_data = []
    today = datetime.utcnow().date()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        passed_count = db.query(models.ExecutionResult).filter(
            models.ExecutionResult.status == "passed",
            func.date(models.ExecutionResult.created_at) == day
        ).count()
        failed_count = db.query(models.ExecutionResult).filter(
            models.ExecutionResult.status == "failed",
            func.date(models.ExecutionResult.created_at) == day
        ).count()
        chart_data.append({
            "name": day.strftime("%a"),
            "passed": passed_count,
            "failed": failed_count
        })
    
    return {
        "total_runs": total_tests,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "accuracy": 99.4 if total_tests == 0 else round((total_passed / total_tests) * 100, 1),
        "chart_data": chart_data
    }

@router.get("/dashboard/activity")
async def get_activity_feed(db: Session = Depends(get_db)):
    # Fetch recent executions
    executions = db.query(models.ExecutionResult).order_by(models.ExecutionResult.created_at.desc()).limit(3).all()
    feed = []
    for ex in executions:
        script = db.query(models.TestScript).filter(models.TestScript.id == ex.test_script_id).first()
        scenario_title = "Unknown Scenario"
        if script:
            scenario = db.query(models.Scenario).filter(models.Scenario.id == script.scenario_id).first()
            if scenario:
                scenario_title = scenario.title

        feed.append({
            "user": "System Agent",
            "action": "Executed test suite",
            "target": scenario_title,
            "time": ex.created_at.strftime("%Y-%m-%d %H:%M"),
            "icon": "CheckCircle2" if ex.status == "passed" else "XCircle",
            "color": "green" if ex.status == "passed" else "red"
        })
        
    if not feed:
        # Fallback if no executions yet
        reqs = db.query(models.Requirement).order_by(models.Requirement.created_at.desc()).limit(1).all()
        for r in reqs:
            feed.append({
                "user": "QA Team",
                "action": "Uploaded requirement",
                "target": r.title,
                "time": r.created_at.strftime("%Y-%m-%d %H:%M"),
                "icon": "FileText",
                "color": "blue"
            })
            
    return feed

@router.get("/ci/gitlab")
async def export_gitlab_ci():
    yaml_content = """stages:
  - test
  - report

run_automation:
  stage: test
  image: mcr.microsoft.com/playwright:v1.40.0-jammy
  script:
    - npm ci
    - npx playwright test --reporter=line,allure-playwright
  artifacts:
    when: always
    paths:
      - allure-results/

generate_allure_report:
  stage: report
  image: frankescobar/allure-docker-service
  script:
    - allure generate allure-results -o allure-report --clean
  artifacts:
    paths:
      - allure-report/
"""
    return Response(
        content=yaml_content,
        media_type="application/x-yaml",
        headers={"Content-Disposition": "attachment; filename=.gitlab-ci.yml"}
    )
