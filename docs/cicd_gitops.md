# CI/CD & GitOps

Continuous Integration and Continuous Delivery / Deployment are the
backbone of modern software delivery. GitOps is a specific evolution
of CD where Git is the single source of truth for system state, and
automated controllers continuously reconcile reality with that truth.

For an architect, the relevant decisions are not "which YAML format"
but **how to structure pipelines so teams ship safely at high velocity
without bypassing security and compliance**.

## CI vs CD vs Deployment

- **Continuous Integration (CI)** — every change to the main branch is
  built, tested, and validated automatically. Goal: integration is a
  cheap, frequent event, not a quarterly merge crisis.
- **Continuous Delivery** — every change that passes CI is *deployable*
  to production. A human still presses the button.
- **Continuous Deployment** — same as above, but the button is auto-
  pressed. Reserved for orgs with strong test, observability, and
  rollback discipline.

The lifecycle for an architect's purposes:

```
commit → build → unit/integration test → security/policy scan →
artifact → infra plan → human gate (if needed) → deploy → smoke test →
post-deploy verification → optional auto-rollback
```

## The major CI/CD platforms

| Platform | Strength | Watch out for |
|---|---|---|
| **GitHub Actions** | Tight GitHub integration, huge marketplace, OIDC to clouds | Reusable workflows still maturing; concurrency models are subtle |
| **Azure DevOps Pipelines** | Mature, enterprise-grade, strong Azure integration | YAML schema is its own dialect |
| **GitLab CI** | Built into GitLab; single-pane DevOps platform | Locking yourself to GitLab |
| **Jenkins** | Universal, every plugin ever | Operational burden; legacy patterns |
| **CircleCI / Buildkite / Travis** | Strong CI; weaker CD | Less integrated than GH Actions / ADO |
| **TeamCity** | JetBrains; powerful but heavy | Niche outside JVM shops |
| **AWS CodePipeline / CodeBuild** | Cloud-native AWS-only | Smaller ecosystem |

For most modern shops: **GitHub Actions for CI, ArgoCD or Flux for CD,
with cloud-specific deployment hooks** is the dominant pattern.

## Deployment strategies

Every strategy is a trade-off between **safety**, **speed**, and
**operational complexity**:

- **Recreate** — shut down old, start new. Simplest; downtime during cutover.
- **Rolling update** — replace pods/instances incrementally. Kubernetes
  default. Old and new versions run simultaneously during rollout.
- **Blue-Green** — two identical environments; switch the router to
  cut over. Fast rollback (switch back), but doubles infrastructure
  cost during the transition.
- **Canary** — gradually route a percentage of traffic to the new
  version (1% → 10% → 50% → 100%), monitoring metrics at each step.
  The standard for high-traffic, high-stakes services.
- **Progressive delivery** — canary + automated rollback when SLOs
  degrade. Argo Rollouts, Flagger.
- **Feature flags** — decouple deploy from release. Ship code dark,
  flip the flag when ready. LaunchDarkly, Unleash, GrowthBook, native
  cloud feature management.
- **Shadow / dark traffic** — copy production traffic to the new
  version without using its responses. Best for validating compute
  or model changes without user impact.

## Rollback strategies

Rollback is not "redeploy the previous artifact." It is a **first-class
runtime capability**:

- **Pin known-good versions** as immutable artifacts (container digests,
  not tags; Git SHAs, not `main`).
- **GitOps revert** — revert the commit, the controller reconciles.
- **Argo Rollouts / Flagger automatic rollback** — when error rate or
  latency violates SLOs, rollback fires without paging anyone.
- **Database migration rollback** — the hardest part. Forward-only
  migrations are simpler; if you must support rollback, every migration
  must have a paired down-migration with the same testing rigor.

## GitOps

GitOps codifies four principles (per OpenGitOps):

1. **Declarative.** The system is described declaratively.
2. **Versioned and immutable.** Desired state is stored in Git (or any
   versioned store).
3. **Pulled automatically.** Approved changes are pulled from the source
   of truth into the environment.
4. **Continuously reconciled.** The system actively converges to the
   desired state.

### Tools

- **ArgoCD** — pull-based, widely adopted, strong UI. Apps are
  Kubernetes-native Application CRDs.
- **Flux** — equally capable, more modular, smaller resource footprint;
  preferred when "less cluster overhead" matters.
- **Atlantis / Spacelift / env0 / Terraform Cloud** — GitOps for
  Terraform; PR-driven plan, approval-driven apply.
- **Crossplane** — extends GitOps to cloud resources via Kubernetes
  CRDs.

### Repository patterns

- **App-of-apps** (ArgoCD) — one root Application points to a Git path
  that contains all other Applications. Common, scales well.
- **ApplicationSets** (ArgoCD) — generators (list, cluster, Git
  directory, matrix) auto-create Applications for many targets.
- **Monorepo for platform config + polyrepo for app config** is a
  common compromise. Helm/Kustomize references compose them.

### Push vs pull

- **Push-based CD** — CI runs, pushes manifests/credentials into the
  cluster. Faster, but requires the CI to hold cluster credentials.
- **Pull-based CD** — GitOps; the cluster pulls and reconciles. CI
  never holds cluster credentials, which is a meaningful security win.

## Environment promotion

Common pattern: a manifest is built once and promoted through
environments by changing the *target*, not the artifact.

```
PR → dev (auto) → staging (auto after passing tests) → prod (gated)
```

- **Manifest builds in one place** (CI), promotion is a Git path
  change in the GitOps repo.
- **Approval gates** for production are explicit and audited.
- **Drift between environments** is visible by diffing the
  environment-specific overlays.

## Security in the pipeline (Shift Left)

Every modern pipeline must include:

- **Pre-commit hooks** — local secret scanning, formatting, basic
  linting.
- **Static analysis** — SonarQube, Semgrep, CodeQL.
- **Software Composition Analysis (SCA)** — Snyk, Dependabot,
  Renovate; scan dependencies for known CVEs.
- **Container scanning** — Trivy, Grype, Snyk; in registry and at
  admission.
- **IaC scanning** — Checkov, tfsec, Terrascan; flag misconfigurations
  before apply.
- **Secret scanning** — gitleaks, TruffleHog; in CI and in pre-commit.
- **Signed artifacts** — Cosign / Sigstore for container images, SLSA
  attestation for build provenance.
- **Policy checks** — OPA / Conftest / Sentinel against IaC plan or
  K8s manifests.
- **OIDC for cloud auth** — replace long-lived cloud keys with
  short-lived federation tokens (GitHub OIDC, ADO Workload Identity
  Federation).

## SBOM and supply-chain integrity

- **SBOM (Software Bill of Materials)** — manifest of every component
  in a build artifact (SPDX or CycloneDX format). Generated by `syft`,
  `cdxgen`, or native build tools.
- **SLSA** (Supply-chain Levels for Software Artifacts) — framework
  for attesting build provenance. Levels 1–4, with L3+ required for
  high-trust software.
- **Image signing** — Cosign signs containers; Sigstore Rekor logs
  signatures publicly.
- **Provenance attestations** — `in-toto` provenance docs prove what
  was built, from what source, by what builder, when.

## Observability of pipelines

- **DORA metrics** (DevOps Research and Assessment): deployment
  frequency, lead time for changes, change failure rate, mean time
  to restore. The most-cited delivery-health metrics.
- **Pipeline analytics** — Faros AI, Sleuth, Sleuth's competitor
  category; visualize DORA and pipeline bottlenecks.
- **Audit logs** — every build, deploy, and rollback recorded;
  searchable, retained.

## Anti-patterns

- **Snowflake builds** — running production deploys from someone's
  laptop. Banned.
- **Long-lived branches** — feature branches that live for weeks
  cause merge hell. Trunk-based development, feature flags, and
  short-lived branches are the modern norm.
- **Blue-green without database compatibility** — old and new versions
  must be able to read/write the same schema during the transition.
- **No rollback testing** — rollback procedures that have never been
  exercised will fail when you need them.
- **Manual approvals as the only safety net** — humans rubber-stamp;
  invest in automated checks first.
- **"Just push to prod" hotfix culture** — every emergency change
  should still go through the same pipeline; speed it up rather than
  bypass it.

## Glossary

- **CI** — Continuous Integration.
- **CD** — Continuous Delivery (manual gate) or Deployment (no gate).
- **GitOps** — Git as the source of truth for system state.
- **Rolling / Blue-Green / Canary** — deployment strategies.
- **Progressive delivery** — canary + automated rollback.
- **Feature flag** — runtime switch decoupling deploy from release.
- **OIDC** — OpenID Connect; basis for short-lived cloud federation.
- **SLSA** — Supply-chain Levels for Software Artifacts.
- **SBOM** — Software Bill of Materials.
- **DORA metrics** — deployment frequency, lead time, change failure
  rate, MTTR. The standard delivery-health metrics.
- **ArgoCD / Flux** — leading GitOps controllers for Kubernetes.
- **OPA / Conftest / Sentinel** — policy-as-code engines.
- **Sigstore / Cosign / Rekor** — open-source supply-chain signing
  ecosystem.
- **Trunk-based development** — short-lived branches, frequent merges
  to main, feature flags for incomplete features.
