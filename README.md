# 🌍 Bias Platform (CAF-MAI1)

![FastAPI](https://img.shields.io/badge/FastAPI-005585?style=flat&logo=fastapi)
![React](https://img.shields.io/badge/React-61DAFB?style=flat&logo=react)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

A **Context-Aware Bias Amplification Detection & Explainable AI System** for responsible ML decision-making.

---

## 🌍 Problem Statement

Automated decision systems often perpetuate societal biases, leading to unfair outcomes for protected groups. Organizations need bias detection, fairness quantification, debiasing, contextual reasoning, and explainable decisions. Existing solutions lack end-to-end integration of these capabilities in a single pipeline.

---

## 💡 Solution Overview

Bias Platform is a **full-stack decision intelligence system** orchestrating an 11-module ML pipeline from data ingestion to monitoring. The system provides calibrated probabilities, bias-aware explanations, and Gemini-powered AI insights with safe fallback mechanisms.

---

## 🎯 Features

- 📊 **End-to-End Pipeline**: Modules 0-11 orchestrated execution
- ⚖️ **Fairness Metrics**: Demographic parity, equal opportunity, bias gaps
- 🔧 **Debiasing**: Reweighting and resampling strategies
- 🧠 **Context Engine**: Operational context weighting (region, hospital_type, resource_level, time_of_day)
- 📝 **Explainability**: Feature importance, context/bias contribution splits
- 🤖 **AI Insights**: Gemini-powered explanations with fallback
- ✅ **Compliance**: Privacy checks, role-based access, policy enforcement
- 📈 **Monitoring**: Data/bias drift detection with alerts
- 🔄 **Calibrated Probabilities**: Sigmoid calibration for reliable confidence
- 💻 **Web UI**: React dashboard for upload, configuration, and results

---

## 🏗️ Architecture

```
┌──────────────────┐     ┌─────────────────────────────────────────┐
│  Frontend        │     │           BACKEND (FastAPI)            │
│  (React + Vite)  │────▶│  /health /upload /init_contract        │
└──────────────────┘     │  /select_bias /run_pipeline /results   │
                          └────────────┬────────────────────────────┘
                                       │
      M0→M1→M2→M4→M5→M6→M7→M8→M9→M10→M11
      Data Prof Bias Model Fair Debi Ctx Dec Val Com Mon
                          │
         ┌────────────────┴────────────────┐
         │    Pipeline Controller           │
         │  (model, fairness, debiasing,    │
         │   context, decision, validation)│
         └──────────────────────────────────┘
```

### Data Flow

1. **Upload** → CSV file parsed into DataFrame
2. **Contract** → Target column validated, features/labels separated
3. **Bias Selection** → User specifies protected attributes
4. **Pipeline Run** → Modules execute sequentially
5. **Results** → Unified JSON response with all module outputs
6. **Context** → Optional context injection for adjusted inference
7. **Decision** → Final decision with explanations

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|--------------|
| Frontend | React 19, Vite 4, Axios |
| Backend | FastAPI, Uvicorn, Pydantic |
| AI/ML | Scikit-learn, XGBoost, Pandas, NumPy |
| AI | Google Generative AI (Gemini) |

---

## 📂 Project Structure

```
CAF-MAI1/
├── bias-platform/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── main.py              # FastAPI entrypoint
│   │   │   ├── pipeline_controller.py # Pipeline orchestration
│   │   │   ├── schemas.py            # Pydantic schemas
│   │   │   ├── config.py             # Configuration
│   │   │   └── modules/
│   │   │       ├── module0/          # Data contract
│   │   │       ├── module1/          # Profiling
│   │   │       ├── module2/          # Bias discovery
│   │   │       ├── module3/          # Aggregation
│   │   │       ├── module4/          # Model training
│   │   │       ├── module5/          # Fairness metrics
│   │   │       ├── module6/          # Debiasing
│   │   │       ├── module7/          # Context engine
│   │   │       ├── module8/          # Decision + explainability
│   │   │       ├── module9/          # Validation
│   │   │       ├── module10/         # Compliance
│   │   │       └── module11/         # Monitoring
│   │   └── requirements.txt
│   └── frontend/
│       ├── src/
│       │   ├── App.jsx               # Main component
│       │   ├── main.jsx              # React entrypoint
│       │   ├── index.css            # Global styles
│       │   ├── components/          # UI components
│       │   └── services/
│       │       └── api.js           # API client
│       ├── package.json
│       └── vite.config.js
├── run-backend.sh
├── run-frontend.sh
└── README.md
```

---

## ⚙️ Installation

### 1. Clone & Setup
```bash
git clone <repo-url>
cd CAF-MAI1
```

### 2. Backend
```bash
cd bias-platform/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### 3. Frontend
```bash
cd bias-platform/frontend
npm install
npm run dev
```

**Backend**: `http://localhost:8000` | **Frontend**: `http://localhost:5173`

---

## 🔌 API Endpoints

### Core Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/upload` | Upload CSV dataset |
| `POST` | `/init_contract` | Initialize with target column |
| `POST` | `/select_bias` | Select bias columns |
| `POST` | `/run_pipeline` | Execute full pipeline |
| `GET` | `/results` | Get pipeline results |

### Decision

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/decision/final` | Get final decision with explanations |

### Example Usage
```bash
# Upload CSV file
curl -X POST -F "file=@data.csv" http://localhost:8000/upload

# Initialize contract with target column
curl -X POST -H "Content-Type: application/json" \
  -d '{"target_column": "outcome"}' \
  http://localhost:8000/init_contract

# Select bias columns
curl -X POST -H "Content-Type: application/json" \
  -d '{"bias_columns": ["gender", "age"]}' \
  http://localhost:8000/select_bias

# Run full pipeline
curl -X POST http://localhost:8000/run_pipeline

# Get results
curl http://localhost:8000/results
```

---

## 🧠 AI/ML Pipeline

### Module Descriptions

| Module | Name | Function |
|--------|------|----------|
| M0 | Data Contract | Validates target/bias columns, builds canonical payload |
| M1 | Profiling | Row/column counts, nulls, uniqueness |
| M2 | Bias Discovery | Suggests bias columns, detects hidden bias via clustering |
| M3 | Aggregation | Harmonizes module outputs into unified response |
| M4 | Model Training | Preprocessing, logistic regression/XGBoost, inference |
| M5 | Fairness | Subgroup metrics, bias gaps, intersectional analysis |
| M6 | Debiasing | Reweighting/resampling, pre/post fairness comparison |
| M7 | Context Engine | Context weighting based on region, hospital_type, etc. |
| M8 | Decision | Final decision, confidence, explanations |
| M9 | Validation | Action feasibility checks |
| M10 | Compliance | Privacy, role-based access, policy enforcement |
| M11 | Monitoring | Data/bias drift detection, alerts |

### Fairness Metrics

- **Demographic Parity**: Equal positive rates across groups
- **Equal Opportunity**: Equal true positive rates
- **Bias Gap**: Difference in fairness metrics between groups
- **Subgroup Analysis**: Per-group performance breakdown
- **Intersectional Fairness**: Multi-attribute bias detection

### Model Configuration

- **Algorithm**: Logistic Regression (default), XGBoost (optional)
- **Preprocessing**: Median imputation + scaling (numeric), Most-frequent + one-hot (categorical)
- **Calibration**: Sigmoid calibration for probability reliability
- **Test Size**: 20% holdout for evaluation

---

