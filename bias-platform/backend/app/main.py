import logging
import threading
from collections import OrderedDict

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, MAX_ROWS, MAX_SESSIONS, MAX_UPLOAD_MB
from app.pipeline_controller import BiasPipeline
from app.schemas import DecisionRequest, InitContractRequest, RunPipelineRequest, SelectBiasRequest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Bias Platform", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Session-ID"],
)


# ---------------- SESSIONS ---------------- #
# Each browser tab sends its own X-Session-ID so users don't overwrite each
# other's data. Least-recently-used sessions are evicted past MAX_SESSIONS.

_sessions: "OrderedDict[str, BiasPipeline]" = OrderedDict()
_sessions_lock = threading.Lock()


def get_pipeline(x_session_id: str = Header(default="default", max_length=128)) -> BiasPipeline:
    with _sessions_lock:
        pipeline = _sessions.pop(x_session_id, None) or BiasPipeline()
        _sessions[x_session_id] = pipeline
        while len(_sessions) > MAX_SESSIONS:
            _sessions.popitem(last=False)
        return pipeline


def _run(pipeline: BiasPipeline, fn, *args, **kwargs):
    with pipeline.lock:
        try:
            return fn(*args, **kwargs)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            logger.exception("Unhandled error")
            raise HTTPException(500, f"Internal error: {e}")


# ---------------- ROUTES ---------------- #

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/limits")
def limits():
    return {"max_rows": MAX_ROWS, "max_upload_mb": MAX_UPLOAD_MB}


@app.post("/upload")
def upload(file: UploadFile = File(...), pipeline: BiasPipeline = Depends(get_pipeline)):
    # Sync handler: parsing runs in the threadpool, reading the spooled upload
    # file directly instead of copying it into memory.
    max_bytes = int(MAX_UPLOAD_MB * 1024 * 1024)
    file.file.seek(0, 2)
    size = file.file.tell()
    if size == 0:
        raise HTTPException(400, "Uploaded file is empty.")
    if size > max_bytes:
        raise HTTPException(413, f"File is larger than {MAX_UPLOAD_MB:g} MB.")
    return _run(pipeline, pipeline.upload_data, file.file)


@app.post("/init_contract")
def init_contract(payload: InitContractRequest, pipeline: BiasPipeline = Depends(get_pipeline)):
    return _run(pipeline, pipeline.initialize_contract, payload.target_column)


@app.post("/select_bias")
def select_bias(payload: SelectBiasRequest, pipeline: BiasPipeline = Depends(get_pipeline)):
    return _run(pipeline, pipeline.select_bias, payload.bias_columns)


@app.post("/run_pipeline")
def run_pipeline(
    payload: RunPipelineRequest | None = None,
    pipeline: BiasPipeline = Depends(get_pipeline),
):
    payload = payload or RunPipelineRequest()
    return _run(pipeline, pipeline.run_pipeline, payload.row_index, payload.available_resources)


@app.post("/decision")
def decision(payload: DecisionRequest, pipeline: BiasPipeline = Depends(get_pipeline)):
    return _run(pipeline, pipeline.decide, payload.row_index, payload.available_resources)


@app.get("/results")
def results(pipeline: BiasPipeline = Depends(get_pipeline)):
    if pipeline.results is None:
        raise HTTPException(404, "Run pipeline first")
    return pipeline.results
