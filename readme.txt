================================================================================
  BIAS PLATFORM (CAF-MAI1) — ENGINEERING README
================================================================================

  What it is   A web app that trains a classifier on an uploaded CSV, measures
               whether its outcomes differ across groups (e.g. gender), applies
               bias mitigation, and explains individual decisions.
  Stack        Python 3.11-3.14 / FastAPI / scikit-learn / pandas  (backend)
               React 19 / Vite 4 / Recharts / Axios               (frontend)
               Google Gemini (optional, for natural-language explanations)
  Status       Working end to end. 32 backend tests pass. Verified in a
               browser on small datasets and on a 471 MB / 6.36M-row CSV.

  Contents
    1.  Quick start
    2.  How to use the app
    3.  Architecture
    4.  The pipeline, stage by stage
    5.  HTTP API
    6.  Configuration
    7.  Frontend
    8.  Testing
    9.  Performance and limits
    10. Engineering assessment (risks and limitations)
    11. Recommended roadmap
    12. Troubleshooting
    13. Repository layout


================================================================================
1. QUICK START
================================================================================

Prerequisites: Python 3.11+ and Node.js 18+ (with npm) on PATH.

  Terminal 1 (backend):
      ./run-backend.sh            (Windows: .\run-backend.ps1)

  Terminal 2 (frontend), after the backend says it is running:
      ./run-frontend.sh           (Windows: .\run-frontend.ps1)

  Then open the "Local:" URL Vite prints, normally http://127.0.0.1:5173

What the scripts do:
  - run-backend.sh creates bias-platform/backend/.venv on first run, installs
    requirements.txt, picks the first free port from 8000-8010 (override with
    BACKEND_PORT), writes it to bias-platform/backend/.port, and starts uvicorn
    on 127.0.0.1 with --reload.
  - run-frontend.sh reads that port, sets API_PROXY_TARGET, installs npm
    packages and starts Vite. The browser only ever talks to Vite; Vite
    forwards /api/* to the backend. There is no CORS or port setup to do.
  - If you restart the backend and it lands on a different port, restart the
    frontend too.

Optional AI explanations: create bias-platform/backend/.env containing
      GEMINI_API_KEY=your_key
Without a key everything still works; explanations fall back to rule-based
text. The .env file is git-ignored.


================================================================================
2. HOW TO USE THE APP
================================================================================

  1. Upload a CSV.
  2. Target column: the outcome to predict. It must have exactly two values
     (yes/no, 0/1, True/False). Other columns are disabled in the dropdown.
     A default is suggested (names like target, label, survived, approved,
     fraud, churn are preferred).
  3. Sensitive attribute: the column whose groups are compared (gender, region,
     age band...). It needs at most 50 distinct values.
  4. Optionally set "Available Resources" (used by the feasibility check).
  5. Run the pipeline. The dashboard shows model quality, fairness before and
     after mitigation, a decision for one record (choose any record number and
     click "Score record"), feasibility, monitoring and explanations.

Good test datasets: Titanic (target Survived, attribute Sex or Pclass), Adult
Income (target income, attribute sex/race), German Credit. The PaySim fraud
dataset runs fine but has no demographic attribute, so it says little about
bias.


================================================================================
3. ARCHITECTURE
================================================================================

    Browser (React SPA)
        |   all calls to /api/*  + header X-Session-ID (one per browser tab)
        v
    Vite dev server  --(proxy, strips /api)-->  FastAPI (app/main.py)
                                                   |
                                    session registry (LRU, in memory)
                                                   |
                                        BiasPipeline (pipeline_controller.py)
                                                   |
        M0 data contract -> M4 train -> M5 fairness (before) -> M6 mitigation
        -> M5 fairness (after) -> M8 decision -> M9 feasibility -> M11 monitoring
                                                   |
                                     Gemini (optional, M5 / M8 / M11 text)

Key design points
  - State: each session holds the uploaded DataFrame, the data contract, the
    fitted models and the last results, in process memory. Nothing is
    persisted; restarting the backend clears everything.
  - Sessions: the frontend generates a random id per tab (sessionStorage) and
    sends it as X-Session-ID. The server keeps at most MAX_SESSIONS (default
    10), evicting the least recently used. Each session has a lock, so
    requests within one session run one at a time.
  - Errors: ValueError -> HTTP 400 with a user-readable message; anything
    else -> HTTP 500 "Internal error: ..." and a logged stack trace.
  - Module numbers (0, 4, 5, 6, 8, 9, 11) are historical; 1-3, 7 and 10 were
    removed or never implemented.


================================================================================
4. THE PIPELINE, STAGE BY STAGE
================================================================================

M0  Data contract  (modules/module0/data_contract.py)
  - Drops rows with a missing target.
  - Target must have exactly two distinct values. Values are sorted and the
    SECOND one becomes the positive class (1): no<yes, 0<1, False<True.
    Original labels are kept in metadata.class_labels.
  - Identifier columns are excluded from modelling: text columns where
    distinct values > 50% of rows, or > 1,000 and > 5% of rows (e.g. customer
    or account IDs). Listed in metadata.excluded_id_columns.
  - Numeric columns -> float (inf becomes NaN); other columns -> string,
    keeping NaN so the model's imputer handles it.

M4  Training  (modules/module4/)
  - Stratified 80/20 train/test split (random_state=42). Needs >= 20 rows
    and >= 2 rows per class.
  - If the training split exceeds MAX_TRAIN_ROWS (500k), a stratified sample
    of that size is used for fitting. The test split is never sampled.
  - Preprocessing: numeric = median impute + standardize; categorical =
    impute "missing" + one-hot (max 50 categories per column, rarer ones
    pooled into an "infrequent" bucket; unseen categories handled).
  - Model: LogisticRegression (liblinear, max_iter 1200).
  - Note: the sensitive attribute is an ordinary input feature (see 10.1).

M5  Fairness  (modules/module5/) — always computed on the held-out test split
  - Per group: positive-prediction rate, TPR (equal opportunity), FPR,
    precision, confusion counts; also intersectional metrics across all
    selected attributes.
  - Bias gap per attribute, from the groups' positive-prediction rates:
        gap = clamp( 0.7 * (max - min) + 0.3 * mean|pairwise difference|,
                     0, 0.95 )
    The headline bias_gap is the maximum over attributes.
  - Bias level (shared by backend and UI): < 0.10 low, < 0.20 moderate,
    otherwise high.
  - Also: global accuracy/F1, confusion matrix, outcome distribution, and an
    optional Gemini summary (only for the "after" pass).

M6  Mitigation  (modules/module6/service.py) — fitted on the training split
  - Skipped when the bias gap is below 0.03 (reported as "Already Fair").
  - Step 1, reweighing (Kamiran & Calders): weight = P(group) * P(label) /
    P(group, label), normalised to mean 1; a second logistic regression is
    trained with these weights.
  - Step 2, group thresholds (demographic-parity post-processing): the target
    rate is the share of training rows the reweighed model scores >= 0.5. For
    each group with >= 5 training rows, the threshold is the (1 - rate)
    quantile of that group's scores, clipped to [0.05, 0.95]. Unseen groups
    use 0.5. Groups are the combination of all selected attributes.
  - Adjusted probability shown in the UI: sigmoid(logit(p) - logit(t)), so it
    is >= 0.5 exactly when p clears its group threshold t.
  - The pipeline reports before/after bias gap and before/after accuracy on
    the test split.

M8  Decision  (modules/module8/decision.py)
  - Scores one record (any row of the dataset; default row 0). "Original"
    probability comes from the baseline model, the used probability from the
    mitigated model (if mitigation ran).
  - Top features: the 5 largest absolute coefficients of the baseline model
    (on standardised / one-hot features). These are global, not per-record.
  - Explanation: Gemini text if available, otherwise a rule-based sentence.

M9  Feasibility  (modules/module9/service.py)
  - approve -> allocate_resources, reject -> no_action (needs 0 resources).
  - Required resources for an approval = clamp(int(confidence * 10), 1, 10).
  - Feasible if required <= available; otherwise "fallback" with a partial
    allocation or "delay_action". Risk is high if bias is high, moderate if
    confidence < 0.6, else low.
  - This is an illustrative business rule, not a learned model.

M11 Monitoring  (modules/module11/service.py)
  - "Data drift": PSI between training and test split for every numeric
    column, using quantile bins from the training data (bins sized for
    ~20 rows each; skipped below 30 rows). Alert above 0.15.
  - Bias trend: compared with the previous run of the same configuration
    (same columns, row count, target and attributes) in the same session.
    First run = "baseline". Alert if the gap rose by more than 0.10.
  - Alerts also name the most and least favoured group for any attribute with
    a moderate or high gap.


================================================================================
5. HTTP API
================================================================================

Base: the backend port directly, or /api through the Vite dev server.
Optional header on every call: X-Session-ID: <any string up to 128 chars>.

  GET  /health                 -> {"status": "ok"}
  POST /upload                 multipart field "file" (CSV, <= MAX_UPLOAD_MB).
                               Encodings tried: UTF-8 (with/without BOM),
                               Windows-1252, Latin-1.
                               -> columns, rows, binary_columns, suggested_target
  POST /init_contract          {"target_column": "Survived"}
                               -> rows, columns (model features), metadata
  POST /select_bias            {"bias_columns": ["Sex"]}
                               rejects unknown, target, ID-like and >50-group
                               columns
  POST /run_pipeline           {"row_index": 0, "available_resources": 8}
                               -> decision, validation, model, class_labels,
                                  fairness, fairness_before, module6, monitoring
  POST /decision               {"row_index": 42, "available_resources": 8}
                               re-scores one record without retraining
  GET  /results                last results for this session (404 if none)

Step order is enforced: upload -> init_contract -> select_bias -> run_pipeline
-> decision. Uploading again or changing the target or attributes clears
earlier results. Interactive docs: http://127.0.0.1:<port>/docs


================================================================================
6. CONFIGURATION
================================================================================

Backend (bias-platform/backend/.env, all optional):

  GEMINI_API_KEY         none                    enables AI explanations
  GEMINI_MODEL           gemini-3.5-flash-lite   tried first
  GEMINI_FALLBACK_MODEL  gemini-3.8-flash        tried if the first fails
  GEMINI_TIMEOUT_MS      10000                   per call; Gemini's minimum
  MAX_UPLOAD_MB          1024                    upload size limit
  MAX_TRAIN_ROWS         500000                  training sample cap
  MAX_BIAS_GROUPS        50                      max groups per attribute
  MAX_SESSIONS           10                      sessions kept in memory
  CORS_ORIGINS           localhost:5173 and      only matters when a browser
                         127.0.0.1:5173          calls the backend directly

Scripts / frontend:

  BACKEND_PORT           force the backend port (both run scripts honour it)
  API_PROXY_TARGET       backend URL for the Vite proxy (set by run-frontend)
  VITE_API_BASE_URL      make the browser call the API directly instead of
                         /api (then add the frontend origin to CORS_ORIGINS)

What is sent to Gemini: aggregate metrics (bias gap, parity values), the
decision, confidence and top feature names/coefficients. No raw rows. Model
names get retired by Google over time; if explanations stop, check the backend
log and update GEMINI_MODEL.


================================================================================
7. FRONTEND
================================================================================

  src/App.jsx                    flow state: upload -> target/attribute -> run
                                 -> dashboard; stepper; loading overlay; errors
  src/services/api.js            Axios client, session header, timeouts
                                 (30 s default, 5 min data calls, 15 min
                                 pipeline), response normalisation
  components/ColumnSelector      target dropdown (non-binary disabled) and
                                 attribute dropdown
  components/PipelineRunner      resources input + run button
  components/FairnessPanel       accuracy, F1, bias gap, before/after
  components/OutcomeCharts       per-group parity bar chart, confusion matrix
  components/DecisionCard        record selector, decision, probabilities
  components/ValidationCard      feasibility
  components/MonitoringCard      drift, trend, alerts
  components/ExplainabilityPanel top features
  components/ResultsDashboard    layout + AI explanation accordions

Notes: the stepper lights a step only once completed. Results are cleared
whenever upload, target or attribute changes. A minimum 3 s loading animation
is enforced on pipeline runs (deliberate UX choice).


================================================================================
8. TESTING
================================================================================

    cd bias-platform/backend
    .venv/bin/pip install -r requirements-dev.txt
    .venv/bin/python -m pytest tests

  32 tests, ~1 s, offline (Gemini is disabled in tests). Verified on Python
  3.11, 3.13 and 3.14.
  - tests/test_modules.py  unit tests per module: target encoding, ID
    exclusion, fairness maths, reweighing balance, mitigation reducing the
    gap, decision, feasibility fallback, drift and trend.
  - tests/test_api.py      HTTP flow end to end: step-order errors, full
    run, record re-scoring, session isolation, large-dataset sampling, input
    validation, encodings.

  There are no frontend tests and no CI (see roadmap).


================================================================================
9. PERFORMANCE AND LIMITS
================================================================================

Measured on an Apple Silicon Mac:

  Dataset                          Upload   Set target   Pipeline   Memory
  500 rows, 5 columns              <1 s     <1 s         ~3 s*      small
  6,362,620 rows, 471 MB (PaySim)  ~6-13 s  ~3-4 s       ~10-12 s   ~1 GB per
                                                                     session
  * includes the 3 s minimum loading animation.

  Gemini adds up to ~10-20 s per call when the service is slow (up to two
  calls per run, one per "Score record"). Use the lite model to keep it fast.

Hard limits: 1 GB upload, binary targets only, <= 50 groups per attribute,
>= 20 rows. Memory: with 10 sessions each holding a multi-million-row file,
the backend can need ~10 GB.


================================================================================
10. ENGINEERING ASSESSMENT (RISKS AND LIMITATIONS)
================================================================================

Severity: HIGH = can mislead users or block real use; MED = notable gap;
LOW = polish.

10.1 Methodology (what the numbers mean)

  [HIGH] The sensitive attribute is a model input, and group thresholds need
         it at decision time. Treating people differently by group is
         explicitly regulated in lending, hiring and insurance. Offer a
         "fairness through unawareness" option that excludes the attribute
         from features, and document when group-aware thresholds are allowed.

  [HIGH] Positive class is chosen alphabetically. "approved"/"rejected"
         makes "rejected" the positive outcome, which inverts every approval
         rate and the approve/reject labels. Let the user pick the positive
         label.

  [HIGH] Mitigation optimises demographic parity only and can overshoot. In
         a 500-row test the gap flipped direction (men favoured before,
         women after). With small test splits, group rates carry large
         sampling error (+/- 0.1 at ~50 rows per group). Add confidence
         intervals (bootstrap), a minimum group size, and a choice of
         criterion (demographic parity vs equalised odds).

  [MED]  The headline "bias gap" is a custom blend (0.7 range + 0.3 mean
         pairwise difference, capped at 0.95). It is not a standard metric.
         Report the standard demographic-parity difference and the
         disparate-impact ratio (four-fifths rule) alongside or instead.

  [MED]  Imbalanced targets make accuracy misleading. On PaySim accuracy is
         99.9% while recall is 32%. Show balanced accuracy, recall and PR-AUC
         prominently; offer class_weight="balanced".

  [MED]  The "probability after mitigation" is a threshold-shifted score,
         not a calibrated probability. Label it as an adjusted score.

  [MED]  "Data drift" compares the training and test splits of one file,
         which is a sanity check, not production drift monitoring. Real drift
         needs a reference dataset and new scoring data over time.

  [LOW]  Top features are global coefficients, not per-record explanations.
         Per-record attributions (coefficient x value, or SHAP) would make
         "Why this decision?" accurate.

  [LOW]  The feasibility rule in M9 (confidence x 10 resources) is
         illustrative. Make it configurable or clearly label it as a demo.

  [LOW]  Only logistic regression is supported.

10.2 Engineering

  [HIGH] All state lives in one process's memory. A restart loses every
         session; the app cannot run on more than one worker; memory grows
         with ~1 GB per large session. Needed for multi-user use: persisted
         uploads (disk/object storage), job ids, and stored results.

  [HIGH] No authentication or authorisation. The session id is a
         client-chosen string, not a credential. This is acceptable only
         while the server binds to 127.0.0.1 (the default). Add auth before
         exposing it on a network.

  [MED]  Long work runs inside the HTTP request (up to minutes for big files)
         with no progress reporting or cancellation. Move training to a
         background job and poll for status.

  [MED]  No production deployment path. The /api proxy exists only in the
         Vite dev/preview server, and uvicorn runs with --reload. Production
         needs a static frontend build behind a reverse proxy (nginx/Caddy)
         routing /api, uvicorn/gunicorn workers without --reload, and a
         container image.

  [MED]  Frontend dependencies: npm audit reports 11 issues (8 high), including
         the direct dependencies axios 1.15.2 and vite 4.5.14. "npm audit fix"
         resolves them; a Vite 5+/6 upgrade is due. The dev server binds to
         127.0.0.1, which limits exposure.

  [MED]  No CI. Add a workflow that runs pytest and the frontend build on
         every pull request.

  [MED]  No typed API contract. FastAPI endpoints return dicts without
         response models, and api.js re-normalises every field by hand. Add
         Pydantic response models and generate client types (or move the
         frontend to TypeScript).

  [LOW]  Frontend: no tests; 1,600-line global stylesheet; 634 KB bundle
         (mostly Recharts; code-split the dashboard); formatFeature is
         duplicated in two components.

  [LOW]  Backend: thresholds and magic numbers are spread across modules;
         collect them in config.py. fairness_before, intersectional metrics,
         group thresholds and per-column drift are computed but not shown in
         the UI.

  [LOW]  No LICENSE file.

10.3 What is in good shape

  - Clear stage separation; each module is small and testable.
  - Metrics are evaluated on held-out data; mitigation is fitted only on
    training data (no leakage between them).
  - Inputs are validated early with actionable messages (non-binary target,
    ID columns, too many groups, wrong step order, file size, encodings).
  - Scales to millions of rows on a laptop (vectorised code, sampling, ID
    exclusion, capped one-hot encoding).
  - Gemini is optional, time-limited, has a fallback model and never breaks
    a run.
  - Fast, offline, deterministic test suite covering the full HTTP flow.


================================================================================
11. RECOMMENDED ROADMAP
================================================================================

  P0 (correctness / trust)
    1. Let the user choose the positive label.
    2. Option to exclude the sensitive attribute from model features.
    3. Confidence intervals and minimum group size for fairness metrics.
    4. Report standard demographic-parity difference and disparate-impact
       ratio; show balanced accuracy and recall for imbalanced data.

  P1 (operability)
    5. CI: pytest + frontend build on every PR.
    6. npm audit fix; upgrade Vite.
    7. Background jobs with progress; persisted uploads and results.
    8. Production packaging: Dockerfile(s), static frontend + reverse proxy.
    9. Authentication before any network exposure.

  P2 (product)
    10. Per-record explanations; choice of fairness criterion and model.
    11. Show intersectional metrics, before/after per group and thresholds.
    12. Typed API contract (Pydantic response models + generated client).


================================================================================
12. TROUBLESHOOTING
================================================================================

  Page stuck on the loading spinner
      Check the backend terminal for errors. Make sure you started
      run-backend.sh BEFORE run-frontend.sh; if the backend was restarted,
      restart the frontend so it picks up the backend's port.

  "Cannot reach the backend" / "could not reach the backend"
      The backend is not running or the proxy points at the wrong port.
      Restart both scripts in order.

  "Target column ... has N distinct values"
      Choose a two-valued column (only those are enabled in the dropdown).

  "'<column>' has N distinct values; a sensitive attribute needs at most 50"
      You picked a continuous or ID-like column (e.g. amount). Pick a
      categorical attribute such as gender, region or age band.

  "... look like identifier columns"
      ID columns are excluded from modelling and cannot be attributes.

  "File is larger than N MB"
      Raise MAX_UPLOAD_MB in .env (memory: ~1 GB per ~6M rows).

  Explanations say "Explanation unavailable" or are rule-based
      No GEMINI_API_KEY, the model is overloaded, or the model name was
      retired. Check the backend log for "Gemini request ... failed".

  Port 8000 already in use
      Handled automatically (8001-8010). Force one with BACKEND_PORT=8005.

  pip fails to install numpy/pandas
      Use Python 3.11-3.14. Delete bias-platform/backend/.venv and rerun
      run-backend.sh to rebuild the environment.


================================================================================
13. REPOSITORY LAYOUT
================================================================================

  run-backend.sh / .ps1          start API (venv, deps, free port)
  run-frontend.sh / .ps1         start UI with /api proxy
  README.md                      shorter overview
  readme.txt                     this document
  bias-platform/
    backend/
      app/main.py                routes, sessions, error mapping
      app/pipeline_controller.py orchestration and per-record decisions
      app/config.py              environment settings
      app/schemas.py             request models
      app/utils/gemini_client.py Gemini wrapper (timeout, fallback)
      app/modules/module0        data contract
      app/modules/module4        preprocessing + training
      app/modules/module5        fairness metrics, bias gap
      app/modules/module6        mitigation
      app/modules/module8        decision + explanation
      app/modules/module9        feasibility
      app/modules/module11       monitoring
      tests/                     pytest suite
      requirements.txt           runtime dependencies (pinned)
      requirements-dev.txt       + pytest, httpx
    frontend/
      vite.config.js             dev server + /api proxy
      src/                       React app (see section 7)

================================================================================
