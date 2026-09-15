---
name: agentic-harness-designer
description: >
  Agent-harness design for an AI-powered product or serious automation: tools,
  authority, durable execution, context, evaluation, and operator visibility.
  Use for agent architecture, design review, or agent-system debugging; not
  model selection alone or ordinary non-agent automation.
argument-hint: "[system or automation to design or review]"
license: MIT
---

# agentic-harness-designer

> **Quick usage:**
> ```
> agentic-harness-designer <system or automation>
> agentic-harness-designer review the invoice-reconciliation agent
> agentic-harness-designer design a support-triage workflow
> ```
>
> If invoked with no target, ask for the system boundary, the outcome it must
> produce, and the operator who owns it; then stop until those are supplied.

Use a **harness-first** pass: decide the controls around the model before
selecting or tuning the model. A model recommendation is an implementation
choice constrained by the resulting system design.

## Evidence boundary

- For an existing system, inspect its tools, state stores, logs, and tests;
  label anything else as an assumption or open question.
- Scale controls to impact: read-only drafting, external communication, money,
  and production changes require different authority and recovery boundaries.
- Put controls at tool and service boundaries. Prompts express intent; they do
  not supply enforcement.

## Design walk

Work through these sections in order. For each, record a decision, rationale,
evidence or assumption, and open owner before continuing.

### 1. Tools and contracts

List every tool the agent receives. For each, specify its purpose; input and
output schema; authority and data scope; side effects; idempotency key or
deduplication behavior; timeout and retry rules; expected errors; and the
verifiable receipt it returns. State whether it is read-only, reversible, or
externally consequential.

Give the agent the smallest capability that completes the job. Put validation
and authorization in the tool or service boundary. For writes, define
preconditions and a read-back or receipt check.

**Done when:** a developer could implement every tool adapter without inferring
the agent's authority, and an operator can audit every consequential call.

### 2. Permission model

Make an explicit capability matrix with three classes:

| Class | Rule to define |
| --- | --- |
| Autonomous | Exact bounded actions, limits, and stop conditions |
| Approval required | Who approves, what exact action and evidence they see, and when approval expires |
| Forbidden | Actions and data scopes the system cannot perform, including indirect paths through tools |

Define identity, tenant/environment boundaries, spending or volume limits, and
how approval binds to the proposed action. When approval, identity, or policy
is uncertain, create a review item and take no side effect.

**Done when:** every side effect has a policy-enforced path, not merely an
instruction asking the model to be careful.

### 3. Workflow state and durability

Draw the workflow as states and transitions, including waiting for approval,
retry, terminal success, cancellation, and failure. Record durable task input,
plan/version, state transitions, tool requests and receipts, approvals,
idempotency keys, and checkpoints.

Specify lease ownership, retry/backoff, duplicate delivery handling, restart
behavior, and compensation or human escalation for partial effects. A restart
resumes from a recorded checkpoint; without one, it safely stops for review.

**Done when:** a crash at any side-effect boundary has a known recovery path
and can be tested with a replay or fault injection.

### 4. Context and memory

Separate:

- **Run context:** task facts needed now, with source, freshness, and a budget.
- **Durable workflow state:** facts and receipts required to resume safely.
- **Long-term memory:** curated, attributable knowledge with retention and
  review rules.

Name the sources, access checks, retrieval method, freshness policy, and
compaction/expiry rules. Identify excluded material explicitly: incidental chat
history, secrets, sensitive raw tool output, unreviewed model claims, and stale
decisions. Retain only the minimum needed for the stated purpose.

**Done when:** the agent can explain each material fact's source and a bounded
run cannot grow its context or memory indefinitely.

### 5. Evaluation

Turn the intended outcome into concrete checks. Cover tool-contract validation,
permission denials and approvals, workflow restart and duplicate delivery,
context provenance/budgets, expected successful runs, likely failures, and
adversarial or ambiguous requests.

For each check, state the fixture or environment, oracle, pass condition, and
whether it runs in CI, staging, or controlled production replay. Define release
thresholds and regression ownership. Use model graders only where a deterministic
oracle is unavailable, with sampled human review.

**Done when:** the team can demonstrate that the system works and fails safely,
rather than reporting that it "seems helpful."

### 6. Observability and operator control

Define structured events for run and trace IDs, workflow state, tool request and
receipt IDs, policy decision, approval status, retry, error, and final outcome.
Log sufficient metadata to reconstruct a run while redacting secrets and
minimizing sensitive content.

Specify the operator view during a live run: current state, next action,
evidence, pending approval, tool activity, cost/usage where relevant, and
controls to pause, cancel, retry, resume, or escalate. Define alerts for stuck
runs, repeated policy denials, anomalous volume, and failed evaluations.

**Done when:** an on-call operator can answer "what is it doing, why, and how
do I safely intervene?" without reading model internals.

## Failure-mode review

Before finalizing, review these common killers. Record the control and its
evidence, or the gap, risk, owner, and first remediation phase.

| Killer | Required review |
| --- | --- |
| Missing approval gates | Can the agent reach every consequential action only through a policy check and action-bound approval? |
| Non-durable state | Can a process crash, retry, or duplicate message cause a lost, repeated, or ambiguous side effect? |
| Unbounded context growth | Are retrieval, retention, and compaction bounded and source-aware? |
| No evals | Do executable checks cover intended behavior, unsafe behavior, and regressions? |
| Invisible execution | Can an operator reconstruct and control an in-progress run with safe logs? |

Count a mitigation only when it names its enforcement point, test, and
operating evidence.

## Output

Produce one concise design document with this structure:

```markdown
# <System> agent-harness design

## Scope and assumptions
## Decisions and rationale
### Tools and contracts
### Permission model
### Durable workflow
### Context and memory
### Evaluation
### Observability and operator control
## Failure-mode review
| Killer | Status | Enforcement and evidence | Gap / owner |
## Open questions and explicit risks
## Phased implementation plan
| Phase | Independently shippable slice | Acceptance checks | Rollback / safe stop |
```

Build vertical slices. Every phase delivers a useful bounded capability,
preserves the previous phase's safety properties, and names executable
acceptance checks. Expand authority only after its tools, permissions,
durability, evaluation, and operator visibility exist. Include a safe-stop or
rollback path per phase.

End by separating confirmed decisions from assumptions and questions that need
an owner. If the target is an existing system, distinguish observed behavior
from proposed change.
