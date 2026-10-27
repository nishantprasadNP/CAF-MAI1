from pydantic import BaseModel, Field


class InitContractRequest(BaseModel):
    target_column: str


class SelectBiasRequest(BaseModel):
    bias_columns: list[str] = Field(default_factory=list)


class RunPipelineRequest(BaseModel):
    row_index: int = Field(default=0, ge=0)
    available_resources: int = Field(default=8, ge=0, le=1000)


class DecisionRequest(BaseModel):
    row_index: int = Field(ge=0)
    available_resources: int = Field(default=8, ge=0, le=1000)
