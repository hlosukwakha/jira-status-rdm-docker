import json, os, pathlib, yaml, datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models.param import Param

CATALOG_PATH = "/opt/catalog/statuses.yaml"
TEMPLATES_DIR = "/opt/templates"
SCRIPTS_DIR = "/opt/runners/scripts"

def _read_yaml():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def task_validate(**_):
    import sys
    sys.path.append(SCRIPTS_DIR)
    from validate import validate_catalog
    doc = _read_yaml()
    validate_catalog(doc)

def task_diff_with_jira(**context):
    import sys, json
    sys.path.append(SCRIPTS_DIR)
    from sync_jira import diff_with_jira
    doc = _read_yaml()
    diff = diff_with_jira(doc)
    context['ti'].xcom_push(key="diff", value=diff)

def task_sync_to_jira(**context):
    import sys, os
    sys.path.append(SCRIPTS_DIR)
    from sync_jira import apply_changes
    diff = context['ti'].xcom_pull(key="diff")
    approve = context['params'].get("approve_sync") or os.getenv("APPROVED_SYNC", "false").lower() == "true"
    apply_changes(diff, approve=approve)

def task_publish_confluence(**context):
    import sys, os
    sys.path.append(SCRIPTS_DIR)
    from publish_confluence import publish_catalogue
    doc = _read_yaml()
    publish = context['params'].get("publish_confluence", True)
    if publish:
        publish_catalogue(doc, templates_dir=TEMPLATES_DIR)

with DAG(
    dag_id="status_rdm",
    start_date=datetime.datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    params={
        "approve_sync": Param(False, type="boolean"),
        "publish_confluence": Param(True, type="boolean")
    },
    doc_md="""
### Jira Status RDM
Validates the golden status catalogue, diffs with Jira, **optionally** applies changes, and publishes Confluence docs.
"""
) as dag:
    validate = PythonOperator(task_id="validate_catalog", python_callable=task_validate)
    diff = PythonOperator(task_id="diff_with_jira", python_callable=task_diff_with_jira)
    sync = PythonOperator(task_id="sync_to_jira", python_callable=task_sync_to_jira)
    publish = PythonOperator(task_id="publish_confluence", python_callable=task_publish_confluence)

    validate >> diff >> sync >> publish
