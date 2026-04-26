from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.modules.module8.router import router as module8_router
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

app.include_router(module8_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return pipeline.upload_data(content)
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/init_contract")
def init_contract(payload: InitContractRequest):
    try:
        return pipeline.initialize_contract(payload.target_column)
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/select_bias")
def select_bias(payload: SelectBiasRequest):
    try:
        return pipeline.select_bias(payload.bias_columns)
    except Exception as e:
        raise HTTPException(400, str(e))


@app.post("/run_pipeline")
def run_pipeline():
    try:
        return pipeline.run_pipeline()
    except Exception as e:
        raise HTTPException(400, str(e))


@app.get("/results")
def results():
    if pipeline.results is None:
        raise HTTPException(404, "Run pipeline first")
    return pipeline.results