# FinOps & Cloud Cost Optimization

FinOps is the discipline of bringing financial accountability to the
variable spend model of cloud. It is not a tool category — it is an
organizational practice that gives engineering and finance a shared
language and shared accountability for cloud costs.

The FinOps Foundation defines six core principles:

1. **Teams need to collaborate.** Engineering, finance, product own
   cost together.
2. **Decisions are driven by business value of cloud.** Cost per unit
   of customer value, not absolute cost.
3. **Everyone takes ownership.** Engineers see and own their costs.
4. **FinOps data should be accessible and timely.** Daily, not monthly.
5. **A centralized team drives FinOps.** A small team enables the rest.
6. **Take advantage of the variable cost model.** Don't treat cloud
   like a data center.

## The FinOps lifecycle (three phases, continuous)

- **Inform.** Visibility into who is spending what, on what, why.
  Tagging, allocation, anomaly detection.
- **Optimize.** Right-size, commit to reservations, eliminate waste,
  modernize architectures for cost.
- **Operate.** Governance, automation, ongoing accountability.

Teams rotate through these phases continuously. No project ever
"finishes" the optimize phase.

## Cloud cost mental model

Cloud bills break into roughly:

- **Compute** — VMs, containers, serverless invocations, AI / GPU.
- **Storage** — block (EBS, Managed Disks, PD), object (S3, Blob, GCS),
  file (EFS, Azure Files, Filestore).
- **Network** — egress is the surprise category. Inter-AZ, inter-region,
  and internet egress are all priced differently and aggregate fast.
- **Managed services** — databases, queues, search, AI APIs.
- **Licensing** — Windows / SQL / Oracle on cloud, certain
  marketplace tools.

The 80/20 rule is real: compute + storage + a handful of managed
services typically account for 80%+ of spend.

## Pricing models (and how to use them)

- **On-demand** — no commitment, highest unit price. For unpredictable
  or short-lived workloads.
- **Reserved Instances / Savings Plans (AWS)** — 1-year or 3-year
  commits. 30–72% discount.
- **Compute Savings Plans** — flexible across instance family / region;
  recommended over EC2 RIs for most modern environments.
- **Reserved VM Instances / Azure Savings Plan / Azure Hybrid Benefit
  (Azure)** — analogous to AWS, plus on-prem Windows / SQL licensing
  reuse.
- **Committed Use Discounts (CUDs) / Flexible CUDs (GCP)** — comparable.
- **Spot / Preemptible / Spot VM** — 60–90% discount for interruptible
  workloads. Pair with retries and checkpointing.

Practical mix:

- Use **on-demand for the volatile baseline** you can't predict.
- Use **commits for the stable baseline** you know you'll consume.
- Use **spot for stateless, retry-safe workloads** (batch, async, ML
  training).

Target a **commit coverage** somewhere between 60–80% of your
predictable baseline — committing more than that leaves no room for
demand to fall.

## Right-sizing

The single highest-ROI lever for most organizations.

- **CPU and memory utilization** in production typically averages
  10–25% across organizations. Right-sizing to 50–70% utilization
  while preserving headroom is normal practice.
- **Recommendations** — AWS Compute Optimizer, Azure Advisor, GCP
  Active Assist all emit specific resize suggestions.
- **VPA (Vertical Pod Autoscaler) / Goldilocks** for Kubernetes.
- **Quarterly right-sizing reviews** for the long tail; daily anomaly
  detection for new launches.

## Storage levers

- **Lifecycle policies** — automatically move data through hot →
  warm → cold tiers (S3 Standard → IA → Glacier; Azure Hot → Cool →
  Archive; GCS Standard → Nearline → Coldline → Archive).
- **Intelligent tiering** — S3 Intelligent-Tiering, Azure Storage
  Reserved Capacity. Pay for the right tier automatically.
- **Snapshot hygiene** — old, orphaned snapshots accumulate silently.
  Lifecycle them.
- **Right-typing block storage** — gp3 vs gp2 (AWS), Premium SSD v2
  vs Premium SSD (Azure). The newer tiers are cheaper for the same
  performance.

## Network levers

- **Egress traps** — every dataset that flows out of the cloud is
  billable. Architect to keep data in. Use VPC endpoints / Private
  Endpoints / PSC to avoid public-internet egress where possible.
- **Same-AZ traffic** — free or near-free; cross-AZ adds up. Pin
  services to the same AZ where consistency tolerates it.
- **CDN offload** — CloudFront, Front Door, Cloud CDN dramatically
  reduce origin egress costs.
- **Direct Connect / ExpressRoute / Cloud Interconnect** — cheaper
  per-GB than public-internet egress at scale, with predictable
  latency.

## Kubernetes-specific cost levers

- **Karpenter or equivalent** — better bin-packing than Cluster
  Autoscaler. Real-world savings of 20–40% for large clusters.
- **Spot node pools** with appropriate tolerations and PDBs.
- **Right-sized resource requests** (not limits). Most clusters request
  3–5× what they use.
- **Cluster consolidation** — fewer larger clusters > more smaller
  clusters in most cases.
- **GPU sharing** — Multi-Instance GPU (MIG), time-slicing, fractional
  GPU schedulers for inference workloads.
- **Stop dev/staging on nights and weekends.** 30% of dollars saved
  in many shops.

## AI / GPU cost specifics

- **Inference vs training** are different beasts; price them
  separately.
- **Token economics for managed LLMs** — input vs output tokens,
  cached prompts, batch API discounts. Modern providers offer 50%+
  discounts for batch and cached input.
- **Self-hosted breakeven** — typical crossover where self-hosting an
  open-weight model on GPUs becomes cheaper than API calls is
  ~10–30M tokens/day, depending on model size and infrastructure.
- **Model size vs latency vs cost trade-off** — smaller / quantized
  models often deliver 80% of the quality at 20% of the cost.
- **GPU memory dominates GPU cost.** Quantization (4-bit, 8-bit) can
  4–8× your inference density on the same hardware.

## Tagging and allocation

The financial backbone of FinOps. Without consistent tagging, every
question is unanswerable.

Mandatory tags (enforce via policy):

- `environment` (dev / staging / prod)
- `cost-center` or `business-unit`
- `owner` (email or team)
- `application` / `service`
- `data-classification`

Tag policies should be enforced at creation, with automated alerts
on untagged resources. Most tools (Cloudability, Apptio, Anodot,
Vantage, native Cost Explorer) require tagging discipline to be
useful.

## Showback vs chargeback

- **Showback** — report costs back to teams; no money actually moves.
- **Chargeback** — actually allocate costs to team budgets / GLs.

Most organizations start with showback because chargeback requires
strong tagging hygiene first. Chargeback drives behavior change but
creates organizational friction; introduce it incrementally.

## Cost tooling categories

- **Cloud-native:** AWS Cost Explorer + Cost & Usage Report (CUR),
  Azure Cost Management, GCP Cloud Billing reports + BigQuery export.
- **Third-party visibility / optimization:** Cloudability (Apptio),
  Vantage, Anodot, ProsperOps (RI / SP automation), Spot.io
  (formerly Spotinst), CloudHealth (VMware), Densify.
- **Kubernetes cost:** Kubecost (now IBM), OpenCost (CNCF), Stormforge.
- **Anomaly detection:** native services or third-party (Vantage,
  Cloudability, etc.). Catches the 3× spike on day one, not in next
  month's bill.

## The architect's FinOps responsibilities

- **Design for unit economics** — every system should have a cost
  per business unit (per request, per active user, per GB processed)
  that's tracked over time.
- **Architectural cost reviews** — review proposed designs for
  cost trajectory before they're built, not after.
- **Right-defaults in landing zones** — lifecycle policies on by
  default, tagging enforced, basic budget alerts auto-provisioned.
- **Educate** — most engineering teams under-spend the effort on
  cost because they've never seen a bill. FinOps champions per team
  is the standard pattern.

## Anti-patterns

- **Cost as someone else's problem.** Engineering builds, finance
  pays; result is a bill nobody understands.
- **One-time "cost cleanups."** Cost optimization is continuous;
  one-time sprints recover savings that erode in months.
- **Aggressive commit purchases without forecasting.** Over-commit
  and you lock in cost above demand for years.
- **Tag-on-promise, not policy.** Voluntary tagging never works.
- **Cost dashboards no one looks at.** Surface cost data inside the
  tools engineers already use (Slack alerts, PR comments, CI gates).

## Glossary

- **FinOps** — cloud financial management practice.
- **Inform / Optimize / Operate** — the three phases of the FinOps
  lifecycle.
- **Showback vs Chargeback** — visibility vs actual cost transfer.
- **RI / Savings Plan / CUD** — commitment-based discount instruments.
- **Spot / Preemptible** — interruptible compute at deep discount.
- **Tagging / Allocation** — assigning cost to teams / services /
  environments.
- **Egress** — outbound network charges; the #1 surprise.
- **Right-sizing** — matching provisioned capacity to actual demand.
- **Unit economics** — cost per business activity (per request, per
  user).
- **Karpenter** — modern K8s autoscaler that improves bin-packing.
- **CUR / Cost Management / Billing Export** — the native cost-data
  exports for AWS / Azure / GCP.
- **ProsperOps / Spot.io / Cloudability / Vantage / Anodot / Kubecost** —
  the prominent third-party tools in the category.
