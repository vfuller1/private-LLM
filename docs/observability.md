# Observability

Observability is the property of a system that lets you infer its
internal state from its external outputs. Practically, it is the
discipline of instrumenting systems so engineers can answer arbitrary
operational questions without re-deploying — including questions
nobody anticipated when the code was written.

The shorthand: **monitoring** tells you something is wrong;
**observability** tells you *why*.

## The three pillars (and the fourth)

Originally articulated by Cindy Sridharan and codified by the CNCF:

1. **Metrics** — numeric time-series, cheap to store, aggregated.
   Used for dashboards, alerts, SLO tracking.
2. **Logs** — discrete events with context, expensive to store at scale.
   Used for forensic investigation.
3. **Traces** — request-level views across services, showing causality
   and latency contribution.

A widely-acknowledged fourth pillar:

4. **Events / Profiles** — significant state changes (deploys, feature
   flag flips, scaling actions) and continuous profiling (CPU/memory/
   allocation flame graphs from prod). Often the missing context that
   turns an incident from "we don't know" into "the deploy at 10:42
   did it."

## OpenTelemetry (OTel)

The CNCF standard for instrumentation. Critical to understand because
it removes vendor lock-in from the instrumentation layer:

- **Specs and SDKs** — define APIs for metrics, traces, logs across
  every major language.
- **Collector** — vendor-neutral agent that receives, processes, and
  exports telemetry. Sits between your apps and your backend.
- **Auto-instrumentation** — agents that instrument popular frameworks
  with no code changes (JVM bytecode injection, Python wrappers,
  Node.js loaders).
- **Semantic conventions** — standardized attribute names
  (`service.name`, `http.request.method`, `db.system`) so dashboards
  and queries are portable.

The architect's takeaway: **instrument with OpenTelemetry, choose the
backend separately, and swap backends without re-instrumenting**.

## SLI / SLO / SLA / Error Budget

The Google SRE vocabulary that has become standard:

- **SLI (Service Level Indicator)** — a quantitative measure of service
  health (e.g. "fraction of HTTP requests that complete in < 500 ms
  with a 2xx status").
- **SLO (Service Level Objective)** — the target for an SLI over time
  (e.g. "99.9% of requests meet the SLI over a 28-day window").
- **SLA (Service Level Agreement)** — the contractual version of an SLO
  with consequences for breach (refunds, credits).
- **Error budget** — `1 - SLO`. The acceptable amount of failure. If
  your SLO is 99.9% and your error budget is half-burned at the 14-day
  mark, you stop shipping risky changes until it recovers.

Practical patterns:

- **Multi-window, multi-burn-rate alerts** — alert when the error
  budget would be exhausted within both a short window (fast burn) and
  a long window (chronic burn). Reduces alert noise dramatically.
- **Tier services** by criticality: customer-facing prod (99.9%),
  internal critical (99.5%), batch / dev (99%). Don't gold-plate.
- **Error budget policies** — pre-agreed rules for what changes when
  budget is burned (freeze deploys, switch to reliability work, page
  more aggressively).

## RED, USE, and Golden Signals

Frameworks for picking which metrics to instrument:

- **RED** (Tom Wilkie) — Rate, Errors, Duration. For request-driven
  services. The simplest, most universally applicable.
- **USE** (Brendan Gregg) — Utilization, Saturation, Errors. For
  resource-level monitoring (CPU, disk, network, queues).
- **Four Golden Signals** (Google SRE book) — Latency, Traffic, Errors,
  Saturation.

For most app services, RED metrics + SLOs are enough. USE applies
beneath the app layer.

## Tracing and context propagation

Distributed traces require **context propagation**: a unique trace ID
(and span ID) travels with every request through every service.

- **W3C Trace Context** — the standard header format
  (`traceparent`, `tracestate`).
- **Span** — a single operation; has a name, attributes, timing,
  status, and zero or more child spans.
- **Sampling** — at high volume, you can't trace every request.
  - *Head-based* — decision made at the start of the request; cheap
    but may miss interesting requests.
  - *Tail-based* — decision made after the trace completes; expensive
    but catches errors and slow outliers.
- **Critical paths** — once spans are in your backend, "tail latency
  due to which downstream call?" becomes a one-query answer.

## Logs

- **Structured logging** — JSON or key-value, not free text. Lets you
  query, filter, alert.
- **Log levels** — DEBUG, INFO, WARN, ERROR, FATAL. Production
  default INFO; everything below filtered.
- **Correlation IDs** — every log line carries the trace ID; you can
  pivot from trace → logs → metrics.
- **PII / secrets in logs** — the #1 source of incident-induced data
  breaches. Use structured logging libraries with PII redaction;
  audit regularly.
- **Cost** — logs are the most expensive telemetry per byte. Tier:
  hot in the SIEM for 30 days, cold in object storage for years.

## Datadog

The dominant commercial APM/observability platform; named in many
enterprise resumes:

- **Unified platform** — metrics, traces, logs, RUM, synthetics,
  security, profiling in one product. One of the only vendors with
  this breadth.
- **Agent-based** — Datadog Agent runs on hosts/containers, ships
  telemetry to Datadog's backend.
- **Integrations** — 700+ pre-built integrations; AWS / Azure / GCP /
  Kubernetes are first-class.
- **APM and Distributed Tracing** — auto-instrumentation for major
  languages; OpenTelemetry-compatible.
- **Watchdog** — automatic anomaly detection across metrics, traces,
  logs.
- **DDSL** — query language; learn it.
- **Workspaces / monitors / dashboards** — the three primary objects.

Datadog patterns worth knowing:

- **Tag everything consistently** — `env`, `service`, `version`,
  `team`, `cost-center`. Without these, every dashboard is a custom
  query.
- **Service catalog** — Datadog's service definitions auto-discover
  ownership, dependencies, and SLOs.
- **Monitor groups and downstream notifications** — group alerts by
  service / environment to control paging.

## Other major backends

- **Grafana stack** — Prometheus (metrics), Loki (logs), Tempo
  (traces), Pyroscope (profiles), Mimir (long-term metrics). Strong
  open-source story.
- **New Relic** — comparable to Datadog; different pricing model.
- **Honeycomb** — pioneered high-cardinality observability; trace-first
  approach.
- **Splunk** — historically log-heavy; observability cloud since
  acquisition by Cisco.
- **Lightstep / ServiceNow Cloud Observability** — distributed-tracing-
  first.
- **Cloud-native** — CloudWatch + X-Ray (AWS), Azure Monitor +
  Application Insights, Cloud Operations Suite (GCP).

## Cardinality and cost control

The hardest part of observability at scale: **high-cardinality fields
explode storage and query cost**.

- Avoid attribute labels with unbounded values (user IDs, request IDs)
  in metrics; that's what traces and logs are for.
- Use exemplars to link metrics back to representative traces.
- Apply head-based sampling for ingest cost control, tail-based for
  insight retention.
- Roll up / down-sample old data; long-retention storage shouldn't
  be at full fidelity.

## Synthetic monitoring and Real User Monitoring (RUM)

- **Synthetics** — scripted checks that run from external probes.
  Detect end-to-end issues from a user's perspective.
- **RUM** — instrumentation in the browser (or mobile app) that
  captures real user sessions, page loads, errors. Crucial for
  customer-experience SLOs.

## Incident response and chaos engineering

Observability is the prerequisite for both:

- **Runbooks** — every alert links to a runbook with first steps.
- **Postmortems** — blameless, with a clear timeline, root cause
  analysis, and action items.
- **Chaos engineering** — controlled failure injection (Gremlin,
  Chaos Mesh, AWS Fault Injection Service) to verify the system
  behaves as expected under failure.

## Anti-patterns

- **Dashboard sprawl.** 200 dashboards no one looks at; 5 nobody can
  find. Curate.
- **Alert noise.** If pages are routine, paging is broken. Drive every
  alert to actionable; delete the rest.
- **No correlation between traces, logs, and metrics.** Without
  consistent IDs and tags, the three pillars are three silos.
- **Per-team observability stacks.** Cost balloons, comparison across
  services is impossible, on-call hand-off is painful.
- **No SLOs.** "Make it faster" is not a goal; "p99 latency under 200ms"
  is.

## Glossary

- **SLI / SLO / SLA** — Indicator / Objective / Agreement.
- **Error budget** — `1 - SLO`; the amount of failure allowed.
- **RED / USE / Golden Signals** — metric selection frameworks.
- **OpenTelemetry (OTel)** — CNCF standard for instrumentation.
- **Span / Trace** — unit of work / collection of spans for one request.
- **W3C Trace Context** — standard trace propagation headers.
- **Sampling** — head-based vs tail-based.
- **Structured logging** — machine-readable log format.
- **Cardinality** — number of distinct values for a metric label.
- **Exemplar** — link from a metric data point to a specific trace.
- **RUM** — Real User Monitoring (browser/mobile).
- **Synthetic** — scripted external probes.
- **APM** — Application Performance Monitoring.
- **MTTR / MTBF / MTTA** — Mean Time To Repair / Between Failures / To
  Acknowledge.
- **DORA metrics** — deployment frequency, lead time, change failure
  rate, MTTR.
- **Chaos engineering** — controlled failure injection.
- **Runbook** — documented incident-response procedure.
