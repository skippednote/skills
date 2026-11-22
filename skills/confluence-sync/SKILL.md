---
name: confluence-sync
description: "Publish or update a Markdown doc on Confluence (one-way, Markdown is the source of truth), or check whether a doc and its Confluence page are in sync. Confirms the title, parent page and content before every write. Use when the user asks to publish, push, sync or check a doc on Confluence. This is the default for any engagement. A client-specific plugin's skill of the same kind (e.g. `<client>:confluence-sync`) applies only when the working directory is inside that client's own folder; anywhere else, use this one."
---

# Confluence sync

One-way: Markdown → Confluence, through the Atlassian connector. The doc
carries the frontmatter described in the `doc` skill.

## Engagement reference

Walk up from the working directory to the nearest `AGENTS.md` (or `CLAUDE.md`)
with an **Engagement reference** table and read: Jira site / cloudId,
Confluence space (key and id), Confluence parent page, Jira project.

- No such table: say so, and offer (1) run `engagement-init`, (2) give the
  values for this session only, (3) stop.
- A value is empty: ask for it, resolve names to IDs (space key → id, page
  title → id), show what you resolved, then offer to save it. Never guess a
  space or parent.

## Ask first

Publishing is outward-facing. Each time, with numbered options:

- **Which doc**, if the request doesn't name one file.
- **Where**: the parent page. Show its title, not only the ID; ask if the
  doc's `confluence.parent_id` is empty or differs from the engagement default.
- **Title**: confirm it; a page with the same title under that space is a
  conflict, so search first and ask (update that page / rename / stop).
- **The write itself**: show title, parent, a summary of the body and the
  frontmatter values that will be written back afterwards, and publish only
  on approval. Approval to publish one doc doesn't cover the next.

Check mode is read-only and needs no questions.

## Preflight (stop on any failure)

1. Frontmatter has `title`, `audience` and `confluence.parent_id`. A missing
   one is not guessed: ask for it (see Ask first), and add it to the
   frontmatter as an edit the user approves.
2. `audience: customer` → scan the body for ticket keys (`<PROJECT>-\d+`, using
   the project key from the reference table, and any other `[A-Z]+-\d+`), PR
   refs (`#\d+`, `/pull/`), branch names, chat and internal-tool links. Report
   hits; don't publish until fixed.
3. The doc is committed (no uncommitted changes to this file), so the published
   copy matches a commit.
4. Note any Mermaid blocks or local images: Confluence won't render Mermaid without
   a macro, and local images need uploading by hand. Tell the user before publishing.

Report preflight failures as a list with the fix for each, and ask how to
proceed; don't fix the doc silently.

## Body

Send the Markdown body **without** the frontmatter, `contentFormat: "markdown"`.
Title comes from `title`. Don't add a "generated" footer.

## First publish (`page_id` empty)

1. Show the user title, parent and a summary of the body; publish on approval.
2. `createConfluencePage` with `spaceId`, `parentId`, `title`, body.
3. Write the returned `id` to `confluence.page_id` and `version.number` to
   `confluence.version` (covered by the publish approval). Ask whether to set
   `status: published`.

## Update (`page_id` set)

1. `getConfluencePage` → current `version.number`.
2. **If it's higher than `confluence.version`, someone edited the page in
   Confluence.** Stop. Show the user what changed on the page, and let them choose:
   fold those edits into the Markdown first, or overwrite.
3. Otherwise show what changed since the last sync and, on approval,
   `updateConfluencePage` with the new body and title.
4. Write the new version number back to `confluence.version`.

## Afterwards

The frontmatter change is a file edit: show it, and commit only when the user says so.
Report the page URL.

## Check mode

"Is X in sync?" → compare `confluence.version` with the live version and report:
in sync / page edited in Confluence / Markdown changed since last publish
(`git log` on the file after the last sync commit). Don't write anything.

## Permissions

Confluence writes may be blocked by the permission check. If denied, don't retry
or work around it: tell the user, and offer the body as a file they can paste.
