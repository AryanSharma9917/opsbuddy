from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

IssueType = Literal["kubernetes", "docker", "cicd", "general"]


class AnalysisRequest(BaseModel):
    issue_type: IssueType
    details: str = Field(min_length=10, max_length=12_000)


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=500)
    likely_causes: list[str] = Field(min_length=1, max_length=3)
    next_steps: list[str] = Field(min_length=1, max_length=5)
    commands: list[str] = Field(min_length=1, max_length=4)
    safety_note: str = Field(min_length=1, max_length=300)
