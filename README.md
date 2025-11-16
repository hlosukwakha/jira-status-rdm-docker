# Jira Status RDM — Docker project
Manage Jira workflow **statuses as reference data**. This stack syncs a YAML **golden catalogue** to Jira, publishes documentation to **Confluence**, and can open PRs to **GitHub**. Orchestrated by **Airflow**. Everything runs in Docker.

## What you get
- **Golden catalogue** in `rdm-api/statuses/statuses.yaml`
- **Airflow DAG** to validate, diff, (optionally) sync to Jira, and publish Confluence docs
- **FastAPI RDM service** (CRUD over the catalogue)
- **Scripts** to run the same steps locally
- **Confluence templates** to render pages with transitions, conditions, validators, post functions, permissions, requestor, business impact, etc.

## Quick start
1. Install Docker & Docker Compose.
2. Copy `.env.sample` to `.env` and fill your Atlassian + GitHub variables.
3. `docker compose up -d --build`
4. Open Airflow: http://localhost:8080  (user: `airflow`, password: `airflow`)
5. Trigger DAG: `status_rdm` (first run does **dry-run** unless `APPROVED_SYNC=true` or you pass `{"approve_sync": true}` in DagRun conf).

> ⚠️ You need Jira/Confluence Admin rights to create/update statuses, transitions and pages.

## RDM operating model
- Catalogue versioned via Git (this repo). 
- Proposed → Approved → Deprecated → Retired lifecycle.
- Diff step flags unapproved or duplicate statuses.
- Publish step generates a **catalogue index** + one **per-workflow** doc page in Confluence.

## Repo layout
```
airflow/
  dags/status_rdm_dag.py
  requirements.txt
rdm-api/
  app/main.py
  app/repository.py
  app/schemas.py
  requirements.txt
  statuses/statuses.yaml
scripts/
  sync_jira.py
  publish_confluence.py
  validate.py
  github_pr.py
  utils.py
confluence/templates/
  status_page.md.j2
  catalogue_index.md.j2
docker-compose.yml
.env.sample
```

## Passing runtime options
- Airflow DagRun conf:
```json
{"approve_sync": true, "project_keys": ["ABC","SERV"], "publish_confluence": true}
```

## Security notes
- Tokens are read from environment variables. Never commit `.env`.
- In dev, Airflow uses basic auth; change the secret key for any non-local use.

## Troubleshooting
- 403s from Atlassian → ensure account is site admin and has Jira/Confluence Admin.
- Confluence parent page not found → verify `CONFLUENCE_PARENT_PAGE_ID`.
- Dry-run only? Set `APPROVED_SYNC=true` or DagRun conf `approve_sync: true`.
