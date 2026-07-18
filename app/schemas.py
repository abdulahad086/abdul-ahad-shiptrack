import re
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import DeploymentStatus, Environment


class ApplicationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    repo_url: str = Field(..., max_length=255, pattern=r"^https://\S+$")

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("name must not be empty after stripping whitespace")
        return v

    model_config = ConfigDict(extra="forbid")


class ApplicationOut(BaseModel):
    id: int
    name: str
    repo_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeploymentCreate(BaseModel):
    application_id: int = Field(..., gt=0)
    version: str = Field(..., max_length=32)
    environment: Environment
    status: DeploymentStatus = Field(default=DeploymentStatus.pending)

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        pattern = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$"
        if not re.match(pattern, v):
            raise ValueError("version must be semver MAJOR.MINOR.PATCH, e.g. 1.4.0")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: DeploymentStatus) -> DeploymentStatus:
        if v == DeploymentStatus.rolled_back:
            raise ValueError("status 'rolled_back' is not allowed during creation")
        return v

    model_config = ConfigDict(extra="forbid")


class DeploymentOut(BaseModel):
    id: int
    application_id: int
    version: str
    environment: Environment
    status: DeploymentStatus
    deployed_at: datetime

    model_config = ConfigDict(from_attributes=True)
