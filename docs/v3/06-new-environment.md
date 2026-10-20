# New isolated environment — setup steps (no secrets in this file)

The old service `tca-progress-demo` and its database `tca-progress-demo-db` must not be opened for editing, redeployed, restarted or reconnected during any of these steps.

## 1. GitHub

Owner decision (20 Oct 2026): work happens on branch `TCA-progress-v3-redesign` of `StashPlum/TCAassessment` instead of a separate repository (deviation from master prompt §3.2, recorded in 00-isolation-baseline.md).

## 2. Render (owner, after the repository has code)

Use a **new Blueprint** so nothing can attach to the old service. The `render.yaml` on the 3.2 branch uses distinct names (`tca-progress-v32`, `tca-progress-v32-db`) and branch `TCA-progress-v3-redesign`, on the free plan.

1. Render dashboard → **New** → **Blueprint** → choose `StashPlum/TCAassessment`, branch **`TCA-progress-v3-redesign`** (not `TCA_Demo`).
2. Check that the proposed names are the `v32` ones above and **not** `tca-progress-demo`. If Render offers to link an existing service or database, cancel.
3. Enter the secret values Render asks for: a new demo password (not the old one) and optional tester list.
4. Add the private catalogue files as **Secret Files** on the new service only (`tca-catalog.json`, `kaizen-template.json`), generated from your own copy of the originals with `tools/make_demo_secret_files.py`.
5. Apply. Send Claude the new service URL. Claude then smoke-tests it and records service ID, URL and deployed SHA in `00-isolation-baseline.md`.

## 3. Durable data (decision O1: free plan)

The owner chose the free plan (20 Oct 2026). Consequences, shown to testers in the demo bar: uploaded files disappear when the service sleeps or redeploys (report PDFs are rebuilt from saved data), and Render removes the free database after its free period. AC-14 durability therefore stays **Blocked by decision**; the environment is a demo, not a pilot. Upgrading later needs only a paid instance with a disk (or object storage) and a paid database; no code change for the database.
