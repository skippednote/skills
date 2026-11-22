# skills

Agent skills I use with Claude Code and Codex, one per directory under
`skills/<name>/SKILL.md`.

| Skill | What it does |
|---|---|
| [confluence-sync](skills/confluence-sync/SKILL.md) | Publish a Markdown doc to Confluence one-way, or check it is in sync |
| [datadog-triage](skills/datadog-triage/SKILL.md) | Triage a production issue from Datadog down to the deployed line of code |
| [doc](skills/doc/SKILL.md) | Write a runbook, perf report, observability note, guide or decision as Markdown in the engagement's docs repo |
| [engagement-init](skills/engagement-init/SKILL.md) | Interview you and write an engagement's shared `AGENTS.md` and reference table |
| [retro](skills/retro/SKILL.md) | Retrospect on a session and derive the shortest route to the same endpoint |
| [slack-send](skills/slack-send/SKILL.md) | Send Slack messages with the user token, bypassing MCP so there's no "sent with Claude" footer |
| [ticket](skills/ticket/SKILL.md) | Find or create the Jira ticket for a piece of work, group it, link PRs, close it out |
| [workstream](skills/workstream/SKILL.md) | One folder per piece of work: a worktree per repo, a brief, a log and artifacts |

## Engagement skills

`ticket`, `doc`, `confluence-sync`, `workstream` and `datadog-triage` work on
any client engagement or multi-repo project. They hold no project-specific
values: each reads an "Engagement reference" table from the nearest
`AGENTS.md` above the working directory, which `engagement-init` writes after
interviewing you. They ask before creating, naming or publishing anything.

## Install

With the [skills CLI](https://github.com/vercel-labs/skills):

```sh
npx skills add skippednote/skills --skill retro
```

My dotfiles pull this repo in as a pinned, non-flake Nix input and link each
skill into `~/.claude/skills` and `~/.codex/skills`.
