# Roles, information needs and RBAC (Phase 1, deliverables 3 and 6)

Actual roles in code (`core/roles.py`): `assessor` (TCA auditor), `manager` (Site manager), `coach` (Sensei), `staff` (Kaizen team member), `admin` (Technical administrator). A user holds roles per site through `Membership(user, site, role)`; one user may hold several. Nothing below invents a new role.

## 1. Role-task-information matrix (target design)

| # | Auditor | Site manager | Sensei | Kaizen team member | Administrator |
|---|---|---|---|---|---|
| 1 Objective | Prepare, conduct and record accurate TCA assessments | Know the site's verified position and drive actions | Coach, review and validate improvement work | Complete assigned improvement work | Keep sites, people and templates correctly configured |
| 2 Recurring tasks | Start/resume assessment; answer questions; attach evidence | Review blockers, overdue actions, Advisory follow-up; confirm planning | Work the review queue; give feedback; return/finalise | Do my tasks; update Kaizen; use Lean tools | Manage memberships and sites; check audit log |
| 3 Secondary | Plan assessment, prepare evidence list, site question versions, history/export, validate best practice | Share learning; read reports; approve local snapshot **(see decision O3)** | Download A3/A4; spot sustainment risks | Start a Kaizen; read feedback; search lessons | Template governance (technical only) |
| 4 Required info | Official question, site wording, clauses, previous answer + Advisory note, linked evidence | Counts: assessed / pass / open Advisory / blockers per next level; overdue owner+date | Submitted Kaizens, gate status, cause analysis, before/after, evidence | My tasks with due dates, current PDCA step, what is still needed | Users, roles per site, template versions, errors |
| 5 Decisions | Y / A / N per requirement; evidence accepted; approve snapshot | Priorities, owners, dates; availability for planning | Return or finalise; best-practice proposal | Task done / blocked; ready to submit | Grant/revoke access |
| 6 Actions | Answer, comment, attach/link evidence, create draft, submit/approve | Assign owner/date, confirm session, start Kaizen from finding | Feedback per phase, return with comment, finalise | Edit own team's Kaizen, update tasks, submit | Configure; no audit answers |
| 7 Summary only | Site maturity, Kaizen list | Section-level detail, evidence list | Assessment results | Site maturity, matrix | Operational content |
| 8 Drill-down | Clause text, source hash, history | Exact question, evidence, linked action | Full worksheet, revision history | Lean method help | Audit trail |
| 9 Not by default | Kaizen admin, reports config | Auditor configuration, rule versions | Audit planning, evidence preparation | Assessment planning/conduct, evidence prep, history, site question versions | Operational dashboards |
| 10 Inaccessible | Other sites | Other sites; changing answers **(decision O3)** | Other sites; TCA answers | Other sites; restricted (financial/HR) evidence; TCA answers; sensei decisions | TCA answers and official classification (unless also auditor) |
| 11 Scope | Assigned sites | Own site(s) | Assigned sites | Own site(s), own team's events | All sites (technical) |
| 12 Landing | **Assessment work**: one "Continue assessment"/"Start assessment" card | **Site status**: next-level blockers, overdue, decisions | **Review queue** | **My work**: my tasks, my Kaizens | **Administration** |
| 13 Navigation | Overview · Assessment · Evidence · Improvements (read) · Learning · Reports | Overview · Assessment results · Improvements · Learning · Reports | Review · Improvements · Learning · Reports | My work · Improvements · Learning & tools | Administration · Overview |
| 14 Top pending action | Resume draft at next unanswered question | Oldest overdue blocker action | Oldest unreviewed submission | Next due task | Pending access requests / config errors |
| 15 Status indicators | Answered x/150, unanswered, evidence missing | Next level blockers count, overdue count | Waiting, returned, finalised | Due, overdue, returned with feedback | — |
| 16 Exceptions | Save failure, conflict, evidence expired | Overdue past date, missed planning confirmation | Submission older than N days | Returned with feedback | Failed login spikes, migration errors |

## 2. RBAC matrix — current (code) vs target

Legend: ✓ allowed, ✗ denied (404/403), R read-only, ◐ conditional. Current = what the code permits at `ab50e7f`. All rows are additionally scoped to sites where the user holds the role.

| Resource / action | Auditor | Manager | Sensei | Team member | Admin |
|---|---|---|---|---|---|
| Site pages, matrix, history (view) | ✓ / ✓ | ✓ / ✓ | ✓ / ✓ | ✓ / **R summary only** | ✓ / ✓ |
| Create assessment draft | ✓ / ✓ | ✓ / **✗ (O3)** | ✗ / ✗ | ✗ / ✗ | ✓ / **✗ (O3)** |
| Answer requirement (Y/A/N) | ✓ / ✓ (draft only) | ✓ / **✗ (O3)** | ✗ / ✗ | ✗ / ✗ | ✓ / **✗ (O3)** |
| Approve local snapshot | ✗ / **✓ auditor (O3)** | ✓ / **◐ O3** | ✗ | ✗ | ✓ / **✗ (O3)** |
| Site question versions (edit) | ✓ / ✓ | ✗ | ✗ | ✗ | ✗ |
| Plan session: create / confirm availability | ✓ create / ✓ | ✓ confirm / ✓ | ✗ | ✗ | ✓ / ✓ |
| Evidence: upload / review coverage | ✓ / ✓ | ✓ / ✓ | ✗ | claim only / claim only | ✓ / ✓ |
| Restricted (financial/HR) evidence read | ✓ | ✓ | ✗ | ✗ | ✓ |
| Preparation export (XLSX/PDF) | ✓ | ✓ | ✓ / **✗** | ✓ / **✗** | ✓ |
| Kaizen create / edit | ✗ / ✗ | ✓ / ✓ | ✓ / ✓ | ✓ / ◐ own team | ✓ / ✓ |
| Kaizen export (PDF/XLSX/archive) | ✓ R | ✓ | ✓ | ✓ / ◐ own team or published | ✓ |
| Sensei review: return / finalise | ✗ | ✓ | ✓ | ✗ | ✓ / **✗ unless coach** |
| Best-practice validation | ✓ | ✗ | ✗ | ✗ | ✗ |
| Feedback list (demo) | ✗ | ✓ | ✗ | ✗ | ✓ |
| Administration | ✗ | ✗ | ✗ | ✗ | ✓ |
| Mutations on approved/closed records | ✗ all roles (immutable snapshot, revision checks) | | | | |

## 3. Negative-access probe (actual results)

`tools/v3_rbac_probe.py` against the local baseline (31 route checks × 6 users). Full table: `docs/v3/baseline/rbac_probe.json`.

- Cross-site: every site-scoped page, list, export and object route returned **404** for single-role users on a site they are not a member of. ✓
- Role gates: review queue/review detail 404 for auditor and team; feedback list 404 except manager; `/administration/` 404 for all (no admin account exists).
- Gaps vs target: team members get 200 on assessment conduct, preparation, history and preparation XLSX export of their own site (read-only). Allowed by current rules; target design reduces this to summaries (D7) and blocks preparation export.
- Not yet probed: POST mutations per role, downloads of real attachments (seed has no file on disk), mutations after approval. These become automated tests in Phase 6 (AC-02).
