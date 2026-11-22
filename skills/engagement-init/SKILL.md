---
name: engagement-init
description: "Set up or update the shared agent rules for a client engagement or multi-repo project: interview the user, then write an AGENTS.md at the engagement root holding the ways of working and the 'Engagement reference' table that the ticket, doc, confluence-sync, workstream and datadog-triage skills read. Use when the user starts a new engagement, says 'set up this engagement/project for agents', asks to add or change an engagement rule or reference value, or when one of those skills reports that no engagement reference exists."
---

# Engagement init

An engagement is a folder holding the repos for one client or project. This
skill writes one file at its root, `AGENTS.md`, from `templates/AGENTS.md`
beside this file. It holds:

- the ways of working that apply to every repo underneath;
- the **Engagement reference** table: the tracker project, docs repo,
  Confluence space, workstreams root, secrets location and so on. The other
  skills are generic and take every engagement-specific value from this table.

Nothing here is decided for the user. This skill asks, proposes, and writes
only what was approved.

## 1. Look before asking

Read-only, and say what you found:

- The candidate root: the current folder, or its parent if the current folder
  is a single repo. List the git repos underneath.
- An existing `AGENTS.md` or `CLAUDE.md` at that root. If one exists with an
  Engagement reference table, this is an **update**: go to section 4. If one
  exists without the table, show it and ask: add the table and chosen rules to
  it, write a separate file elsewhere, or stop. Never replace it.
- Each repo's default branch and long-lived branches
  (`git -C <repo> branch -r`), its `CLAUDE.md`/`AGENTS.md`, and any ticket-key
  pattern in recent branch names or commit subjects.
- Connected tools: an Atlassian connector (`getAccessibleAtlassianResources`
  gives sites and cloudIds; don't list projects or spaces until the user names
  the site), `op`, `gh`, a Datadog key in the environment.

Use what you find to pre-fill suggestions, never to skip a question.

## 2. Interview

Ask in small batches (up to four questions at a time), each with concrete
options and a recommended one where there is a sensible default, plus "skip /
not used". Skipped values stay empty in the table.

1. **Identity**: engagement name; root folder (confirm the candidate); a short
   name for the file's title.
2. **Focus**: what most work is about right now and its areas, in the user's
   words. Offer to leave the section out.
3. **Tracker**: is every piece of work ticketed? Jira site and project; a
   default parent epic or none; required labels; area labels; the hierarchy
   in use; whether ticket keys go in branch names.
4. **Docs**: is there a shared docs repo (path, or offer to create one, which is
   a separate approved step)? Which doc types and folders; published to
   Confluence or not; the space and parent page.
5. **Workstreams**: used or not; root folder (suggest `<root>/workstreams/`).
6. **Secrets**: manager, account, vault.
7. **Observability**: Datadog or not; site; where the keys live (references,
   never values); services and environments.
8. **Deploy flow**: the branch that deploys to each environment.
9. **Rules**: show the "Ask before deciding" paragraph, the six default rules
   and the four optional ones from the template as a list. Ask which to keep, drop or reword, and whether there
   are rules to add. Don't include a rule the user didn't choose.
10. **Wiring**, two separate questions: also create `CLAUDE.md` as a symlink
    to `AGENTS.md` (Claude Code loads `CLAUDE.md`; an `@import` from a parent
    folder does not load reliably inside a repo)? And should the file live in
    the root itself, or in a kit repo and be symlinked in?

Look values up when the user gives a name instead of an ID (project key →
confirm it exists; space key → id; page title → id) and show what you resolved.

## 3. Write

1. Show the complete file as it will be written, and the path. Wait for approval.
2. Write it. Delete template placeholders and unchosen rules. Every table
   value is one the user gave or confirmed; the template's filled-in values
   (hierarchy, doc folders, Datadog site, `_archive/`) are suggestions to
   offer in the interview, not defaults to keep. Unanswered rows stay, with an
   empty value.
3. Create the symlink if asked: `ln -s AGENTS.md CLAUDE.md`. If a `CLAUDE.md`
   already exists, stop and ask; never overwrite it.
4. Don't commit. If the root or kit is a git repo, say what is uncommitted.

The file may be shared or committed. Put no secret values in it, and no
personal data.

## 4. Update an existing file

Show the current value and the proposed one as a diff. Change only what was
asked. If another skill sent the user here for a missing value, fill that row
and stop.

## 5. Check it works

Tell the user how to confirm the file is picked up: start a new session inside
one repo under the root and ask it which engagement rules apply. Then offer the next step as options:
create the first ticket, spin up a workstream, or stop here.
