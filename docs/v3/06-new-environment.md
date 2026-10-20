# New isolated environment — setup steps (no secrets in this file)

The old service `tca-progress-demo` and its database `tca-progress-demo-db` must not be opened for editing, redeployed, restarted or reconnected during any of these steps.

## 1. GitHub (owner)

1. On github.com → **New repository**. Owner `StashPlum`, name `tca-progress-v3-redesign`, **Private**, no README, no .gitignore, no licence.
2. Tell Claude the name. Claude attaches it to the session, sets it as the only `origin`, pushes branch `development` with the baseline history and tag `baseline-v3.1-ab50e7f`, and verifies the remote SHA.

## 2. Render (owner, after the repository has code)

Use a **new Blueprint** from the new repository so nothing can attach to the old service. The new repository's `render.yaml` will use distinct names (`tca-progress-v32`, `tca-progress-v32-db`, disk `tca-v32-evidence`) and branch `development`.

1. Render dashboard → **New** → **Blueprint** → choose `StashPlum/tca-progress-v3-redesign`, branch `development`.
2. Check that the proposed names are the `v32` ones above and **not** `tca-progress-demo`. If Render offers to link an existing service or database, cancel.
3. Enter the secret values Render asks for: a new demo password (not the old one) and optional tester list.
4. Add the private catalogue files as **Secret Files** on the new service only (`tca-catalog.json`, `kaizen-template.json`), generated from your own copy of the originals with `tools/make_demo_secret_files.py`.
5. Apply. Send Claude the new service URL. Claude then smoke-tests it and records service ID, URL and deployed SHA in `00-isolation-baseline.md`.

## 3. Durable data (decision O1)

The old demo runs on free instances: files vanish on sleep/redeploy and the free database expires. Master prompt §15 requires private persistent storage. Options are in 07-open-decisions.md (O1). The `render.yaml` in the new repository is written for the recommended option and keeps a free-plan fallback commented out.
