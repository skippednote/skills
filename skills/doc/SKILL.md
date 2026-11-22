---
name: doc
description: "Create or update a shared engagement document (runbook, performance report, observability note, guide, decision record) as Markdown in the engagement's docs repo, with frontmatter that makes it ready to hand to the client and sync to Confluence. Asks for the type, name, audience and location before writing. Use when writing or changing project documentation that lives outside a single repo's own docs/. This is the default for any engagement. A client-specific plugin's skill of the same kind (e.g. `<client>:doc`) applies only when the working directory is inside that client's own folder; anywhere else, use this one."
---

# Doc

Shared docs live in the engagement's docs repo as Markdown. The `.md` file is
the source of truth; Confluence, if used, gets a copy via `confluence-sync`.

For docs that belong inside one code repo's `docs/` folder, follow that repo's
conventions instead.

## Engagement reference

Walk up from the working directory to the nearest `AGENTS.md` (or `CLAUDE.md`)
with an **Engagement reference** table and read: docs repo, doc types →
folders, Confluence parent page, Jira project (for the ticket-key pattern),
secrets.

- No such table: say so, and offer (1) run `engagement-init`, (2) give the
  values for this session only, (3) stop.
- A value is empty: ask for it, then offer to save it. No docs repo: ask
  where docs should live; creating a repo is a separate, approved step.

## Ask first

Before writing anything, settle these with the user, as numbered options with
a recommendation:

- **Whether** a new doc is wanted or an existing one should be updated. Search
  the docs repo for the topic first and show what exists.
- **Type** (table below) and so the folder.
- **Name**: two or three candidate file names and titles.
- **Audience**: `customer` or `internal`. This changes what may appear in the
  body, so never assume it.
- **Owner** (a role), whether it will be published to Confluence, and under
  which parent page if not the engagement default.
- **Outline**: show the section headings you intend to fill and what goes in
  each, before drafting the full text.

For an update, show the change as a diff and wait.

## Before writing

1. Make sure there's a ticket (`ticket` skill), unless the user opted out.
2. Copy the type's template from `templates/` beside this file:

| Type (key in the reference table) | Default folder | Template |
|---|---|---|
| Runbook (`runbook`) | `runbooks/` | `templates/runbook.md` |
| Performance report (`perf-report`) | `performance/` | `templates/perf-report.md` |
| Observability note (`observability`) | `observability/` | `templates/observability.md` |
| Guide / explainer (`guide`) | `guides/` | `templates/guide.md` |
| Decision record (`decision`) | `decisions/` | none: MADR headings (context, decision drivers, options, outcome, consequences), plus this frontmatter |

   The reference table's "Doc types → folders" row overrides the folders and
   may add types. A type with no template: propose headings and ask.
3. File name: `kebab-case-topic.md`, no ticket key, no date.

## Frontmatter (required)

```yaml
---
title: Blog page caching            # becomes the Confluence page title
audience: customer                  # customer | internal
status: draft                       # draft | review | published
owner: Platform lead                # a role, not a person
ticket: ABC-123                     # internal; never shown in the body. Empty if unticketed
last_verified: 2026-01-06           # date facts were last checked against the live system; empty until they are
confluence:
  parent_id: ""                     # the engagement's parent page unless a sub-parent exists
  page_id: ""                       # filled by confluence-sync on first publish
  version: 0                        # Confluence version after last sync
---
```

Drop the `confluence` block if the engagement doesn't publish there.

## Writing rules

- **Verify facts against the live system** (hosting config, cloud accounts,
  deploy branches, monitoring) before writing them; update `last_verified`
  when you do. A fact you couldn't verify is marked as such or left out; ask
  which.
- **`audience: customer`**: describe the system as it is. No ticket keys, PR
  numbers, branch names, internal people's names (use roles), chat links,
  internal costs, or before/after tables framed around our tickets. If a
  number needs context, say what changed in plain words.
- Lead with what the reader needs to do or know. Short sections, plain words.
- Commands must be copy-pasteable and never contain secret values; reference
  the secret-manager item instead.
- Diagrams: Mermaid in the source. Confluence won't render it unless the space
  has a Mermaid macro; `confluence-sync` flags this.

## After writing

- Propose a one-line entry for the docs repo's `README.md` index; if there is
  no index, ask whether to start one.
- Ask about each next step rather than doing it: set `status: review`, commit
  (one doc or one logical change per commit, on a branch), sync to Confluence.
