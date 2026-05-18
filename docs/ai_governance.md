# AI Governance — A Practitioner's Primer

AI governance is the discipline of making sure AI systems are built, deployed,
and operated in ways that are safe, lawful, ethical, and aligned with the
goals of the organization. It is the umbrella over policy, risk management,
compliance, evaluation, monitoring, and incident response.

## Why AI governance exists

Three forces created the field:

1. **Scale and opacity.** Modern AI systems make decisions at a volume no
   human reviewer can audit, using internal representations no human can
   directly inspect. Governance is how organizations regain visibility.
2. **Real-world harm.** Documented failures — biased hiring tools, faulty
   facial recognition, hallucinated medical advice, copyright violations —
   forced regulators and businesses to treat AI risk as a category of its own.
3. **Regulation.** Major jurisdictions have moved from voluntary principles
   to binding law. Operating without a governance program is becoming a
   compliance liability.

## Core principles (the "FAT" cluster)

Almost every AI ethics framework converges on the same vocabulary:

- **Fairness** — outputs are not systematically biased against protected
  groups. Measured with metrics like demographic parity, equalized odds, and
  disparate impact ratios.
- **Accountability** — for every AI-driven decision, there is a named human
  or role who is responsible. This is often called the "responsible owner"
  pattern.
- **Transparency** — users are told they are interacting with AI, and the
  system's purpose, training data, and limitations are documented.
- **Explainability** — the system can produce a human-understandable
  rationale for individual decisions, at least for high-impact use cases.
- **Privacy** — personal data is collected lawfully, minimized, secured, and
  used only for stated purposes.
- **Safety and robustness** — the system performs reliably under expected
  conditions and fails gracefully under unexpected ones.
- **Human oversight** — there is a meaningful "human in the loop" or "human
  on the loop" for consequential decisions.

## Key regulations and frameworks

### EU AI Act (in force 2024, phased implementation 2025–2027)

The world's first comprehensive AI law. Uses a **risk-tiered** approach:

- **Unacceptable risk** — banned outright (social scoring, real-time
  biometric ID in public spaces with narrow exceptions, manipulative AI).
- **High risk** — AI used in critical infrastructure, hiring, credit,
  law enforcement, education, etc. Must meet strict requirements: risk
  management, data governance, technical documentation, logging, transparency,
  human oversight, accuracy, robustness, and cybersecurity.
- **Limited risk** — chatbots, deepfakes — must disclose AI involvement.
- **Minimal risk** — no specific obligations beyond existing law.
- **General-purpose AI (GPAI)** — foundation models have their own
  obligations: technical documentation, copyright compliance, training data
  summaries. Models with systemic risk (10²⁵ FLOPs training compute) get
  additional evaluation and incident-reporting duties.

Fines reach €35M or 7% of global revenue for the worst violations.

### NIST AI Risk Management Framework (AI RMF 1.0)

US National Institute of Standards and Technology framework, voluntary but
widely adopted. Four functions:

- **Govern** — establish a culture of risk management.
- **Map** — understand the context and AI risks.
- **Measure** — analyze, assess, benchmark, monitor.
- **Manage** — prioritize and act on the risks.

The companion "Generative AI Profile" (NIST AI 600-1) adapts the framework
specifically to LLMs and image models, addressing hallucination, harmful
output, data leakage, prompt injection, and intellectual property risks.

### ISO/IEC 42001

International standard published in 2023. A management-system standard
(similar in structure to ISO 27001 for infosec). Certifiable. Establishes
requirements for an AI management system covering policy, planning, support,
operation, performance evaluation, and improvement.

### Sector-specific

- **HIPAA** (US healthcare) — AI handling protected health information must
  meet privacy and security rules.
- **GDPR** (EU privacy) — Article 22 limits "solely automated decision-making"
  with legal or significant effects. Right to explanation has been interpreted
  to require meaningful information about the logic involved.
- **EEOC and state hiring laws** (US) — algorithmic hiring tools are subject
  to anti-discrimination scrutiny; some states require bias audits.
- **NYC Local Law 144** — employers must conduct annual bias audits of
  automated employment decision tools.
- **SR 11-7** (US Federal Reserve guidance) — model risk management for
  financial institutions, increasingly applied to AI.

## Risk categories practitioners should know

- **Hallucination** — model fabricates plausible-sounding but false content.
  Mitigations: RAG, citation requirements, output validation, lower
  temperature for factual tasks.
- **Bias and discrimination** — disparate performance or outcomes across
  protected groups. Mitigations: representative training data, bias testing,
  fairness-aware loss functions, post-hoc threshold adjustment.
- **Prompt injection** — attacker-controlled input overrides the model's
  instructions. Mitigations: input sanitization, structured prompts, output
  validation, principle of least privilege for tool access.
- **Data leakage / training data extraction** — model regurgitates
  memorized PII or proprietary content. Mitigations: data minimization,
  deduplication, differential privacy, output filters.
- **Model theft** — adversary reconstructs the model via API queries.
  Mitigations: rate limiting, watermarking, query monitoring.
- **Supply chain risk** — vulnerabilities introduced via base models,
  embeddings, or third-party datasets. Mitigations: model bill of materials
  (MBOM), provenance tracking, vendor assessment.
- **Autonomy risk** — agents take consequential actions without adequate
  oversight. Mitigations: action-level approval, sandboxing, kill switches.

## The governance lifecycle in practice

1. **Inventory.** Maintain a register of every AI system in production,
   classified by risk tier, business owner, data sources, and dependencies.
2. **Pre-deployment review.** New AI use cases go through a structured
   intake (risk assessment, data protection impact assessment, fairness
   review, security review).
3. **Documentation.** Each system has a "model card" or "system card"
   documenting purpose, training data, evaluation results, limitations,
   intended users, and known risks.
4. **Evaluation.** Performance, safety, and fairness metrics are measured
   before launch and on an ongoing basis. Standard evaluation sets exist
   for both general capability (MMLU, GSM8K) and harm (HELM, ToxiGen,
   BOLD, RealToxicityPrompts).
5. **Monitoring.** Production systems are instrumented to detect drift,
   anomalies, and emerging harms. Logs are retained for incident response.
6. **Incident response.** A defined process for triaging, mitigating, and
   reporting AI failures — including external disclosure where required.
7. **Audit.** Periodic, often third-party reviews verify that controls
   are working as designed.

## Roles in a mature AI governance program

- **Chief AI Officer / AI Lead** — accountable executive.
- **AI Governance Committee** — cross-functional (legal, security, privacy,
  ethics, business) approval body for high-risk use cases.
- **Model risk owner** — accountable for a specific system's risk posture.
- **AI ethics review board** — for novel or sensitive applications.
- **Red team** — adversarial testing for safety and security flaws.
- **Auditors** — internal or external, verify control effectiveness.

## Glossary of governance terms practitioners should recognize

- **Model card** — standardized documentation of a model's intended use,
  performance, and limitations. Originated in a 2018 Google paper by
  Mitchell et al.
- **Datasheet for datasets** — analogous documentation for training data
  (Gebru et al.).
- **Algorithmic impact assessment (AIA)** — structured risk evaluation
  performed before deploying an automated decision system.
- **Bias audit** — formal evaluation of disparate outcomes; required by
  several jurisdictions.
- **Right to explanation** — legal interpretation that affected individuals
  can demand the reasoning behind an automated decision (notably under GDPR).
- **Solely automated decision** — a decision with legal or similarly
  significant effect made without meaningful human involvement.
- **Human in the loop (HITL)** — a human approves each AI decision.
- **Human on the loop (HOTL)** — a human monitors AI decisions and can
  intervene.
- **Red team** — adversarial testers attempting to break or misuse the AI.
- **Foundation model** — large, general-purpose model trained on broad
  data and adaptable to many tasks (term coined by Stanford CRFM in 2021).
- **Provenance** — verifiable record of where a model, dataset, or output
  came from.
- **C2PA** — Coalition for Content Provenance and Authenticity standard
  for cryptographically signing media to prove origin.

## Common misconceptions

- *"If we use an open-source model, we don't have governance obligations."*
  False. Obligations attach to the deployer of the system, not just the
  model developer. The EU AI Act, NIST RMF, and most sector laws apply
  regardless of whether the model is open or closed.

- *"Removing protected attributes (race, gender) from training data
  eliminates bias."* False. Models reliably reconstruct protected attributes
  from correlated features (zip code, name, browsing history). This is
  called "fairness through unawareness" and is widely considered insufficient.

- *"Higher accuracy automatically means a fairer model."* False. Aggregate
  accuracy can hide large disparities across subgroups. A model can be
  highly accurate overall and severely biased against a minority population.

- *"Explainability and accuracy are inherently in tension."* Mostly false
  in practice. For most business use cases, interpretable models (logistic
  regression, gradient-boosted trees with SHAP) match or beat black-box
  models. The trade-off is real but often overstated.

- *"Compliance equals governance."* Compliance is the floor, not the
  ceiling. Mature governance addresses risks the regulator has not yet
  identified.

## Practical starting checklist for a small org

1. Maintain an AI inventory (a spreadsheet is fine to start).
2. Write a short AI use policy: what's allowed, what's restricted, who
   approves.
3. Adopt the NIST AI RMF as your reference framework.
4. Require model/system cards for any AI used in production.
5. Define a simple intake process — every new AI use case answers ten
   questions before going live.
6. Set up basic monitoring (sampled output review, error tracking).
7. Establish an incident response procedure for AI failures.
8. Train staff on responsible use, especially around data and prompt hygiene.

The above is the 80/20 of an AI governance program. Everything else is
elaboration for scale or specific regulated industries.
