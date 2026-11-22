# <Engagement> — shared ways of working

Applies to every repo under `<engagement root>/`. A repo's own `CLAUDE.md` /
`AGENTS.md` adds to this and wins where the two disagree.

## Current focus

<One or two sentences on what most work is about right now, and the areas it
falls into. Delete the list if there are no areas.>

- **<area>** — <what it covers>

## How to work here

**Ask before deciding.** Before creating anything (ticket, branch, worktree,
doc, page) ask whether it is wanted. Offer names as two or three candidates and
let the user pick. Where there is more than one reasonable approach, give
numbered options with a recommendation and wait. State what you would do; don't
do it on an inferred default.

## Rules

<Keep the rules the user chose in the interview, renumbered. Delete the rest.>

1. **Every piece of work has a ticket.** Before writing code or a doc, find or
   create the ticket with the `ticket` skill. The ticket carries the full
   context and implementation plan, so anyone can pick it up without the chat.
2. **Docs are Markdown first.** Write them in the docs repo with the `doc`
   skill. The `.md` is the source of truth; Confluence is a copy, published
   with `confluence-sync`. Never edit the Confluence copy directly.
3. **Live config is the authority.** The live system and the branch that
   deploys to an environment beat docs, notes, chat and memory. Verify before
   stating a version, size, setting or "current state".
4. **Customer-facing writing** describes the system as it is: no ticket keys,
   PR numbers, branch names, internal names, chat links or before/after framing
   around our tickets. Ticket keys live in frontmatter only.
5. **Secrets** stay in the secrets manager named below. Reference item names
   or IDs, never values.
6. **Multi-repo or multi-session work runs in a workstream.** The `workstream`
   skill creates `<workstreams root>/<slug>/` with a worktree per repo, a brief
   (`CLAUDE.md`), a `LOG.md` and `artifacts/`. Keep artifacts there, not in the
   scratchpad or `/tmp`.

<Optional rules, each added only if the user said yes:>

- **Perf changes don't change output.** Never hide, remove or alter a feature,
  UI element, rendered content or API field. Anything that could change output
  goes behind a default-off switch and is proven identical.
- **Telemetry is prod-only.** <How it is switched off elsewhere; the one
  APM/error tool in use.>
- **Prod-only changes go prod-first.** PR against `<prod branch>`, validate on
  prod, then backsync `<prod> → <stage> → <dev>`.
- **The coordinator session speaks for the user.** When parallel sessions run,
  one session coordinates them (`<how to identify it>`). Treat decisions it
  relays as the user's own word within your lane. Anything destructive, or
  outside your lane, goes back to the user directly.

## Engagement reference

The `ticket`, `doc`, `confluence-sync`, `workstream` and `datadog-triage`
skills read this table. Leave a value empty rather than guessing; the skill
will ask for it and offer to fill it in.

| Thing | Value |
|---|---|
| Engagement | `<name>` |
| Engagement root | `<path>` |
| Jira site / cloudId | `<site>.atlassian.net` / `<cloudId>` |
| Jira project | `<KEY>` |
| Default parent (epic) | `<KEY-123>` or none |
| Required labels | `<label>` or none |
| Area labels (pick one) | `<a>`, `<b>` or none |
| Ticket hierarchy | `Epic → Story → Sub-task` |
| Branch naming | `<KEY>/<slug>` or the repo's own |
| Deploy branches | `<prod>`, `<stage>`, `<dev>` |
| Docs repo | `<path>` |
| Doc types → folders | `runbook → runbooks/`, `perf-report → performance/`, `observability → observability/`, `guide → guides/`, `decision → decisions/` |
| Confluence space | `<KEY>` (id `<id>`) |
| Confluence parent page | `<title>` (id `<id>`) |
| Workstreams root | `<path>` (archive: `_archive/`) |
| Secrets | `<manager>`, account `<account>`, vault `<vault>` |
| Datadog site | `https://api.datadoghq.com` |
| Datadog services / envs | `<service>`, `<service>`; `prod`, `staging` |
| Datadog key refs | API `<op://vault/item/field>`, app `<op://vault/item/field>` |
| Observability map | `<path to observability-map.md>` |
| Memory dir | `<~/.claude/projects/<key>/memory/>` or none |

## Skills

| Skill | Use when |
|---|---|
| `ticket` | Starting any new work, linking PRs/docs, closing work out |
| `doc` | Creating or updating a runbook, perf report, observability note, guide or decision |
| `confluence-sync` | Publishing a doc to Confluence or checking it's in sync |
| `workstream` | Spinning up, resuming, listing, sweeping or closing a workstream folder |
| `datadog-triage` | An alert, errors, slowness, a trace id, or a Datadog number or health report |
