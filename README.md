# Bias Platform (CAF-MAI1)

A full-stack bias analysis platform with a FastAPI backend and React frontend.  
It lets you upload tabular data, choose target and bias-sensitive attributes, run an end-to-end fairness pipeline, and review decision, fairness, debiasing, validation, and monitoring outputs.

## Project Layout

```text
CAF-MAI1/
├─ bias-platform/
│  ├─ backend/                    # FastAPI + ML pipeline
│  │  ├─ app/
│  │  │  ├─ main.py               # API entrypoint
│  │  │  ├─ pipeline_controller.py
│  │  │  ├─ modules/              # pipeline modules (0,4,5,6,8,9,11)
│  │  ├─ tests/                  # pytest suite
│  │  │  ├─ schemas.py
│  │  │  └─ utils/
│  │  ├─ requirements.txt
│  │  ├─ requirements-dev.txt    # + pytest
│  │  └─ .python-version
│  └─ frontend/                   # React + Vite dashboard
│     ├─ src/
│     │  ├─ components/
│     │  ├─ services/api.js
│     │  └─ App.jsx
│     ├─ package.json
│     └─ vite.config.js
├─ run-backend.ps1 / run-backend.sh
├─ run-frontend.ps1 / run-frontend.sh
```

## Tech Stack

### Backend

- Python 3.11–3.14
- FastAPI + Uvicorn
- pandas, numpy
- scikit-learn (core training path)
- python-dotenv
- Google Gemini client (`google-genai`)

### Frontend

- React 19
- Vite 4
- Axios
- Recharts

## What the App Does

1. Uploads a CSV dataset.
2. Creates a data contract around selected target and detected metadata.
3. Lets you choose bias-sensitive columns (for fairness analysis).
4. Runs an orchestrated backend pipeline:
   - preprocessing and training
   - fairness metrics and subgroup analysis
   - debiasing adjustments
   - decision/explainability
   - feasibility validation
   - monitoring/drift checks
5. Shows results in a visual dashboard.

## Quick Start

### Prerequisites

- Python 3.11 or newer in `PATH` (3.11–3.14 tested)
- Node.js + npm in `PATH`

### 1) Backend setup and run

From project root (`CAF-MAI1`):

- **Windows (PowerShell):**

```powershell
.\run-backend.ps1
```

- **Linux/macOS (bash):**

```bash
chmod +x ./run-backend.sh
./run-backend.sh
```

On first run this creates a virtualenv in `bias-platform/backend/.venv` and installs
`requirements.txt` into it. It then starts the API on the first free port from 8000 to 8010
(set `BACKEND_PORT` to force one) and records the port for the frontend script.

### 2) Frontend setup and run

In another terminal from project root:

- **Windows (PowerShell):**

```powershell
.\run-frontend.ps1
```

- **Linux/macOS (bash):**

```bash
chmod +x ./run-frontend.sh
./run-frontend.sh
```

This installs npm packages and runs the Vite dev server on port `5173` (or the next free
port). The browser only talks to the Vite server: requests to `/api/*` are proxied to the
backend port that `run-backend.sh` chose, so there is no CORS or port configuration to do.

Start the backend first. If you restart the backend and it lands on a different port,
restart the frontend too.

### 3) Open the app

- Frontend: the `Local:` URL Vite prints, normally `http://127.0.0.1:5173`
- Health check through the proxy: `http://127.0.0.1:5173/api/health`

## Environment Variables

### Backend (`bias-platform/backend/.env`)

Create a `.env` file inside `bias-platform/backend`:

```env
GEMINI_API_KEY=your_key_here
# Optional:
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_FALLBACK_MODEL=gemini-3.8-flash
GEMINI_TIMEOUT_MS=10000   # Gemini's minimum; lower values are raised to 10000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
MAX_UPLOAD_MB=1024
MAX_SESSIONS=10
```

If `GEMINI_API_KEY` is omitted, explanations fall back to rule-based text.
`CORS_ORIGINS` only matters if a browser calls the API directly (see `VITE_API_BASE_URL` below).

### Frontend

Optional:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

If not set, the frontend calls `/api` on its own origin and the dev server proxies it
(`API_PROXY_TARGET`, set automatically by `run-frontend.sh`). Set this only to make the
browser call the API directly, and add the frontend's origin to `CORS_ORIGINS`.

## API Endpoints

Base URL: the backend port (e.g. `http://127.0.0.1:8000`), or `/api` through the frontend dev server.

- `GET /health`  
  Service health status.

All endpoints except `/health` accept an optional `X-Session-ID` header. The frontend sends one per browser tab so concurrent users don't share state.

- `POST /upload`  
  Uploads CSV file as multipart form (`file`). UTF-8, UTF-8 with BOM and Windows-1252/Latin-1 are accepted.

- `POST /init_contract`  
  Initializes data contract with selected target column. The target must have exactly two
  distinct values (e.g. `yes`/`no`, `0`/`1`); text labels are encoded in sorted order, so the
  alphabetically second value is treated as the positive outcome. Returns metadata only.

  Example body:

```json
{ "target_column": "approved" }
```

- `POST /select_bias`  
  Selects bias-sensitive columns.

  Example body:

```json
{ "bias_columns": ["gender", "age_group"] }
```

- `POST /run_pipeline`  
  Executes full analysis pipeline. Requires at least one bias column.

```json
{ "row_index": 0, "available_resources": 8 }
```

- `POST /decision`  
  Re-scores a single record (decision + validation) after a pipeline run, without retraining.

```json
{ "row_index": 42, "available_resources": 8 }
```

- `GET /results`  
  Returns consolidated results after pipeline run.


## Backend Module Overview

Pipeline orchestration is centered in `app/pipeline_controller.py`, combining outputs from:

- `module0`: Data contract: binary target validation/encoding, type normalization, metadata
- `module4`: Logistic-regression training on a stratified 80/20 split
- `module5`: Fairness metrics + subgroup/intersectional analysis, measured on the held-out 20%
- `module6`: Bias mitigation: reweighing + group-specific decision thresholds, both fitted on the training split
- `module8`: Decision for one record, with explanation
- `module9`: Operational feasibility / resource validation
- `module11`: Monitoring: train-vs-evaluation PSI per numeric column, bias trend across runs of the same dataset

## Frontend Overview

Main flow in `src/App.jsx`:

- dataset upload
- target + bias column selection
- pipeline execution trigger
- results rendering via dashboard components

Key UI components:

- `ResultsDashboard.jsx`
- `FairnessPanel.jsx`
- `MonitoringCard.jsx`
- `ExplainabilityPanel.jsx`

API client integration lives in `src/services/api.js`.

## Frontend Scripts

From `bias-platform/frontend`:

```bash
npm install
npm run dev
npm run build
npm run preview
```

## Testing

From `bias-platform/backend`:

```bash
pip install -r requirements-dev.txt
python -m pytest tests
```

The suite covers each module and the HTTP flow end to end. Gemini is disabled during tests.

## Known Gaps and Notes

- Pipeline state is kept in memory per session (no database persistence); restarting the backend clears it.
- Only binary targets are supported.

## Suggested Next Improvements

1. Add a production deployment path (Docker + environment profiles).
2. Add persistent storage for datasets, artifacts, and run history.
3. Add CI checks (tests and frontend build validation).

## License

No explicit license file is currently present in this repository.  
Add a `LICENSE` file if you plan to distribute the project.
