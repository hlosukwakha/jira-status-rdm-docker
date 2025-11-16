from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yaml, os, json

CATALOG_PATH = os.environ.get("CATALOG_PATH", "/app/statuses/statuses.yaml")

app = FastAPI(title="Jira Status RDM")

def load_catalog():
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def save_catalog(doc):
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, sort_keys=False, allow_unicode=True)

class Status(BaseModel):
    key: str
    name: str
    category: str
    stage: str | None = None
    description: str | None = None
    lifecycle: str = "Approved"
    transitions_in: list[str] = []
    transitions_out: list[str] = []
    conditions: list[str] = []
    validators: list[str] = []
    post_functions: list[str] = []
    permissions: list[str] = []
    requestor: str | None = None
    business_rationale: str | None = None
    business_impact_if_removed: str | None = None
    related_automations: list[str] = []
    related_reports: list[str] = []

@app.get("/catalog")
def get_catalog():
    return load_catalog()

@app.get("/status/{key}")
def get_status(key: str):
    doc = load_catalog()
    for s in doc.get("statuses", []):
        if s.get("key") == key:
            return s
    raise HTTPException(404, "Status not found")

@app.post("/status")
def add_status(s: Status):
    doc = load_catalog()
    statuses = doc.setdefault("statuses", [])
    if any(x.get("key") == s.key for x in statuses):
        raise HTTPException(409, "Status key already exists")
    statuses.append(s.model_dump())
    save_catalog(doc)
    return {"ok": True}

@app.put("/status/{key}")
def update_status(key: str, s: Status):
    doc = load_catalog()
    statuses = doc.get("statuses", [])
    for i, x in enumerate(statuses):
        if x.get("key") == key:
            statuses[i] = s.model_dump()
            save_catalog(doc)
            return {"ok": True}
    raise HTTPException(404, "Status not found")

@app.delete("/status/{key}")
def delete_status(key: str):
    doc = load_catalog()
    statuses = doc.get("statuses", [])
    new_statuses = [x for x in statuses if x.get("key") != key]
    if len(new_statuses) == len(statuses):
        raise HTTPException(404, "Status not found")
    doc["statuses"] = new_statuses
    save_catalog(doc)
    return {"ok": True}
