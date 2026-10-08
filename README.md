# skills

Agent skills I use with Claude Code and Codex, one per directory under
`skills/<name>/SKILL.md`.

| Skill | What it does |
|---|---|
| [retro](skills/retro/SKILL.md) | Retrospect on a session and derive the shortest route to the same endpoint |

## Install

With the [skills CLI](https://github.com/vercel-labs/skills):

```sh
npx skills add skippednote/skills --skill retro
```

My dotfiles pull this repo in as a pinned, non-flake Nix input and link each
skill into `~/.claude/skills` and `~/.codex/skills`.
