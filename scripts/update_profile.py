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
# Always exclude the profile repository itself. This is required locally too,
# because GITHUB_REPOSITORY is only populated automatically inside GitHub Actions.
EXCLUDED_REPO = os.environ.get("GITHUB_PROFILE_REPO", USERNAME)
MAX_REPOS = 8

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
README = ROOT / "README.md"
MONITOR_TEMPLATE = ASSETS / "monitor.template.svg"
MONITOR_OUTPUT = ASSETS / "monitor.svg"

API_URL = (
    f"https://api.github.com/users/{urllib.parse.quote(USERNAME)}/repos"
    "?type=owner&sort=updated&direction=desc&per_page=100"
)


def fetch_repos() -> list[dict]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
        "User-Agent": "saeed-akbarzadeh-profile-updater",
    }

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(API_URL, headers=headers)

    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)

    repos: list[dict] = []

    for repo in data:
        if repo.get("private"):
            continue
        if repo.get("archived"):
            continue
        if repo.get("fork"):
            continue
        if repo.get("name") in {CURRENT_REPO, EXCLUDED_REPO}:
            continue

        repos.append(repo)

    return repos[:MAX_REPOS]


def escape_text(value: str | None, max_len: int = 74) -> str:
    text = " ".join(str(value or "").split())

    if len(text) > max_len:
        text = text[: max_len - 1] + "…"

    return html.escape(text)


def make_card(repo: dict, index: int) -> str:
    accent = "#00FF00" if index % 2 else "#58A6FF"

    name = escape_text(repo.get("name"), 34)
    description = escape_text(
        repo.get("description") or "No description available.",
        62,
    )
    language = escape_text(repo.get("language") or "n/a", 18)
    stars = int(repo.get("stargazers_count", 0) or 0)

    return f'''<svg xmlns="http://www.w3.org/2000/svg"
    width="570" height="180" viewBox="0 0 570 180">
<defs>
<style>
.pulse {{ animation: pulse 2.8s ease-in-out infinite; }}
.flow {{ stroke-dasharray: 7 11; animation: flow 1.6s linear infinite; }}
@keyframes pulse {{ 0%,100% {{ opacity: .45; }} 50% {{ opacity: 1; }} }}
@keyframes flow {{ to {{ stroke-dashoffset: -36; }} }}
</style>
</defs>
<rect x="2" y="2" width="566" height="176" rx="18" fill="#050A07" stroke="#30363D" stroke-width="2"/>
<rect x="2" y="2" width="566" height="8" rx="5" fill="{accent}" class="pulse"/>
<circle cx="28" cy="31" r="6" fill="#FF5F56"/><circle cx="48" cy="31" r="6" fill="#FFBD2E"/><circle cx="68" cy="31" r="6" fill="#27C93F"/>
<text x="88" y="36" font-family="monospace" font-size="13" fill="#8B949E">repository-terminal</text>
<text x="28" y="76" font-family="monospace" font-size="14" fill="{accent}">PROJECT_{index:02d}</text>
<text x="28" y="108" font-family="Arial,sans-serif" font-size="24" font-weight="700" fill="#FFFFFF">{name}</text>
<text x="28" y="133" font-family="monospace" font-size="13" fill="#8B949E">{description}</text>
<text x="28" y="158" font-family="monospace" font-size="13" fill="#F2CC60">{language} · ★ {stars}</text>
<text x="428" y="158" font-family="monospace" font-size="13" fill="{accent}">OPEN →</text>
<line x1="380" y1="166" x2="530" y2="166" stroke="{accent}" stroke-opacity=".55" class="flow"/>
</svg>'''


def update_monitor(repos: list[dict]) -> None:
    template = MONITOR_TEMPLATE.read_text(encoding="utf-8")

    repo_count = len(repos)
    total_stars = sum(int(repo.get("stargazers_count", 0) or 0) for repo in repos)
    total_forks = sum(int(repo.get("forks_count", 0) or 0) for repo in repos)
    languages = {
        str(repo.get("language"))
        for repo in repos
        if repo.get("language")
    }
    language_count = len(languages)

    latest_update = "n/a"
    if repos:
        latest = max(repos, key=lambda repo: str(repo.get("updated_at") or ""))
        latest_update = str(latest.get("updated_at") or "n/a")[:10]

    values = {
        "{{REPO_COUNT}}": str(repo_count),
        "{{TOTAL_STARS}}": str(total_stars),
        "{{TOTAL_FORKS}}": str(total_forks),
        "{{LANGUAGE_COUNT}}": str(language_count),
        "{{LATEST_UPDATE}}": html.escape(latest_update),
    }

    for placeholder, value in values.items():
        template = template.replace(placeholder, value)

    MONITOR_OUTPUT.write_text(template, encoding="utf-8")


def update_readme(repos: list[dict]) -> None:
    start_marker = "<!-- REPOSITORIES:START -->"
    end_marker = "<!-- REPOSITORIES:END -->"

    generated: list[str] = [
        start_marker,
        '<table align="center" width="100%" cellspacing="0" cellpadding="0" border="0">',
    ]

    if repos:
        for index, repo in enumerate(repos, start=1):
            filename = f"repo-{index:02d}.svg"
            (ASSETS / filename).write_text(
                make_card(repo, index),
                encoding="utf-8",
            )

            repository_url = html.escape(repo.get("html_url", "#"), quote=True)
            repository_name = html.escape(repo.get("name", "Repository"))

            # Keep the repository cards as normal HTML links. The SVG itself is
            # only the visual layer; the outer anchor owns navigation.
            if index % 2 == 1:
                generated.append("<tr>")
            generated.append(
                '<td width="50%" align="center">'
                f'<a href="{repository_url}">'
                f'<img src="./assets/{filename}" alt="{repository_name}" width="100%">'
                f"</a>"
                '</td>'
            )
            if index % 2 == 0 or index == len(repos):
                if index % 2 == 1:
                    generated.append('<td width="50%"></td>')
                generated.append('</tr>')
    else:
        generated.append(
            '<tr><td colspan="2" align="center">'
            '<img src="./assets/repositories-empty.svg" alt="No public repositories" width="100%">'
            '</td></tr>'
        )

    generated.extend(["</table>", end_marker])

    content = README.read_text(encoding="utf-8")

    if start_marker not in content or end_marker not in content:
        raise RuntimeError("README.md is missing repository generation markers.")

    before = content.split(start_marker, 1)[0]
    after = content.split(end_marker, 1)[1]

    README.write_text(
        before + "\n".join(generated) + after,
        encoding="utf-8",
    )


def remove_stale_cards() -> None:
    for card in ASSETS.glob("repo-*.svg"):
        card.unlink()


def main() -> None:
    remove_stale_cards()
    repos = fetch_repos()
    update_monitor(repos)
    update_readme(repos)

    print(
        json.dumps(
            {
                "username": USERNAME,
                "excluded_repo": EXCLUDED_REPO,
                "repositories": [
                    {"name": repo["name"], "url": repo["html_url"]}
                    for repo in repos
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
