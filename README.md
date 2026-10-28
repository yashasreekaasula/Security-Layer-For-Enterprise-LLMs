# Privacy Budget Autopilot — Company Copilot

Standalone enterprise assistant MVP. It includes a FastAPI API, React/TypeScript frontend, SQLite local database, PostgreSQL deployment configuration, synthetic employee registry, synthetic knowledge base, a PPO actor-critic training pipeline, privacy decision enforcement, persistent budgets, and audit events. **All seeded business records are synthetic.** This project is a development MVP, not a certified security product.

## Contents

- `backend/app`: API, ORM models, authentication, retrieval, policy enforcement, data generation, PPO training/inference, admin bootstrap.
- `backend/tests`: API/security/integration tests.
- `frontend`: React + TypeScript + Vite light-theme UI.
- `data/company_copilot.db`: seeded SQLite database (50,000 documents, 3,000 employees, 26 projects).
- `data/generated/company_knowledge_base.csv`: separate, readable export of all 50,000 documents (not just a generator script or a small sample).
- `data/employees/employee_directory.xlsx`, `employees.csv`: synthetic directory exports.
- `models/privacy_ppo.pt`: PPO checkpoint; `reports/`: separate validation and test reports.
- `scripts/`: Windows setup, data generation, training/evaluation, startup, and tests.

## Windows PowerShell: fresh checkout

Prerequisites: Python 3.12, Node.js 20+, npm. PostgreSQL is optional for local development; SQLite is used by default.

```powershell
# Run from the extracted project root
Set-ExecutionPolicy -Scope Process Bypass
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r .\backend\requirements.txt
alembic upgrade head
cd frontend
npm install
cd ..
```

### Generate all synthetic data (can take several minutes)

```powershell
$env:PYTHONPATH = "$PWD\backend"
python -m app.seed 3000 50000
```

This writes the database to `data\company_copilot.db`, the employee exports to `data\employees\`, and 50,000 document records into the `documents` table. The ZIP also includes the complete CSV export at `data\generated\company_knowledge_base.csv`; the SQLite database is the app source of truth, while CSV is provided for inspection and reuse.

### Train and evaluate PPO

```powershell
$env:PYTHONPATH = "$PWD\backend"
python -m app.train
```

This performs clipped PPO policy optimization and writes `models\privacy_ppo.pt`, `reports\evaluation_validation.json`, and `reports\evaluation_test.json`. The 12,000 synthetic scenarios are split before training into 8,400 train, 1,800 validation, and 1,800 test samples. The reports explicitly label the data as synthetic and heuristic-labelled. PPO output is a recommendation only; mandatory backend policy checks can override it.

### Create the first local administrator

After generating data, in PowerShell:

```powershell
$env:PYTHONPATH = "$PWD\backend"
python -m app.create_admin
```

Use a strong unique password. This is a local bootstrap utility. Do not expose it as a public API or reuse demo secrets in production.

### Start the backend

PowerShell window 1, from project root:

```powershell
$env:PYTHONPATH = "$PWD\backend"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs

### Start the frontend

PowerShell window 2:

```powershell
cd .\frontend
npm run dev
```

Open the exact URL Vite prints (normally http://localhost:5173).

### Run tests and frontend build

PowerShell window 3, project root:

```powershell
$env:PYTHONPATH = "$PWD\backend"
python -m pytest .\backend\tests -q
cd .\frontend
npm test
npm run build
```

Tests create a temporary SQLite database in `backend/tests/test.db`. If a previous test run left it behind, the test setup removes it on startup.

## Demo employee activation

Use an exact employee ID, email, and full name from `data\employees\employee_directory.xlsx`. Create your own password. This synthetic matching flow is for demos only and is not secure identity proofing: production must use verified SSO or administrator-approved one-time activation tokens. New public registrations receive the `Employee` role and remain pending approval.

## Optional OpenAI provider

Install the OpenAI SDK (`pip install openai`) and set environment variables in the backend process; never hard-code the key:

```powershell
$env:OPENAI_API_KEY = "your-key"
$env:OPENAI_MODEL = "gpt-4o-mini"
```

Without a key, the app runs in local demo mode. Local coding help covers a few examples; general coding assistance requires a configured LLM provider. Company answers without an LLM are extractive summaries from authorized synthetic documents.

## PostgreSQL / Docker

Run `docker compose up --build` from the project root to start PostgreSQL, the API, and the web frontend. The backend container seeds 3,000 employees and 50,000 documents into PostgreSQL on first startup. To create the first administrator, run `docker compose exec backend python -m app.create_admin`.

Set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL and configure a strong `JWT_SECRET`. `docker-compose.yml` provides PostgreSQL and backend/frontend containers. For a production deployment, add a managed secret store, HTTPS termination, revocable sessions, formal identity verification, backup/restore procedures, observability, and security review. The bundled local DB and demo activation are not production identity/security controls.

## Security model and limitations

- Server derives identity, department, and role from a signed bearer token and database row; clients cannot set roles in chat requests.
- Retrieval filters documents by department/classification/role before constructing the LLM context.
- Credential requests are refused; sensitive requests are blocked or routed before retrieval when the caller lacks the required role.
- Disclosure budgets are persistent enterprise allowances, **not** differential privacy epsilon guarantees.
- Every chat decision creates a budget transaction and audit event without storing the raw message in the audit detail.
- Current MVP access tokens expire but logout is client-side token deletion; production should implement revocable server-side sessions/refresh-token rotation.
- Demo registry matching is not strong identity proofing. Some policy matrices and local retrieval are intentionally lightweight and require security review before real employee data is introduced.
- Synthetic metrics do not prove real-world privacy guarantees. Evaluate the reports; do not claim 100% privacy or production readiness.

## Troubleshooting

- `python` not found: install Python 3.12 and enable the PATH option; run `py -3.12 --version`.
- npm not found: install Node.js LTS and reopen PowerShell.
- `ModuleNotFoundError: app`: from project root, set `$env:PYTHONPATH = "$PWD\backend"`.
- SQLite locked: stop other API/test processes before reseeding.
- `npm install` DNS error: check network/DNS and retry; don't edit source files to work around registry outages.
- Port busy: change the backend `--port` or Vite `--port` and update CORS accordingly.

## Verification report for this archive

See `reports/validation_status.json`, `reports/data_validation.json`, `reports/training_log.txt`, and `reports/end_to_end_smoke.txt` for captured results.

- Data validation: **50,000 documents**, **50,000 unique titles and content records**, 26 projects, 20 document types; **3,000 unique employees** across 10 departments; no pre-activated employee accounts in the shipped database.
- Backend tests: **27 passed**. End-to-end smoke flow passed for employee activation, authorization denial, policy retrieval, Project Bumblebee retrieval, credential refusal, missing-fact behavior, coding routing, privacy-budget/audit persistence, ambiguous-query handling, and logout revocation.
- PPO validation: action accuracy **88.50%**, macro F1 **0.7392**. PPO test: action accuracy **88.89%**, macro F1 **0.7363**. The raw model sometimes recommends an unsafe action in synthetic cases; mandatory enforcement reduced measured unsafe disclosure to **0%** in these synthetic evaluation cases. This is not a real-world privacy guarantee.
- Baseline accuracy is **100%** because the rule-based baseline defines the synthetic labels; this is not evidence of production superiority.
- Frontend source smoke checks and TSX syntax checks passed, but the npm install timed out in the build environment, so the full Vite production build could not be verified here. PostgreSQL/Docker execution was not run.


## Security hotfix notes
- Named-person financial and sensitive-record requests now require explicit authorization and skip retrieval, including for administrator accounts.
- Local Python print-statement requests are handled without an external LLM.
- If an optional LLM provider fails, the backend falls back to labelled extractive excerpts from authorized evidence instead of returning a generic provider failure.
