---
name: slack-send
description: "Send Slack messages, DMs, thread replies, edits, deletes, reactions, and file uploads using the user's Slack user token — bypassing the Slack MCP so messages don't carry the 'sent with Claude' footer. Use whenever the user asks to send, post, DM, reply in thread, edit, delete, react to, or upload something to Slack. Prefer this over any Slack MCP send tool for every send-side action. Read-side (search, read channel/thread) still goes through MCP."
---

# slack-send

Send to Slack as the user, via `chat.postMessage` and friends, using a user
token. Messages appear as sent by the user directly — no "sent with Claude"
footer.

## Prefer this over MCP

For any send-side action — post, DM, reply, edit, delete, react, upload —
default to the helper here, not `mcp__*slack*send*` or similar. If a call
fails for a reason the user can fix (missing scope, bad channel, token
unset), surface that; don't silently fall back to MCP.

Read-side actions (search, read channel/thread, canvas reads) are not
touched by this skill — keep using MCP for those.

## Before sending — verify the destination

The user's own words for a channel/handle are often approximate (missing
prefix like `eng-`, typo'd suffix, different capitalisation). Resolve
before drafting; don't resolve on send.

- Run `slack resolve <name>` first. On a miss the script prints the
  closest substring matches from channels the user is in — read them back
  and confirm which one.
- If the user gave only a vague description ("the PE stream channel"), use
  the Slack search MCP to find the exact channel first, then pass the
  resolved id (or confirmed `#name`) to `slack send`.
- Prefer raw ids (`C...`, `D...`, `U...`) in loops or scripts — no API
  round-trip, no rate-limit exposure.

## The helper

Use `scripts/slack` from this skill directory. It is a self-contained Python
script with no third-party deps. Resolve its path from the skill directory
when calling it.

### Subcommands

```
slack send    CHANNEL TEXT   [--thread TS] [--blocks JSON_OR_PATH]
slack dm      TARGET  TEXT   [--thread TS] [--blocks ...]
slack reply   CHANNEL THREAD_TS TEXT [--blocks ...]
slack update  CHANNEL TS TEXT [--blocks ...]
slack delete  CHANNEL TS
slack react   CHANNEL TS EMOJI [--remove]
slack permalink CHANNEL TS
slack upload  CHANNEL FILE [--text ...] [--title ...] [--thread TS]
slack resolve TARGET
slack whoami
slack raw     METHOD  [--field key=value]...   # escape hatch for any Slack method
```

### Targets

`CHANNEL` and `TARGET` accept:

- `#name` — channel the user is in, resolved via `users.conversations`
  (not `conversations.list`, which is heavily rate-limited). Only channels
  the user is a member of resolve this way — which is also the set the
  user token can post to as the user.
- `@handle` — user handle or display name, resolved via `users.list`, DM
  opened via `conversations.open`.
- `someone@example.com` — email, resolved via `users.lookupByEmail`, DM opened.
- raw id — `C...` channel, `G...` group, `D...` DM, or `U...`/`W...` user
  (user ids auto-open a DM). Prefer this in loops.

Name→id lookups are cached at `~/.cache/slack-send/{channels,users}.json`
so repeated runs don't re-page. On rename, run `slack cache --clear`.

Rate-limited calls (HTTP 429 or `error: ratelimited`) are retried once,
honoring Slack's `Retry-After`.

### Blocks

`--blocks` accepts either a JSON string (starting `[` or `{`) or a path to a
file containing JSON. The script sets `text` as a plaintext fallback.

### The `raw` escape hatch

For any method the subcommands don't cover (e.g. `pins.add`,
`conversations.history`, `bookmarks.add`), use `raw`:

```
slack raw pins.add --field channel=C123 --field timestamp=1700000000.000100
slack raw conversations.history --field channel=C123 --field limit=5
```

Values starting with `[` or `{` are parsed as JSON before being sent.

## Token setup

The script resolves the token in this order:

1. `op read "$SLACK_USER_TOKEN_OP_REF"` if `SLACK_USER_TOKEN_OP_REF` is set.
2. `op read` against the baked-in default ref in the script (points at the
   author's 1Password item). Override via the env var above.
3. `$SLACK_USER_TOKEN` from env.
4. Fail with instructions.

So the usual flow is just:

```sh
op signin   # once per session
```

To point at a different 1Password item, override the ref:

```sh
export SLACK_USER_TOKEN_OP_REF='op://Vault/Item/field'
```

Or skip op entirely with a raw token:

```sh
export SLACK_USER_TOKEN=xoxp-...
```

The token must be a **user token** (`xoxp-...`), not a bot token. Required
scopes depend on what you call; if a call errors with `missing_scope`, the
response names the needed scope — add it at api.slack.com/apps and
re-install. Common scopes:

- `chat:write` — send, update, delete your own messages
- `chat:write:bot` — some workspaces require this on the user token too;
  if a send errors `missing_scope: chat:write:bot`, add it and reinstall
- `im:write`, `im:read` — open and post DMs
- `users:read`, `users:read.email` — resolve `@handle` and email targets
- `channels:read`, `groups:read` — resolve `#name` channels (needed by
  `users.conversations`)
- `reactions:write` — add/remove reactions
- `files:write` — upload files

The user token can only post to channels the user is a member of. A
"channel not found" error from `slack send` on a channel that visibly
exists usually means the user needs to join it first (or send via bot).

## When to invoke this skill

Any request to:

- "send a slack message to #channel"
- "DM X", "slack @handle", "message them on slack"
- "reply in that thread", "post in the thread"
- "edit that message", "fix the typo", "delete that message"
- "react to that with :emoji:"
- "share this file in slack", "upload to #channel"

Also invoke on `/slack-send ...` or whenever the user names a Slack method
to call directly.

## Rules

- **Confirm destination and text before sending.** Slack is a shared system
  and messages can't be unsent cleanly. Show the resolved channel/user and
  the exact body; wait for explicit approval. Rule carries over from the
  user's working preferences.
- **Match the user's voice.** Short, plain, Slack-terse. No AI-sounding
  phrasing, no sign-off, no emoji unless they used one.
- **Never print the token value** or echo it in logs. The script already
  reads it into memory and uses it as a bearer header — don't `echo`, don't
  pass it on a command line, don't commit it anywhere.
- **Don't silently fall back to MCP** when a send fails. Report the error
  verbatim so the user can fix scope or wiring.
