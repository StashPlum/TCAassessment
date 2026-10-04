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

