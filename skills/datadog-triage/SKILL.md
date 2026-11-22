---
name: datadog-triage
description: "Triage a production issue from Datadog (monitors, APM traces, metrics, RUM, logs), correlate it with the code that is actually deployed, and name the root cause with evidence. Confirms scope, window and baseline with the user before measuring. Use when the user mentions an alert, a monitor, 5xx, errors, slowness, a trace id, 'what's wrong with prod', 'why is X failing', or asks for a Datadog number or health report. Can also post the result to Slack. This is the default for any engagement. A client-specific plugin's skill of the same kind (e.g. `<client>:datadog`) applies only when the working directory is inside that client's own folder; anywhere else, use this one."
---

# Datadog triage

Go from a symptom to a root cause that is backed by a query result and a line
of deployed code. Three kinds of request:

1. **Triage**: "sign-in is throwing 500s", an alert, a trace id. Sections 1 to 6.
2. **Ad-hoc number**: "p95 on the API today?" Sections 1, 2 and 3.1, answer, stop.
3. **Report**: "health of the frontend this week". Sections 1, 2, 3.1, 5 and 6; section 7 only if it is to be posted.

If it isn't plain which of the three is wanted, ask.

## 0. Rules

- **Read-only.** Query Datadog and read code. No monitor edits, mutes, deploys,
  rollbacks or code changes: propose them and wait. A fix is new work, so it
  goes through the engagement's ticket process (`ticket` skill).
- **Never invent or estimate a number.** Every figure comes from a query run in
  this session, with its window and unit. Nothing back: say "no data for
  `<query>` in `<window>`", then check the names.
- **Check which environments send telemetry** (observability map). An
  environment that sends nothing cannot be triaged from Datadog: say so and go
  to platform logs, pipeline logs or a local reproduction.
- **Spans and logs can carry personal data.** Summarise; don't paste emails,
  tokens, user ids or full URLs with query strings into chat, Slack or tickets.
- Keys stay in the secrets manager. Never echo them, never run the helper
  under `bash -x`.

## 1. Setup

### Engagement reference

Walk up from the working directory to the nearest `AGENTS.md` (or `CLAUDE.md`)
with an **Engagement reference** table and read: Datadog site, Datadog key
refs, observability map, secrets, deploy branches, workstreams root.

- No such table: say so, and offer (1) run `engagement-init`, (2) give the
  values for this session only, (3) stop.
- A value is empty: ask for it, then offer to save it.

### Observability map

The estate-specific knowledge (services → repos, request path, metric names,
ownership, sampling traps) lives in the engagement's observability map, not in
this skill. If the reference table has no map, or the file doesn't exist:

1. Say that triage without it means discovering names as you go.
2. Offer: (1) build it now from `templates/observability-map.md` beside this
   file, (2) carry on without it for this request, (3) stop.
3. To build it, discover what you can read-only (`dd.py monitors ''`, services
   from `spans-agg '*' --by service`, monitor and SLO definitions in the
   repos), show the draft with the gaps marked, and ask the user to fill or
   confirm each section. Ask where to save it; write it only on approval.

When triage turns up a new trap or a wrong row, propose the map edit at the end.

### Access

Use the helper beside this file, `scripts/dd.py`. It takes everything from the
environment; nothing is hard-coded:

```sh
export DD_SITE=<Datadog site from the reference table>
export DD_API_KEY_REF=<op://… API key ref>   DD_APP_KEY_REF=<op://… app key ref>
export OP_ACCOUNT=<1Password account, if more than one is signed in>
DD=<path to this skill>/scripts/dd.py

python3 $DD monitors 'status:(alert OR warn)'
python3 $DD metric 'sum:trace.web.request.errors{service:<service>,env:prod} by {resource_name}.as_count()' --from 4h --baseline 7d
python3 $DD spans-agg 'service:<service> env:prod status:error' --by resource_name --from 1h
python3 $DD spans-agg 'service:<service> env:prod' --by resource_name --compute pc95:@duration
python3 $DD spans 'service:<service> env:prod status:error resource_name:"GET /api/x"' --limit 10
python3 $DD trace <trace_id> --from 6h          # span tree across services
python3 $DD logs 'service:<service> env:prod status:error' --from 1h
python3 $DD events 'source:alert' --from 24h    # monitor transitions
python3 $DD raw POST /api/v2/rum/events/search '{"filter":{"query":"@type:error service:<service> env:prod","from":"now-1h","to":"now"}}'
```

`DD_API_KEY` / `DD_APP_KEY` set directly also work. The helper prints compact
tables and takes `--out <file>` for the raw JSON. Times are `15m`, `4h`, `7d`,
`now` or ISO 8601. If the secrets manager is locked, ask the user to sign in
(`! op signin`). If a Datadog MCP server is also connected, ask which to use;
recommend the helper, since the rest of this skill is written against its output.

Save raw results with `--out` under the workstream's `artifacts/` when in one,
otherwise the session scratchpad (say where), and do arithmetic (deltas, rates, top-N) in
Python on those files.

## 2. Signal → repo → deployed code

Take the mapping from the observability map: Datadog service, repo, deploy
branch, how `version` is tagged, where monitors and SLOs are defined, where the
runbooks are, and which monitors and services are ours. Anything in the
Datadog org that the map doesn't claim belongs to someone else: mention it only
when it explains our symptom, and never touch it.

**The local checkout is not what is deployed.** Checkouts sit on feature
branches. Read deployed code by ref, without switching anyone's branch:

```sh
git -C <repo> fetch origin --quiet
git -C <repo> log -1 --format='%h %ci %s' <version-sha>          # what is running
git -C <repo> branch -r --contains <version-sha>                 # confirm it is on the deploy branch
git -C <repo> grep -n '<error text or symbol>' <sha> -- src/     # find the code as deployed
git -C <repo> show <sha>:path/to/file                            # read it as deployed
```

## 3. Triage loop

### 3.1 Frame it, confirm, then measure

Pin down four things. Work out a proposal from the request and the map, then
**confirm it with the user in one question** before running the measuring
queries: the proposed frame as the recommended option, plus the obvious
alternatives (a wider window, a different baseline, a narrower scope).

| | Usual proposal |
|---|---|
| Scope | service, route or host named by the user; else every service in the map |
| Window | "now" = last 1 h, "today" = since 00:00 in the map's timezone, "recently" = 24 h |
| Baseline | same window 7 days earlier (`--baseline 7d`) |
| Measure | latency = p95/p99, never avg; errors = rate and count; traffic = req/s |

Skip the question only when the user gave all four, or said to use the usual
frame. Ask once per triage; don't re-confirm each narrowing step.

Take exact metric names and thresholds from the map and from the monitor's own
query in the repo (read it at the deploy branch). Don't guess names.

Two calls are not measurements and don't depend on the frame, so run them
before asking and use the result to make the proposal better: alerting
monitors for our tags, and monitor transitions for the last 24 h. They give
the onset time for free.

### 3.2 Size it

- **How bad**: error rate and count against baseline; who is affected (route,
  host, locale, signed-in or not).
- **Since when**: narrow the onset to a few minutes by re-querying a tighter
  window. A step change points to a deploy or config change; a ramp points to
  load, a leak or a queue; a spike that self-heals points to an upstream blip
  or a cache event.
- **Where it stops**: group errors by `resource_name`, then `peer.service`,
  `@http.status_code`, `version`, host or replica, `@error.type`. The dimension
  where the errors concentrate is the lead; one where they spread evenly is ruled out.

### 3.3 Walk the layers

Follow the request path in the map, outermost layer first. Find the deepest
layer that is unhealthy; the layers above it are victims. Typically:

1. Edge / CDN: requests by status and host. 5xx at the edge with a healthy origin is an edge or platform problem.
2. Application: request errors by `resource_name`, then per-instance health and saturation.
3. Calls out: client-span errors by `peer.service`. A failing peer names the next system.
4. Backend: p95 and errors by `resource_name`; then cache, database and queue spans inside a slow trace.
5. Async: logs, then worker, function and pipeline-lag monitors.

### 3.4 Read exemplar traces

Pull 5 to 10 failing spans and open 2 or 3 traces with `trace`. Read the tree
for the first span that errors or the span that owns the time. Note its
`resource_name`, `operation_name`, error type and message, peer URL, status
and `version`. Then pull a healthy trace of the same route to see what differs.

### 3.5 What changed

Around the onset time, check each of these and say which you ruled out:

```sh
git -C <repo> log origin/<deploy branch> --since='<onset - 6h>' --until='<onset + 1h>' --format='%h %ci %s'
git -C <repo> diff --stat <prev-version-sha> <version-sha>       # the release that went out
git -C <repo> log -S'<symbol or string>' origin/<deploy branch> -5    # when the suspect line arrived
```

- **Release**: does the error start with a new `version` value? `spans-agg ... --by version` before and after.
- **Config**: environment variables, application config, edge/CDN settings, feature switches. Live config is the authority; a doc or note is not.
- **Upstream**: third-party and client-owned APIs, identity providers. Their monitors in the org are a quick check.
- **Traffic**: hits against baseline; bots or a crawl by user agent and path at the edge.
- **Content or data**: one page, one locale, one record. A publish, a purge storm or an index rebuild.

### 3.6 Tie it to code

For the failing span, find the code **at the deployed sha** (section 2):
`git grep` the error message or the route named by `resource_name`, follow the
call to the client that makes the peer request, and for slow SQL or cache
spans find the code that owns the table or cache key.

Read the function, its error handling and its callers. State the mechanism in
one sentence: *input or state X reaches line Y, which does Z, which produces
the observed span or status*. Then test it: the mechanism must predict
something you have not looked at yet (only signed-in users, only one locale,
only after cache expiry, only one instance). Query for that. If the prediction
fails, the hypothesis is wrong; go back to 3.2.

When two hypotheses fit equally and separating them is expensive (wide
queries, a reproduction), show both and ask which to chase first.

## 4. Traps

Read the map's **Traps** section before interpreting anything. These apply
almost everywhere:

- **Sampled spans are not a census.** If errors or slow requests are always
  kept and the rest are sampled, raw span counts over-represent errors, and
  percentiles from trace metrics read high. Rates come from the unsampled
  `hits`/`errors` metrics; find out which those are before quoting a rate.
- **Half a trace can be missing** when services sample independently.
- **Errors recorded on a span are not failed requests.** A span with
  `status:error` and HTTP 200 is noise until a user-visible effect is shown.
  Check the status code and RUM.
- **The status the client saw may not be the status the app returned.**
  Hosting platforms and CDNs substitute their own error pages.
- **Not every system ships logs.** No log results may mean no log pipeline.
- **Caches and circuit breakers hide outages** as stale content rather than errors.
- **Deploy windows produce expected blips**; check the pipeline time before
  calling it an incident.
- **An environment with no data proves nothing** if it doesn't send telemetry.

## 5. Verdict

Open with one status and a reason in a few words:

- 🟢 **Healthy**: within 10% of baseline, no monitor of ours alerting
- 🟡 **Watch**: 10 to 50% worse, a monitor in Warn, or a rising trend
- 🔴 **Act now**: more than 50% worse, an SLO burning, a monitor in Alert, users blocked

The percentages are a starting point; if the map or the user gives other
thresholds, use those. Judge against the SLO, not the percentage alone: a doubling from a tiny base
can still be inside budget. Read the target where the map says SLOs are
defined and say which side of it we are on.

Label the root cause honestly:

- **Confirmed**: mechanism found in deployed code, and a prediction from it checked out in data.
- **Likely**: evidence points one way, one link in the chain is unverified. Say which link and what would verify it.
- **Unknown**: say what was ruled out and what access or data is missing.

## 6. Report

Lead with the result. Terminal output, terse:

```
🔴 <service> <symptom> <number> (<× or Δ vs baseline>): <cause in a clause>, since <time and timezone>

Impact      <who, how many, which routes>            Window <…> · Baseline <…>
Root cause  <Confirmed|Likely|Unknown>: <mechanism in one or two sentences>
Evidence    1. <query result with number>            (trace <id>, monitor <id>)
            2. <code> repo/path/file:123 at <sha>
            3. <the prediction that was tested and its result>
Ruled out   <release / config / upstream / traffic, with the reason>
Do next     1. <concrete action: rollback to <sha> per <runbook> | fix in <file> | ask the owner of <API>>
            2. …
Not checked <anything skipped or unavailable>
```

Rules: round for humans (1.8 s, 2.4%, 1.2k); link the dashboard, monitor or
trace for every claim (`<app site>/apm/trace/<trace_id>`,
`<app site>/monitors/<id>`); name the runbook when one covers it; an action is
something a person can do today, never "investigate further".

End by asking what to do next, as numbered options: open a ticket, start a fix
branch, post to Slack, update the observability map, nothing. Do none of them
unasked.

## 7. Posting to Slack (only when asked)

- Ask for the channel if it wasn't named, and check its topic first. Show the
  draft and wait, unless the user named the channel **and** said to post.
- Send in the user's voice, with the `slack-send` skill if it is installed.
- The first line is the whole story, as it shows in notifications: `🔴 sign-in 5xx at 2.1% (7× last Thu): token refresh rejected by the auth gateway since 14:05 UTC`
- Then, skipping empty parts: a **Key numbers** table (Metric · Now · Last week · Δ with 🔺 worse / 🔻 better · Trend sparkline, which `dd.py metric` prints), **What it means** in one or two plain sentences, **Do next** as a numbered list, a links line, and `_Window … · Baseline … · Source: Datadog_`.
- Under 1,500 characters; detail goes in a thread reply. No ticket keys, PR numbers or internal names if the channel includes client staff. Mention an owner only on 🔴.
- A chart only when the shape matters (spike, step, drift): title it with the takeaway, baseline dashed grey, current solid, threshold line, deploy marker, the report timezone on the axis; upload to the same thread. If the upload fails, post the sparkline table instead; don't retry in a loop.
- Recurring reports: ask for the cadence and channel; one parent message, every run replies in that thread and ends with a parseable footer (`_run #14 · 2026-01-18 09:00 UTC · p95=420ms · err=0.9% · status=🟡_`); broadcast to the channel only on 🔴 or a worsening status.

## Before you answer

- [ ] The frame (scope, window, baseline, measure) was confirmed or given by the user
- [ ] Every number came from a query in this session, with window, unit and baseline
- [ ] Rates use unsampled metrics, not raw span counts
- [ ] Code was read at the deployed sha, not the local checkout
- [ ] The root cause label matches the evidence, and one prediction was tested
- [ ] What was ruled out and what was not checked are both stated
- [ ] No personal data, no secrets, nothing outside our ownership touched
