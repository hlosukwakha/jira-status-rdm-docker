import fastjsonschema, yaml, os, sys
from typing import Any

SCHEMA = {
  "type": "object",
  "required": ["statuses"],
  "properties": {
    "version": {"type":"string"},
    "statuses": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["key","name","category"],
        "properties": {
          "key": {"type":"string"},
          "name": {"type":"string"},
          "category": {"enum": ["To Do","In Progress","Done"]},
          "stage": {"type":"string"},
          "description": {"type":"string"},
          "lifecycle": {"enum":["Proposed","Approved","Deprecated","Retired"]},
          "transitions_in": {"type":"array","items":{"type":"string"}},
          "transitions_out": {"type":"array","items":{"type":"string"}},
          "conditions": {"type":"array","items":{"type":"string"}},
          "validators": {"type":"array","items":{"type":"string"}},
          "post_functions": {"type":"array","items":{"type":"string"}},
          "permissions": {"type":"array","items":{"type":"string"}},
          "requestor": {"type":"string"},
          "business_rationale": {"type":"string"},
          "business_impact_if_removed": {"type":"string"},
          "related_automations": {"type":"array","items":{"type":"string"}},
          "related_reports": {"type":"array","items":{"type":"string"}}
        }
      }
    }
  }
}

def validate_catalog(doc: Any):
    validate = fastjsonschema.compile(SCHEMA)
    validate(doc)
    # Duplicate key check
    keys = [s["key"] for s in doc["statuses"]]
    if len(set(keys)) != len(keys):
        dupes = set(k for k in keys if keys.count(k) > 1)
        raise ValueError(f"Duplicate status keys: {dupes}")
    # Orphan transition check
    valid = set(keys)
    for s in doc["statuses"]:
        for target in s.get("transitions_out", []):
            if target not in valid:
                raise ValueError(f"Transition from {s['key']} to unknown status {target}")
    print("Catalogue validation OK")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "/opt/catalog/statuses.yaml"
    with open(path, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    validate_catalog(doc)
