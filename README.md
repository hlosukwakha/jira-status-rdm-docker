
# Jira Status RDM — Manage Jira Workflow Statuses as Reference Data (Docker)

[![Stack](https://img.shields.io/badge/Stack-Docker%20%7C%20Airflow%20%7C%20Postgres%20%7C%20FastAPI%20%7C%20Jinja2%20%7C%20Confluence%20API%20%7C%20GitHub-blue)](#tech-stack)
[![Airflow](https://img.shields.io/badge/Airflow-2.9.2-017CEE?logo=apache-airflow&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python-3.11%2F3.12-3776AB?logo=python&logoColor=white)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)

---

## Why this exists (short blog-style intro)

Most teams treat Jira workflow statuses like admin trivia… until the sprawl hits. One team creates **“Pending Triage,”** another adds **“Awaiting PO”**, and before long your reports break, boards get noisy, and nobody remembers why half the statuses exist.

This project treats **Jira workflow statuses as reference data**. You maintain a single **golden catalogue** (YAML). The stack validates it, compares it with Jira, (optionally) enforces it, and publishes human‑readable docs to **Confluence**. It can also push catalogue changes to **GitHub** for review.

**How it works end‑to‑end:**

1. You **author** statuses in `statuses.yaml` (or via a tiny **FastAPI** RDM service).  
2. **Airflow** runs a DAG that **validates** the data, **diffs** it with Jira, **optionally syncs** it (guarded), and **publishes** a catalogue + per‑status pages to **Confluence**.  
3. Optionally, the run opens a **GitHub branch/PR** to review catalogue changes.  
4. The result: a small, consistent, auditable set of statuses—and clear documentation for humans.

> Human docs include: *status name, category, transitions in/out, conditions, validators, post‑functions, permissions, who requested it, business rationale, business impact if removed, related automations/reports, lifecycle*, etc.

---

## Contents

- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Git Clone & Project Layout](#git-clone--project-layout)
- [Configuration](#configuration)
- [Run the Stack](#run-the-stack)
- [Airflow DAG: What It Does](#airflow-dag-what-it-does)
- [Day‑to‑Day Usage](#day-to-day-usage)
- [Extending the Project](#extending-the-project)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Tech Stack

- **Docker & Docker Compose** for local orchestration  
- **Apache Airflow 2.9.2** (LocalExecutor) + **Postgres** (metadata DB)  
- **FastAPI** RDM service (CRUD over the catalogue)  
- **YAML** golden catalogue (`statuses.yaml`)  
- **Jinja2** templates + **Confluence Cloud API** to publish documentation  
- **GitHub** branch/PR helper (optional)  

---

## Architecture

High‑level diagram of what runs and how it connects:

- Airflow orchestrates: **validate → diff → (optional) sync → publish**  
- RDM API exposes CRUD for the same `statuses.yaml`  
- Confluence pages are generated from templates  
- GitHub flow is optional for PR‑based governance

If you generated the SVG earlier, you can view/download it here:

**[Download architecture.svg](sandbox:/mnt/data/jira-status-rdm-architecture.svg)**

---

## Quick Start

1. **Prerequisites**
   - Docker Desktop / Docker Engine + Compose
   - Atlassian Cloud admin access (Jira + Confluence)
   - (Optional) GitHub repo + token if you want the PR workflow

2. **Copy environment file**
   ```bash
   cp .env.sample .env
   # edit .env with your Atlassian + GitHub details
   ```

3. **Start the stack**
   ```bash
   docker compose up -d --build
   ```

4. **Open Airflow**
   - http://localhost:8080 (credentials created on first start: `airflow / airflow`)

5. **Trigger the DAG** `status_rdm`
   - First run is **dry‑run** by default. Review the plan.
   - To allow writes to Jira, either set `APPROVED_SYNC=true` in `.env` or pass DagRun conf:
     ```json
     {"approve_sync": true}
     ```

---

## Git Clone & Project Layout

```bash
git clone https://github.com/hlosukwakha/jira-status-rdm-docker.git
cd jira-status-rdm-docker
```

```
airflow/
  dags/status_rdm_dag.py            # validate → diff → sync → publish
  requirements.txt                  # provider‑compatible pins
rdm-api/
  app/main.py                       # FastAPI — CRUD over the catalogue
  app/repository.py                 # (placeholder for future DB-backed repo)
  app/schemas.py                    # Pydantic models (Status, etc.)
  requirements.txt                  # API dependencies
  statuses/statuses.yaml            # GOLDEN CATALOGUE
scripts/
  validate.py                       # schema + integrity checks
  sync_jira.py                      # diff with Jira + guarded apply plan
  publish_confluence.py             # render and publish pages
  github_pr.py                      # optional — branch/PR helper
  utils.py                          # env helpers
confluence/templates/
  status_page.md.j2                 # per‑status doc
  catalogue_index.md.j2             # catalogue index
docker-compose.yml
.env.sample
LICENSE
README.md
```

---

## Configuration

Copy `.env.sample` → `.env` and fill the variables:

```ini
# ===== Atlassian Cloud =====
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USER_EMAIL=you@example.com
JIRA_API_TOKEN=xxxxx

CONFLUENCE_BASE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_SPACE_KEY=DATA
CONFLUENCE_PARENT_PAGE_ID=123456

# Optional GitHub PR flow
GITHUB_TOKEN=ghp_xxx
GITHUB_REPO=yourorg/jira-status-rdm
GIT_USER_NAME=automation-bot
GIT_USER_EMAIL=bot@example.com

# Airflow (dev only values)
AIRFLOW__WEBSERVER__SECRET_KEY=dev_secret_key_change_me

# Approvals
APPROVED_SYNC=false  # default dry‑run; set true to allow writes
```

**Airflow image recommendation** (quiet logs + provider compatibility):  
Use `apache/airflow:2.9.2` or `apache/airflow:2.9.2-python3.11`.

**Provider‑compatible pins** (`airflow/requirements.txt`):

```text
pandas==2.1.4          # google provider requires <2.2
requests==2.31.0       # docker provider requires <2.32
PyYAML==6.0.2
Jinja2==3.1.4
atlassian-python-api==3.41.16
tenacity==9.0.0
gitpython==3.1.43
fastjsonschema==2.20.0
```

**Compose command** (uses constraints, initializes DB, then starts services):

```yaml
command:
  - bash
  - -lc
  - |
    pip install -r /opt/airflow/requirements.txt       --constraint https://raw.githubusercontent.com/apache/airflow/constraints-2.9.2/constraints-$(python - <<'PY'
import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")
PY
).txt &&     airflow db upgrade &&     airflow users create --username airflow --firstname Air --lastname Flow       --role Admin --email admin@example.com --password airflow || true &&     airflow webserver & airflow scheduler
```

---

## Run the Stack

```bash
# 1) Build/Start
docker compose up -d --build

# 2) Check Airflow is healthy and DB initialized
docker compose logs airflow --since=2m | grep -E "Initialized|upgrade|running"

# 3) Open the UI
open http://localhost:8080   # or use your browser

# 4) Trigger the DAG: dry‑run
# In the UI or via CLI:
# docker compose exec airflow airflow dags trigger status_rdm

# 5) Approve sync (optional)
# Rerun with conf to apply changes to Jira
# {"approve_sync": true}
```

---

## Airflow DAG: What It Does

1. **Validate**  
   - Schema checks, duplicate keys, orphan transitions.
2. **Diff with Jira**  
   - Lists existing statuses from Jira; identifies *create/keep/extra_in_jira*.
3. **(Optional) Sync**  
   - Guarded by `approve_sync` or `APPROVED_SYNC=true`.  
   - Jira Cloud restricts status creation via public REST. The project prints an **actionable plan**; wire in your admin route (e.g., Connect/Forge) for full automation if desired.
4. **Publish to Confluence**  
   - Generates a **catalogue index** and one **page per status** with:  
     *status name, category, transitions in/out, conditions, validators, post functions, permissions, requestor, business rationale, business impact if removed, related automations/reports, lifecycle*, etc.
5. **(Optional) GitHub PR**  
   - Push a branch with catalogue updates for review.

---

## Day‑to‑Day Usage

- **Edit catalogue**: update `rdm-api/statuses/statuses.yaml` (or use the RDM API).  
- **Run DAG**: trigger `status_rdm` → review diff → (optionally) approve sync.  
- **Read docs**: check Confluence pages for the catalogue and each status.  
- **Governance**: use GitHub PRs to review changes if you prefer four‑eyes.

---

## Extending the Project

- **Full automation to Jira**: connect `apply_changes` to your internal admin endpoints or an Atlassian app with elevated scopes.  
- **Impact analysis**: scan projects/boards/filters/SLAs/automations/dashboards that reference a status and auto‑populate “business impact if removed.”  
- **Overlays per project type**: keep a small global set; allow controlled overlays (Software/Service/Business).  
- **CI/CD**: trigger the DAG when `statuses.yaml` changes (webhook → `airflow dags trigger`).

---

## Troubleshooting

- **Airflow DB errors (e.g., relation "log" does not exist)**  
  Run `airflow db upgrade` (already in the compose command). If needed, wipe local metadata volume (`./airflow/pgdata`) and re‑init.
- **Dependency conflicts**  
  Requirements are pinned and installed with Airflow **constraints** to avoid provider clashes.
- **Azure SyntaxWarnings on Python 3.12**  
  Either suppress via `PYTHONWARNINGS`, pin to the `-python3.11` image, or remove unused Azure providers.
- **Jira writes not happening**  
  Set `APPROVED_SYNC=true` or pass `{"approve_sync": true}` in DagRun conf. Note: Jira Cloud may require admin routes for programmatic status creation.

---

## License

This project is released under the [MIT License](./LICENSE).
