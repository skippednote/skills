#!/usr/bin/env python3
"""Read-only Datadog queries for triage. Prints compact tables; --out saves the raw JSON.

Configuration, all from the environment (nothing is hard-coded, keys are never printed):

  DD_SITE          API base URL, default https://api.datadoghq.com (EU: https://api.datadoghq.eu)
  DD_API_KEY       API key, or
  DD_API_KEY_REF   a 1Password reference (op://<vault>/<item>/<field>) read with `op read`
  DD_APP_KEY       application key, or
  DD_APP_KEY_REF   a 1Password reference
  OP_ACCOUNT       optional 1Password account for `op read --account`

  dd.py metric   'sum:trace.web.request.hits{service:<service>,env:prod}.as_count()' --from 4h --baseline 7d
  dd.py spans    'service:<service> env:prod status:error' --from 1h --limit 20
  dd.py spans-agg 'service:<service> env:prod status:error' --by resource_name --from 1h
  dd.py spans-agg 'service:<service> env:prod' --by resource_name --compute pc95:@duration
  dd.py trace    <trace_id> --from 6h
  dd.py logs     'service:<service> env:prod status:error' --from 1h
  dd.py logs-agg 'service:<service> env:prod status:error' --by @http.status_code
  dd.py monitors 'status:(alert OR warn)'
  dd.py events   'source:alert' --from 24h
  dd.py raw POST /api/v2/rum/events/search '{"filter":{"query":"@type:error service:<service> env:prod","from":"now-1h","to":"now"}}'

Times: 15m, 4h, 7d (ago), "now", or ISO 8601 (2026-01-18T09:00:00Z).
"""
import argparse, datetime as dt, json, os, re, subprocess, sys, urllib.error, urllib.parse, urllib.request

SITE = os.environ.get("DD_SITE", "https://api.datadoghq.com").rstrip("/")
BARS = "▁▂▃▄▅▆▇█"
UTC = dt.timezone.utc


def key(env):
    if os.environ.get(env):
        return os.environ[env]
    ref = os.environ.get(env + "_REF")
    if not ref:
        sys.exit(f"set {env}, or {env}_REF to a 1Password reference (op://vault/item/field)")
    account = os.environ.get("OP_ACCOUNT")
    r = subprocess.run(["op", "read", ref] + (["--account", account] if account else []), capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"cannot read {env} from 1Password: {r.stderr.strip()} (try: op signin)")
    return r.stdout.strip()


_headers = None


def call(method, path, body=None, params=None):
    global _headers
    if _headers is None:
        _headers = {"DD-API-KEY": key("DD_API_KEY"), "DD-APPLICATION-KEY": key("DD_APP_KEY"),
                    "Content-Type": "application/json"}
    url = SITE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=_headers, method=method), timeout=90) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Datadog {e.code} on {path}: {e.read().decode()[:600]}")


def when(s, now):
    if s == "now":
        return now
    m = re.fullmatch(r"(\d+)([smhdw])", s)
    if m:
        return now - dt.timedelta(seconds=int(m.group(1)) * {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}[m.group(2)])
    t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=UTC)


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def spark(vals, n=12):
    vals = [v for v in vals if v is not None]
    if not vals:
        return ""
    size = max(1, len(vals) // n)
    b = [sum(vals[i:i + size]) / len(vals[i:i + size]) for i in range(0, len(vals), size)][:n]
    lo, hi = min(b), max(b)
    return "".join(BARS[int((v - lo) / (hi - lo) * 7)] if hi > lo else BARS[0] for v in b)


def num(v):
    if v is None:
        return "-"
    a = abs(v)
    return f"{v/1e6:.2f}M" if a >= 1e6 else f"{v/1e3:.1f}k" if a >= 1e4 else f"{v:.0f}" if a >= 100 else f"{v:.2f}" if a >= 1 else f"{v:.4f}"


def series(query, t0, t1):
    d = call("GET", "/api/v1/query", params={"from": int(t0.timestamp()), "to": int(t1.timestamp()), "query": query})
    if d.get("status") == "error":
        sys.exit(f"metric query failed: {d.get('error')}")
    return d, {s.get("scope") or s.get("expression", "*"): [p[1] for p in s["pointlist"]] for s in d.get("series", [])}


def stat(v):
    v = [x for x in v if x is not None]
    return (min(v), sum(v) / len(v), max(v), v[-1], sum(v)) if v else (None,) * 5


def cmd_metric(a, t0, t1):
    raw, cur = series(a.query, t0, t1)
    out = {"current": raw}
    base = {}
    if a.baseline:
        shift = dt.datetime.now(UTC) - when(a.baseline, dt.datetime.now(UTC))
        out["baseline"], base = series(a.query, t0 - shift, t1 - shift)
    if not cur:
        print(f"no data for this query in {iso(t0)} to {iso(t1)}: check the metric and tag names")
    print("scope\tmin\tavg\tmax\tlast\tsum\ttrend" + ("\tbase avg\tbase max\tavg delta" if a.baseline else ""))
    for scope, v in sorted(cur.items()):
        lo, avg, hi, last, tot = stat(v)
        row = [scope, num(lo), num(avg), num(hi), num(last), num(tot), spark(v)]
        if a.baseline:
            _, bavg, bhi, _, _ = stat(base.get(scope, []))
            delta = f"{(avg - bavg) / bavg * 100:+.0f}%" if avg is not None and bavg else "-"
            row += [num(bavg), num(bhi), delta]
        print("\t".join(row))
    return out


def span_filter(a, t0, t1):
    return {"query": a.query, "from": iso(t0), "to": iso(t1)}


def flat(d, prefix=""):
    out = {}
    for k, v in (d or {}).items():
        if isinstance(v, dict):
            out.update(flat(v, prefix + k + "."))
        else:
            out[prefix + k] = v
    return out


def span_row(s):
    at = s.get("attributes", {})
    f = flat(at.get("attributes")) | flat(at.get("custom"))
    start, end = at.get("start_timestamp"), at.get("end_timestamp")
    ms = None
    if start and end:
        ms = (when(end, None) - when(start, None)).total_seconds() * 1000
    elif f.get("duration"):
        ms = f["duration"] / 1e6
    err = f.get("error.message") or f.get("error.msg") or f.get("exception.message") or ""
    return [start or "", at.get("service", ""), (at.get("resource_name") or "")[:70], str(f.get("http.status_code") or f.get("http.response.status_code") or ""),
            f"{ms:.0f}ms" if ms is not None else "", str(f.get("version") or f.get("service.version") or "")[:10], at.get("trace_id", ""), str(err)[:120]]


def cmd_spans(a, t0, t1):
    d = call("POST", "/api/v2/spans/events/search", {"data": {"type": "search_request", "attributes": {
        "filter": span_filter(a, t0, t1), "sort": "-timestamp", "page": {"limit": a.limit}}}})
    print("start\tservice\tresource\tstatus\tduration\tversion\ttrace_id\terror")
    for s in d.get("data", []):
        print("\t".join(span_row(s)))
    if not d.get("data"):
        print("no spans matched")
    return d


def cmd_trace(a, t0, t1):
    a.query = f"trace_id:{a.query}"
    d = call("POST", "/api/v2/spans/events/search", {"data": {"type": "search_request", "attributes": {
        "filter": span_filter(a, t0, t1), "sort": "timestamp", "page": {"limit": 1000}}}})
    spans = d.get("data", [])
    kids, by_id = {}, {}
    for s in spans:
        at = s["attributes"]
        by_id[at.get("span_id")] = s
        kids.setdefault(at.get("parent_id"), []).append(s)

    def walk(s, depth):
        r = span_row(s)
        op = s["attributes"].get("operation_name") or ""
        print(f"{'  ' * depth}{r[4]:>8}  {r[1]}  {op}  {r[2]}  {r[3]}  {r[7]}".rstrip())
        for c in kids.get(s["attributes"].get("span_id"), []):
            walk(c, depth + 1)

    roots = [s for s in spans if s["attributes"].get("parent_id") not in by_id]
    for s in roots:
        walk(s, 0)
    if not spans:
        print("no spans for this trace in the window: widen --from, or it was not sampled")
    return d


def compute(spec):
    agg, _, metric = spec.partition(":")
    c = {"aggregation": agg, "type": "total"}
    if metric:
        c["metric"] = metric
    return c


def cmd_spans_agg(a, t0, t1):
    d = call("POST", "/api/v2/spans/analytics/aggregate", {"data": {"type": "aggregate_request", "attributes": {
        "compute": [compute(a.compute)], "filter": span_filter(a, t0, t1),
        "group_by": [{"facet": a.by, "limit": a.limit, "sort": {"type": "measure", "order": "desc", "aggregation": compute(a.compute)["aggregation"],
                                                                 **({"metric": compute(a.compute)["metric"]} if ":" in a.compute else {})}}]}}})
    rows = [(b["attributes"]["compute"].get("c0"), "\t".join(str(v) for v in b["attributes"]["by"].values())) for b in d.get("data", [])]
    ns = a.compute.endswith("@duration")  # span durations are nanoseconds
    print(f"{a.compute}{' (ms)' if ns else ''}\t{a.by}")
    for c, k in sorted(rows, key=lambda r: -(r[0] or 0)):
        print(f"{num(c / 1e6 if ns and c is not None else c)}\t{k}")
    if not rows:
        print("no spans matched")
    return d


def cmd_logs(a, t0, t1):
    d = call("POST", "/api/v2/logs/events/search", {"filter": span_filter(a, t0, t1), "sort": "-timestamp", "page": {"limit": a.limit}})
    print("time\tservice\tstatus\thost\tmessage")
    for e in d.get("data", []):
        at = e["attributes"]
        print("\t".join([str(at.get("timestamp", "")), at.get("service", ""), at.get("status", ""), at.get("host", ""),
                         " ".join(str(at.get("message", "")).split())[:240]]))
    if not d.get("data"):
        print("no logs matched (check that this service ships logs to Datadog at all)")
    return d


def cmd_logs_agg(a, t0, t1):
    c = {"aggregation": a.compute.partition(":")[0], "type": "total"}
    if ":" in a.compute:
        c["metric"] = a.compute.partition(":")[2]
    d = call("POST", "/api/v2/logs/analytics/aggregate", {"compute": [c], "filter": span_filter(a, t0, t1),
                                                          "group_by": [{"facet": a.by, "limit": a.limit}]})
    rows = [(list(b.get("computes", {}).values())[0], "\t".join(str(v) for v in b.get("by", {}).values())) for b in d.get("data", {}).get("buckets", [])]
    print(f"{a.compute}\t{a.by}")
    for c0, k in sorted(rows, key=lambda r: -(r[0] or 0)):
        print(f"{num(c0)}\t{k}")
    if not rows:
        print("no logs matched")
    return d


def cmd_monitors(a, t0, t1):
    d = call("GET", "/api/v1/monitor/search", params={"query": a.query, "per_page": a.limit})
    print("status\tid\tname\ttags")
    for m in d.get("monitors", []):
        print("\t".join([m.get("status", ""), str(m.get("id")), m.get("name", ""), ",".join(m.get("tags", []))[:80]]))
    if not d.get("monitors"):
        print("no monitors matched")
    return d


def cmd_events(a, t0, t1):
    d = call("GET", "/api/v2/events", params={"filter[query]": a.query, "filter[from]": iso(t0), "filter[to]": iso(t1), "page[limit]": a.limit})
    print("time\ttitle\ttags")
    for e in d.get("data", []):
        at = e.get("attributes", {})
        inner = at.get("attributes", {})
        print("\t".join([str(at.get("timestamp", "")), str(inner.get("title") or at.get("message", ""))[:120], ",".join(at.get("tags", []))[:120]]))
    if not d.get("data"):
        print("no events matched")
    return d


def cmd_raw(a, t0, t1):
    method, path = a.query.upper(), a.rest[0]
    if method != "GET" and not re.search(r"/(search|aggregate|query|scalar|timeseries)(/|$|\?)", path):
        sys.exit("raw is read-only: non-GET calls are limited to search/aggregate/query endpoints")
    d = call(method, path, json.loads(a.rest[1]) if len(a.rest) > 1 else None)
    print(json.dumps(d, indent=1)[:6000])
    return d


CMDS = {"metric": cmd_metric, "spans": cmd_spans, "spans-agg": cmd_spans_agg, "trace": cmd_trace, "logs": cmd_logs,
        "logs-agg": cmd_logs_agg, "monitors": cmd_monitors, "events": cmd_events, "raw": cmd_raw}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=CMDS)
    p.add_argument("query", help="query, trace id, or HTTP method for raw")
    p.add_argument("rest", nargs="*", help="raw only: path and optional JSON body")
    p.add_argument("--from", dest="t0", default="1h")
    p.add_argument("--to", dest="t1", default="now")
    p.add_argument("--baseline", help="metric only: compare with the same window this long ago, e.g. 7d")
    p.add_argument("--by", default="resource_name", help="facet to group by (aggregates)")
    p.add_argument("--compute", default="count", help="count, or pc95:@duration, avg:@duration, cardinality:@usr.id")
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--out", help="save the raw JSON response here")
    a = p.parse_args()
    now = dt.datetime.now(UTC)
    d = CMDS[a.cmd](a, when(a.t0, now), when(a.t1, now))
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w") as f:
            json.dump(d, f)
        print(f"raw -> {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
