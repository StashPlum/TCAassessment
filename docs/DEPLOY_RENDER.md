# Hosted feedback demo on Render (free plan)

This puts the TCA Progress demo online with a link for invited testers. It uses fictional data, local demo accounts and Render's free plan. It is **not** a production setup: there is no CEVA company login, and free-plan limits apply.

## What you need

- Your Render account, connected to GitHub with access to `StashPlum/TCAassessment` (private repository).
- About 15 minutes.

## Steps

1. **Optional: prepare the two private files** (shows the official TCA wording and Kaizen template texts). On your own computer, in the project folder, run:

   ```powershell
   & 'C:\Users\stash\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools/make_demo_secret_files.py
   ```

   This writes `tca-catalog.json` and `kaizen-template.json` to `output\render-secrets\`. That folder is never committed. Skip this step to run the demo with clearly labelled synthetic requirements.

2. In Render, click **New** → **Blueprint**. Choose the repository `StashPlum/TCAassessment` and the branch **`TCA_Demo`**. Render reads `render.yaml` and proposes a web service `tca-progress-demo` and a free PostgreSQL database `tca-progress-demo-db`, both in Frankfurt.

3. Render asks for two values:
   - **`TCA_DEMO_PASSWORD`**: one password for all demo accounts, at least 10 characters. Share it only with your testers.
   - **`TCA_TESTERS`** (optional): named tester accounts, comma separated, each `name:role` with role `auditor`, `manager`, `sensei` or `team`. Example: `Anna de Boer:auditor, Ben Smit:team`. Usernames become `anna.de.boer`, `ben.smit`.

4. Click **Apply**. The first build takes a few minutes.

5. Optional, if you did step 1: open the web service → **Environment** → **Secret Files** → add a file named `tca-catalog.json` and paste the content of that file; add `kaizen-template.json` the same way. Save, then choose **Manual Deploy** → **Deploy latest commit**.
   - Do this before testers start. The catalog is loaded only into an empty database. If the demo already started with synthetic requirements, delete and recreate the database in Render, then deploy again.

6. Open the link Render shows (`https://tca-progress-demo-….onrender.com`) and sign in, for example as `auditor_demo`, `manager_demo`, `sensei_demo` or `team_demo` with your demo password.

7. Share the link, the usernames and the password with your testers. Every page has a red **Feedback** button. Signed in as `manager_demo` (or a tester with role `manager`), open **Read tester feedback** in the yellow demo bar to read or export all feedback as CSV.

## Accounts and data

| Account | Role in the demo |
|---|---|
| `auditor_demo` | TCA auditor: assessments, evidence, best-practice validation |
| `manager_demo` | Site manager: results, sharing learning, reading feedback |
| `sensei_demo` | Sensei: review queue, return or finalise Kaizens |
| `team_demo`, `team_demo2` | Kaizen team members |
| `demo` | All roles on the original fictional sites |

Sites to open: **Fictional Matrix Pilot** (56 Y / 19 A / 75 N matrix, learning for 4.C.3) and **Fictional Advisory Pilot** (Kaizens with team, Gantt and review).

## Free-plan limits

- The web service sleeps after about 15 minutes without visitors; the next visit takes about a minute to wake up.
- The free database is removed by Render after its free period (currently 30 days). Export the feedback CSV before then.
- Uploaded files are temporary: they disappear when the service sleeps or redeploys. Report PDFs are rebuilt from the saved data when needed. The demo bar says this to testers.
- Everything testers enter stays in the database until it is deleted, including after the service sleeps.

## Safety notes

- Use fictional data only. Do not upload real CEVA documents or personal data.
- The official TCA wording (step 1) is internal CEVA text. Share the link only with invited people.
- Search engines are asked not to index the demo (`noindex`).
- Deployment settings live in `render.yaml`; demo mode is `TCA_DEMO=1` in `config/settings.py`. Accounts and seeds come from `manage.py prepare_demo`, which runs at every start.
