# Dynamic repository profile

The profile is generated from the user's public GitHub repositories.

## Behavior

- Public, non-fork, non-archived repositories are discovered automatically.
- The profile repository itself is excluded automatically.
- Repository cards are normal HTML links, so navigation goes to GitHub rather than the SVG asset.
- The monitor dashboard is regenerated from live repository metadata.
- No repository URLs are hardcoded in `README.md`.
- Stale generated repository cards are removed on every run.

Run locally:

```powershell
python scripts\update_profile.py
```

The GitHub Action runs the same generator on schedule and can also be triggered manually.
