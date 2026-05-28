# Multi-Cloud Landing Zones

A landing zone is the foundational set of accounts, policies, networks,
identity, logging, and guardrails that every workload deployed in a
cloud is expected to inherit. Building it well is the difference between
"each team builds their own AWS account from scratch" and "every new
workload starts compliant, observable, and connected."

## Why landing zones exist

Without one, organizations end up with:

- Snowflake accounts/subscriptions with inconsistent security baselines.
- Inability to enforce policy centrally — every team configures CIS
  benchmarks (or fails to) independently.
- Bespoke networking, IAM, and logging in every account.
- No clear blast-radius separation between teams or environments.
- Audit findings every quarter.

A landing zone replaces this with **opinionated, automated scaffolding**
that every new account / subscription / project gets by default.

## The reference architectures

### AWS — Control Tower & AWS Organizations

- **AWS Organizations** — hierarchical management of multiple AWS
  accounts; root → Organizational Units (OUs) → accounts.
- **AWS Control Tower** — opinionated landing zone built on top of
  Organizations. Bakes in management account, log archive account,
  audit account, plus guardrails (preventive via SCPs, detective via
  AWS Config).
- **AWS Landing Zone Accelerator (LZA)** — newer, more flexible
  open-source implementation; favored for complex compliance regimes
  (FedRAMP, IL5).
- **Account vending** — Control Tower's Account Factory or LZA
  templates auto-create new accounts that inherit baselines.

### Azure — Cloud Adoption Framework & Azure Landing Zones (ALZ)

- **Management group hierarchy** — Root → Tenant Root → "Platform"
  (identity, management, connectivity, sandbox) and "Landing Zones"
  (corp, online).
- **Azure Policy** — preventive and detective controls; Policy
  Initiatives bundle policies (NIST 800-53, CIS, ISO).
- **Azure Lighthouse** — multi-tenant management, common in MSPs.
- **Bicep templates and Terraform modules** — Microsoft publishes
  reference ALZ implementations in both.

### GCP — Cloud Foundation Fabric & Setup Checklist

- **Organization → Folders → Projects** — three-level hierarchy; Folders
  group projects by environment/business unit.
- **Organization Policies** — preventive guardrails (e.g. restrict
  resource locations, require shielded VMs, prohibit external IPs).
- **Cloud Foundation Fabric** — Google's reference Terraform landing-zone
  modules.
- **Resource Manager** — controls who can do what at each level.

## Core building blocks

Every mature landing zone has these regardless of cloud:

### 1. Account / subscription / project structure

Common pattern:

```
Org root
├── platform/
│   ├── management        (CI/CD, billing, IaC pipelines)
│   ├── log-archive       (centralized immutable logs)
│   ├── security          (SIEM, audit, threat detection)
│   ├── network-hub       (transit gateway / hub VNet / Shared VPC host)
│   └── identity          (Entra ID / Workspaces / federation)
├── workloads/
│   ├── dev/<account-per-team-or-app>
│   ├── staging/<account-per-team-or-app>
│   └── prod/<account-per-team-or-app>
└── sandbox/
    └── <ephemeral / personal>
```

### 2. Identity and access

- **Centralized IdP** — Okta, Azure Entra ID, Google Workspace, AWS
  Identity Center. SSO and federation push identity to the cloud, not
  the other way around.
- **Just-in-time (JIT) access** — temporary elevation for production
  via tools like AWS IAM Identity Center, Entra ID PIM, or
  ConductorOne / Sym.
- **Service identities** — workload identity federation (no static
  keys); break-glass accounts in a vault.
- **MFA** required everywhere, FIDO2 / hardware tokens preferred over
  TOTP for admins.

### 3. Networking

- **Hub-and-spoke topology** — central transit VPC/VNet houses shared
  services (firewall, DNS, observability). Spokes (workload VPCs/VNets)
  peer to the hub.
- **Transit Gateway / vWAN / Network Connectivity Center** — scalable
  inter-VPC routing on AWS / Azure / GCP respectively.
- **Private connectivity to SaaS** — VPC endpoints (AWS), Private
  Endpoint (Azure), Private Service Connect (GCP).
- **DNS** — private hosted zones / Private DNS / Cloud DNS, peered
  through the hub.
- **Egress control** — central NAT, central proxy, or third-party
  firewall in the hub; egress should never go directly from a workload
  account to the internet without inspection in regulated environments.

### 4. Logging and audit

- **Central log archive** — every account ships audit logs (CloudTrail,
  Activity Log, Cloud Audit Logs) to an immutable bucket / storage
  account / GCS bucket in a dedicated, tightly-controlled account.
- **Retention** — typically 1–7 years for audit, longer for regulated
  industries.
- **Log integrity** — object lock / WORM storage; protect from deletion
  by the workload teams that produced them.
- **Centralized SIEM** — Sentinel / Chronicle / Splunk / Sumo / Datadog
  reads from the log archive.

### 5. Guardrails (policy as code)

- **Preventive** — Service Control Policies (AWS), Azure Policy assign
  with `deny` effect, GCP Organization Policy. Block forbidden actions
  before they happen.
- **Detective** — AWS Config rules, Azure Policy `audit` effect, GCP
  Security Command Center, Open Policy Agent. Find drift and report.
- **Tagging policy** — required tags (`environment`, `cost-center`,
  `owner`, `data-classification`); enforced at creation.

### 6. Workload identity for AI / data platforms

- **AI workloads** — give pods / functions identities that can read
  specific catalogs, models, and storage paths without static keys.
- **Cross-account / cross-cloud access** — federation tokens, not
  shared access keys; OIDC trust between clouds.

## Multi-cloud realities

Real "multi-cloud" rarely means each workload runs on all three clouds.
Usually it means:

- Different business units on different clouds (legacy).
- Specific services chosen for their best-of-breed home (BigQuery on
  GCP, Cognitive Services / Foundry on Azure, SageMaker on AWS).
- Disaster recovery into a different cloud.
- M&A — you inherited what you inherited.

The architect's job is to make multi-cloud **bearable**, not "seamless."
Seamless multi-cloud is an over-promise. Realistic goals:

- Identity federation across clouds via a central IdP.
- Common observability and SIEM (one pane of glass).
- Common IaC patterns and module taxonomy (Terraform shines here).
- Cost rollup across clouds (Anodot, Cloudability, Apptio, native cost
  exports to a central warehouse).
- One CI/CD platform that targets all three.

## Common interview-worthy patterns

- **Account vending machine** — pipeline that creates a new account
  with baseline IAM, networking, logging, and guardrails on every
  request. Reduces account creation from days to minutes.
- **Hub-and-spoke with shared egress** — central NAT and inspection;
  audit-friendly egress.
- **PrivateLink everywhere** — workloads consume cloud services via
  private endpoints, never the public internet.
- **Service catalog / blueprint / Cloud Foundation Toolkit** — pre-
  approved patterns teams pick from, reducing toil and ensuring
  consistency.
- **CI/CD-driven IaC** — landing zone changes flow through PRs and
  policy-checked pipelines, not console clicks.

## Anti-patterns

- **One giant account / subscription** with everything in it. Loses
  blast-radius separation, makes IAM impossible.
- **Networking decided per workload.** Every team builds a VPC its own
  way; later integration is excruciating.
- **Logs in the same account as the workloads producing them.** A
  compromised workload can erase its own evidence.
- **"We'll add the guardrails later."** It is exponentially harder
  after teams have deployed than before.
- **Hand-managed identity providers.** Federation should be IaC-managed
  and reviewed.

## Glossary

- **Landing zone** — opinionated baseline for new accounts/subscriptions.
- **Control Tower / Azure Landing Zones / Cloud Foundation Fabric** —
  the three clouds' reference implementations.
- **Account / subscription / project** — the unit of isolation in
  AWS / Azure / GCP.
- **Organization / management group / folder** — hierarchical containers.
- **SCP / Azure Policy / Organization Policy** — preventive guardrails.
- **Hub-and-spoke** — network topology with shared services in the hub.
- **Transit Gateway / vWAN / NCC** — scalable inter-network routing.
- **VPC endpoint / Private Endpoint / PSC** — private access to managed
  services.
- **Workload identity federation** — pods/functions get cloud creds via
  short-lived federation tokens.
- **Account vending** — automated account creation with baselines.
- **WORM** — write-once-read-many; for tamper-evident logs.
- **SIEM** — Security Information and Event Management; central log
  analysis platform.
