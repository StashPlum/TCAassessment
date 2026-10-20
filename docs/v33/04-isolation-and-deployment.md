# 3.3 isolation record and deployment handover

## Owner decision (deviation)

The master prompt asks for a new repository. On 20 Oct 2026 the owner chose a new branch, **`TCA-progress-v33`** in `StashPlum/TCAassessment`, cut from `TCA-progress-v3-redesign` @ `a7ee3fe`.

This is the same deviation as O7 in `docs/v3/00-isolation-baseline.md`: the branch shares repository settings, Actions and webhooks with the old code. Moving it to its own repository later is a plain push of this branch to a new remote.

## Protected references (SAFE-39, AC-31…34)

| Ref | Required | After the 3.3 push (`git ls-remote`, 20 Oct 2026) |
|---|---|---|
| `main` | `a6af62675b7c15dd0f561608239581dc319031c5` | unchanged |
| `TCA_Demo` | `ab50e7f55b610e8c23eb2a58401654667a0a4dbb` | unchanged |
| `TCA-progress-v3-redesign` | `a7ee3fe` | unchanged |
| `TCA-progress-v33` | new | the only ref pushed |

The workspace restricts pushes with `remote.origin.push = refs/heads/TCA-progress-v33:refs/heads/TCA-progress-v33`.

None of the following happened:
- no PR, merge or force push
- no Render API call
- no connection to the old service `tca-progress-demo`, its database or its storage

The following were not committed:
- the workbook or its extract
- databases or uploads
- secrets
- screenshots that show official wording

## New Render service (LIVE-40, blocked on the owner)

`render.yaml` on this branch defines:
- service `tca-progress-v33` (free plan, Frankfurt, branch `TCA-progress-v33`)
- database `tca-progress-v33-db`

These names differ from 3.2 and from the old demo, so the Blueprint cannot attach to an existing service.

1. In Render, go to **New → Blueprint** and choose `StashPlum/TCAassessment`, branch `TCA-progress-v33`. Check that the plan lists only `tca-progress-v33` and `tca-progress-v33-db`.
2. Set the environment values:
   - `TCA_DEMO_PASSWORD`: choose a new password.
   - `TCA_TESTERS`: optional.
3. Add the secret file **`tca-v3-source.json`** under **Secret Files**. Upload the extract from the project files (`tca-v33-private/tca-v3-source.json`). It is made with `tools/extract_v3_source.py` and carries the workbook's SHA-256.
4. Deploy. On start, `prepare_demo` imports and activates the V3 catalogue from `/etc/secrets/tca-v3-source.json`. It maps the two fictional demo sites to GROUP_02 and GROUP_12, and leaves "Fictional Harbor Site" unmapped to show the blocker.
5. Smoke test:
   - `/healthz/`
   - Sign in as `auditor_demo` and open the assessment of the stage-one site. It should show QuestionIDs without a suffix.
   - Check the role start pages for `manager_demo`, `sensei_demo` and `team_demo`.
   - Sign in as `admin_demo`, go to Administration and preview the group for the Harbor site.

Without the secret file the service still runs, on the legacy synthetic catalogue.

## Known limits

- **Data on the free plan.** It is temporary (decision O1 from 3.2). Uploads do not survive a redeploy.
- **Site group mapping.** Only the fictional demo sites are mapped. Real sites need an administrator mapping, because no site→group configuration was supplied and none is guessed.
- **History across catalogues.** Earlier answers from the legacy catalogue are not shown as "prior answer" on V3 questions. No mapping between the two catalogues was supplied, so none is invented.
