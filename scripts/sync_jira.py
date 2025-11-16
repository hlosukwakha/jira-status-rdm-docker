import requests, os, base64, json, time
from utils import env

JIRA_BASE = env("JIRA_BASE_URL", required=True)
JIRA_USER = env("JIRA_USER_EMAIL", required=True)
JIRA_TOKEN = env("JIRA_API_TOKEN", required=True)

def _auth_headers():
    return {
        "Authorization": "Basic " + base64.b64encode(f"{JIRA_USER}:{JIRA_TOKEN}".encode()).decode(),
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def _get_statuses():
    # Jira Cloud statuses (global list)
    r = requests.get(f"{JIRA_BASE}/rest/api/3/status", headers=_auth_headers())
    r.raise_for_status()
    return r.json()

def _index_statuses(jira_statuses):
    idx = {}
    for s in jira_statuses:
        name = s.get("name")
        category = s.get("statusCategory", {}).get("name", "")
        idx[name] = {"id": s.get("id"), "name": name, "category": category}
    return idx

def diff_with_jira(doc):
    jira_statuses = _get_statuses()
    idx = _index_statuses(jira_statuses)
    desired = {(s["name"], s["category"]): s for s in doc["statuses"]}
    current = {(v["name"], v["category"]): v for v in idx.values()}

    to_create = [v for k, v in desired.items() if k not in current]
    to_keep = [v for k, v in desired.items() if k in current]
    extra = [k for k in current.keys() if k not in desired]

    diff = {
        "create": to_create,
        "keep": to_keep,
        "extra_in_jira": [{"name":k[0], "category":k[1]} for k in extra]
    }
    print(json.dumps(diff, indent=2))
    return diff

def apply_changes(diff, approve=False):
    if not approve:
        print("Dry-run: set DagRun conf approve_sync=true or env APPROVED_SYNC=true to apply.")
        return

    # Creating statuses via public API is limited in Jira Cloud; typically you define statuses and add them to workflows.
    # Here we prepare the payload and print guidance. If your site has the necessary scope (Jira Cloud Admin APIs),
    # you can replace the following with the appropriate POSTs to the *Workflow Statuses* admin APIs.
    planned = diff.get("create", [])
    if planned:
        print("Planned creations (manual/administrative step due to API limitations):")
        for s in planned:
            print(f" - Create status '{s['name']}' in category '{s['category']}'")
    else:
        print("No new statuses to create.")
    # Transitions are managed within workflows; recommend managing via workflow schemes & export/import.
    print("Sync applied (conceptual). For production, connect your internal admin APIs or Atlassian Connect app.")
