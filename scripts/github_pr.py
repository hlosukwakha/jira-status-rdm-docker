import os, subprocess, tempfile, pathlib, shutil
from utils import env

def create_pr(branch="catalog-update", message="Update status catalogue"):
    token = env("GITHUB_TOKEN", required=True)
    repo = env("GITHUB_REPO", required=True)
    user = env("GIT_USER_NAME", "automation-bot")
    email = env("GIT_USER_EMAIL", "bot@example.com")

    # Use git in the mounted working directory
    subprocess.check_call(["git", "init"])
    subprocess.check_call(["git", "config", "user.name", user])
    subprocess.check_call(["git", "config", "user.email", email])
    subprocess.check_call(["git", "add", "."])
    subprocess.check_call(["git", "commit", "-m", message])
    subprocess.check_call(["git", "branch", "-M", branch])
    subprocess.check_call(["git", "remote", "add", "origin", f"https://{token}:x-oauth-basic@github.com/{repo}.git"], stderr=subprocess.DEVNULL)
    subprocess.check_call(["git", "push", "-u", "origin", branch, "--force"])
    print(f"Pushed branch {branch} to {repo}. Create PR in GitHub UI or use gh CLI.")
