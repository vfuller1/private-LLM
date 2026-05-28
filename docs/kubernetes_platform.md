# Kubernetes Platform Engineering

Kubernetes is the dominant container orchestration platform and the backbone
of modern cloud-native architectures. For an architect, the relevant
expertise is not "how do I write a YAML manifest" — it is "how do I run
this safely, observably, and economically at scale, across multiple
clouds, for many teams."

## Cluster offerings (managed)

- **Amazon EKS** — EKS-managed control plane (HA, patched by AWS). Pay
  per cluster per hour plus worker nodes. Recent additions: EKS Auto Mode
  (managed nodes + add-ons + Karpenter), Pod Identity (better than IRSA),
  Hybrid Nodes for on-prem joining EKS.
- **Azure AKS** — Managed control plane is free; pay for worker nodes
  only. Tight integration with Entra ID, Azure Policy, Azure Monitor.
  Strong recent investment in Karpenter-style autoscaling and KAITO for
  AI workloads.
- **Google GKE** — Two flavors: Standard (you manage node pools) and
  Autopilot (Google manages nodes; pay per pod). The most opinionated and
  arguably most "managed" of the three.
- **OpenShift** — Red Hat's commercial Kubernetes distribution; comes with
  built-in CI/CD (Tekton), service mesh (Istio), and developer portal.
  Common in regulated enterprises and on-prem.

## Cluster architecture decisions

- **One cluster per environment vs many small clusters** — fewer clusters
  reduce ops overhead; more clusters limit blast radius and improve isolation.
  Default modern pattern: cluster-per-environment-per-region, plus a
  separate "platform" cluster for shared services.
- **Multi-tenancy model** — namespace-per-team (cheap, weak isolation) vs
  cluster-per-team (expensive, strong isolation) vs virtual clusters with
  vCluster / Capsule (middle ground).
- **Node groups / node pools** — segment nodes by workload type (CPU,
  GPU, memory-optimized) and by trust boundary (system / general / sensitive).
- **Autoscaling** — Cluster Autoscaler (legacy) vs **Karpenter** (modern,
  preferred on EKS/AKS, more efficient bin-packing, faster scale).

## Networking

- **CNI plugin** — picks how pods get IPs. AWS VPC CNI, Azure CNI Overlay,
  Calico, Cilium (eBPF-based, increasingly the default for advanced
  workloads).
- **Ingress** — NGINX, Traefik, HAProxy, cloud-native (ALB, App Gateway,
  GCLB), or Gateway API (the newer, more expressive standard replacing
  Ingress).
- **Service mesh** — Istio, Linkerd, Cilium Service Mesh. Adds mTLS,
  observability, traffic policies. Don't add a mesh until you have a
  specific reason; the operational cost is non-trivial.
- **Pod security and network policies** — default-deny network policies,
  pod-to-pod TLS via mesh, egress restrictions to known endpoints.

## Identity and secrets

- **Workload identity** — pods authenticate to cloud APIs without long-
  lived secrets. AWS: IAM Roles for Service Accounts (IRSA), now superseded
  by EKS Pod Identity. Azure: Workload Identity (federates with Entra ID).
  GCP: Workload Identity Federation.
- **Secrets management** — never store secrets in plain `Secret` objects
  long-term. Use External Secrets Operator + AWS Secrets Manager / Azure
  Key Vault / Google Secret Manager / HashiCorp Vault.
- **RBAC** — Kubernetes RBAC is namespace-scoped or cluster-scoped. Pair
  with cloud IAM for end-to-end control.
- **Admission control** — OPA Gatekeeper, Kyverno, or Validating Admission
  Policy (built-in since 1.30) enforce policies at admission.

## GitOps

GitOps is the dominant deployment model on Kubernetes:

- **ArgoCD** — pull-based GitOps controller. Watches Git, reconciles cluster
  to match. The most widely deployed.
- **Flux** — equally capable, more modular, smaller footprint.
- **Mental model** — Git is the source of truth; cluster state converges
  to Git. Operators never `kubectl apply` against prod.
- **Why** — auditable change history, easy rollback (revert the commit),
  separation of CI (build) and CD (deploy).

## Workload patterns

- **Deployment** — stateless apps, rolling updates.
- **StatefulSet** — for ordered, named pods with stable storage
  (databases, message queues that haven't moved off K8s).
- **DaemonSet** — one pod per node (log shippers, CNI, monitoring agents).
- **Job / CronJob** — batch and scheduled workloads.
- **HorizontalPodAutoscaler / KEDA** — HPA scales on CPU/memory; KEDA
  scales on external signals (queue length, message broker depth).

## Storage

- **PV / PVC** — pods request persistent volumes via claims; controllers
  provision them from a StorageClass.
- **CSI drivers** — cloud-specific drivers (EBS, Azure Disk, GCE PD)
  surface block storage; **EFS / Azure Files / Filestore** for shared
  filesystems.
- **Stateful workloads** trend off Kubernetes for databases (RDS / Cloud
  SQL / Azure SQL are easier) but back onto it for streaming and search
  (Kafka, ClickHouse, OpenSearch via operators).

## Observability

- **Logs** — fluent-bit or vector to a backend (Loki, Datadog, CloudWatch).
- **Metrics** — Prometheus is the de facto standard; managed offerings
  via Amazon Managed Prometheus, Azure Monitor for Prometheus, Google
  Cloud Managed Service for Prometheus.
- **Tracing** — OpenTelemetry collectors, exported to Jaeger, Tempo,
  Datadog APM, etc.
- **eBPF-based observability** — Cilium Hubble, Pixie, Inspektor Gadget
  collect telemetry without modifying apps.

## Security at the cluster level

- **Pod Security Standards** — `restricted`, `baseline`, `privileged`
  levels. Replace deprecated PodSecurityPolicy.
- **Image security** — sign images (Cosign / Sigstore), scan in registry
  (Trivy, Snyk, ECR scanning), enforce admission to only allow signed
  images.
- **Audit logging** — must be enabled on every cluster; routed to a
  central log store outside the cluster.
- **Encryption** — etcd encryption at rest (provider-managed in EKS/AKS/
  GKE), TLS for control plane API.
- **Network egress controls** — restrict cluster egress to known
  endpoints (artifact registries, observability, API endpoints).

## Cost levers

- **Right-sized requests and limits** — most clusters request 3–5× what
  they actually use. Use VPA recommendations or Goldilocks to right-size.
- **Spot / Preemptible / Spot VM nodes** — 60–90% discount, schedule
  stateless workloads on them with tolerations.
- **Karpenter** — bin-packs better than Cluster Autoscaler, lowering node
  count for the same workload.
- **Node consolidation** — Karpenter and AKS Karpenter equivalents
  proactively repack workloads onto fewer nodes.
- **Reserved capacity / Savings Plans / Committed Use Discounts** — apply
  to instances; mix with spot for the unpredictable portion.

## Common pitfalls in interviews

- **Confusing namespace isolation with cluster isolation.** Namespaces
  are not security boundaries by default.
- **Treating `Secret` objects as confidential.** They're base64-encoded,
  not encrypted, unless you've explicitly enabled etcd encryption and
  RBAC-scoped access.
- **Not knowing the difference between RoleBinding and ClusterRoleBinding.**
- **Defaulting to Helm without knowing the alternatives** (Kustomize,
  Timoni, raw YAML with envsubst, ArgoCD ApplicationSet generators).
- **Over-engineering with a service mesh** when the use case doesn't
  require it.

## Glossary

- **CNI** — Container Network Interface; the plugin that gives pods IPs.
- **CSI** — Container Storage Interface; the plugin that mounts volumes.
- **CRI** — Container Runtime Interface; the plugin that runs containers
  (containerd, CRI-O).
- **HPA / VPA / KEDA** — Horizontal / Vertical Pod Autoscalers; KEDA
  scales on external metrics.
- **Karpenter** — modern node autoscaler that provisions exactly the
  instance types you need.
- **GitOps** — pull-based deployment model where Git is the source of
  truth.
- **ArgoCD / Flux** — the two main GitOps controllers.
- **Gateway API** — newer, more expressive replacement for Ingress.
- **eBPF** — kernel-level observability and networking technology;
  basis of Cilium, Pixie, etc.
- **Workload Identity** — federated identity that lets pods authenticate
  to cloud APIs without static credentials.
- **Admission controller** — webhook that intercepts API requests; used
  for policy enforcement (Gatekeeper, Kyverno).
- **OPA / Gatekeeper / Kyverno** — Kubernetes-native policy engines.
