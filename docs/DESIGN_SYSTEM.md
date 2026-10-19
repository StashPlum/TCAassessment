# TCA Progress design foundation — stage 2

This is the local pilot's shared interface contract. Existing CEVA branding in the application is a text identification and a restrained navy/blue/red palette. No approved CEVA logo or font file is present in this repository; do not create or imply an official mark. Replace these provisional tokens only after corporate brand assets and usage rules are supplied.

## Roles and tokens

| Role | Token / use |
|---|---|
| Navigation / headings | `--navy: #0b1d3b`; short, informative headings |
| Links / primary actions / accepted progress | `--blue: #2458a6` |
| Body / muted / lines / canvas | `--ink: #17243b`, `--muted: #4c5b70`, `--line: #cbd4e0`, `--canvas: #f3f5f8` |
| Keyboard focus | `--focus: #b35c00`, 3 px visible outline |
| Y / accepted answer | `--yes-ink: #155b39` on `--yes-bg: #e4f3e9`, always with **Y** |
| A / Advisory answer | `--advisory-ink: #754600` on `--advisory-bg: #fff0c7`, always with **A** and follow-up |
| N / failed answer | `--no-ink: #8d2631` on `--no-bg: #fbe9eb`, always with **N** |
| Unanswered | `--neutral-ink: #47566b` on `--neutral-bg: #edf1f5`, always with **—** |

System typography uses Segoe UI with Arial fallback, 16 px body, 1.5 line height, 1.85 rem desktop / 1.55 rem mobile page heading and concise labels. Spacing tokens are 4, 8, 12, 16, 24, 32 px. Corners are 2–5 px. Transitions are 120 ms for feedback and disabled by reduced-motion preference. There are no decorative gradients, hero areas or animated metrics.

## Reusable patterns

- **Site context:** header shows selected site, baseline and rule version. Site switcher stays available; each destination and download still enforces membership server-side. The Authorized locations shortcut is hidden.
- **Role summary:** two-column dense work sections at desktop and a single column below 760 px. Lead with progress, next tasks and drill-down, then historical detail.
- **Progress:** a labeled 12 px bar means *accepted pass / effective frozen scope*. Percentage, numerator/denominator, local level, assessed count, open Advisory and CAT status are separate. Explain gates in a disclosure. Never infer official standing from the bar.
- **Filters:** `filter-bar` with labels immediately above 44 px controls, main choices visible, extra choices in a disclosure, active state and Reset. Existing `filter-panel` forms use the same padding and control scale. Invalid parameters are normalized before display. Results show empty state rather than implied success.
- **Tables:** left-aligned short headers, horizontal scrolling inside a bounded region, source IDs linking to details. Pagination keeps active filters. Long content wraps within cells.
- **Matrix:** frozen requirement scope determines rows/positions and C(1–5), B(6–8), A(9–10) bands for the standard catalog. Alternate scopes use their own available positions and group counts. The section header remains visible while the matrix scrolls within its region; the page does not scroll horizontally. Each Y/A/N/— cell links to the same source question, evidence, comments, follow-up and actions. Local work has its own table.
- **Statuses:** color always accompanies text or a symbol. Amber Advisory means an answer with an open improvement and retest, not a closed task. CAT standing has separate language.
- **Errors and empty states:** form errors keep values, open the relevant disclosure and link to its fields; empty filters offer Reset. A blank or unknown denominator does not become 150 by default.

## Responsive and accessibility checks

Design breakpoints: desktop 1440 px, tablet 1024 px and narrow 390 px. The matrix owns horizontal scroll on narrow screens. Buttons/inputs are at least 44 px tall; links, disclosures and cells use keyboard focus. Measured text contrast on actual status backgrounds: Y 7.07:1, Advisory 7.04:1, N 7.32:1, neutral 6.58:1; blue on white 6.95:1; muted on canvas 6.33:1. These values cover the tested text colors, not every future combination.

Rendered evidence is in `docs/verification/stage2-*.png`. Three real routes were rendered first on a fictional 150-answer site, then the existing filter-panel shell was brought into this foundation. The original questions and assessment data remain in their existing models and links.

## Stage 4 token reconciliation with the v3 prototype

`workspace.css` section "E4" adopts the prototype values as the provisional tokens: navy `#0B1A48` (hover `#1C2F70`) for headings, links and primary buttons; ink `#14182B`; muted `#4B5265`; accent marker `#E4002B`; lines `#D8DBE3`/`#C3C8D4`/`#E6E8EE`/`#EEF0F3`; canvas `#F3F4F7`; tints `#E8EBF4`/`#F3F5FA`/`#F7F8FA`; status Y `#2F7D45` (soft `#E2F1E6`, text `#1D5A30`), A `#F0B43C` (`#FDF0D3`, `#6B4300`), N `#B3261E` (`#F9E1DF`, `#8E1D17`), unassessed `#E3E6EC`/`#3E4556`. Square corners, 2 px navy focus outline with 2 px offset. Headings use "Barlow Condensed" 600 and body "Barlow"; the fonts are not bundled (no approved font file), so Arial Narrow/Segoe UI/Arial render as fallbacks. New shared components: `.blueprint` card with corner marks, `.chip`, `.tag-ok/-warn/-bad/-neu`, `.pdca-steps`, `.pdca-bar`, `.gate-list`, `.segmented`, `.gantt`, `.task-table`, `.choice-cards`, `.state-chips`, `.tool-card`. The supplied CEVA logo is used in report PDFs with a cleaned transparent background; brand usage approval remains open.
