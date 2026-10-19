# TCA Progress — Codex master build prompt

This is a reusable implementation brief for a local TCA assessment and Kaizen application. It authorizes development, testing, and a local demonstration. It does not authorize public publication, production deployment, external messages, or changing official assessment requirements.

## How to use this file

1. Create or open a private project folder in Codex. Use an organization-approved Codex environment for the source documents.
2. Place this file in the project root. Place the two original workbooks in `sources/original/`:
   - `TCA assessment work categorisation.xlsx`
   - `Global_Kaizen_Template_20241219.xlsx`
3. Give Codex the kickoff instruction below. Codex should create the project documents and implement the milestones without asking you to approve routine development steps.
4. Review the completed local demonstration and the business-policy questions. Before organizational deployment, involve the appropriate IT, security, and assessment owners.

Kickoff instruction:

> Read TCA_Progress_Codex_Master_Prompt.md and execute the Master prompt below. Create the project plan, then implement and verify the local application milestone by milestone. Continue through routine development without asking me to confirm each step. Keep progress and unresolved business policies in the repository. Finish with a working local demonstration, verification evidence, and exact startup instructions.

Resume instruction, if another session is needed:

> Read AGENTS.md, docs/PRODUCT.md, docs/PLAN.md, and docs/STATUS.md. Check the actual repository state, continue the next unfinished milestone, repair relevant failures, and update the status. Preserve the product requirements and do not stop after proposing a plan.

## Master prompt

Act as the lead developer responsible for delivering TCA Progress: a simple, professional internal web application for TCA assessments, evidence management, improvement planning, and Kaizen events. Build the application locally and make it ready for a controlled pilot. Optimize for accurate assessment, minimal documentation effort, maintainability, and modest computing requirements.

The business goal is to help sites move from Certified to Advanced to Showcase while maintaining quality. Staff should see their current position, the exact remaining requirements, and the actions needed to improve. Assessment integrity is more important than visual polish or the number of features.

### 1. Working agreement and project memory

Inspect the existing project and applicable instructions first. Preserve existing user work. Reuse sound implementation where present; do not rebuild an existing application unnecessarily.

Use a small number of durable project files:

- `AGENTS.md`: concise development conventions, commands, authorization boundaries, and critical invariants; link to detailed documents instead of duplicating them.
- `docs/PRODUCT.md`: the product specification, roles, workflows, rules, and observable acceptance criteria.
- `docs/PLAN.md`: ordered milestones with their validation and completion criteria.
- `docs/SOURCE_MAP.md`: source versions, field and requirement mappings, coverage, transformations, and source ambiguities.
- `docs/STATUS.md`: completed work, actual checks and results, pending policies, known limitations, and the next task.

After establishing these files, implement the plan. Do not end after planning, scaffolding, or producing mockups. Make normal technical choices autonomously and record meaningful decisions. Ask for clarification only when a missing decision materially affects official scoring, mandatory requirements, access policy, or an external action. Continue unrelated development while a policy is unresolved. Do not turn an assumption into an approved business rule.

Local code edits, dependency installation from standard registries where permitted, disposable test database migrations, synthetic fixtures, relevant tests, and local application startup are authorized. Use a project branch and small local Git checkpoints where Git is available. Do not overwrite unrelated changes or rewrite history. Do not publish, push, deploy, contact others, use production credentials, or modify production data without separate authorization.

Read the documents needed for the current task; do not reread the entire repository before every edit. Run appropriate checks for meaningful changes, repair failures, and repeat affected checks. Once they pass, progress rather than repeatedly running unchanged suites. If execution is interrupted, leave an accurate checkpoint and exact next action. Never report tests as passed unless they actually ran successfully.

### 2. Architecture and local setup

Use a modular Django application with PostgreSQL, server-rendered pages, and HTMX for targeted interactions. Verify supported dependency versions against official documentation during setup, lock dependencies, and keep infrastructure minimal. Provide a reproducible development environment, `.env.example` without secrets, and documented startup, migration, seed, test, backup, and restore commands.

Use PostgreSQL during normal shared development and the pilot. Store documents through a private storage interface that supports a local development folder and a future corporate storage adapter. Prepare a corporate OIDC SSO integration boundary; development login must be clearly limited to local testing. Actual identity-provider configuration depends on approved corporate details.

Keep scoring and workflow rules in a deterministic, testable domain layer shared by screens, dashboards, and exports. Keep business data separate from presentation. Avoid unnecessary microservices, a separate single-page application, mandatory AI services, or GPU requirements. Add background infrastructure only when a demonstrated workload requires it.

### 3. Preserve the source material completely

Treat the original workbooks as immutable source records. Archive their exact bytes and SHA-256 hashes, with version information. Never save over them or silently repair their formulas. Keep the private originals and operational data out of public repositories.

Inventory visible and hidden sheets, cell text and formulas, comments, validations, defined names, lookup lists, meaningful embedded content, and export mappings. Retain the original archive even where a feature cannot yet be interpreted. Classify workbook content as an application field, display instruction, calculation, reference data, output mapping, or archived legacy content. Explain any transformation and identify unsupported functionality explicitly.

Import the complete TCA catalog. The supplied source is expected to contain 15 categories and 150 parent requirements: 75 Certified, 45 Advanced, and 30 Showcase. Verify these against the workbook rather than treating a count match as sufficient evidence. Preserve every requirement ID, all detail clauses, reasoning, expected evidence, assessment methods, source address, and original wording. Keep duplicate requirements as separate official records. Add searchable tags and simplified explanations separately; neither replaces the official text.

Maintain a traceability register from source cells and fields to stored data, screens, validation rules, and exports. Check exact text coverage and applicable structured mappings. A correct total alone does not prove that every clause was preserved. Use source hashes, import reports, and independent fixtures to demonstrate preservation. Imports must be transactional and repeatable without creating duplicates.

Record source defects and ambiguities rather than guessing: the meaning of response A; conflicting meeting duration guidance; the Environment evidence period discrepancy; missing FAQ and User Guide references; dated qualifiers; and broken Kaizen defined names. Source documents outrank this brief for exact question wording and template details. User-provided scoring guidance is a separate policy input. Conflicts must remain visible.

### 4. TCA assessment rules

Keep response codes and maturity codes in separate fields. Y means Yes and N means No. The response A is unresolved: preserve it without treating it as Yes or automatically interpreting it as Not Applicable. A maturity level means Showcase and must never be confused with response A. Distinguish unanswered, unresolved response, and any explicitly approved applicability exception.

Implement the following cumulative interpretation as a versioned draft policy until the assessment owner confirms it:

- Certified: all first five requirements in a category have accepted Y responses.
- Advanced: all first eight requirements have accepted Y responses.
- Showcase: all ten requirements have accepted Y responses.

An unresolved response cannot satisfy a gate under this draft policy. Higher-level gaps do not erase a valid lower level. Represent confirmed applicability exceptions separately, retaining justification, scope, source authority, and approval; do not invent how they affect scoring. Show the rule version and approval status. Allow local demonstration using the draft, but prevent publication of an official result under unapproved policy.

Keep draft assessment, approved dated assessment, current readiness, and target level distinct. Freeze approved assessment records; later changes create new versions with actor, time, rationale, and supporting evidence. Show why a level was earned or blocked. Do not average category scores into an invented overall site certification.

### 5. Evidence, semantic grouping, and other audits

Provide one evidence register with document or observation type, owner, version, relevant date or period, site, validity, access classification, and source. Map evidence to individual requirement clauses through many-to-many coverage links.

Allow shared evidence collections and assessment sessions for related questions, while retaining separate requirement conclusions. A grouped interview or observation must not imply that every linked requirement passed. Deterministic decision tables must have explainable conditions, outputs, source references, versions, and boundary tests. Text similarity alone must never establish compliance.

For another audit, record the audit scope, period, tested control, finding, and accepted TCA clause coverage. Reuse valid accepted evidence to reduce duplicate work. The existence of an accountant audit must not automatically make Finance requirements Yes. Recheck uncovered clauses and relevant changes. Preserve the source restrictions on remote assessment and requirement-specific observation or sampling rules.

Produce an advance evidence preparation list filtered by site, category, level, evidence type, owner, and due date. Distinguish missing documentation, an operational gap, and pending verification so that every missing file does not generate a Kaizen event.

### 6. Improvement planning and staff dashboards

Implement My Work, Site Progress, Assessment, Improvement Opportunities, Kaizen Workspace, and Evidence & Reports views. Use clear status labels, accessible controls, keyboard support, responsive layouts, and visible save feedback. Keep technical implementation details out of staff workflows.

Show dated approved maturity, current readiness, target level, exact blockers, required evidence, owners, due dates, and related events. Staff see understandable actions, with official requirement text available when needed.

Give categories equal formal scoring importance. Sequence operational work using immediate corrective needs, blockers for the next level, prerequisite work, and opportunities to address several gaps together. Explain the proposed sequence and allow authorized human adjustment. Do not create hidden weighting that makes Finance or another category count less. Accepted audit coverage reduces verification effort, not requirement importance.

Suggest Kaizen candidates from verified operational gaps and other improvement inputs, including Gemba and performance boards. Show the linked TCA requirements, observed problem, intended measure, next-level contribution, evidence needed, and overlapping projects. Do not invent root causes or promise that one event will automatically satisfy several requirements. Suggestions require human acceptance before becoming assigned work.

### 7. Kaizen workflow and reporting

Transform the Global Kaizen workbook into progressive Plan–Do–Check–Act forms. Capture information once and reuse it in review, reports, and exports. Preserve every meaningful template field, controlled vocabulary, conditional requirement, lookup mapping, formula meaning, attachment, review criterion, and downstream output field. Retain reference-data versions and flag stale location or business-unit lists for owner review.

Support the template's A4, A3, and Business Process Kaizen profiles. Derive mandatory and conditional fields from the workbook and any provided guide; do not invent exceptions. Separate overall problem, specific problem, investigated root cause, and countermeasure. Retain teams and roles, timing and effort, measures, baseline, targets, actions, actual implementation dates, results, sustain actions, document updates, benefits, and review records. Distinguish mandatory submission fields from optional supporting tools and quality-ranking criteria.

Keep Kaizen completeness, coach review, ten-star quality ranking, financial validation, and TCA maturity separate. Preserve the exact ten-star criteria and their logic. In particular, check the documented results criterion requiring more than 30 days of data and more than five points, comparable measures, and the specified treatment of an unmet target; preserve the sustain criterion involving at least two different document or site-tool types. Neither these criteria nor a closed event automatically creates an accepted TCA Yes.

Support statuses for proposed, planned, in progress, implemented, results under review, verified, sustained, and TCA reassessment pending or accepted. Make transitions and authority explicit. Completion should prompt review of affected requirements, not rewrite a previous approved assessment. Requirement-specific evidence windows, including longer participation windows, still apply.

Store measure units, direction, population, period, data source, and actual observations. Compare equivalent before-and-after measures. Distinguish estimated from validated benefits; keep cost avoidance, realized savings, customer benefits, time released, and environmental benefits separate. Count one project's benefit once even when it supports several TCA requirements. Keep unique participant counts and actual project roles suitable for source-specific participation calculations.

Create a concise PDCA report and a complete archive containing all captured information, actions, measurements, evidence, and approvals. Preserve full data when a summary displays fewer actions or shorter text. Offer documented Excel output and validate compatible mappings to supplied templates and upload layouts. Never silently truncate text to fit external limits. Do not claim full workbook calculation compatibility unless it was verified in a suitable spreadsheet engine. Treat AUTO_UPLOAD selectors as legacy mappings, not proof that a supported corporate API exists.

### 8. Permissions, history, and reliability

Enforce site and role permissions on the server for pages, queries, direct object requests, exports, and attachments. Provide staff, assessor, coach, site manager, and administrator roles with documented permissions. Protect sensitive HR and financial details separately from staff progress summaries. Never rely on hidden buttons as authorization.

Use safe private uploads, restricted download access, CSRF protection, secure production settings, secret configuration, audit history, and backup/restore procedures. Approved changes must be attributable. Concurrent edits must not silently overwrite another user's work; implement an appropriate revision check. Verify drafts survive reloads and report save failures clearly. Local startup should bind to loopback by default. Keep public exposure and production setup outside this development authorization.

### 9. Milestones and evidence of completion

Work in this order, progressing automatically after each milestone's relevant checks pass:

1. Source inventory, complete import, traceability, recorded ambiguities, and runnable local foundation.
2. Domain model, versioned scoring, assessment history, evidence coverage, and permission foundation.
3. One complete user journey: assess a gap, link evidence, propose and complete a PDCA event, review results, request reassessment, and approve a new result. The complete catalog remains imported throughout.
4. Remaining role-specific screens, evidence preparation, shared assessment sessions, improvement sequencing, and full Kaizen profiles.
5. Reports, complete archives, mapped exports, benefit controls, and reuse of other audits.
6. Security and concurrency checks, realistic workload measurements, backup/restore exercise, user-journey verification, and pilot handover.

For each milestone, define observable acceptance criteria, implement the behavior, exercise it, fix relevant failures, inspect the result, and update project status. Use automated checks for consequential business rules and access boundaries; do not replace manual visual inspection with tests that only mirror implementation.

Mandatory verification includes source text and field coverage; repeat imports; scoring combinations including unresolved A and higher-level gaps; strict threshold and date boundaries; accepted versus unaccepted evidence reuse; Kaizen closure without automatic Y; preservation of historical assessments; cross-site access denial including exports and files; correct before-and-after measurement and benefit counting; conflicting edits; report completeness and external text-limit errors; and a successful backup restoration.

Use synthetic operational fixtures clearly labeled as fictional. Derive expected rule outputs independently from the written/source policy, not from the function under test. Run a browser-based acceptance journey using the actual local application. Inspect main screens and error states. Report measured latency and resource use under a documented dataset and concurrency level; set explicit pilot performance budgets and do not extrapolate these into an unsupported global capacity claim. Use pagination, appropriate indexes, and targeted rendering where measured behavior warrants them.

Perform a separate final review against source mappings and acceptance criteria, concentrating on data loss, incorrect certification, access leaks, unsupported audit conclusions, and premature event closure. Fix material findings and rerun affected checks. This review is a distinct pass; it does not require multiple agents.

### 10. Definition of done and handover

Done means a locally runnable, functionally verified pilot application, with complete source preservation and mappings; all planned local workflows implemented; explicit policy limitations; accurate verification results; tested startup and backup/restore instructions; and a clear production preparation list. A static dashboard, disconnected forms, scaffold, or passing build alone is not sufficient.

Finish with: what works; how to start and demonstrate it; which checks ran and their results; material unresolved issues; business-owner decisions; and corporate integration details needed for deployment. Identify anything not verified. Do not call the system enterprise-ready merely because local tests passed.

Begin by inspecting the source workbooks and project, establishing the milestone plan, and then implementing the local application.

## Recommended review points for the product owner

The aim is limited human involvement, with high-value review concentrated in three places:

1. Confirm the official interpretation of response A, cumulative levels, exceptions, source conflicts, and missing guide rules. Codex can continue with a clearly labeled local draft beforehand.
2. Try the complete local assessment-to-Kaizen-to-reassessment journey with a site assessor and a working team. Check whether entering and locating information takes less effort than the workbooks.
3. Have corporate owners review identity, permissions, hosting, document storage, retention, recovery, and integrations before a controlled deployment.

## Workflow rationale and references

Use a clear specification, milestone plan, persistent status, and implement–verify–repair loops. Keep AGENTS.md concise and task-relevant. These practices align with OpenAI's guidance; the detailed TCA and Kaizen acceptance requirements above are specific to this product.

- OpenAI, Custom instructions with AGENTS.md: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- OpenAI, Run long horizon tasks with Codex: https://developers.openai.com/blog/run-long-horizon-tasks-with-codex
- OpenAI, Rethinking skills and prompts for GPT-6 Astra: https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra

Prepared 4 October 2026. This is a build brief, not an approval of unresolved assessment policies.
