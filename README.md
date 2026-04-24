# Bias Platform

Unified full-stack bias analysis application built as a monorepo with:

- One FastAPI backend
- One React frontend
- A single orchestrated 5-step pipeline flow

---

## Monorepo Structure

```text
CAF-MAI1/
├── bias-platform/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── pipeline_controller.py
│   │   │   ├── schemas.py
│   │   │   └── modules/
│   │   │       ├── module0/
│   │   │       │   └── data_contract.py
│   │   │       ├── module1/
│   │   │       │   └── profiler.py
│   │   │       ├── module2/
│   │   │       │   └── service.py
│   │   │       ├── module3/
│   │   │       │   └── aggregator.py
│   │   │       └── module4/
│   │   │           ├── preprocess.py
│   │   │           ├── train.py
│   │   │           ├── predict.py
│   │   │           └── service.py
│   │   └── requirements.txt
│   └── frontend/
│       ├── src/
│       │   ├── App.jsx
│       │   ├── index.css
│       │   ├── main.jsx
│       │   └── services/
│       │       └── api.js
│       ├── package.json
│       └── vite.config.js
├── run-backend.sh
├── run-frontend.sh
└── README.md
```

---

## System Design

### Core Principles

- **Single backend app**: all server APIs are exposed from one FastAPI application.
- **Single frontend app**: all UI steps live in one React application.
- **Pipeline orchestration only**: modules do not call each other directly.
- **Clear module boundaries**:
  - Module 0: Data contract
  - Module 1: Profiling
  - Module 2: Bias detection
  - Module 3: Aggregation
  - Module 4: Model training + inference

### Backend Flow

`BiasPipeline` in `bias-platform/backend/app/pipeline_controller.py` orchestrates:

1. `upload_data()`  
   - Decodes CSV
   - Loads DataFrame
   - Returns columns + preview
2. `initialize_contract()`  
   - Builds structured dataset using Module 0
3. `select_bias()`  
   - Stores user-selected bias columns
   - Generates suggested bias columns using Module 2
4. `run_pipeline()`  
   - Profiles dataset via Module 1
   - Detects hidden bias via Module 2
   - Runs model training + inference via Module 4
   - Aggregates outputs via Module 3

The backend stores working state in-memory in the singleton `pipeline` object.

---

## Module Responsibilities

### Module 0 (`module0/data_contract.py`)

- Validates target and bias column presence.
- Infers column types and target type.
- Produces canonical payload:
  - `X`, `Y`
  - `B_user`, `B_suggested`, `B_hidden`
  - `metadata`

### Module 1 (`module1/profiler.py`)

- Profiles feature dataset:
  - row and column count
  - null count by column
  - unique count by column

### Module 2 (`module2/service.py`)

- Suggests bias columns (variance-based heuristic on numeric features).
- Detects hidden bias:
  - feature encoding
  - KMeans clustering
  - cluster distribution
  - top hidden candidates

### Module 3 (`module3/aggregator.py`)

- Aggregates final response sections:
  - `dataset`
  - `profile`
  - `module2`
  - `module4`
  - unified bias `registry`

### Module 4 (`module4/`)

- Implements Module 4 training layer tasks:
  - **Task 4.1 Preprocessing pipeline**:
    - Imputation (numeric: median, categorical: most frequent)
    - Encoding (OneHotEncoder)
    - Normalization (StandardScaler)
    - Built using sklearn `ColumnTransformer`
  - **Task 4.2 Baseline trainer**:
    - Train/test split (`test_size=0.2`)
    - Logistic Regression baseline
    - Optional XGBoost support (if installed)
    - Returns accuracy, precision, recall, f1-score
  - **Task 4.3 Prediction engine**:
    - Batch inference (`predict_batch`)
    - Single-row inference (`predict_single`)
    - Probability outputs through `predict_proba`

---

## API Endpoints

All routes are defined in `bias-platform/backend/app/main.py`.

### 1) `POST /upload`

Uploads CSV file and initializes raw dataset.

- Content type: `multipart/form-data`
- Field: `file`

Response:

```json
{
  "columns": ["col1", "col2", "target"],
  "rows": 1000,
  "preview": [{ "...": "..." }]
}
```

### 2) `POST /init_contract`

Initializes data contract with target column.

Request:

```json
{
  "target_column": "target"
}
```

### 3) `POST /select_bias`

Saves user-selected bias columns and computes suggested bias columns.

Request:

```json
{
  "bias_columns": ["gender", "region"]
}
```

Response:

```json
{
  "B_user": ["gender", "region"],
  "B_suggested": ["age", "income"]
}
```

### 4) `POST /run_pipeline`

Runs profile + hidden bias detection + module-4 model training + aggregation.

Request body: empty object.

### 5) `GET /results`

Returns final results from last successful `run_pipeline`.

---

## Frontend Flow (5-Step UI)

Implemented in `bias-platform/frontend/src/App.jsx`:

1. Upload Dataset
2. Select Target Column
3. Select Bias Columns
4. Run Analysis
5. Results Dashboard

API calls are centralized in `bias-platform/frontend/src/services/api.js`:

- `uploadFile()`
- `initContract()`
- `selectBias()`
- `runPipeline()`
- `getResults()`

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+

---

## Quick Start

From repo root:

### Start backend (one command)

```bash
./run-backend.sh
```

Backend runs on: `http://0.0.0.0:8000`

### Start frontend (one command)

```bash
./run-frontend.sh
```

Frontend dev server typically runs on: `http://localhost:5173`

---

## Manual Run Commands

### Backend

```bash
python3 -m pip install -r bias-platform/backend/requirements.txt
PYTHONPATH="bias-platform/backend" uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
npm --prefix bias-platform/frontend install
npm --prefix bias-platform/frontend run dev
```

### Frontend production build

```bash
npm --prefix bias-platform/frontend run build
```

---

## Configuration

Frontend API base URL:

- Default: `http://127.0.0.1:8000`
- Override with environment variable: `VITE_API_BASE_URL`

Example:

```bash
VITE_API_BASE_URL="http://localhost:8000" npm --prefix bias-platform/frontend run dev
```

---

## Notes and Limitations

- Current backend pipeline state is in-memory (single process memory).
- Restarting backend clears uploaded dataset and results state.
- This version is optimized for local development and iterative integration.
- XGBoost is optional at runtime: logistic regression remains the default baseline.

---

## Troubleshooting

### "No uploaded dataset found. Call upload_data first."

- Run Step 1 (`/upload`) before `/init_contract`.

### "Data contract is not initialized."

- Run `/init_contract` before `/select_bias` and `/run_pipeline`.

### Frontend cannot connect to backend

- Ensure backend is running on port `8000`.
- Verify `VITE_API_BASE_URL` if using a non-default host/port.

### CORS issues

- Backend currently allows all origins in development (`allow_origins=["*"]`).
- If deploying, restrict CORS to trusted frontend origins.

---

