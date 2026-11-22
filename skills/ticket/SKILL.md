---
name: ticket
description: "Find or create the Jira ticket for a piece of work on a client engagement or project, group related work under shared outcomes, link PRs and docs, and close it out. Asks before creating, naming or restructuring anything. Use before starting new work (code, infra, docs, runbooks), when opening a PR, and when work is done. This is the default for any engagement. A client-specific plugin's skill of the same kind (e.g. `<client>:ticket`) applies only when the working directory is inside that client's own folder; anywhere else, use this one."
---

# Ticket

Work on an engagement is ticketed by default, and the ticket is written so
that someone with no access to this chat can finish the work.

## Engagement reference

Engagement-specific values are not in this skill. Walk up from the working
directory to the nearest `AGENTS.md` (or `CLAUDE.md`) with an **Engagement
reference** table and read from it: Jira site / cloudId, Jira project, default
parent (epic), required labels, area labels, ticket hierarchy, branch naming,
workstreams root.

- No such table: say so, and offer (1) run `engagement-init`, (2) give the
  values for this session only, (3) stop.
- A value is empty: ask for it, then offer to save it to the table. Never
  guess a project key, epic or label.

Below, `<PROJECT>`, `<EPIC>` and `<labels>` mean those values.

## Ask first

This skill proposes; the user decides. At each of these points, stop and ask,
with numbered options and a recommendation:

- **Whether** to ticket this work at all, when the user hasn't said (new
  ticket / reuse `<KEY>` / no ticket for this). Offer "no ticket" even when
  the engagement's rules say all work is ticketed; say that the rule exists
  and let the user decide.
- **Which** existing ticket, when more than one could fit.
- **Names**: offer two or three candidate summaries; the user picks or rewrites.
- **Where it sits**: parent, type, labels, and nest vs link vs standalone.
- **Any Jira write**: show the exact content first. One approval of the shown
  content covers that write; it doesn't cover the next one.

Don't fold several of these into one "shall I proceed?"; ask about the choice
that is actually open. Once the user has answered, don't ask the same thing again.

## Explicit user opt-out

If the user explicitly says to skip ticket creation ("no ticket for this",
"skip Jira"), honor that for the stated work:

- Acknowledge the opt-out once and proceed. Do not block on ticket lookup or
  creation, repeatedly ask for an exception, or silently create a ticket later.
- Keep the exception scoped to the task the user specifies. Do not infer an
  opt-out from urgency, a small change, or generic approval to proceed;
  unrelated work still follows the default.
- Reuse a known existing ticket where appropriate, but do not treat the opt-out
  as permission for Jira writes. If the user says to skip Jira entirely, make no
  Jira calls for that work.
- Do not invent a ticket key for branches, PRs or frontmatter. Follow the repo's
  documented no-ticket convention; if a mandatory format has no such convention,
  ask only about that specific conflict.
- Other requirements remain in force: workstream approval, review, verification,
  secrets handling and authorization for commits, pushes, deployments or other
  consequential actions. A ticket opt-out grants none of those.

When the opt-out applies, ticket-dependent steps below do not block the work.

## 1. Find before creating

Search for an existing ticket first:

```
project = <PROJECT> AND statusCategory != Done AND text ~ "<keywords>" ORDER BY updated DESC
```

Narrow with `parent = <EPIC>` or `labels = <label>` when the reference table
has them. Also try the user's words and obvious synonyms. Show the candidates
(key, summary, status, assignee) and ask which to use, or whether none fits.

### Find the right group, not just a duplicate

Before proposing a new ticket, inspect the epic's existing work and any relevant
Story's children and links. Read candidate descriptions, acceptance criteria,
status and ownership; similar titles alone are not enough.

- **Same deliverable:** reuse the existing ticket rather than creating a duplicate.
- **Distinct, bounded work toward a shared outcome:** prefer an existing Story
  as parent, or propose one Story grouping two or more coherent pieces of work.
  Its acceptance criteria must describe the shared outcome, not just list tickets.
- **Related but independently scoped work:** keep its existing hierarchy and
  use an appropriate issue link. A dependency or a shared keyword is not itself
  a parent-child relationship.
- **Independent work:** keep it directly under the epic. Do not force every
  ticket into a group or create an umbrella for a single standalone task.

Present these as options with the one you'd pick and why. Follow the
hierarchy in the reference table (commonly Epic → Story → Sub-task) when a
coherent group exists. When reviewing an entire epic, propose meaningful groups
of outstanding work; link completed work as supporting evidence rather than
reopening or moving it by default.

### Preserve existing work when nesting

Show the proposed parent, child keys, related-only tickets and rationale. Obtain
approval before creating a parent or converting/reparenting existing tickets;
approval to investigate grouping is not approval to change Jira.

Prefer converting an existing bounded task to a subtask, preserving its key,
history, description, status, assignee and evidence. Check for existing subtasks
and hierarchy constraints first; do not orphan children or flatten a wider
initiative to fit a group. Keep broader implementation tickets linked when their
scope spans multiple outcomes. Do not create duplicate tracking subtasks merely
to make a hierarchy look complete.

Use a supported conversion/move operation. Do not assume editing `issuetype` and
`parent` together can convert a Task into a Sub-task. If the available operation
fails or is unavailable, stop that conversion, preserve the original issue, and
report the exact blocker and remaining UI/admin step. With authorization, use
related links as an explicitly interim grouping, not as a claimed parent-child
relationship. Do not bypass permission denials or manufacture replacement issues.

Read back the resulting issue types, parents and links. After a timeout, check
whether the write succeeded before retrying. Update the parent description with
the actual grouping and outstanding conversions. Report **created**, **linked**
and **nested** separately; never claim subtasks exist based only on issue links.
Hierarchy organization does not authorize implementation, deployment or closure.

## 2. Propose, then create

Show the proposed ticket and create it only after the user approves. Never
create silently or override an opt-out.

- **Type:** Story for a shared outcome, Sub-task for bounded work within it;
  otherwise Task (Bug only for a defect in shipped behaviour). State the type
  you propose and why, as a choice the user can change.
- **Parent:** the relevant Story for a Sub-task; `<EPIC>` if the reference
  table has a default parent; otherwise ask which epic, or none.
- **Labels:** the required labels plus one area label, if the table defines
  them. Ask which area; don't pick one.
- **Summary:** what changes, in plain words, ≤ 80 chars. Offer two or three.
- **Assignee / sprint / priority:** leave unset unless the user says.
- **Description** (Markdown), below.

**The ticket must be enough on its own.** Someone with no chat history, no
memory notes and no access to this session should be able to pick it up and
finish it. Research first (read the code on the deploy branch, query the live
system), then write down what you found. Never write "see chat" or "as
discussed", and don't leave a step that only makes sense to whoever wrote it.

```markdown
## Context
Why this matters now, and the current state as checked against the live system:
what exists, what's missing, numbers, IDs. Say when it was checked.

## Goal
The outcome, observable by someone outside the team.

## Decisions needed
Open choices, each with the options and a recommendation. Omit if none.

## Implementation plan
Numbered steps, concrete enough to run without asking anyone:
repo and branch to start from, files to change and how, commands
(plan/apply/deploy), the order of steps, and the repo's merge/promotion flow.

## Where things are
| What | Where |
|---|---|
Repos and paths, live resource IDs, dashboards, state/backends, and the
secret-manager items that hold credentials (names, never values).

## Scope
- In: …
- Out: … (with the follow-up ticket key if one exists)

## Acceptance criteria
- [ ] …

## Verification
How we'll prove it on the real environment (URL, dashboard, query, command),
and the expected result.

## Risks / rollback
What could go wrong and how to undo it. Omit for trivial work.

## Links
Docs, dashboards, related tickets.
```

Where the plan depends on a choice the user hasn't made, put it under
**Decisions needed** and ask; don't write the plan as if it were settled.

Keep the plan current: when the approach changes or a decision is made, edit
the description (don't only add a comment), so it always shows the current plan.

## 3. While working

- Branch and PR names follow the repo's own convention, then the reference
  table's; include the ticket key where one exists and the convention allows.
  Propose the name and let the user confirm.
- When a ticket exists, include its key in the PR description you propose, so
  Jira links it.
- A doc for ticketed work gets the key in its frontmatter (see the `doc`
  skill). For explicitly unticketed work, omit the key; never fabricate one.

## 4. Close out

For explicitly unticketed work, report verification and remaining work to the
user; do not create a ticket just to close out.

When ticketed work is verified, propose one comment for the ticket: what
shipped, where (PRs, environments), how it was verified, and anything left open
(as new tickets, not as notes). Ask before posting it, and ask separately
which status to transition to (list the available transitions).

Then check for a workstream, if the reference table has a workstreams root:
`grep -l "<KEY>" <workstreams root>/*/CLAUDE.md`.

- The ticket is that workstream's main ticket: offer `workstream close <slug>`.
- The ticket is one of its other tickets and work continues there: offer
  `workstream sweep <slug>` to drop the worktrees this ticket no longer needs.

If a workstream matched, close-out isn't finished until one of the two has
run or the user has declined it. No match: nothing more to do.

## Permissions

Jira writes (create, edit, comment, transition) may be blocked by the permission
check. If a call is denied, don't retry or work around it: give the user the exact
change to make in Jira, or ask them to allow the tool.
