# Terraform & Infrastructure as Code

Terraform is the de facto standard for declarative, multi-cloud infrastructure
provisioning. It describes desired state in HCL (HashiCorp Configuration
Language), compares it to actual state in a backend, and applies the diff
through provider plugins.

## Core concepts

- **Providers** — plugins that translate Terraform resources to API calls
  for a specific platform (AWS, Azure, GCP, Kubernetes, Datadog, GitHub,
  Snowflake, etc.). Versioned independently of Terraform core.
- **Resources** — declarative units (`aws_s3_bucket`, `azurerm_storage_account`,
  `google_compute_instance`) that map to real infrastructure.
- **Data sources** — read-only lookups (`data "aws_ami"`) used to reference
  existing infrastructure or compute derived values.
- **Modules** — reusable, composable units of Terraform code. A module is just
  a directory with `.tf` files plus inputs (variables) and outputs.
- **State** — the source of truth Terraform compares against. Without state,
  every plan would diff against the world from scratch.
- **Plan** — the diff between desired and actual state.
- **Apply** — execution of the plan.

## State management

State is the single most important architectural concern in Terraform.

- **Local state** (`terraform.tfstate` on disk) — fine for solo experimentation,
  unsafe for any team or production scenario.
- **Remote state backends** — store state in S3 + DynamoDB (locking), Azure
  Storage + blob lease, GCS, Terraform Cloud / Enterprise, or HCP Terraform.
- **Locking** — prevents two `apply`s from racing. Must be enabled for any
  shared backend.
- **State encryption at rest** — required for production. Most cloud backends
  encrypt by default; verify.
- **State drift** — when the real world diverges from state (someone clicked
  in the console). `terraform refresh` detects drift; `terraform plan` shows
  it. Drift detection should be part of CI.
- **State surgery** — `terraform state mv`, `terraform state rm`,
  `terraform import` for moving resources between modules, removing
  resources from state without destroying them, or adopting existing
  infrastructure. Powerful and dangerous; always back up state first.

## Modules and composition

The most important architectural choice is *granularity*. Too small and you
end up assembling Lego bricks; too large and modules become un-reusable.

Common module taxonomy:

- **Primitive modules** — wrap a single resource with sensible defaults
  (`module.s3_bucket`, `module.kms_key`).
- **Service modules** — compose primitives into a working service
  (`module.web_app` = ALB + ECS + RDS + secrets + DNS).
- **Account / landing-zone modules** — wire up the scaffolding of a whole
  account (logging, IAM, networking baseline).

Module best practices:

- Pin module versions explicitly (Git tags, registry versions). Never use
  `master` or `main` in production.
- Inputs should have sensible defaults and clear types. Use `validation`
  blocks for guardrails.
- Outputs should be minimal — only what consumers actually need.
- Document the module's purpose, inputs, outputs, and usage in README.md
  next to the code.

## Workspaces and environment separation

- **CLI workspaces** — multiple named state files under one configuration.
  Reasonable for trivial dev/staging separation; widely considered an
  anti-pattern for production because all environments share the same code
  with implicit branching.
- **Directory-per-environment** — separate `envs/dev`, `envs/staging`,
  `envs/prod` directories, each with its own backend config. Explicit,
  auditable, the dominant pattern.
- **Workspace-per-stack** — Terragrunt, Spacelift, or Atlantis-style
  patterns where each "stack" gets its own state file.

## Drift detection and remediation

In a mature platform:

- **Scheduled drift detection** — nightly `terraform plan` job that fails
  loudly when drift is detected.
- **Auto-remediation** — for non-prod, auto-apply the plan back. For prod,
  open a ticket / PR.
- **Out-of-band change policy** — console changes should be forbidden by
  IAM policy, not just convention. Use SCPs in AWS, Azure Policy, or
  Organization Policies in GCP.

## Policy as code

Terraform code can pass `plan` while still violating compliance. Policy
engines enforce guardrails *before* `apply`:

- **OPA / Conftest** — open-source, uses Rego language. Works in any CI.
- **Sentinel** — HashiCorp's commercial policy engine, integrated into
  Terraform Cloud / Enterprise.
- **Checkov, tfsec, Terrascan, Trivy** — static analysis tools that flag
  known misconfigurations (open security groups, unencrypted buckets,
  IAM `*:*`, etc.). Run in pre-commit and CI.

Policy examples worth enforcing:

- All S3 buckets must have versioning + encryption.
- All resources must carry a `cost-center` and `owner` tag.
- No security group with `0.0.0.0/0` on port 22 or 3389.
- All RDS / databases must be in private subnets.
- AKS / EKS clusters must have audit logging enabled.

## Patterns to know

- **Remote state references** (`terraform_remote_state` data source) — let
  downstream stacks read outputs of upstream stacks. Common for shared
  networking referenced by app stacks.
- **for_each over count** — `for_each` is keyed by string and stable across
  reorders; `count` is positional and re-indexes destructively when items
  are removed.
- **Move blocks** (`moved { from = ... to = ... }`) — refactor module
  hierarchy without state surgery, introduced in Terraform 1.1.
- **Import blocks** — declarative imports introduced in 1.5, friendlier
  than `terraform import` for IaC adoption of existing resources.
- **Lifecycle meta-arguments** — `create_before_destroy`,
  `prevent_destroy`, `ignore_changes`. Each is a signal of an awkward
  resource lifecycle worth understanding.

## Terraform vs alternatives

| Tool | Strength | Watch out for |
|---|---|---|
| **Terraform** | Multi-cloud, mature, huge ecosystem | HCL is not a programming language; complex logic gets ugly |
| **OpenTofu** | Open-source fork of Terraform after BSL relicensing; drop-in compatible | Younger; some commercial integrations behind |
| **Pulumi** | Real programming languages (TS, Python, Go); strong loops/conditions | Smaller ecosystem; team must know a programming language |
| **AWS CDK** | Real code; tight AWS integration; constructs library | AWS-only; CDK→CloudFormation translation can surprise |
| **Crossplane** | Kubernetes-native; declarative API style | Different mental model; CRDs everywhere |
| **CloudFormation / ARM / Deployment Manager** | First-party | Single-cloud; verbose; weaker module story |

## Anti-patterns

- **One giant root module.** State files balloon, blast radius becomes
  uncontrollable, plans take 20 minutes.
- **Hardcoded secrets in tf files.** Use a secrets manager and `data`
  sources, or pass via environment variables to CI.
- **No CI gating of apply.** `apply` from a developer laptop with production
  credentials is a recipe for outages.
- **Mixing manually-managed and Terraform-managed resources** with no
  documentation of which is which.
- **Letting `count` resources drift due to list reordering** — switch to
  `for_each` keyed by stable identifiers.
- **Storing state in Git.** Never. State contains secrets and merge
  conflicts on state are not reconcilable.

## Glossary

- **HCL** — HashiCorp Configuration Language; Terraform's declarative syntax.
- **Backend** — where state is stored (S3, GCS, Azure Storage, Terraform Cloud).
- **Provider** — plugin that maps resources to a real API.
- **Module** — reusable bundle of Terraform code.
- **Plan** — the proposed diff.
- **Apply** — execution of a plan.
- **Drift** — divergence between state and the real world.
- **Workspace** — a named instance of state under one configuration.
- **Sentinel / OPA** — policy-as-code engines.
- **Terragrunt** — wrapper that adds composition, DRY config, and
  multi-stack orchestration on top of Terraform.
- **Move block** — Terraform construct that refactors state references
  declaratively.
