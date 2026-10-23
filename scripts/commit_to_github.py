#!/usr/bin/env python3
"""
commit_to_github.py — Commit a file to a GitHub repository via the Git Data API.

Usage:
    cat file.md | python scripts/commit_to_github.py path/in/repo.md "Commit message"
    
Environment:
    GITHUB_REPO    — e.g. "owner/repo"
    GITHUB_BRANCH  — e.g. "main"
    GITHUB_TOKEN   — GitHub personal access token (classic or fine-grained)
"""

import os
import sys
import json
import urllib.request
import urllib.error


def github_api_request(method, url, token, data=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "aibriefingdaily-script/1.0",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")
    else:
        body = None

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def main():
    repo = os.environ.get("GITHUB_REPO", "")
    branch = os.environ.get("GITHUB_BRANCH", "main")
    token = os.environ.get("GITHUB_TOKEN", "")

    if len(sys.argv) < 3:
        print("Usage: python commit_to_github.py <repo_path> <commit_message>", file=sys.stderr)
        sys.exit(1)

    repo_path = sys.argv[1]
    commit_message = sys.argv[2]

    # Read file content from stdin
    content = sys.stdin.read()

    api_base = f"https://api.github.com/repos/{repo}"

    # 1. Get the current commit SHA for the branch
    status, ref_data = github_api_request("GET", f"{api_base}/git/ref/heads/{branch}", token)
    if status != 200:
        print(f"Failed to get ref: {status} — {ref_data}", file=sys.stderr)
        sys.exit(1)
    current_commit_sha = ref_data["object"]["sha"]

    # 2. Get the tree for the current commit
    status, commit_data = github_api_request("GET", f"{api_base}/git/commits/{current_commit_sha}", token)
    if status != 200:
        print(f"Failed to get commit: {status} — {commit_data}", file=sys.stderr)
        sys.exit(1)
    base_tree_sha = commit_data["tree"]["sha"]

    # 3. Create a new tree with the file
    tree_data = {
        "base_tree": base_tree_sha,
        "tree": [
            {
                "path": repo_path,
                "mode": "100644",
                "type": "blob",
                "content": content,
            }
        ],
    }
    status, new_tree = github_api_request("POST", f"{api_base}/git/trees", token, tree_data)
    if status != 201:
        print(f"Failed to create tree: {status} — {new_tree}", file=sys.stderr)
        sys.exit(1)

    # 4. Create a new commit
    commit_data = {
        "message": commit_message,
        "tree": new_tree["sha"],
        "parents": [current_commit_sha],
    }
    status, new_commit = github_api_request("POST", f"{api_base}/git/commits", token, commit_data)
    if status != 201:
        print(f"Failed to create commit: {status} — {new_commit}", file=sys.stderr)
        sys.exit(1)

    # 5. Update the branch reference
    ref_update = {"sha": new_commit["sha"]}
    status, ref_result = github_api_request("PATCH", f"{api_base}/git/refs/heads/{branch}", token, ref_update)
    if status != 200:
        print(f"Failed to update ref: {status} — {ref_result}", file=sys.stderr)
        sys.exit(1)

    print(f"Successfully committed to {repo}@{branch}: {repo_path}")
    print(f"Commit SHA: {new_commit['sha']}")


if __name__ == "__main__":
    main()
