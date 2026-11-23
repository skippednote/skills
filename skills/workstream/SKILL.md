---
name: workstream
description: "Spin up, resume, list, sweep or close a workstream: a dedicated folder holding git worktrees of every repo a piece of work touches plus its context files (brief, log, artifacts), so any session can pick the work up. Asks before creating, naming or removing anything. Use when the user says 'spin up a worktree/workstream', starts work spanning several repos or several sessions, wants to pick up or wrap up such work, or asks to clean up merged worktrees. This is the default for any engagement. A client-specific plugin's skill of the same kind (e.g. `<client>:workstream`) applies only when the working directory is inside that client's own folder; anywhere else, use this one."
---

# Workstream

One folder per piece of work. Every session for it starts in that folder, so
`claude --continue` there resumes this work and nothing else, and the context
files carry over to anyone (or any session) picking it up later.

```
<workstreams root>/<slug>/
├── CLAUDE.md     brief: ticket, goal, repos/branches, decisions, state, next steps
├── LOG.md        dated entries, newest last
├── artifacts/    query results, drafts, plans, screenshots, scripts
└── repos/<repo>/ git worktree per repo
```

`CLAUDE.md` loads automatically there; the engagement's shared rules load above
it when the workstreams root sits under the engagement root; each repo's own
`CLAUDE.md` loads when its files are touched. Templates: `templates/CLAUDE.md`,
`templates/LOG.md` beside this file.

## Engagement reference

Walk up from the working directory to the nearest `AGENTS.md` (or `CLAUDE.md`)
with an **Engagement reference** table and read: engagement root, workstreams
root, branch naming, deploy branches, memory dir.

- No such table: say so, and offer (1) run `engagement-init`, (2) give the
  values for this session only, (3) stop.
- A value is empty: ask for it, then offer to save it. If there is no
  workstreams root, suggest `<engagement root>/workstreams/` and ask.

Below, `<root>` is the engagement root and `<ws>` the workstreams root.

## Ask first

Modes: `new`, `resume`, `add-repo`, `status`, `sweep`, `close`. If the request
doesn't make the mode plain, ask which. Then, with numbered options and a
recommendation:

- **Whether** a workstream is wanted, when the user only described the work
  (workstream / a plain branch in the one repo / nothing yet).
- **Names**: two or three candidate slugs, the branch name per repo, and the
  session name.
- **Which repos**, and the **base branch** for each when more than one is
  plausible.
- **Every write** (folders, worktrees, removals, archive moves): shown
  as a plan and run on approval.

`status` is read-only and needs no questions.

## new [`<slug>`] [`<repos…>`]

A slug or repos given in the request are taken as the user's choice; anything
not given is asked.

1. **Ticket.** Once the user has confirmed a workstream is wanted, find or
   create the ticket with the `ticket` skill, unless the user has opted out. One workstream, one main ticket; others go in the brief's list.
2. **Slug.** Kebab-case topic, no ticket key (`alert-routing`). Offer
   candidates. Stop if `<ws>/<slug>/` exists: offer `resume` or another name.
3. **Repos.** Ask which repos the work touches; list the ones under `<root>`.
4. **Per repo**, from `<root>/<repo>`:
   - Base branch: the repo's own convention (its CLAUDE.md/AGENTS.md), then
     the engagement's rules (e.g. prod-only changes start from the prod
     branch), else `origin/HEAD`. Repos with no remote: the local default
     branch. Where two are plausible, or the repo has no commits, ask.
     Otherwise show the base in the plan, where the user can change it.
   - Branch: the repo's convention, then the reference table's; otherwise
     propose `<KEY>/<slug>`, or `<slug>` with no ticket, and confirm it. Never an AI-tool prefix such
     as `claude/` or `codex/`. If the branch exists, ask: reuse it (worktree
     without `-b`) or rename.
   - Plan the commands:
     ```sh
     git -C <root>/<repo> fetch origin
     git -C <root>/<repo> worktree add <ws>/<slug>/repos/<repo> -b <branch> origin/<base>
     ```
   - Repos with a per-checkout local environment (DDEV, docker compose
     project names, fixed ports): the worktree needs its own project name to
     run beside the main checkout (DDEV: `ddev config
     --project-name=<repo>-<slug>` inside the worktree). Put the proposed name
     in the plan and say so in the brief.
     Don't start any environment unless asked.
5. **Show the plan**: folder, per-repo base → branch, the filled brief
   (`CLAUDE.md`) and first LOG entry as they will be written, and how it will
   be opened. Wait for approval.
6. **Create.** `mkdir -p` the folder, `artifacts/` and `repos/`; run the
   worktree commands; fill `CLAUDE.md` and `LOG.md` from the templates (first
   LOG entry: created, with ticket and branches), as approved.
7. **Open it.** Ask how:
   - a new session, started by the user: give the command
     `cd <ws>/<slug> && claude -n <slug> "Read CLAUDE.md and LOG.md, then start on Next steps."`
     (confirm the session name; `<slug>` is the suggestion);
   - or continue in this session, if the user prefers.
8. Report the folder, branches and how to get into it. Unless the user chose
   to continue here, the work happens in that session, not this one.

## resume `<slug>`

No slug given: list the workstreams (as `status`) and ask which.

1. If a session is already running in the folder
   (`lsof -d cwd -Fn | grep <ws>/<slug>`), say so and stop: the user switches
   to it.
2. Otherwise give the command to open it, as in `new` step 7:
   - `cd <ws>/<slug> && claude --continue` if a session exists for the folder:
     any `*.jsonl` in `~/.claude/projects/<key>/`, where `<key>` is the folder
     path with every `/` and `.` replaced by `-`;
   - else `claude -n <slug>` with the same task as `new`.
3. Interactive `--continue` ignores sessions run with `claude -p`. If it
   reports "No conversation found to continue", start fresh there:
   `claude -n <slug> "Read CLAUDE.md and LOG.md, then start on Next steps."`.

## add-repo `<slug>` `<repo>`

`new` step 4 for one repo; add it to the brief's Repos table and a LOG entry.

A second worktree of a repo already in the workstream (another PR, a
promotion, a backsync) goes in `repos/<repo>-<topic>/` (ask for the topic name) and gets its own row in
the Repos table. Never put a worktree or clone under `artifacts/`. Offer to
remove it as soon as its PR merges; don't wait for `close`.

## status

For each folder in `<ws>` (skip `_archive`): the ticket and state line from
its `CLAUDE.md`, the newest LOG heading, and per worktree the branch,
`git status --porcelain` count and commits ahead of upstream
(`git rev-list --count @{u}..HEAD`, or "no upstream"). One table, read-only.

## sweep [`<slug>`]

Removes worktrees whose work has landed, across every repo under `<root>` (or
only those inside `<ws>/<slug>/`). It covers linked worktrees wherever they
live. Main checkouts are never touched.

1. **Collect.** Per repo with linked worktrees: `git fetch --prune origin`,
   then `git worktree list --porcelain`. Records whose folder is gone are
   cleared with `git worktree prune -v` (records only, no files).
2. **Classify** each linked worktree. Propose removal only when all of these hold:
   - `git status --porcelain` is empty (no changes, no untracked files);
   - HEAD has landed: it is an ancestor of a deploy branch from the reference
     table or of `origin/develop`, `main`, `master`, `production`, `stage` or
     `staging`, or `gh pr list --head <branch> --state merged --json
     headRefOid` returns a PR whose head is exactly HEAD (a squash merge). A
     merged PR with a different head is not enough;
   - it holds no ignored `.env*` file (`git status --porcelain --ignored`);
   - no process is running in its workstream folder
     (`lsof -d cwd -Fn | grep <folder>`).

   Everything else is kept, with the reason: dirty, not merged, open PR, no
   remote to check against, local env file, live session.
3. **Show the plan**: remove and keep counts per repo and per workstream, and
   the keep list with reasons, and the LOG entries and Repos-table edits that
   follow from the removals. Ask: remove all proposed / choose which / none.
4. **Remove.** Re-check clean and the same HEAD right before each
   `git -C <root>/<repo> worktree remove <worktree>`. Never `--force`.
   Branches are kept.
5. **Report**: what was removed, what was kept and why, and which workstreams
   now have no worktrees or only merged ones: offer `close` for those. Add a
   LOG entry to each workstream that lost worktrees and drop their rows from
   its Repos table.

## close `<slug>`

1. Per worktree anywhere under the folder (including any left under
   `artifacts/`): uncommitted changes, unpushed commits, PR state (`gh pr view
   <branch>`). Any dirty or unpushed worktree → stop and report; never discard work.
2. Size up `artifacts/` (`du -sm artifacts/*`):
   - reinstallable or rebuildable folders (`node_modules`, `vendor`, `.next`,
     `dist`, `build`, `target`, `.terraform`, `cdk.out`) are proposed for deletion;
   - anything else over 100 MB is listed with its size and a keep/delete
     question. Evidence a ticket points at is kept unless the user says delete.
3. Propose, as separate items the user can accept or skip: the final LOG entry
   (what shipped, where, what's open), ticket close-out with the `ticket` skill
   if the ticket is done, the `artifacts/` deletions from step 2, the worktree
   removals, whether to delete the branches (default: keep), and the move to
   the archive.
4. On approval run the accepted items, then move the context to
   `<ws>/_archive/<slug>/` (`CLAUDE.md`, `LOG.md`, `artifacts/`; the now-empty
   `repos/` goes).

## Working inside a workstream

These are written into each brief so the session there follows them:

- Artifacts go in `artifacts/`, never the session scratchpad or `/tmp`.
- When a decision is made or the state changes, edit `CLAUDE.md` (State,
  Decisions, Next steps) so it's always current.
- Add a LOG entry at each milestone and before stopping: what was done, what
  was found, where it stopped.
- The ticket stays the shareable plan; the workstream holds local working
  state. Anything others need goes in the ticket too.
- Saved memory is per folder, so the engagement's memory doesn't load here.
  If the reference table names a memory dir, read its `MEMORY.md` when
  background is needed.
- Commits happen inside `repos/<repo>/` on the workstream branch, under that
  repo's rules.
- When a PR merges, offer to remove its worktree. When the ticket is closed,
  offer to close the workstream.
