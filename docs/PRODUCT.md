# TCA Progress product specification

## Purpose and scope

TCA Progress helps a site assess 150 original requirements across 15 categories, find exact blockers, retain evidence, plan improvements, complete Kaizen PDCA work, and request reassessment. It is a local pilot. Official certification remains with the assessment owner.

## Roles

- Staff: view assigned-site progress and evidence preparation, suggest and work on improvements.
- Assessor: record draft responses and evidence conclusions, submit a dated assessment.
- Coach: review Kaizen completeness, measures, results, and sustain work.
- Site manager: review priorities, assignments, and proposed approval.
- Administrator: manage sites, user assignments, and local draft policy. Corporate SSO is a future adapter.

All roles are scoped to assigned sites. Financial and HR detail require separate access. Exports and files use the same site checks as pages.

## Core records and rules

Store each official requirement separately with its complete clause text, reasoning, expected evidence, remote method, source address, and immutable source version. Preserve duplicate text as distinct IDs. Responses are Y, N, unresolved A, or unanswered. Applicability exceptions have separate approval fields and no scoring effect pending policy. Draft policy v1 awards each category Certified for the first five accepted Y responses, Advanced for the first eight, and Showcase for all ten. Report lower levels even if higher requirements fail. Do not average categories into an overall certification. Show the policy version and its unapproved status.

Assessment drafts and approved dated snapshots are separate. Approval freezes responses and their evidence references. Changes create a new draft and later snapshot with actor, time, and reason. Current readiness can change without rewriting a historical snapshot.

Evidence has site, type, owner, version, relevant period, validity, classification, source, and private file. Coverage links reference individual clauses and an assessor conclusion. Shared sessions never imply shared compliance. Other-audit coverage is accepted only for named clauses, period, and scope. Missing documentation, an operational gap, and pending verification are distinct actions.

Kaizen events progress through proposal, Plan, Do, Check, Act, review, verified/sustained, and reassessment pending/accepted. The source's A4, A3, and Business Process profiles remain distinct. Preserve every entered field and action in the archive even when a concise report omits them. Measures record units, direction, population, period, source, and observations. Benefits have separate types and validation state; one project benefit is counted once. Ten-star quality, completeness, coach review, financial validation, and TCA maturity are separate. Event closure never changes a TCA response.

## Screens and acceptance

My Work, Site Progress, Assessment, Improvement Opportunities, Kaizen Workspace, and Evidence & Reports must show site context, clear labels, exact blockers, owners, due dates, and official wording on demand. Forms save durably with visible feedback and reject stale revision numbers. Search and pagination cover the full catalog. A complete journey: record a gap, attach evidence, propose a Kaizen, enter PDCA work and results, request reassessment, and approve a new dated snapshot. Verify cross-site denial on pages, exports, and downloads. Review screen output in a browser.

## Business decisions pending

Meaning of response A; formal approval of cumulative levels; whether and how exceptions affect gates; conflicting meeting duration guidance; Environment evidence period; missing FAQ and User Guide; dated qualifiers; Kaizen profile mandatory fields and ten-star interpretation where guide is absent; authority for approval and remote methods. Do not fill these by inference.

## Technical boundaries

Target Django 5.2 LTS, PostgreSQL 14+, server-rendered pages and HTMX. Local file storage behind a private access interface. Development login only on loopback. No public API, external upload, or corporate identity connection in the local pilot. Use synthetic data for demonstrations.

## Upgrade interpretation

The 12 October upgrade has three bounded milestones described in PLAN.md. Governance interpretation is in GOVERNANCE_DELTA.md. CAT controls official standing and recognition; local section readiness is separate. Site-specific assessments will be governed immutable configurations in U2, retaining canonical IDs and approved historical records. U1 changes interface/location metadata only: organization is separate from site, Benelux is a grouping, countries are NL/BE/LU/GB with blank metadata allowed. No applicability, frequency, standing or publication rule is inferred from the UI changes. Technical administrators have no implicit program approval authority.

## Local toolbox extension

Input size (small, medium, extensive, legacy), methodological A4/A3/Business Process, analysis method, local closure, global review and A3 output are separate. Small exposes a concise single-page PDCA path while retaining all stored fields and source-backed global gates. Profile switches, worksheets, attachments, imports and reports retain revisions. Stale writes fail. Worksheets use method schema versions and preserve archived rows; a future schema requires an explicit migration before editing.

Verified requirements coverage counts unique current accepted Y responses with accepted clause evidence within the frozen baseline scope. Pending claims and Kaizen closure do not contribute. An accepted claim creates a new dated snapshot; previous approved versions remain immutable. Empty, unknown or changed scopes are marked as such. The figures are local operational indicators, not CAT certification.

Private A3 PDFs snapshot the event revision and renderer version. The full archive contains retained detail, worksheets and authorized original files. Locally approved cross-site learning contains a deliberately small approach summary and explicit recipient sites; adaptation begins a new unapproved event with no inherited evidence, metrics, benefits or TCA answers. Corporate sharing authority remains pending.
