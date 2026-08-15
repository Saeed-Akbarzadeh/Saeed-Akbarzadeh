#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "Saeed-Akbarzadeh")
CURRENT_REPO = os.environ.get("GITHUB_REPOSITORY", "").split("/", 1)[-1]
MAX_REPOS = 8

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
README = ROOT / "README.md"

API_URL = (
    f"https://api.github.com/users/{urllib.parse.quote(USERNAME)}/repos"
    "?type=owner&sort=updated&direction=desc&per_page=100"
)

CARD_TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" width="570" height="180" viewBox="0 0 570 180">
<defs>
<style>
.pulse{animation:p 2.8s ease-in-out infinite}
.flow{stroke-dasharray:7 11;animation:d 1.6s linear infinite}
@keyframes p{0%,100%{opacity:.45}50%{opacity:1}}
@keyframes d{to{stroke-dashoffset:-36}}
</style>
</defs>
<rect x="2" y="2" width="566" height="176" rx="18" fill="#050A07" stroke="#30363D" stroke-width="2"/>
<rect x="2" y="2" width="566" height="8" rx="5" fill="{accent}" class="pulse"/>
<circle cx="28" cy="31" r="6" fill="#FF5F56"/><circle cx="48" cy="31" r="6" fill="#FFBD2E"/><circle cx="68" cy="31" r="6" fill="#27C93F"/>
<text x="88" y="36" font-family="monospace" font-size="13" fill="#8B949E">repository-terminal</text>
<text x="28" y="76" font-family="monospace" font-size="14" fill="{accent}">PROJECT_{index:02d}</text>
<text x="28" y="108" font-family="Arial,sans-serif" font-size="24" font-weight="700" fill="#FFFFFF">{name}</text>
<text x="28" y="133" font-family="monospace" font-size="13" fill="#8B949E">{desc}</text>
<text x="28" y="158" font-family="monospace" font-size="13" fill="#F2CC60">{language} · ★ {stars}</text>
<text x="428" y="158" font-family="monospace" font-size="13" fill="{accent}">OPEN →</text>
<line x1="380" y1="166" x2="530" y2="166" stroke="{accent}" stroke-opacity=".55" class="flow"/>
</svg>'''

def fetch_repos() -> list[dict]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
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
        if repo.get("private") or repo.get("archived") or repo.get("fork"):
            continue
        if repo.get("name") == CURRENT_REPO:
            continue
        repos.append(repo)
    return repos[:MAX_REPOS]

def esc(value: str, max_len: int = 74) -> str:
    text = " ".join(str(value or "").split())
    if len(text) > max_len:
        text = text[: max_len - 1] + "…"
    return html.escape(text)

def make_card(repo: dict, index: int) -> str:
    return CARD_TEMPLATE.format(
        accent="#00FF00" if index % 2 else "#58A6FF",
        index=index,
        name=esc(repo.get("name"), 34),
        desc=esc(repo.get("description") or "No description available.", 74),
        language=esc(repo.get("language") or "n/a", 18),
        stars=int(repo.get("stargazers_count", 0)),
    )

def update_readme(repos: list[dict]) -> None:
    start = "<!-- REPOSITORIES:START -->"
    end = "<!-- REPOSITORIES:END -->"
    parts = [start, '<div align="center">']
    if repos:
        for index, repo in enumerate(repos, start=1):
            filename = f"repo-{index:02d}.svg"
            (ASSETS / filename).write_text(make_card(repo, index), encoding="utf-8")
            url = html.escape(repo.get("html_url", "#"), quote=True)
            name = html.escape(repo.get("name", "Repository"))
            parts.append(
                f'<a href="{url}"><img src="./assets/{filename}" alt="{name}" width="48%"></a>'
            )
            if index % 2 == 0:
                parts.append("<br>")
    else:
        parts.append(
            '<img src="./assets/repositories-empty.svg" alt="No public repositories" width="100%">'
        )
    parts += ["</div>", end]
    content = README.read_text(encoding="utf-8")
    before = content.split(start, 1)[0]
    after = content.split(end, 1)[1]
    README.write_text(before + "\n".join(parts) + after, encoding="utf-8")

def remove_stale_cards() -> None:
    for card in ASSETS.glob("repo-*.svg"):
        card.unlink()

def main() -> None:
    remove_stale_cards()
    repos = fetch_repos()
    update_readme(repos)
    print(json.dumps({
        "username": USERNAME,
        "excluded_repo": CURRENT_REPO,
        "repositories": [{"name": r["name"], "url": r["html_url"]} for r in repos],
    }, indent=2))

if __name__ == "__main__":
    main()
