from typing import Any

from pydantic import BaseModel, Field


class DatasetPayload(BaseModel):
    X: list[dict[str, Any]]
    Y: list[Any]
    B_user: list[str] = Field(default_factory=list)
    B_suggested: list[str] = Field(default_factory=list)
    B_hidden: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    columns: list[str]
    rows: int
    preview: list[dict[str, Any]]


class InitContractRequest(BaseModel):
    target_column: str


class SelectBiasRequest(BaseModel):
    bias_columns: list[str] = Field(default_factory=list)


class RunPipelineRequest(BaseModel):
    pass
