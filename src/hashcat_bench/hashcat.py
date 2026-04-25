from __future__ import annotations

import json
import re
from urllib.request import urlopen, Request
from urllib.error import URLError

GITHUB_API = "https://api.github.com/repos/hashcat/hashcat"
GITHUB_TAGS_URL = f"{GITHUB_API}/tags"
GITHUB_RELEASES_URL = f"{GITHUB_API}/releases"
GITHUB_BRANCHES_URL = f"{GITHUB_API}/branches"
GITHUB_COMMITS_URL = f"{GITHUB_API}/commits"

VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+$")


def fetch_tags(limit: int = 100) -> list[str]:
    req = Request(
        f"{GITHUB_TAGS_URL}?per_page={limit}",
        headers={"Accept": "application/vnd.github+json"},
    )
    with urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return [t["name"] for t in data if VERSION_RE.match(t["name"])]


def fetch_releases(limit: int = 30) -> list[dict]:
    req = Request(
        f"{GITHUB_RELEASES_URL}?per_page={limit}",
        headers={"Accept": "application/vnd.github+json"},
    )
    with urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    releases = []
    for r in data:
        if not VERSION_RE.match(r.get("tag_name", "")):
            continue
        releases.append({
            "version": r["tag_name"],
            "date": r.get("published_at", "")[:10],
            "prerelease": r.get("prerelease", False),
        })
    return releases


def fetch_branch_head(branch: str = "master") -> dict | None:
    req = Request(
        f"{GITHUB_COMMITS_URL}/{branch}",
        headers={"Accept": "application/vnd.github+json"},
    )
    try:
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except URLError:
        return None
    sha = data.get("sha", "")[:8]
    date = data.get("commit", {}).get("committer", {}).get("date", "")[:10]
    message = data.get("commit", {}).get("message", "").split("\n")[0][:60]
    return {"branch": branch, "sha": sha, "date": date, "message": message}


def latest_stable() -> str | None:
    for r in fetch_releases():
        if not r["prerelease"]:
            return r["version"]
    return None
