from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.models.models import RequirementType

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str
    role: Optional[str] = "qa_developer"

class User(UserBase):
    id: int
    role: str
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    role: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str


class RequirementBase(BaseModel):
    title: str
    content: str
    type: RequirementType
    project_id: int

class RequirementCreate(RequirementBase):
    pass

class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None

class Requirement(RequirementBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    owner_id: Optional[int] = None

class GithubProjectCreate(BaseModel):
    name: str
    type: str = "Playwright"
    language: str = "TypeScript"
    visibility: str = "private"

class Project(ProjectBase):
    id: int
    created_at: Optional[datetime] = None
    github_url: Optional[str] = None
    owner_id: Optional[int] = None
    class Config:
        from_attributes = True

class ProjectDashboard(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None
    github_url: Optional[str] = None
    owner_username: Optional[str] = None
    last_execution_status: str = "Unknown"
    class Config:
        from_attributes = True

class ScenarioBase(BaseModel):
    title: str
    gherkin_content: str
    requirement_id: int

class Scenario(ScenarioBase):
    id: int
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class ScenarioUpdate(BaseModel):
    gherkin_content: str

class GithubWebhookPayload(BaseModel):
    repository: str
    status: str

class TestScriptBase(BaseModel):
    scenario_id: int
    tool: str
    language: str
    code: str

class TestScript(TestScriptBase):
    id: int
    class Config:
        from_attributes = True

class ExecutionResultBase(BaseModel):
    status: str
    output: Optional[str] = None
    duration: int
    kpis: Optional[dict] = None

class ExecutionResult(ExecutionResultBase):
    id: int
    test_script_id: int
    created_at: datetime
    # Alias for frontend compatibility
    executed_at: Optional[datetime] = None
    class Config:
        from_attributes = True

    def model_post_init(self, __context):
        # Mirror created_at to executed_at for frontend consumption
        if self.executed_at is None and self.created_at:
            object.__setattr__(self, 'executed_at', self.created_at)
