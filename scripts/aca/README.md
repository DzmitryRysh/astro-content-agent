# `scripts/aca` — local helpers and outputs

## Repository root

Run documented commands with the **repository root** as the current working directory (the folder that contains `main.py`). Set `PYTHONPATH` to the **parent** of that folder so `import astro_content_agent` resolves (e.g. on Windows PowerShell: `$env:PYTHONPATH = (Resolve-Path ..).Path` when the repo folder is named `astro_content_agent`).

## Artifact policy

| Path | Purpose | Version control |
|------|---------|-----------------|
| `scripts/aca/weekly_venus/` | Per-week Venus pipeline output: ISO week-start subfolders (`YYYY-MM-DD/`) with drafts, `venus_weekly_state_*.json`, handoff/final-check/publish JSON, etc. Prior week folders feed file-based anti-repeat for the next run. | **Gitignored.** Do not commit. Prune old week directories when no longer needed for ops or audit. |
| `scripts/aca/out/` | Scratch or one-off script exports and experiments. | **Gitignored.** Safe to delete at any time. |

Scripts should create these directories as needed. Nothing under these paths is required for application runtime unless an operator explicitly points tooling at them.
