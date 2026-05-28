# Cloud Security & Zero Trust

Cloud security is no longer about perimeter defenses. The perimeter is
gone — workloads run in someone else's data center, users connect from
anywhere, services talk to each other across cloud and SaaS boundaries.
Modern enterprise security architecture is built on **Zero Trust**:
verify every request, regardless of origin, against identity, device,
context, and policy.

## The Zero Trust mental model

Originating from John Kindervag's 2010 work at Forrester and formalized
in NIST SP 800-207 (2020), Zero Trust rests on three principles:

1. **Never trust, always verify.** Every request is authenticated and
   authorized, including east-west traffic inside a network.
2. **Assume breach.** Design as if attackers are already inside;
   minimize blast radius.
3. **Least privilege per request.** Grant the minimum access needed
   for this specific action, for the shortest time.

Implementation pillars (per NIST and CISA's Zero Trust Maturity Model):

- **Identity** — strong authentication, MFA, conditional access.
- **Devices** — health and posture verification.
- **Networks** — micro-segmentation, encryption in transit.
- **Applications** — least-privilege access, secure by default.
- **Data** — classification, encryption, access governance.

Three cross-cutting layers: **visibility & analytics**, **automation &
orchestration**, **governance**.

## Identity and Access Management (IAM)

The most consequential control plane. Everything else is built on top.

### Principles

- **Identity is the new perimeter** — control of identity = control of
  the cloud.
- **Federation over local accounts** — use a single source of truth
  (Entra ID / Okta / Workspaces) and federate to cloud IAM.
- **Least privilege** — start from zero, grant the specific actions
  needed, on the specific resources, for the specific time.
- **Just-in-time (JIT) elevation** — temporary privileged access
  granted on request with approval and logging.
- **Break-glass accounts** — emergency-only, vaulted credentials,
  alerting on any use.

### IAM primitives across clouds

| Concept | AWS | Azure | GCP |
|---|---|---|---|
| Users | IAM users / Identity Center users | Entra ID users | Workspace users |
| Service identities | IAM roles | Managed identities / service principals | Service accounts |
| Workload identity | IRSA / EKS Pod Identity | Workload Identity | Workload Identity Federation |
| Authorization | IAM policies (JSON) | Azure RBAC + Custom Roles | IAM bindings |
| Boundary control | Service Control Policies (SCPs) | Azure Policy | Organization Policies |

### Common pitfalls

- **Wildcards in policies** (`"Action": "*", "Resource": "*"`) — most
  common cause of catastrophic IAM mistakes.
- **Long-lived access keys** — should be replaced with federated
  short-lived credentials.
- **Owner / Global Admin sprawl** — these roles should be vanishingly
  rare; PIM-style JIT for any privileged action.
- **Confused deputy** — service A is tricked into performing actions
  on behalf of attacker via service B's permissions. Mitigated with
  resource conditions (`aws:SourceArn`, `iam.GoogleResource`).

## RBAC vs ABAC vs ReBAC

- **RBAC (Role-Based Access Control)** — users get roles, roles have
  permissions. Simple, dominant in cloud IAM today.
- **ABAC (Attribute-Based Access Control)** — decisions based on
  attributes of user, resource, and environment (tags, time, location).
  More flexible, harder to reason about. AWS supports it via tag-based
  conditions; Entra ID has growing support.
- **ReBAC (Relationship-Based Access Control)** — used by Google's
  Zanzibar, OpenFGA, AuthZed; models permissions as a graph of
  relationships. Best for "X is the owner of doc Y" / "Y is a child of
  folder Z" semantics.

Most enterprises use RBAC as the baseline with selective ABAC for
tag-driven separations (cost-center, data-classification).

## Secrets management

- **The unbreakable rule:** never commit secrets to Git. Pre-commit
  hooks (`gitleaks`, `detect-secrets`) and CI scans (TruffleHog) are
  baseline.
- **Cloud-native vaults** — AWS Secrets Manager, Azure Key Vault, Google
  Secret Manager. All support rotation, access policies, audit.
- **HashiCorp Vault** — multi-cloud, dynamic secrets (generate creds
  on demand), strong leasing model. Enterprise-grade alternative.
- **External Secrets Operator** — bridges cloud vaults to Kubernetes
  `Secret` objects without checking secrets into Git.
- **Sealed Secrets / SOPS** — encrypted secrets in Git, decrypted at
  apply time. Acceptable for low-sensitivity config; not for tokens.

## Encryption

- **In transit:** TLS 1.2+ everywhere, mTLS for service-to-service in
  zero-trust networks (service mesh provides this).
- **At rest:** all storage, databases, queues should be encrypted by
  default. Most clouds enable this without ask.
- **Key management:** customer-managed keys (CMK) for sensitive
  workloads — AWS KMS, Azure Key Vault, GCP KMS / Cloud HSM. BYOK
  (Bring Your Own Key) for regulated environments.
- **Envelope encryption** — KMS encrypts data keys, data keys encrypt
  data. Allows key rotation without re-encrypting everything.

## Network security

- **Private subnets by default** — workloads should not have public
  IPs unless explicitly required.
- **Security groups / NSGs / VPC firewalls** — stateful filtering at
  the resource level.
- **WAF + DDoS protection** — for any public-facing endpoint
  (CloudFront + Shield + WAF; Front Door + WAF; Cloud Armor).
- **Micro-segmentation** — service mesh (Istio, Linkerd, Cilium) or
  Network Policies in Kubernetes; flat networks are a thing of the
  past in mature shops.
- **Egress control** — central proxy or NAT with inspection; deny by
  default, allow-list known destinations. Particularly important for
  AI workloads to prevent data exfiltration via outbound calls.
- **Private connectivity to SaaS** — VPC endpoints (AWS), Private
  Endpoints (Azure), Private Service Connect (GCP) keep traffic off
  the public internet.

## Detection, response, and audit

- **SIEM** — Sentinel, Chronicle, Splunk, Sumo, Datadog; central log
  analysis.
- **CSPM** (Cloud Security Posture Management) — Wiz, Prisma, Orca,
  Defender for Cloud, Security Command Center; continuously scan for
  misconfigurations.
- **CNAPP** (Cloud-Native Application Protection Platform) — CSPM +
  workload protection + image scanning + IaC scanning in one platform.
- **CIEM** (Cloud Infrastructure Entitlement Management) — analyzes
  IAM for over-privileged identities.
- **EDR / XDR** — endpoint detection on hosts that still exist.
- **Runtime threat detection** — Falco, Sysdig, AWS GuardDuty, Defender
  for Containers; behavioral anomaly detection on workloads.
- **Audit logging** — every API call captured (CloudTrail / Activity Log /
  Cloud Audit Logs), shipped to immutable storage, retained for years.

## AI-specific security risks

The AI security category has its own emerging threat model:

- **Prompt injection** — attacker-controlled input overrides the model's
  instructions. Mitigations: input sanitization, structured prompts,
  output validation, isolated tool execution.
- **Indirect prompt injection** — malicious instructions hidden in
  documents the model retrieves. Particularly dangerous with agents
  that have tool access.
- **Data leakage / training-data extraction** — model regurgitates
  memorized PII. Mitigations: data minimization, deduplication,
  differential privacy, output filters.
- **Model theft** — adversary reconstructs the model via API queries.
  Mitigations: rate limiting, watermarking, query monitoring.
- **Supply-chain risk** — vulnerabilities introduced via base models,
  embeddings, third-party datasets. Mitigations: model bill of
  materials (MBOM), provenance tracking.
- **Autonomy / over-action risk** — agents take consequential actions
  without adequate oversight. Mitigations: action-level approval,
  sandboxing, kill switches, principle of least privilege for tool
  access.

OWASP's Top 10 for LLM Applications is a current reference for these
risks.

## Compliance frameworks worth knowing

- **NIST CSF / SP 800-53 / SP 800-207** (Zero Trust) — US baseline.
- **NIST AI RMF + GenAI Profile (AI 600-1)** — AI-specific risk framework.
- **SOC 2** — service-org control attestation; commonly required by
  enterprise customers.
- **ISO 27001 / 27017 / 27018** — international information security,
  cloud-specific extensions.
- **ISO 42001** — AI management systems.
- **HIPAA** — US healthcare; protected health information.
- **PCI-DSS** — payment card data.
- **GDPR** — EU privacy; right to access, rectify, erase; lawful basis
  for processing.
- **FedRAMP** — US federal cloud authorization; Moderate, High, IL5.
- **EU AI Act** — first comprehensive AI regulation, risk-tiered.

## Glossary

- **Zero Trust** — security model based on "never trust, always verify."
- **NIST SP 800-207** — the canonical Zero Trust architecture document.
- **IAM** — Identity and Access Management.
- **RBAC / ABAC / ReBAC** — Role / Attribute / Relationship-based access.
- **JIT (just-in-time) access** — temporary privileged access.
- **PIM** — Privileged Identity Management (Microsoft's JIT system).
- **MFA / FIDO2** — Multi-factor authentication; phishing-resistant
  hardware-token MFA.
- **CMK / BYOK** — Customer-Managed Keys / Bring Your Own Key.
- **KMS / HSM** — Key Management Service / Hardware Security Module.
- **WAF** — Web Application Firewall.
- **CSPM / CNAPP / CIEM** — categories of cloud security tooling.
- **SIEM** — Security Information & Event Management.
- **EDR / XDR** — Endpoint / Extended Detection & Response.
- **Service mesh** — micro-segmentation and mTLS for K8s workloads.
- **Prompt injection** — adversarial input that overrides model instructions.
- **MBOM** — Model Bill of Materials; supply-chain manifest for AI.
- **OWASP LLM Top 10** — open list of the most common LLM security risks.
- **Confused deputy** — security flaw where authorized component is
  tricked into using its authority on behalf of an attacker.
