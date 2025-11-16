from atlassian import Confluence
from jinja2 import Template
import os, yaml, pathlib

BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
SPACE = os.getenv("CONFLUENCE_SPACE_KEY")
PARENT_PAGE_ID = os.getenv("CONFLUENCE_PARENT_PAGE_ID")
USER = os.getenv("JIRA_USER_EMAIL")
TOKEN = os.getenv("JIRA_API_TOKEN")

def _render(template_path, **ctx):
    with open(template_path, "r", encoding="utf-8") as f:
        t = Template(f.read())
    return t.render(**ctx)

def publish_catalogue(doc, templates_dir="/opt/templates"):
    if not BASE_URL or not SPACE or not PARENT_PAGE_ID:
        print("Confluence env not set; skipping publish.")
        return
    conf = Confluence(url=BASE_URL, username=USER, password=TOKEN, cloud=True)
    idx_html = _render(os.path.join(templates_dir, "catalogue_index.md.j2"), doc=doc)
    title = "Workflow Status Catalogue (Global)"
    page = conf.update_or_create(parent_id=PARENT_PAGE_ID, title=title, body=idx_html, representation='wiki', minor_edit=True, type='page', full_width=True)
    parent_id = page["id"]
    for s in doc["statuses"]:
        html = _render(os.path.join(templates_dir, "status_page.md.j2"), s=s)
        conf.update_or_create(parent_id=parent_id, title=f"{s['name']} ({s['key']})", body=html, representation='wiki', minor_edit=True, type='page', full_width=True)
    print("Confluence publish complete.")

if __name__ == "__main__":
    path = "/opt/catalog/statuses.yaml"
    with open(path, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    publish_catalogue(doc, templates_dir="/opt/templates")
