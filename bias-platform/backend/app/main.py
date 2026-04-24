from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.pipeline_controller import BiasPipeline
from app.schemas import InitContractRequest, SelectBiasRequest

app = FastAPI(title="Bias Platform", version="1.0.0")
pipeline = BiasPipeline()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    try:
        content = await file.read()
        return pipeline.upload_data(content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to upload dataset: {exc}") from exc


@app.post("/init_contract")
def init_contract(payload: InitContractRequest) -> dict:
    try:
        return pipeline.initialize_contract(payload.target_column)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/select_bias")
def select_bias(payload: SelectBiasRequest) -> dict:
    try:
        return pipeline.select_bias(payload.bias_columns)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/run_pipeline")
def run_pipeline() -> dict:
    try:
        pipeline.run_pipeline()
        return {"status": "completed"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/results")
def get_results() -> dict:
    if pipeline.results is None:
        raise HTTPException(status_code=404, detail="No pipeline results available yet.")
    return pipeline.results
