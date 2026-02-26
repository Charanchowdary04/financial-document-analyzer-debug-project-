# Financial Document Analyzer

A production-ready API that analyzes financial PDFs (10-K, 10-Q, earnings reports, etc.) using AI agents (CrewAI), with **sync** and **async queue-based** processing, and **database** storage of results.

---

## Submission Requirements Checklist

| Requirement | Status | Where in this repo |
|-------------|--------|--------------------|
| **Format: GitHub repository** | ✅ | Push this folder to GitHub and submit the repository link. |
| **Fixed, working code** | ✅ | All bugs fixed in `main.py`, `agents.py`, `tools.py`, `task.py`; app runs with `python main.py`. |
| **Comprehensive README** | ✅ | This file. |
| **Bugs found and how you fixed them** | ✅ | [Bugs Found and Fixes](#bugs-found-and-fixes) (10 bugs documented). |
| **Setup and usage instructions** | ✅ | [Setup](#setup) and [Usage](#usage). |
| **API documentation** | ✅ | [API Documentation](#api-documentation) (endpoints, request/response, curl examples). |
| **Bonus: Queue worker (Redis/Celery)** | ✅ | [Queue Worker (Celery + Redis)](#queue-worker-celery--redis). Code: `celery_app.py`, `celery_tasks.py`; `POST /analyze` enqueues jobs, worker processes concurrently. |
| **Bonus: Database for results/user data** | ✅ | [Database](#database). Code: `database.py` (SQLAlchemy, `analysis_jobs` table); stores job status, query, result, errors; `GET /analyze/{job_id}` reads from DB. |
| **Resources: CrewAI Documentation** | ✅ | [Resources](#resources) links to CrewAI docs; project uses CrewAI agents, tasks, tools. |

---

## Table of Contents

- [Bugs Found and Fixes](#bugs-found-and-fixes)
- [Setup](#setup)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Queue Worker (Celery + Redis)](#queue-worker-celery--redis)
- [Database](#database)
- [Project Structure](#project-structure)
- [Resources](#resources)

---

## Bugs Found and Fixes

### 1. **agents.py – Undefined `llm`**

- **Bug:** `llm = llm` caused a `NameError` because `llm` was never defined.
- **Fix:** LLM is now set from environment variables: `LLM_MODEL` (e.g. `gpt-4o-mini`), with `OPENAI_API_KEY` or `GOOGLE_API_KEY` used for authentication. The agent receives a valid model identifier.

### 2. **agents.py – Wrong parameter name `tool=`**

- **Bug:** The CrewAI `Agent` API expects `tools` (plural) and a list. Using `tool=` meant the agent had no tools.
- **Fix:** Replaced `tool=[...]` with `tools=[read_financial_document]`.

### 3. **tools.py – `Pdf` not defined**

- **Bug:** The code used `Pdf(file_path=path).load()` but `Pdf` was never imported, causing `NameError`.
- **Fix:** Replaced with LangChain’s PDF loader: `from langchain_community.document_loaders import PyPDFLoader` and `PyPDFLoader(file_path=path).load()`. Added `pypdf` and `langchain-community` to `requirements.txt`.

### 4. **tools.py – Tool not compatible with CrewAI**

- **Bug:** An `async` instance method without `self` was passed as a tool; CrewAI expects a proper tool interface (e.g. a function or `BaseTool`).
- **Fix:** Implemented a sync tool with CrewAI’s `@tool` decorator: `read_financial_document(path: str) -> str`, which loads the PDF and returns its text. The agent now receives a single, correctly defined tool.

### 5. **main.py – Uploaded file never used**

- **Bug:** `run_crew(query=query, file_path=file_path)` was called but `kickoff()` only received `{'query': query}`. The task and tool always used the default path (`data/sample.pdf`), so the uploaded file was never analyzed.
- **Fix:** The crew is invoked with both inputs: `kickoff({'query': query, 'file_path': file_path})`. The task description in `task.py` includes `{file_path}` and instructs the agent to call the read tool with that path.

### 6. **main.py – Blocking call in async endpoint**

- **Bug:** `run_crew()` is synchronous; calling it directly in an `async def` endpoint blocked the event loop and hurt concurrency.
- **Fix:** The sync endpoint now runs the crew in a thread pool: `await asyncio.to_thread(run_crew, query=query, file_path=file_path)`.

### 7. **main.py – Bare `except: pass`**

- **Bug:** In the `finally` block, `except: pass` hid all errors during file cleanup.
- **Fix:** Cleanup is wrapped in `try/except OSError` (or the same block is left to fail visibly in dev). No bare `except: pass`.

### 8. **task.py – Task not given file path**

- **Bug:** The task description only used `{query}`. The agent had no way to know which file to read.
- **Fix:** The task description now includes `{file_path}` and explicitly tells the agent to call the “Read Financial Document” tool with that path.

### 9. **task.py – Unused / incorrect imports**

- **Bug:** `search_tool` and `verifier` were imported but the verification task used `financial_analyst`; also `FinancialDocumentTool.read_data_tool` was the old interface.
- **Fix:** Task uses `read_financial_document` from `tools`. Verification task can use the `verifier` agent (currently the main flow uses only the analyst). Unused imports removed or kept only where used.

### 10. **requirements.txt and README**

- **Bug:** Missing dependencies: `uvicorn`, `python-dotenv`, PDF support (`pypdf`, `langchain-community`). README said `requirement.txt` instead of `requirements.txt`.
- **Fix:** All required packages are listed in `requirements.txt`. README uses the correct filename: `requirements.txt`.

---

## Setup

### 0. Python version (important)

**CrewAI 0.130 requires Python >=3.10 and <3.14.** If you see `No matching distribution found for crewai==0.130.0`, you are likely on **Python 3.14** or **Python 3.9 or older**.

- **If you have Python 3.14:** Use a virtual environment with Python 3.12 (or 3.10/3.11/3.13):
  ```powershell
  # Windows: install Python 3.12 from https://www.python.org/downloads/, then:
  py -3.12 -m venv .venv
  .venv\Scripts\activate
  pip install -r requirements.txt
  ```
- **If you have Python 3.9 or older:** Install Python 3.10, 3.11, or 3.12 and use it for a venv as above.

Check your version: `python --version`. Optional: run `python check_python.py` to validate before installing.

### 1. Clone and install

```bash
cd financial-document-analyzer-debug
pip install -r requirements.txt
```

### 2. Environment variables

Copy the example env and set at least one LLM key:

```bash
cp .env.example .env
# Edit .env and set:
# OPENAI_API_KEY=sk-...   (for OpenAI)
# and/or GOOGLE_API_KEY=... (for Gemini)
```

Optional:

- `LLM_MODEL` – e.g. `gpt-4o-mini` or `gemini/gemini-1.5-flash`
- `DATABASE_URL` – default `sqlite:///./financial_analyzer.db`
- `REDIS_URL` / `CELERY_BROKER_URL` – required for async queue (see below)

### 3. (Optional) Redis for async queue

For the **async** endpoint (`POST /analyze`), Redis and a Celery worker are needed:

- **Windows:** Install Redis via WSL, Docker, or [Redis for Windows](https://github.com/microsoftarchive/redis/releases).
- **Mac/Linux:** `brew install redis` or `sudo apt install redis-server`, then start Redis (e.g. `redis-server`).

---

## Usage

### Run API only (sync mode)

Sync endpoint works without Redis:

```bash
python main.py
# or: python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
(If `uvicorn` is not found as a command, use `python -m uvicorn`.)

- Open **http://localhost:8000/docs** for Swagger UI.
- Use **POST /analyze/sync** with a PDF file and optional `query` to get the analysis in the response.

### Run with queue (async mode)

1. Start Redis (e.g. `redis-server`).
2. Start the Celery worker (from the project root):

   ```bash
   celery -A celery_app worker --loglevel=info
   ```

3. Start the API:

   ```bash
   python main.py
   ```

4. Use **POST /analyze** to submit a job (returns `job_id`), then **GET /analyze/{job_id}** to poll for status and result.

### Sample document

For testing without uploading:

1. Download e.g. [Tesla Q2 2025 Update](https://www.tesla.com/sites/default/files/downloads/TSLA-Q2-2025-Update.pdf).
2. Save as `data/sample.pdf`.
3. You can call the crew locally with `file_path="data/sample.pdf"` (e.g. from a small script or the sync endpoint with that file).

---

## API Documentation

Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check. |
| POST | `/analyze/sync` | **Synchronous.** Upload a PDF + optional query; response includes full analysis. Blocking. |
| POST | `/analyze` | **Asynchronous.** Upload a PDF + optional query; returns `job_id`. Requires Redis + Celery. |
| GET | `/analyze/{job_id}` | Get status and result (or error) for an async job. |

### POST /analyze/sync

- **Request:** `multipart/form-data`
  - `file` (required): PDF file.
  - `query` (optional): Analysis prompt; default: `"Analyze this financial document for investment insights"`.
- **Response (200):**
  ```json
  {
    "status": "success",
    "query": "...",
    "analysis": "Full text of the analysis.",
    "file_processed": "original_name.pdf"
  }
  ```

### POST /analyze (async)

- **Request:** Same as `/analyze/sync`.
- **Response (200):**
  ```json
  {
    "job_id": "uuid",
    "status": "pending",
    "message": "Analysis queued. Poll GET /analyze/{job_id} for result."
  }
  ```

### GET /analyze/{job_id}

- **Response (200):**
  - While processing: `"status": "pending"` or `"processing"`.
  - On success: `"status": "completed"`, `"analysis": "..."`.
  - On failure: `"status": "failed"`, `"error": "..."`.

Example with `curl`:

```bash
# Sync
curl -X POST "http://localhost:8000/analyze/sync" \
  -F "file=@data/sample.pdf" \
  -F "query=Summarize revenue and margins"

# Async
JOB=$(curl -s -X POST "http://localhost:8000/analyze" -F "file=@data/sample.pdf" | jq -r .job_id)
curl "http://localhost:8000/analyze/$JOB"
```

---

## Queue Worker (Celery + Redis)

- **Broker/backend:** Redis (`REDIS_URL` / `CELERY_BROKER_URL` in `.env`).
- **Flow:**
  1. `POST /analyze` saves the file, creates a row in `analysis_jobs` with `status=pending`, and enqueues a Celery task.
  2. A Celery worker runs the CrewAI crew (same logic as sync), then updates the job to `completed` or `failed` and stores the result or error message.
  3. The client polls `GET /analyze/{job_id}` until `status` is `completed` or `failed`.
- **Concurrency:** Run multiple workers or use `celery -A celery_app worker --concurrency=4` to handle several analyses in parallel. On Windows you may need `--pool=solo`: `celery -A celery_app worker --loglevel=info --pool=solo`.
- **File cleanup:** The worker deletes the uploaded file after processing.

---

## Database

- **Default:** SQLite, file `financial_analyzer.db` in the project root (overridable with `DATABASE_URL`).
- **Table:** `analysis_jobs`
  - `id` (UUID), `status`, `file_path`, `original_filename`, `query`, `result_text`, `error_message`, `created_at`, `updated_at`.
- **Usage:** All async jobs are stored here; `GET /analyze/{job_id}` reads from this table. Sync endpoint does not create a job row unless you add that behavior.
- **Migrations:** Tables are created on startup via `init_db()` in `main.py`. For production, consider Alembic or similar.

---

## Project Structure

```
financial-document-analyzer-debug/
├── main.py           # FastAPI app, /analyze/sync and /analyze + GET /analyze/{id}
├── agents.py         # CrewAI agents (financial_analyst, verifier)
├── task.py           # CrewAI tasks (analyze_financial_document, verification)
├── tools.py          # read_financial_document tool (PDF via LangChain)
├── config.py         # Env-based config (LLM, DB, Redis)
├── database.py       # SQLAlchemy model and session for analysis_jobs
├── celery_app.py     # Celery app
├── celery_tasks.py   # Celery task that runs crew and updates DB
├── requirements.txt
├── .env.example
└── README.md
```

---

## Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [CrewAI – Create Custom Tools](https://docs.crewai.com/learn/create-custom-tools)
- [CrewAI – LLM Connections](https://docs.crewai.com/en/learn/llm-connections)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Celery](https://docs.celeryq.dev/)

---

**Summary:** All identified bugs are fixed, the uploaded PDF is used via `file_path` in the crew, and the app supports both synchronous analysis and concurrent async processing with a queue and database storage.

---

## Submitting This Project

1. Create a new GitHub repository (e.g. `financial-document-analyzer`).
2. Push this project. A `.gitignore` is included so `.venv`, `.env`, `*.db`, and `__pycache__` are not committed. Example:
   ```bash
   git init
   git add .
   git commit -m "Financial Document Analyzer - fixed code, README, queue, DB"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```
3. Submit the **GitHub repository link** (e.g. `https://github.com/YOUR_USERNAME/YOUR_REPO`).
