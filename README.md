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
│  │  │  ├─ schemas.py
│  │  │  └─ utils/
│  │  ├─ requirements.txt
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
└─ test.py, test7.py, test_modules.py
```

## Tech Stack

### Backend

- Python 3.11
- FastAPI + Uvicorn
- pandas, numpy
- scikit-learn (core training path)
- xgboost and joblib available as dependencies
- python-dotenv
- Google Gemini client (`google-generativeai`)

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

- Python 3.11+ in `PATH`
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

This installs Python dependencies from `bias-platform/backend/requirements.txt` and runs:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

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

This installs npm packages and runs Vite dev server on port `5173`.

### 3) Open the app

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Health check: `http://localhost:8000/health`

## Environment Variables

### Backend (`bias-platform/backend/.env`)

Create a `.env` file inside `bias-platform/backend`:

```env
GEMINI_API_KEY=your_key_here
```

If omitted, AI explanation features that depend on Gemini may not return enriched text.

### Frontend

Optional:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

If not set, frontend defaults to `http://127.0.0.1:8000`.

## API Endpoints

Base URL: `http://127.0.0.1:8000`

- `GET /health`  
  Service health status.

- `POST /upload`  
  Uploads CSV file as multipart form (`file`).

- `POST /init_contract`  
  Initializes data contract with selected target column.

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
  Executes full analysis pipeline.

- `GET /results`  
  Returns consolidated results after pipeline run.

- `POST /decision/final`  
  Final decision endpoint exposed via module 8 router.

## Backend Module Overview

Pipeline orchestration is centered in `app/pipeline_controller.py`, combining outputs from:

- `module0`: Data contract creation / schema & metadata handling
- `module4`: Train/inference flow
- `module5`: Fairness metrics + subgroup/intersectional analysis
- `module6`: Debiasing service
- `module8`: Decision scoring and explanation
- `module9`: Operational feasibility / resource validation
- `module11`: Drift and alert monitoring

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
npm run lint
npm run preview
```

## Testing Status

Current repository includes script-style tests:

- `test.py`
- `test7.py`
- `test_modules.py`

There is no standardized `pytest` test suite or CI configuration in this project yet.

## Known Gaps and Notes

- CORS is currently fully open (`allow_origins=["*"]`) for development convenience.
- Some legacy test references appear out of sync with current module structure.
- Monitoring UI expects a `trend` field and falls back to `"stable"` if missing.
- The pipeline appears to keep runtime state in memory (no database persistence configured).

## Suggested Next Improvements

1. Add formal backend tests with `pytest`.
2. Add a production deployment path (Docker + environment profiles).
3. Restrict CORS for non-local environments.
4. Add persistent storage for datasets, artifacts, and run history.
5. Add CI checks (`lint`, `test`, and build validation).

## License

No explicit license file is currently present in this repository.  
Add a `LICENSE` file if you plan to distribute the project.
