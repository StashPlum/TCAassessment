# Quality and efficiency report (phase 6)

All checks below ran on 2026-10-20 against branch `TCA-progress-v3-redesign` with synthetic data. Source-free CI: **65/65** (`tools/run_source_free_ci.py`), also run by GitHub Actions on every push to the branch.

## 1. Server-side authorization (AC-02)

`core/test_v32_rbac.py` sends direct requests, without using the interface:

- **Other site.** A user who holds the auditor, manager, sensei and team roles at another site gets 403/404/405 on all 52 site routes, as GET and as POST. That covers pages, answers, approval, configuration, planning, evidence acceptance, Kaizen edits, worksheets, A3 finalisation, every export and every download. The database stays unchanged afterwards (10 model counts plus the answer, Kaizen, coverage, benefit and session state).
- **Control.** The same routes open (200) for a site manager of that site, so the refusals above come from the site check and are not caused by broken URLs.
- **Team member and sensei.** They cannot answer, approve, start an assessment, change site questions, plan or confirm sessions, accept evidence, register another audit, or change preparation needs.
- **Team member.** Cannot write sensei feedback, open the review screen or queue, or validate benefits.
- **Auditor.** Cannot edit a Kaizen they are not part of (fields, autosave, additions, tasks, progress, toolbox, input view).

**Defect found and fixed:** the sensei review screen crashed (server error) for a Kaizen that had no problem text yet. A template filter read a missing field. It now shows "Not recorded".

## 2. Error recovery and autosave (AC-09, AC-15)

`tools/v3_quality_checks.py` (browser) cuts the connection for answer saves only, then selects N:

- The page shows "Not saved — no connection. Your entry stays on screen and will be sent when you change it again." N stays selected.
- After the connection returns, selecting Y shows "Saved". The answer is still Y after a reload.

The conflict case (409 when another person saved first) and the logout/login case were verified in phase 2. Evidence: `phase6/autosave-offline.png`, `phase6/autosave-recovered.png`, `phase6/quality.json`.

## 3. Responsive layout (AC-24)

Every menu target was checked for each of the 5 demo roles at 1024, 768 and 390 px wide: 147 page loads, with no horizontal page overflow (`phase6/quality.json`). Wide tables scroll inside their own region. Two overflows were fixed along the way: the evidence library (phase 3) and the Kaizen task table at 390 px (phase 4). Visual regression against the design prototype has not been run yet.

## 4. Efficiency compared with the baseline (AC-22)

| Journey or screen | Baseline `ab50e7f` | 3.2 | Evidence |
|---|---|---|---|
| Auditor: from the menu to the first answer saved as Y | 5 selections, 1 mandatory text, 4 screens, plus a detour to accept evidence | **3 selections**, 0 mandatory text, 2 screens | phase2/journey.json |
| Auditor: continue a draft | 3 selections and a search for the open question | 1 ("Continue at X" on the start page) | test_v32_roles |
| Answer the next question | Separate page, save, then reload | 1 selection plus "Next", no reload | phase2 |
| Menu items | 12–13 for every role | team 5 · sensei 6 · auditor 11 · admin 10 · manager 12 | phase3/crawl.json |
| Sensei: open a waiting review | 2 page changes | 1 ("Review …" on the start page) | test_v32_roles |
| Manager: see what blocks the next level | Work it out from the matrix | Count on the start page; matrix marks it and filters "only blockers" in 1 click | test_v32 matrix test |
| Prepare evidence | ~1,060 words, 30 inputs visible | 780 words, 0 inputs visible until filters/selection are opened; "Show what is missing" in 1 click | phase5/metrics.json |
| Team member: find a Lean method for "why does this happen?" | Scan 45 method cards | 1 click shows 3 methods in the order to try | phase4/kaizen_toolbox.json |
| Kaizen workspace actions | 4 equal buttons, including 2 that fail with an error | 1 primary action per stage; actions that are not yet possible are explained and disabled | phase4 |

## 5. Not yet verified

- Real-user first-use test (AC-29) needs people from the site.
- Official catalogue wording on the new service (AC-10) needs the owner's secret file.
- Deployment checks (AC-27, AC-32, AC-33) need the owner to create the new Render service.
- Separation of duties (P3.2) waits for decision O3.
