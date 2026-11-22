# Workstream: <title>

| | |
|---|---|
| Ticket | <KEY> (others: <KEY>, …) |
| Created | <YYYY-MM-DD> |
| State | <one line: active / blocked on X / in review / done> |

## Goal

<The outcome, in a sentence or two. The full plan lives in the ticket.>

## Repos

| Repo | Worktree | Branch | Base | Notes |
|---|---|---|---|---|
| <repo> | `repos/<repo>` | `<branch>` | `origin/<base>` | <e.g. local environment project name> |

## Decisions

- <YYYY-MM-DD> <decision and why>

## Next steps

1. <the next concrete thing to do>

## Where things are

| What | Where |
|---|---|
| <dashboards, live resource IDs, secret-manager item names (never values)> | |

## How to work here

- Artifacts (query results, drafts, plans, screenshots, scripts) go in
  `artifacts/`, never the session scratchpad or `/tmp`.
- When a decision is made or the state changes, update this file (State,
  Decisions, Next steps) so it's always current.
- Add an entry to `LOG.md` at each milestone and before stopping.
- The ticket stays the shareable plan: anything others need goes there too
  (`ticket` skill).
- Ask before deciding: names, approach and anything that creates, removes or
  publishes go to the user as options first.
- <If the engagement has a memory dir:> Saved engagement memory doesn't load
  in this folder. Read `<memory dir>/MEMORY.md` when background is needed.
- Commit inside `repos/<repo>/` on the branch above, under that repo's rules.
- When a PR merges, offer to remove its worktree. When the ticket is closed,
  offer to close this workstream (`workstream close <slug>`).
