#!/usr/bin/env python3
"""
Commit a file directly to a GitHub repository via the REST API.
Designed to be called by the Kimi automation after generating the daily briefing.

Environment variables required:
  GITHUB_TOKEN   – Personal Access Token with 'repo' scope
  GITHUB_REPO    – e.g. "username/repo-name"

Optional:
  GITHUB_BRANCH  – default 'main'
"""

import os
import sys
import base64
import json
import urllib.request
import urllib.error


def api_request(method, url, token, data=None):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "kimi-daily-briefing/1.0"
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
        payload = json.dumps(data).encode("utf-8")
    else:
        payload = None

    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, json.loads(body) if body else {}


def commit_file(repo, path, content, message, branch="main", token=None):
    token = token or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN environment variable is not set")

    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"

    # 1. Check if file already exists (we need its SHA to update)
    status, resp = api_request("GET", f"{api_url}?ref={branch}", token)
    sha = resp.get("sha") if status == 200 else None

    # 2. Create or update
    body = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": branch
    }
    if sha:
        body["sha"] = sha

    status, resp = api_request("PUT", api_url, token, body)
    if status not in (200, 201):
        raise RuntimeError(f"GitHub API error {status}: {resp.get('message', resp)}")

    commit_sha = resp.get("commit", {}).get("sha", "unknown")
    print(f"Committed {path} to {repo}@{branch} (commit {commit_sha})")
    return resp


def main():
    repo = os.environ.get("GITHUB_REPO")
    if not repo:
        print("ERROR: Set GITHUB_REPO environment variable, e.g. 'ade/ai-briefing'", file=sys.stderr)
        sys.exit(1)

    branch = os.environ.get("GITHUB_BRANCH", "main")

    if len(sys.argv) < 3:
        print("Usage: python commit_to_github.py <file_path> <commit_message>", file=sys.stderr)
        print("  file_path      – path inside repo, e.g. state/daily/2026-10-21.md", file=sys.stderr)
        print("  commit_message – git commit message", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    message = sys.argv[2]
    content = sys.stdin.read()
    commit_file(repo, file_path, content, message, branch=branch)


if __name__ == "__main__":
    main()
