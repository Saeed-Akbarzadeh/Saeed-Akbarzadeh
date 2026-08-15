# Profile updater

`update_profile.py` queries GitHub's public repository API, excludes the current profile
repository automatically, filters out forks/archived/private repositories, and regenerates
the repository showcase.

It is invoked by `.github/workflows/update-profile.yml`.
