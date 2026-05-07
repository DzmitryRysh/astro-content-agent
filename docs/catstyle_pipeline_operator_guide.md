# Catstyle Pipeline Operator Guide v1

A concise manual for running the **deterministic local Catstyle production pipeline** from **PowerShell** on Windows. This pipeline turns **planet-cat image jobs** plus **generated images** into a **manual Instagram-ready publish handoff**. Nothing here talks to Instagram, Cloudinary, or automated publishing — the operator posts by hand.

---

## 1. Overview

**Catstyle** in this repo is built around:

1. **Image generation jobs** (`image_generation_jobs.json`) describing prompts and outputs.
2. **Generated images** on disk (e.g. PNGs from stub/OpenAI execution).
3. **Post tooling** that bundles copy + paths into **`catstyle_post_packages/<date>/`**, checks quality, records manual review/approval, and optionally emits **`catstyle_publish_handoffs/<date>/`** for final paste-into-IG workflows.

All steps are **local**, **deterministic**, and safe to run without API keys **unless** you explicitly execute jobs with an OpenAI-backed provider.

---

## 2. Current pipeline

Conceptual flow:

```text
Manifest + generated images
        → post package (JSON + Markdown + caption/hook snippets)
        → quality check (scores / gates)
        → manual review (worksheet JSON + Markdown)
        → optional approval (writes decision + timestamp)
        → publish handoff (only after approve + gates pass)
```

Rough CLI alignment:

| Stage | Typical CLI |
|--------|-------------|
| Jobs manifest + prompts | `build_catstyle_image_generation_jobs.py` |
| Generate/store images | `execute_catstyle_image_jobs.py` (stub or OpenAI) |
| Post package | `build_catstyle_post_package.py` **or** orchestrator |
| Quality | `check_catstyle_post_package.py` **or** orchestrator |
| Manual review | `build_catstyle_manual_review.py` **or** orchestrator |
| Approval | `approve_catstyle_manual_review.py` **or** orchestrator (`--approve`) |
| Publish handoff | `build_catstyle_publish_handoff.py` **or** orchestrator |

The **orchestrator** (`run_catstyle_post_pipeline.py`) runs the **post** side (package → QC → manual review → optional approve → handoff) in one go **after** images already exist.

---

## 3. Main one-command flow

From the repo root (adjust paths and date to your run):

```powershell
python scripts/aca/run_catstyle_post_pipeline.py `
  --manifest ".\catstyle_image_jobs\2026-05-02\image_generation_jobs.json" `
  --generated-images-dir ".\catstyle_image_jobs\2026-05-02\generated_images_style_ref" `
  --approve `
  --approval-notes "Primary image looks strong. Text is good enough for manual post." `
  --overwrite
```

**What this creates**

- **`catstyle_post_packages\2026-05-02\`** (default package dir under cwd unless you pass `--post-package-dir`):
  - `post_package.json`, `post_package.md`, `caption.txt`, `hook.txt`, etc.
- **Quality** is evaluated internally; manual **`manual_review.json`** / **`manual_review.md`** are written into **that same** package folder.
- With **`--approve`**, the tool updates approval fields and UTC **`reviewed_at`**, then builds:
  - **`catstyle_publish_handoffs\2026-05-02\`** (default unless `--publish-handoff-dir`):
    - `publish_handoff.json`, `publish_handoff.md`, `caption_final.txt`, `primary_image_path.txt`, `publish_checklist.txt`

Use **`--json`** if you want a single JSON blob printed for tooling/logs:

```powershell
python scripts/aca/run_catstyle_post_pipeline.py `
  --manifest ".\catstyle_image_jobs\2026-05-02\image_generation_jobs.json" `
  --generated-images-dir ".\catstyle_image_jobs\2026-05-02\generated_images_style_ref" `
  --approve --overwrite --json
```

---

## 4. Review-only flow

Same command **without** `--approve` (and without `--approval-notes`):

```powershell
python scripts/aca/run_catstyle_post_pipeline.py `
  --manifest ".\catstyle_image_jobs\2026-05-02\image_generation_jobs.json" `
  --generated-images-dir ".\catstyle_image_jobs\2026-05-02\generated_images_style_ref" `
  --overwrite
```

**Behavior**

- Stops after **manual review** is generated when quality passes (**`review_ready`** in orchestrator terms).
- **Does not** run approval or **publish handoff** until you explicitly approve (separate CLI or re-run orchestrator with `--approve`).

---

## 5. Individual commands

All paths below assume repo root and `python` on `PATH`.

### Post package

```powershell
python scripts/aca/build_catstyle_post_package.py `
  --manifest ".\catstyle_image_jobs\YYYY-MM-DD\image_generation_jobs.json" `
  --generated-images-dir ".\catstyle_image_jobs\YYYY-MM-DD\generated_images" `
  --overwrite
```

Default output: **`catstyle_post_packages\YYYY-MM-DD\`**.

### Quality check

```powershell
python scripts/aca/check_catstyle_post_package.py `
  --package-dir ".\catstyle_post_packages\YYYY-MM-DD"
```

Optional **`--json`** for machine-readable output.

### Manual review worksheet

```powershell
python scripts/aca/build_catstyle_manual_review.py `
  --package-dir ".\catstyle_post_packages\YYYY-MM-DD" `
  --overwrite
```

Writes **`manual_review.json`** / **`manual_review.md`** next to **`post_package.json`** by default.

### Manual approval (decision + timestamp)

```powershell
python scripts/aca/approve_catstyle_manual_review.py `
  --package-dir ".\catstyle_post_packages\YYYY-MM-DD" `
  --decision approve `
  --notes "Looks good for manual publish." `
  --overwrite
```

**Choices:** `approve`, `revise_text`, `regenerate_images`, `reject`. Only **`approve`** (plus QC/copy gates) satisfies **`build_catstyle_publish_handoff`**.

### Publish handoff (after approve)

```powershell
python scripts/aca/build_catstyle_publish_handoff.py `
  --package-dir ".\catstyle_post_packages\YYYY-MM-DD" `
  --overwrite
```

Default output: **`catstyle_publish_handoffs\YYYY-MM-DD\`**.

### Orchestrator (package → QC → review → optional approve → handoff)

See **sections 3-4** for **`run_catstyle_post_pipeline.py`**.

---

## 6. Output folders

| Folder | Typical contents |
|--------|------------------|
| **`catstyle_image_jobs\<date>\`** | Job manifests (`image_generation_jobs.json`), prompts, executor outputs (`generated_images*`, stubs). Ignored by git — see `.gitignore`. |
| **`catstyle_post_packages\<date>\`** | `post_package.json`, `post_package.md`, text snippets, **`manual_review.json`**, **`manual_review.md`** after review build/approve. Usually ignored. |
| **`catstyle_publish_handoffs\<date>\`** | Final **`publish_handoff.*`** + `caption_final.txt`, **`primary_image_path.txt`**, checklist — manual IG paste helpers. Usually ignored. |

Exact layout may vary slightly if you pass **`--output-dir`** / **`--post-package-dir`** / **`--publish-handoff-dir`** on the respective scripts.

---

## 7. Git rules

- **Commit:** application **source**, **tests**, **docs** (including this guide), config templates **without secrets**.
- **Usually do not commit:** **`catstyle_image_jobs/`**, **`catstyle_post_packages/`**, **`catstyle_publish_handoffs/`**, stub/generated image trees — these are in **`.gitignore`** so daily artifacts stay local.
- **Never commit:** **`.env`**, API tokens, Cloudinary / OpenAI / Instagram credentials, private URLs with embedded secrets.

Tracked **`references/`** style-reference PNGs are an exception by design (approved reusable assets).

---

## 8. Troubleshooting

### Mojibake / broken Cyrillic in `.txt` / `.md`

If **`Get-Content`** shows garbage instead of Russian:

- Prefer **`utf-8-sig`**-saved producer files where implemented (BOM helps PowerShell pick UTF-8).
- Open files in an editor that shows UTF-8.
- Re-run **`build_catstyle_post_package`** after fixing encoding issues upstream.

### Missing primary image

Orchestrator / QC / publish handoff expect **`recommended_primary_image`** to exist **on disk** and **`generated_image_paths`** to line up with **`--generated-images-dir`**. Fix filenames vs **`suggested_output_name`** in the manifest, re-run execution, then re-run the pipeline.

### Quality **`needs_attention`**

Orchestrator will **not** approve or build publish handoff when QC is not **`ready`** or score/rules fail. Run **`check_catstyle_post_package.py`** with **`--json`**, fix warnings/errors (paths, Cyrillic/mojibake, hooks/captions, asset counts), then retry.

### Non-approved review blocks publish handoff

**`build_catstyle_publish_handoff.py`** requires **`approval_status == approve`** (and QC/copy gates). Approve via **`approve_catstyle_manual_review.py`** or **`run_catstyle_post_pipeline.py --approve`**.

### Generated folders "missing" from `git status`

They are **ignored by `.gitignore`** — working as intended. Use Explorer or explicit paths to inspect **`catstyle_post_packages`** / **`catstyle_publish_handoffs`**.

---

## 9. Quick verification commands

```powershell
python -m pytest -q
git status
git log --oneline -3
```

Healthy iteration loop: change **code/docs/tests** → run **pytest** → commit tracked files only → keep heavy **`catstyle_*`** outputs local.

---

*v1 — aligns with deterministic local Catstyle CLIs only; no live publishing.*
