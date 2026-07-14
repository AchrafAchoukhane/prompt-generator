from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TaskType(str, Enum):
    GENERAL = "General"
    IMAGE_GENERATION = "Image Generation"
    CODE_GENERATION = "Code Generation"
    WRITING = "Writing"
    RESEARCH = "Research"
    DATA_ANALYSIS = "Data Analysis"
    CYBERSECURITY = "Cybersecurity"
    LEARNING = "Learning"


class ScoreBreakdown(BaseModel):
    objective: int
    context: int
    audience: int
    output_format: int
    constraints: int
    specificity: int
    success_criteria: int


class OptimizationCreate(BaseModel):
    prompt: str = Field(min_length=3, max_length=12_000)


class AIOptimizationPayload(BaseModel):
    optimized_prompt: str = Field(min_length=20)
    improvements: list[str] = Field(min_length=1, max_length=8)
    missing_information: list[str] = Field(default_factory=list, max_length=8)


class OptimizationRead(BaseModel):
    id: str
    original_prompt: str
    optimized_prompt: str
    task_type: TaskType
    original_score: int
    optimized_score: int
    weaknesses: list[str]
    improvements: list[str]
    missing_information: list[str]
    score_breakdown: ScoreBreakdown
    provider: str
    model: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OptimizationList(BaseModel):
    items: list[OptimizationRead]
    total: int


class HealthRead(BaseModel):
    status: str
    database: str
    ai_provider: str
    ai_configured: bool
