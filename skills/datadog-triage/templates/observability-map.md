# Observability map: <engagement>

Read by the `datadog-triage` skill. Everything here is specific to this
estate; keep it current, and date anything that can change. No secret values.

Last checked: <YYYY-MM-DD>

## Signal → repo → deployed code

| Datadog service (env) | What | Repo | Deploy branch | `version` tag | Monitors as code | Runbooks |
|---|---|---|---|---|---|---|
| `<service>` (`env:prod`) | <app and where it runs> | `<path>` | `<branch>` | <commit sha / release / none> | `<path>` | `<path>` |

RUM applications, synthetic tests and custom metric prefixes:

- <name → what it covers>

## Ownership

Which monitors, services and tags are ours (e.g. a `managed_by:` or `team:`
tag), and which belong to someone else in the same Datadog org and must not
be touched.

## Request path

The layers a request crosses, outermost first, and the metric that shows each
layer's health:

1. <edge / CDN> — `<metric>` by <tag>
2. <application> — `<metric>` by `resource_name`
3. <calls out> — `<metric>` by `peer.service`
4. <backend / data> — …

## Metrics that matter

| Question | Metric / query | Notes |
|---|---|---|
| Request rate and errors | `<metric>` | <sampled or not> |
| Latency | `<metric>` | |
| Capacity / saturation | `<metric>` | |

SLO definitions: `<path>`.

## Environments

Which environments send telemetry, and which are empty by design.

## Defaults

| | Value |
|---|---|
| Timezone for reports | <e.g. UTC> |
| "today" starts at | <00:00 in that timezone> |
| Usual baseline | <same window 7 days earlier> |
| Incident channel | <name, or none> |

## Traps

Things that make a naive reading of this estate's data wrong. One bullet each,
with how to read it correctly:

- **Sampling:** <which spans are kept and at what rate; what that does to raw
  counts and percentiles; which metrics are unsampled>
- **Missing signals:** <systems with no logs / no traces in Datadog and where
  to look instead>
- **Platform behaviour:** <error pages substituted by the host, caches that
  serve stale content, circuit breakers>
- **Expected noise:** <monitors muted during deploys, known benign span errors>
- **Delays:** <metrics that arrive late or in batches>
