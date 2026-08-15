#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "Saeed-Akbarzadeh")
CURRENT_REPO = os.environ.get("GITHUB_REPOSITORY", "").split("/", 1)[-1]
MAX_REPOS = 8

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
README = ROOT / "README.md"

API_VERSION = "2026-03-10"
API_URL = (
    f"https://api.github.com/users/{urllib.parse.quote(USERNAME)}/repos"
    "?type=owner&sort=updated&direction=desc&per_page=100"
)

def fetch_repos() -> list[dict]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "saeed-akbarzadeh-profile-updater",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(API_URL, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.load(response)

    repos = []
    for repo in data:
        if repo.get("private"):
            continue
        if repo.get("archived"):
            continue
        if repo.get("fork"):
            continue
        if repo.get("name") == CURRENT_REPO:
            continue
        repos.append(repo)

    return repos[:MAX_REPOS]

def esc(text: str) -> str:
    return (
        str(text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

def short(text: str, n: int = 72) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"

def date_label(iso: str | None) -> str:
    if not iso:
        return "unknown"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return "unknown"

def generate_svg(repos: list[dict]) -> str:
    rows = []
    y = 96

    if not repos:
        return """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="360" viewBox="0 0 1200 360">
<rect width="1200" height="360" rx="18" fill="#050A07" stroke="#30363D" stroke-width="2"/>
<text x="30" y="48" font-family="monospace" font-size="18" fill="#00FF00">$ open ./repositories</text>
<text x="30" y="95" font-family="monospace" font-size="16" fill="#F2CC60">NO PUBLIC PROJECTS DETECTED</text>
<text x="30" y="135" font-family="monospace" font-size="14" fill="#8B949E">Create a public repository and it will appear here automatically.</text>
<text x="30" y="205" font-family="monospace" font-size="15" fill="#7EE787">[ AUTO-DISCOVERY ENABLED ]</text>
</svg>"""

    # One row per repo. Links are rendered separately in README for clickability.
    for index, repo in enumerate(repos, start=1):
        name = esc(short(repo.get("name"), 34))
        desc = esc(short(repo.get("description"), 72))
        language = esc(repo.get("language") or "n/a")
        stars = int(repo.get("stargazers_count", 0))
        updated = date_label(repo.get("pushed_at"))
        color = "#00FF00" if index % 2 else "#58A6FF"
        rows.append(
            f'<rect x="30" y="{y}" width="1140" height="82" rx="12" fill="#0A100C" stroke="{color}" stroke-opacity=".28"/>'
            f'<text x="52" y="{y+28}" font-family="monospace" font-size="15" fill="{color}">PROJECT_{index:02d}</text>'
            f'<text x="185" y="{y+28}" font-family="Arial,sans-serif" font-size="20" font-weight="700" fill="#FFFFFF">{name}</text>'
            f'<text x="185" y="{y+53}" font-family="monospace" font-size="13" fill="#8B949E">{desc}</text>'
            f'<text x="890" y="{y+28}" font-family="monospace" font-size="13" fill="#F2CC60">{language}</text>'
            f'<text x="890" y="{y+52}" font-family="monospace" font-size="12" fill="#8B949E">★ {stars} · {updated}</text>'
        )
        y += 94

    height = max(250, y + 35)
    body = "\n".join(rows)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}">
<rect width="1200" height="{height}" rx="18" fill="#050A07" stroke="#30363D" stroke-width="2"/>
<text x="30" y="48" font-family="monospace" font-size="18" fill="#00FF00">$ open ./repositories</text>
<text x="30" y="76" font-family="monospace" font-size="13" fill="#8B949E">AUTO-DISCOVERED · CURRENT PROFILE REPO EXCLUDED</text>
{body}
</svg>"""

def update_readme(repos: list[dict]) -> None:
    content = README.read_text(encoding="utf-8")
    start = "<!-- REPOSITORY_LINKS:START -->"
    end = "<!-- REPOSITORY_LINKS:END -->"

    links = [
        start,
        "## `$ open ./repositories`",
        "",
        "> Automatically generated from your public repositories. The current profile repository is excluded.",
        "",
    ]

    if repos:
        for index, repo in enumerate(repos, start=1):
            name = repo.get("name", "unknown")
            url = repo.get("html_url", "#")
            desc = " ".join((repo.get("description") or "No description.").split())
            language = repo.get("language") or "n/a"
            stars = repo.get("stargazers_count", 0)
            links.append(
                f'{index:02d}. **[{name}]({url})** — {desc} · `{language}` · ★ {stars}'
            )
    else:
        links.append("- No public portfolio repositories detected yet.")

    links.append(end)
    replacement = "\n".join(links)
    before = content.split(start, 1)[0]
    after = content.split(end, 1)[1]
    README.write_text(before + replacement + after, encoding="utf-8")

def main() -> None:
    repos = fetch_repos()
    (ASSETS / "repositories-panel.svg").write_text(generate_svg(repos), encoding="utf-8")
    update_readme(repos)
    print(json.dumps({
        "username": USERNAME,
        "excluded_repo": CURRENT_REPO,
        "repositories": [
            {"name": r["name"], "url": r["html_url"]}
            for r in repos
        ],
    }, indent=2))

if __name__ == "__main__":
    main()
