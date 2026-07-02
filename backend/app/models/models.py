from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
import datetime
import enum

from app.core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    QA_DEVELOPER = "qa_developer"
    MANAGER = "manager"
    USER = "user"

class RequirementType(str, enum.Enum):
    USER_STORY = "USER_STORY"
    SWAGGER = "SWAGGER"
    DOCUMENT = "DOCUMENT"

class ExecutionStatus(str, enum.Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.QA_DEVELOPER)
    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    github_url = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="projects")
    requirements = relationship("Requirement", back_populates="project")

class Requirement(Base):
    __tablename__ = "requirements"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    title = Column(String)
    content = Column(Text)
    type = Column(Enum(RequirementType))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    project = relationship("Project", back_populates="requirements")
    scenarios = relationship("Scenario", back_populates="requirement", cascade="all, delete-orphan")

class Scenario(Base):
    __tablename__ = "scenarios"
    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    title = Column(String)
    gherkin_content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    requirement = relationship("Requirement", back_populates="scenarios")
    test_scripts = relationship("TestScript", back_populates="scenario", cascade="all, delete-orphan")

class TestScript(Base):
    __tablename__ = "test_scripts"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    tool = Column(String)  # playwright, selenium, karate
    language = Column(String) # javascript, python, java
    code = Column(Text)
    scenario = relationship("Scenario", back_populates="test_scripts")
    results = relationship("ExecutionResult", back_populates="test_script", cascade="all, delete-orphan")

class ExecutionResult(Base):
    __tablename__ = "execution_results"
    id = Column(Integer, primary_key=True, index=True)
    test_script_id = Column(Integer, ForeignKey("test_scripts.id"))
    status = Column(Enum(ExecutionStatus))
    output = Column(Text)
    duration = Column(Integer) # in seconds
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    kpis = Column(JSON) # e.g., {"coverage": 85, "bugs_detected": 2}
    test_script = relationship("TestScript", back_populates="results")
