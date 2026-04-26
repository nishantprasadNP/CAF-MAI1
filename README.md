# Bias Platform (CAF-MAI1)

Bias Platform is a FastAPI + React decision intelligence platform with an integrated Modules 0-11 pipeline.

---

## Latest Updates (Apr 2026)

This project is now a **Context-Aware Bias Amplification Detection & Explainable AI System**.

- **CBAS added (Module 7):** `cbas = context_bias - base_bias`
- **Fairness expansion (Module 5):** equalized odds, predictive parity, group-wise confusion matrix
- **Debiasing effect fix (Module 6):** probability adjustment now applies deterministic bias-gap reduction
- **Decision explainability extension (Module 8):** `top_features`, `contextContribution`, `biasContribution`
- **Compliance rule engine (Module 10):** `status` + `violations` with risk/context checks
- **Monitoring drift update (Module 11):** absolute bias drift + thresholded alerts
- **Gemini augmentation:** LLM explanations added for context/decision/compliance/drift with safe fallback

### New/Updated Result Fields

- `context.cbas`, `context.impact`, `context.reason`, `context.confidence`
- `decision.top_features`, `decision.contextContribution`, `decision.biasContribution`
- `decision.decisionExplanation`, `decision.featureExplanation`
- `compliance.status`, `compliance.violations`, `compliance.aiComplianceNote`
- `monitoring.bias_drift`, `monitoring.alerts`, `monitoring.driftExplanation`

### Gemini + Environment Setup

1. Set API key in:
   - `bias-platform/backend/.env`
2. Use:
   - `GEMINI_API_KEY=your_actual_api_key_here`
3. Install dependencies:
   - `python-dotenv`
   - `google-generativeai`

Gemini is **non-blocking**: if API/config fails, backend returns fallback text (`"Explanation unavailable"`) and pipeline continues.

### Local Run (Important)

Run backend from the backend directory so `app.main:app` imports correctly.

**Windows (PowerShell):**

```powershell
cd C:\CAF-MAI1\bias-platform\backend
python -m uvicorn app.main:app --reload
```

**Frontend (PowerShell):**

```powershell
cd C:\CAF-MAI1\bias-platform\frontend
npm install
npm run dev
```

**Linux/macOS:**

```bash
./run-backend.sh
./run-frontend.sh
```

### Quick Validation

- Backend health: `GET http://localhost:8000/health`
- Frontend: `http://localhost:5173`
- Module checks script: `python test_modules.py`

---

## Pipeline Flow

The orchestrated execution order is unchanged:

**Data -> Bias -> Model -> Fairness -> Debias -> Context -> Decision -> Validation -> Compliance -> Monitoring**

Primary runtime pattern:
1. `POST /run_pipeline`
2. `GET /results`
3. Optional `POST /context`
4. `POST /run_pipeline` (recompute with context)
5. `GET /results`

---

## Realistic System Behavior

- **Calibrated probabilities:** Module 4 now uses sigmoid calibration (`CalibratedClassifierCV`) for more reliable confidence.
- **Model metadata:** Model responses now include `model_type` and `calibrated`.
- **Bounded context effect:** Frontend context delta display is clamped for stability and interpretability.
- **Selective debiasing:** Module 6 can skip intervention when fairness gap is already low (`bias_gap < 0.05`), returning a clear reason.

---

## Explainability Enhancements

- **Structured decision explanation:** Module 8 now returns:
  - summary
  - signed top feature impacts (`+/-`)
  - contribution split (`feature`, `context`, `bias`)
- **Frontend explainability fallback:** If high-fidelity explainability is unavailable, UI falls back to model feature importance / coefficients.
- **Interpretability labels:** Explainability panel renders contribution strength as Strong / Moderate / Weak with percentages.

---

## Monitoring Enhancements

- Module 11 now returns:
  - `previous_bias_drift`
  - `current_bias_drift`
  - `bias_drift`
  - `alerts` (always non-empty)
- Alert trigger logic:
  - Drift above threshold generates alerts.
  - Otherwise a default health message (`No anomalies detected`) is provided.

---

## Validation Enhancements

- Module 9 includes quantitative feasibility context:
  - `required_resources`
  - `available_resources`
  - `status`
  - `reason`
- Fallback behavior is more realistic:
  - partial allocation is suggested when feasible
  - delayed action is used when resources are unavailable

---

## Module Upgrade Summary (4-11)

### Module 4 - Model
- Probability calibration enabled (sigmoid)
- Added metadata:
  - `model_type`
  - `calibrated`

### Module 5 - Fairness
- Added summary metrics:
  - `demographic_parity`
  - `equal_opportunity`
  - `bias_gap`
- Added subgroup breakdown in `summary.groups`

### Module 6 - Debiasing
- Added threshold gate (`bias_gap < 0.05`)
- Added explicit skip payload:
  - `status: skipped`
  - `reason: dataset already balanced`

### Module 7 - Context Engine
- Unknown context values are neutralized (`weight = 1.0`)
- Added `context_confidence`
- Added clearer reason text for weak signals

### Module 8 - Decision + Explainability
- Added structured explanation object
- Added signed feature impact direction
- Preserved backward-compatible fields

### Module 9 - Validation
- Added quantitative resource reasoning
- Added fallback reason and improved alternatives

### Module 10 - Compliance
- Added soft warnings for sensitive attributes
- Added `policy_checks` block

### Module 11 - Monitoring
- Added historical drift comparison
- Ensured alerts are always populated

---

## Frontend UX Upgrades

- Decision card readability improved (`0 -> REJECT`, `1 -> APPROVE`)
- Decision card now highlights:
  - summary
  - feature impact directions
  - contribution split
- Context card now includes:
  - Base -> Debiased -> Context-adjusted flow
  - Context confidence
- Validation card now shows:
  - required vs available resources
- Monitoring card now shows:
  - drift trend (previous -> current)
  - non-empty alerts

---

## API Endpoints

### Core
- `GET /health`
- `POST /upload`
- `POST /init_contract`
- `POST /select_bias`
- `POST /run_pipeline`
- `GET /results`

### Context
- `POST /context`
- `POST /context/apply-context` (legacy/specialized)
- `POST /context/explain`
- `POST /context/bias-score`

### Decision
- `POST /decision/final` (legacy/specialized)
- `POST /decision/explain-final` (legacy/specialized)

---

## Local Run

From repository root:

```bash
./run-backend.sh
./run-frontend.sh
```

Frontend build:

```bash
npm --prefix bias-platform/frontend run build
```

---

## Notes

- Pipeline/API contracts are preserved; enhancements are additive.
- Outputs remain JSON-serializable.
- Runtime state is in-memory for the active backend process.
# Bias Platform (CAF-MAI1)

Bias Platform is a fairness-aware decision intelligence system with:
- FastAPI backend
- React (Vite) frontend
- End-to-end pipeline modules **0 -> 11**

---

## Pipeline Flow

The orchestrated backend flow is:

**Data -> Bias -> Model -> Fairness -> Debias -> Context -> Decision -> Validation -> Compliance -> Monitoring**

Primary execution pattern:
1. `POST /run_pipeline`
2. `GET /results`
3. (optional) `POST /context`
4. `POST /run_pipeline` again
5. `GET /results`

---

## Module Deep Dive

### Module 0 - Data Contract
- Validates target and bias columns
- Builds canonical payload (`X`, `Y`, metadata, bias fields)
- Produces stable input for downstream model/fairness modules

### Module 1 - Profiling
- Computes row/column summaries, nulls, uniqueness
- Generates quality and shape signals for governance

### Module 2 - Bias Discovery
- Suggests likely bias columns
- Detects hidden bias via cluster/subgroup patterns
- Outputs bias candidates and cluster distribution

### Module 3 - Aggregation
- Harmonizes and serializes intermediate module outputs
- Maintains backward-compatible response envelope

### Module 4 - Model Training + Inference
- Runs preprocessing and baseline model training
- Produces predictions/probabilities
- Emits model metrics (accuracy, precision, recall, F1)

### Module 5 - Fairness
- Computes subgroup and intersectional fairness metrics
- Tracks bias gaps and fairness outcomes

### Module 6 - Debiasing
- Applies fairness-aware reweighting/resampling
- Re-evaluates model after debiasing
- Produces before/after fairness effect summaries

### Module 7 - Context Engine
- Accepts context (`region`, `hospital_type`, `resource_level`, `time_of_day`)
- Applies context weighting to probabilities
- Produces context-adjusted probability and bias signal

### Module 8 - Decision + Explainability
- Converts adjusted probabilities to final decision
- Computes confidence and explanation metadata
- Exposes feature/context/bias contributions

### Module 9 - Validation
- Validates action feasibility
- Returns action status, fallback, and reason

### Module 10 - Compliance
- Applies privacy/compliance checks
- Enforces role/policy constraints
- Produces compliance status and policy-violation summary

### Module 11 - Monitoring
- Tracks data and bias drift
- Emits alerts and monitoring health indicators

---

## Frontend UX (Current)

1. Upload dataset
2. Select target + bias columns
3. Run full pipeline
4. Set context (optional)
5. Re-run final inference
6. View multi-layer dashboard

Dashboard sections:
- Model + Fairness Summary
- Debiasing Impact
- Context Impact
- Decision Card
- Explainability
- Validation
- Compliance
- Monitoring

---

## Required UX Logic Implemented

### 1) Decision readability
- Numeric decision labels are normalized in UI:
  - `0 -> REJECT`
  - `1 -> APPROVE`

### 2) Context stability guard
- Context impact delta is capped in UI:
  - `delta = P_after - P_before`
  - `delta = max(min(delta, 0.2), -0.2)`
- Prevents extreme swings from being displayed.

### 3) Context impact flow
- Dashboard now shows:
  - `Base Probability`
  - `Debiased Probability`
  - `Context-adjusted Probability`
  - `Impact`

### 4) Explainability fallback
- If SHAP/explicit explainability payload is unavailable, UI falls back to:
  - module feature importance
  - model coefficients
  - deterministic fallback feature signals
- Always shows:
  - top features
  - context contribution
  - bias contribution

### 5) Debiasing wording
- Replaces empty/N/A states with:
  - `"No significant change detected"`
  - or concrete before/after values

### 6) Validation reason
- Validation card now includes:
  - `Reason` (e.g., insufficient resources)

### 7) Monitoring alert defaults
- Alerts are always populated:
  - `"None"` when no alerts
  - or meaningful alert text

### 8) UI enhancements
- Risk color coding:
  - green = safe
  - yellow = moderate
  - red = high
- Decision card is visually prominent.
- Added expandable `"Why this decision?"` details section.

---

## API Endpoints

### Core
- `GET /health`
- `POST /upload`
- `POST /init_contract`
- `POST /select_bias`
- `POST /run_pipeline`
- `GET /results`

### Context
- `POST /context`
- `POST /context/apply-context` (legacy/specialized)
- `POST /context/explain`
- `POST /context/bias-score`

### Decision
- `POST /decision/final` (legacy/specialized)
- `POST /decision/explain-final` (legacy/specialized)

---

## Run Locally

From repo root:

```bash
./run-backend.sh
./run-frontend.sh
```

Manual frontend build:

```bash
npm --prefix bias-platform/frontend run build
```

---

## Notes

- `POST /run_pipeline` triggers processing; read full result payload via `GET /results`.
- Pipeline state is in-memory for the active backend process.
- Legacy standalone context/decision endpoints remain available for compatibility.
# Bias Platform (CAF-MAI1)

Bias Platform is a full-stack decision-intelligence system for responsible ML.  
It combines bias discovery, fairness evaluation, debiasing, contextual inference, decisioning, validation, compliance, and monitoring in one orchestrated pipeline.

---

## Tech Stack

- **Backend:** FastAPI
- **Frontend:** React (Vite)
- **Pipeline:** Modules **0 -> 11** with shared in-memory state

---

## End-to-End Pipeline

The production pipeline now follows this strict sequence:

**Data -> Bias -> Model -> Fairness -> Debias -> Context -> Decision -> Validation -> Compliance -> Monitoring**

This executes through `POST /run_pipeline`, and the latest full payload is read from `GET /results`.

---

## Project Structure

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
│   │   │       ├── module1/
│   │   │       ├── module2/
│   │   │       ├── module3/
│   │   │       ├── module4/
│   │   │       ├── module5/
│   │   │       ├── module6/
│   │   │       ├── module7/
│   │   │       ├── module8/
│   │   │       ├── module9/
│   │   │       ├── module10/
│   │   │       └── module11/
│   │   └── requirements.txt
│   └── frontend/
│       ├── src/
│       │   ├── App.jsx
│       │   ├── components/
│       │   ├── services/api.js
│       │   └── index.css
│       ├── package.json
│       └── vite.config.js
├── run-backend.sh
├── run-frontend.sh
└── README.md
```

---

## Module-by-Module Deep Dive

### Module 0 - Data Contract
**Purpose:** Convert uploaded data into a validated, canonical contract used by downstream modules.

**Inputs**
- Uploaded CSV dataset
- Selected target column
- Selected bias columns

**Core responsibilities**
- Schema normalization for tabular processing
- Validation of target and protected/bias attributes
- Separation of features (`X`) and labels (`Y`)
- Construction of metadata used by model, fairness, and debiasing layers

**Outputs**
- Contract-safe dataset bundle with stable keys consumed by modules 1, 2, 4, 5, and 6

---

### Module 1 - Profiling
**Purpose:** Build a statistical profile for data quality and auditability before model use.

**Core responsibilities**
- Row/column counts
- Missingness and cardinality checks
- Distribution diagnostics for key features
- Early warning flags for skew, sparsity, or malformed fields

**Outputs**
- Profile snapshot included in final results for transparency and debugging

---

### Module 2 - Bias Discovery
**Purpose:** Discover potential fairness risks prior to final decisioning.

**Core responsibilities**
- Suggested bias feature detection from dataset semantics
- Hidden bias discovery using subgroup and clustering patterns
- High-risk cohort surfacing for fairness review

**Outputs**
- Suggested/user/hidden bias sets
- Cluster-level bias indicators used by fairness and review dashboards

---

### Module 3 - Aggregation
**Purpose:** Aggregate intermediate outputs into a stable envelope and state model.

**Core responsibilities**
- Harmonize shapes and field names from previous modules
- Preserve backward-compatible response sections
- Keep module payloads serializable and API-safe

**Outputs**
- Unified result envelope feeding modules 4+ and external API responses

---

### Module 4 - Model Training + Inference
**Purpose:** Produce baseline predictive performance and calibrated probabilities.

**Core responsibilities**
- Feature preprocessing (for mixed numeric/categorical schemas)
- Baseline model training (logistic pipeline, optional XGBoost path)
- Batch and/or single inference
- Probability extraction for downstream fairness and context stages

**Outputs**
- Predictions and class probabilities
- Core model metrics (accuracy, precision, recall, F1)

---

### Module 5 - Fairness
**Purpose:** Quantify group-level and intersectional fairness behavior.

**Core responsibilities**
- Subgroup metric computation
- Bias gap and disparity measurement
- Intersectional fairness checks
- Consolidated fairness metrics across protected segments

**Outputs**
- Fairness score sets and gap objects consumed by debiasing and dashboard summaries

---

### Module 6 - Debiasing
**Purpose:** Mitigate unfairness while preserving predictive utility.

**Core responsibilities**
- Fairness-aware sample reweighting
- Optional resampling strategy
- Refit/evaluate under debiasing policies
- Compare pre/post fairness outcomes

**Outputs**
- Debiased predictions/probabilities
- Debiasing effect metrics including fairness improvements

---

### Module 7 - Context Engine
**Purpose:** Adjust inference according to operational context while retaining traceability.

**Supported context dimensions**
- `region`
- `hospital_type`
- `resource_level`
- `time_of_day`

**Core responsibilities**
- Context encoding from policy-safe schema
- Context weighting of model probabilities
- Context impact quantification and bias score support

**Outputs**
- Context-adjusted probability distribution
- Context weight map and context-sensitive bias signal

---

### Module 8 - Decision + Explainability
**Purpose:** Convert adjusted inference into actionable decision outputs with explanations.

**Core responsibilities**
- Final decision label computation
- Confidence estimation
- Bias-aware metadata generation
- Explainability surface (feature/context contribution where available)

**Outputs**
- Final decision payload used by validation, compliance, and dashboard cards

---

### Module 9 - Decision Validation
**Purpose:** Validate whether the recommended action is operationally feasible.

**Core responsibilities**
- Map prediction/decision to concrete action
- Feasibility checks under operational constraints
- Fallback or alternative strategy generation

**Outputs**
- Action, status (`Feasible` / `Not Feasible`), and alternative recommendation

---

### Module 10 - Privacy + Compliance
**Purpose:** Ensure policy and governance compliance before operational use.

**Core responsibilities**
- Privacy/PII handling hooks
- Role-based access checks
- Policy validation and violation reporting
- Auditability of pipeline events

**Outputs**
- Compliance status block (role decision, PII status, policy violations)

---

### Module 11 - Monitoring
**Purpose:** Track system health post-inference and detect drift or fairness decay.

**Core responsibilities**
- Data drift monitoring
- Bias drift monitoring
- Alert generation for unstable or risky trends

**Outputs**
- Monitoring block with drift scores, labels, and alerts for ongoing governance

---

## Backend API

### Core Pipeline
- `GET /health`
- `POST /upload`
- `POST /init_contract`
- `POST /select_bias`
- `POST /run_pipeline`
- `GET /results`

### Context Routes
- `POST /context`
- `POST /context/apply-context` (legacy/specialized)
- `POST /context/explain`
- `POST /context/bias-score`

### Decision Routes
- `POST /decision/final` (legacy/specialized)
- `POST /decision/explain-final` (legacy/specialized)

---

## Frontend UX Flow (Updated)

The frontend now follows this user flow:

1. **Upload Dataset**
2. **Select Target + Bias Columns**
3. **Run Full Pipeline (0-11)**
4. **Set Context (Optional)**
5. **Re-run Final Inference**
6. **View Multi-Layer Results Dashboard**

Dashboard includes:
- Model + fairness summary
- Debiasing impact
- Context impact
- Decision card
- Validation card
- Compliance card
- Monitoring card
- Explainability panel

---

## Frontend API Usage Contract

Primary flow in `frontend/src/services/api.js`:

1. `runPipeline()`
2. `getResults()`
3. `setContext()`
4. `runPipeline()` again
5. `getResults()`

**Notes**
- `applyContext()` and `getFinalDecision()` are preserved for backward compatibility, but deprecated for primary UI flow.

---

## Local Run

From repo root:

### Backend
```bash
./run-backend.sh
```

### Frontend
```bash
./run-frontend.sh
```

If macOS blocks execution with `operation not permitted`, clear quarantine on project scripts/folders and retry.

---

## Operational Notes

- `POST /run_pipeline` triggers processing; full structured output is retrieved via `GET /results`.
- Pipeline state is in-memory for the active backend process.
- For production, persistent state storage and auth/policy hardening should be added around compliance and monitoring modules.
# Bias Platform (CAF-MAI1)

Bias Platform is a full-stack fairness and decision-intelligence system built as a monorepo.

- **Backend:** FastAPI
- **Frontend:** React (Vite)
- **Pipeline:** Modules 0 -> 11, orchestrated through a shared `pipeline_state`

---

## Project Structure

```text
CAF-MAI1/
├── bias-platform/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── pipeline_controller.py
│   │   │   ├── schemas.py
│   │   │   └── modules/
│   │   │       ├── module0/   # data contract
│   │   │       ├── module1/   # profiling
│   │   │       ├── module2/   # bias discovery
│   │   │       ├── module3/   # aggregation
│   │   │       ├── module4/   # model training + inference
│   │   │       ├── module5/   # fairness
│   │   │       ├── module6/   # debiasing
│   │   │       ├── module7/   # context engine
│   │   │       ├── module8/   # decision + explainability
│   │   │       ├── module9/   # decision validation
│   │   │       ├── module10/  # privacy + compliance
│   │   │       └── module11/  # monitoring
│   │   └── requirements.txt
│   └── frontend/
│       ├── src/
│       │   ├── App.jsx
│       │   ├── index.css
│       │   ├── main.jsx
│       │   └── services/api.js
│       ├── package.json
│       └── vite.config.js
├── run-backend.sh
├── run-frontend.sh
└── README.md
```

---

## Backend Architecture

Backend entrypoint: `bias-platform/backend/app/main.py`

- Single FastAPI app instance
- Routers included from Module 7 and Module 8
- Pipeline state retained in memory per running backend process

### Shared Pipeline State

`pipeline_controller.py` maintains a shared `pipeline_state` object with these top-level sections:

- `model_output`
- `fairness`
- `debiasing`
- `context`
- `decision`
- `validation`
- `compliance`
- `monitoring`

---

## Sequential Pipeline Flow (Current)

Inside `run_pipeline()`:

1. Existing preprocessing and fairness stages:
   - Module 0, 1, 2, 4, 5, 6
2. Strict post-model decision chain:
   - **Module 7 (Context Injection)**
   - **Module 8 (Decision + Explainability)**
   - **Module 9 (Decision Validation)**
   - **Module 10 (Privacy + Compliance)**
   - **Module 11 (Monitoring)**
3. Unified JSON-serializable output is stored and returned via `/results`.

---

## Module Functionalities

### Module 0 - Data Contract
- Validates target and bias columns
- Builds canonical dataset payload (`X`, `Y`, bias fields, metadata)

### Module 1 - Profiling
- Row/column/null/unique summaries

### Module 2 - Bias Discovery
- Suggested bias features
- Hidden bias cluster detection

### Module 3 - Aggregation
- Legacy-compatible output envelope for frontend compatibility

### Module 4 - Model Training
- `ColumnTransformer` preprocessing
- Logistic regression baseline (xgboost path supported)
- Batch/single inference with probability outputs

### Module 5 - Fairness
- Subgroup metrics, bias gaps, intersectional metrics, fairness metrics

### Module 6 - Debiasing
- Fairness-aware sample weights
- Reweighted and resampled retraining outputs
- Debiasing effect comparison

### Module 7 - Context Engine
- Strict context schema:
  - `region`
  - `hospital_type`
  - `resource_level`
  - `time_of_day`
- Context encoding and multiplicative context weighting
- Probability adjustment + context bias score

### Module 8 - Decision Engine
- Final label + confidence from context-adjusted probabilities
- Bias-aware decision metadata and explanation

### Module 9 - Decision Validation
- Maps decision to action
- Checks resource feasibility
- Returns feasible or fallback strategy

### Module 10 - Privacy & Compliance
- Data anonymization hooks
- Role checks (run and bias-view permissions)
- Audit log entry for pipeline actions

### Module 11 - Monitoring
- Data drift signal
- Bias drift over time
- Alert generation for trend/feedback-loop indicators

---

## API Endpoints

### Health + Pipeline

- `GET /health`
- `POST /upload`
- `POST /init_contract`
- `POST /select_bias`
- `POST /run_pipeline`
- `GET /results`

### Module 7 (`/context`)

- `POST /context`
- `POST /context/apply-context`
- `POST /context/explain`
- `POST /context/bias-score`

### Module 8 (`/decision`)

- `POST /decision/final`
- `POST /decision/explain-final`

---

## Endpoint Contracts (Quick)

- `POST /upload`:
  - multipart CSV upload (`file`)
  - returns columns, row count, preview
- `POST /init_contract`:
  - `{ "target_column": "..." }`
- `POST /select_bias`:
  - `{ "bias_columns": ["..."] }`
- `POST /run_pipeline`:
  - executes full pipeline
  - returns `{ "status": "completed" }`
- `GET /results`:
  - returns full unified results payload

---

## Frontend Overview

Main app: `bias-platform/frontend/src/App.jsx`

### Current UI

- Light, minimalist, single-page layout
- Top nav + hero + examples + footer
- Ingest zone with:
  - optional repo URL input
  - ingest button
  - CSV upload input
- Step-based flow up to decision stage and results
- Dashboard displays structured module summaries (raw JSON blocks removed)

### Frontend API Layer

`bias-platform/frontend/src/services/api.js` exposes:

- `uploadFile`
- `initContract`
- `selectBias`
- `runPipeline`
- `getResults`
- `setContext`
- `applyContext`
- `getFinalDecision`
- `explainDecision`

---

## Run Commands

From repo root:

```bash
./run-backend.sh
./run-frontend.sh
```

Manual backend:

```bash
python3 -m pip install -r bias-platform/backend/requirements.txt
PYTHONPATH="bias-platform/backend" python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Manual frontend:

```bash
npm --prefix bias-platform/frontend install
npm --prefix bias-platform/frontend run dev
```

Build frontend:

```bash
npm --prefix bias-platform/frontend run build
```

---

## Configuration

- Default frontend API base: `http://127.0.0.1:8000`
- Override using `VITE_API_BASE_URL`

Example:

```bash
VITE_API_BASE_URL="http://localhost:8000" npm --prefix bias-platform/frontend run dev
```

---

## Notes

- Pipeline state is in-memory; restart clears state.
- `POST /run_pipeline` triggers execution but detailed output is read from `GET /results`.
- Outputs are runtime-stripped for JSON serialization safety.

# Bias Platform (CAF-MAI1)

Bias Platform is a full-stack monorepo for fairness-aware ML workflows.

- **Backend:** FastAPI
- **Frontend:** React (Vite)
- **Pipeline:** Modules 0 through 8 integrated in one orchestrated flow

---

## Repository Structure

```text
CAF-MAI1/
├── bias-platform/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── pipeline_controller.py
│   │   │   ├── schemas.py
│   │   │   └── modules/
│   │   │       ├── module0/  # data contract
│   │   │       ├── module1/  # profiling
│   │   │       ├── module2/  # hidden bias + suggestions
│   │   │       ├── module3/  # aggregation
│   │   │       ├── module4/  # model training + inference
│   │   │       ├── module5/  # fairness metrics
│   │   │       ├── module6/  # debiasing
│   │   │       ├── module7/  # context engine
│   │   │       └── module8/  # decision engine
│   │   └── requirements.txt
│   └── frontend/
│       ├── src/
│       │   ├── App.jsx
│       │   ├── index.css
│       │   ├── main.jsx
│       │   └── services/api.js
│       ├── package.json
│       └── vite.config.js
├── run-backend.sh
├── run-frontend.sh
└── README.md
```

---

## Backend Overview

Backend entrypoint: `bias-platform/backend/app/main.py`

### Core Behavior

- Single FastAPI app instance (no split apps)
- In-memory pipeline state for active session
- `/run_pipeline` executes full orchestration and stores results
- `/results` returns latest stored pipeline output

---

## Pipeline Functionalities

Pipeline orchestrator: `bias-platform/backend/app/pipeline_controller.py`

### Module 0 — Data Contract

- Validates target and selected bias columns
- Creates canonical payload:
  - `X`, `Y`
  - `B_user`, `B_suggested`, `B_hidden`
  - metadata

### Module 1 — Profiling

- Dataset summary:
  - row count
  - column count
  - null counts
  - unique counts

### Module 2 — Bias Discovery

- Suggests candidate bias columns
- Detects hidden bias clusters
- Produces cluster labels and distribution

### Module 3 — Aggregation

- Combines module outputs into unified response envelope

### Module 4 — Model Training Layer

- Preprocessing pipeline (`ColumnTransformer`)
  - numeric: median imputation + standard scaling
  - categorical: most-frequent imputation + one-hot encoding
- Baseline model training
  - logistic regression (default)
  - xgboost path available
- Prediction engine
  - batch predictions + probabilities
  - single prediction + probability

### Module 5 — Fairness Layer

- Subgroup metrics
- Bias gap calculations
- Intersectional analysis
- Fairness metrics (e.g., demographic parity / equal opportunity)

### Module 6 — Debiasing Layer

- Fairness-aware sample weighting
- Reweighted training run
- Resampled training run
- Pre/post fairness comparison
  - `bias_reduction`
  - `fairness_improvement`

### Module 7 — Context Engine

- Stores context (`region`, `hospital_type`, `resource_level`, `time_of_day`)
- Applies context to probabilities
- Returns context weights
- Calculates context-driven bias score
- Provides context explanation

### Module 8 — Decision Engine

- Takes probabilities (typically context-adjusted)
- Produces:
  - final class decision
  - confidence
  - bias score
  - decision explanation

---

## API Endpoints

### Health + Core Pipeline

- `GET /health`
  - health check
- `POST /upload`
  - upload CSV (`multipart/form-data`)
  - returns columns, rows, preview
- `POST /init_contract`
  - body: `{ "target_column": "..." }`
- `POST /select_bias`
  - body: `{ "bias_columns": ["..."] }`
- `POST /run_pipeline`
  - runs full modules pipeline and stores results
  - returns: `{ "status": "completed" }`
- `GET /results`
  - returns full latest results object

### Module 7 — Context Routes (`/context`)

- `POST /context`
  - set context
- `POST /context/apply-context`
  - body: `{ "probabilities": [..] }`
  - returns original/adjusted probabilities + context weights
- `POST /context/explain`
  - body: `{ "probabilities": [..] }`
  - returns explanation of context impact
- `POST /context/bias-score`
  - body: `{ "probabilities": [..] }`
  - returns bias score and impact label

### Module 8 — Decision Routes (`/decision`)

- `POST /decision/final`
  - body: `{ "probabilities": [..] }`
  - returns final decision output
- `POST /decision/explain-final`
  - body: `{ "probabilities": [..] }`
  - returns explanation alongside decision fields

---

## Frontend Overview

Main app: `bias-platform/frontend/src/App.jsx`

### UI Functionalities

- Light minimalist single-page UI
- Top navigation + hero section + helper text + examples + footer
- Context URL input (workflow note field) + `Ingest` CTA
- CSV upload integrated with pipeline flow
- Multi-step workflow:
  1. Upload dataset
  2. Select target
  3. Select bias columns
  4. Run modules 0–6 pipeline
  5. Set context (module 7)
  6. Run final decision (module 8)
  7. View dashboard results

### Results Dashboard Includes

- Dataset summary
- Bias lists (`B_user`, `B_suggested`, `B_hidden`)
- Module 2 cluster distribution
- Module 4 model metrics
- Module 5 fairness outputs
- Module 6 debiasing outputs
- Module 7 context outputs
- Module 8 decision outputs
- Full JSON snapshot

### Frontend API Layer

File: `bias-platform/frontend/src/services/api.js`

- `uploadFile(file)`
- `initContract(targetColumn)`
- `selectBias(biasColumns)`
- `runPipeline()`
- `getResults()`
- `setContext(data)`
- `applyContext(data)`
- `getFinalDecision(data)`
- `explainDecision(data)`

---

## Run Commands

From `CAF-MAI1` root:

### One-command startup

```bash
./run-backend.sh
./run-frontend.sh
```

### Manual backend

```bash
python3 -m pip install -r bias-platform/backend/requirements.txt
PYTHONPATH="bias-platform/backend" python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Manual frontend

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

- Frontend backend URL default: `http://127.0.0.1:8000`
- Override with env: `VITE_API_BASE_URL`

Example:

```bash
VITE_API_BASE_URL="http://localhost:8000" npm --prefix bias-platform/frontend run dev
```

---

## Notes

- Pipeline state is in-memory; restarting backend clears state/results.
- CORS is open in dev (`allow_origins=["*"]`).
- `POST /run_pipeline` returns status only; consume detailed output through `GET /results`.

---

## Troubleshooting

- **No uploaded dataset found**
  - run `/upload` before `/init_contract`
- **Data contract not initialized**
  - run `/init_contract` before `/select_bias` and `/run_pipeline`
- **Frontend cannot reach backend**
  - verify backend on port `8000`
  - verify `VITE_API_BASE_URL`

# Bias Platform (CAF-MAI1)

Bias Platform is a full-stack monorepo with:

- FastAPI backend (`bias-platform/backend`)
- React frontend (`bias-platform/frontend`)
- Pipeline modules currently integrated through **Module 0 to Module 6**

This README is aligned with the code currently present in the repo.

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
│   │   │       ├── module0/  # data contract
│   │   │       ├── module1/  # profiling
│   │   │       ├── module2/  # hidden bias + suggestions
│   │   │       ├── module3/  # aggregation
│   │   │       ├── module4/  # preprocessing + training + inference
│   │   │       ├── module5/  # fairness metrics layer
│   │   │       └── module6/  # debiasing layer
│   │   └── requirements.txt
│   └── frontend/
│       ├── src/
│       │   ├── App.jsx
│       │   ├── index.css
│       │   ├── main.jsx
│       │   └── services/api.js
│       ├── package.json
│       └── vite.config.js
├── run-backend.sh
├── run-frontend.sh
└── README.md
```

---

## Backend

Backend entrypoint: `bias-platform/backend/app/main.py`

### API Endpoints

- `GET /health`
- `POST /upload`
- `POST /init_contract`
- `POST /select_bias`
- `POST /run_pipeline`
- `GET /results`

### Endpoint Behavior

- `POST /upload`
  - accepts CSV (`multipart/form-data`)
  - returns columns, row count, preview
- `POST /init_contract`
  - input: `{ "target_column": "..." }`
- `POST /select_bias`
  - input: `{ "bias_columns": ["..."] }`
- `POST /run_pipeline`
  - triggers full pipeline execution
  - returns: `{ "status": "completed" }`
- `GET /results`
  - returns the full latest pipeline results payload

---

## Pipeline Architecture

Orchestration is centralized in `bias-platform/backend/app/pipeline_controller.py`.

Pipeline execution order (current):

1. **Module 0**: create data contract
2. **Module 1**: profile dataset
3. **Module 2**: bias suggestions + hidden bias clustering
4. **Module 4**: model preprocessing/training/inference
5. **Module 5**: fairness metrics and bias-gap analysis
6. **Module 6**: debiasing with weighted/resampled training and validation
7. **Module 3**: aggregate and shape result envelope

### Runtime Notes

- Pipeline state is in-memory.
- Results are persisted in process memory until restart.
- Non-serializable runtime objects are stripped before returning `/results`.

---

## Module Summary

### Module 0 - Data Contract

- Validates target + bias columns
- Builds canonical payload:
  - `X`, `Y`
  - `B_user`, `B_suggested`, `B_hidden`
  - metadata

### Module 1 - Profiling

- row/column count
- null count by column
- unique count by column

### Module 2 - Bias Detection

- suggested bias columns
- hidden bias discovery with clustering
- cluster labels + distribution

### Module 3 - Aggregation

- combines outputs into unified response object

### Module 4 - Model Training Layer

- preprocessing (`ColumnTransformer`)
  - numeric: median imputation + standard scaling
  - categorical: most-frequent imputation + one-hot encoding
- baseline training
  - logistic regression (default)
  - optional xgboost path
- metrics
  - accuracy, precision, recall, f1
- inference
  - batch predictions + probabilities
  - single prediction + probability

### Module 5 - Fairness Layer

- subgroup metrics
- bias gap calculations
- intersectional bias metrics
- fairness metrics (e.g., demographic parity/equal opportunity)

### Module 6 - Debiasing Layer

- computes fairness-aware sample weights
- runs weighted training
- runs resampled training
- compares pre/post fairness
  - `bias_reduction`
  - `fairness_improvement`

---

## Frontend

Frontend root: `bias-platform/frontend`

Main app: `bias-platform/frontend/src/App.jsx`

### Current UI

- light-mode, minimal single-page layout
- top nav + centered hero + helper text + footer
- CTA includes:
  - repository URL text input (context field)
  - `Ingest` button
  - CSV file upload input
- supporting examples section
- step-based workflow UI

### Step Flow (UI)

1. Upload dataset
2. Select target column
3. Select bias columns
4. Run analysis
5. View results dashboard

### Results Dashboard Sections

- dataset summary
- user/suggested/hidden bias lists
- cluster distribution (Module 2)
- model metrics (Module 4)
- fairness outputs (Module 5)
- debiasing outputs (Module 6)
- full JSON snapshot

### Frontend Service Layer

File: `bias-platform/frontend/src/services/api.js`

- `uploadFile(file)`
- `initContract(targetColumn)`
- `selectBias(biasColumns)`
- `runPipeline()`
- `getResults()`

---

## Run the Project

From repo root (`CAF-MAI1`):

### Start Backend

```bash
./run-backend.sh
```

### Start Frontend

```bash
./run-frontend.sh
```

---

## Manual Commands

### Backend

```bash
python3 -m pip install -r bias-platform/backend/requirements.txt
PYTHONPATH="bias-platform/backend" python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
npm --prefix bias-platform/frontend install
npm --prefix bias-platform/frontend run dev
```

### Frontend Build

```bash
npm --prefix bias-platform/frontend run build
```

---

## Configuration

Frontend API base URL:

- default: `http://127.0.0.1:8000`
- override with `VITE_API_BASE_URL`

Example:

```bash
VITE_API_BASE_URL="http://localhost:8000" npm --prefix bias-platform/frontend run dev
```

---

## Notes

- Backend CORS is open in development (`allow_origins=["*"]`).
- Pipeline data resets on backend restart.
- `POST /run_pipeline` does not return full results; use `GET /results`.

---

## Troubleshooting

- **"No uploaded dataset found. Call upload_data first."**
  - Call `/upload` before `/init_contract`.
- **"Data contract is not initialized."**
  - Call `/init_contract` before `/select_bias` and `/run_pipeline`.
- **Frontend cannot connect to backend**
  - Ensure backend runs on port `8000`.
  - Verify `VITE_API_BASE_URL`.

