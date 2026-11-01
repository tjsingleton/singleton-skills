# Pair B, revision 2

Synthetic comparison. Original uses formatting assistance (headings and line
breaks) while preserving the controlled source semantics. It is not a natural
issue archive. Revised is verbatim fresh skill execution. Present only one
version at a time. Keep the separate facilitator key withheld.

## Original with formatting assistance

```markdown
# EX-107 — Export CSV and JSON

Workspace: Example / team: Example / project: Export.
Native status: In Progress.

Export CSV and JSON; preserve Unicode and nulls; support cancellation.
Current statement: tests pending.
New accessible run-8 proves CSV Unicode/null behavior only.
Human walkthrough required and missing; activation separately approved.

Queue: EX-108 depends on EX-107; EX-109 independent and ready.
All comments and parents read: no additional constraints.
Before-write fresh read: unchanged. No version preconditions.
Draft only. Reported activation approval must be verified for applicability;
no activation authorized.
```

## Revised

```markdown
# Preserve Unicode and nulls in CSV and JSON exports with cancellation

Deliver CSV and JSON exports that preserve Unicode and nulls and support cancellation.

**Current position:** EX-107 remains In Progress. Accessible run-8 verifies CSV Unicode and null behavior only. The earlier statement “Current tests pending” is partially superseded by that bounded result; the remaining tests are pending. The required human walkthrough is missing.

**Next action:** Verify JSON Unicode/null behavior and cancellation, complete remaining test coverage, and obtain the required human walkthrough. Preserve the separately reported activation approval, but verify its scope and applicability before relying on it. This draft authorizes no activation.

## Acceptance criteria and evidence

- [x] CSV export preserves Unicode and nulls. Evidence: run-8, accessible in the supplied scenario; establishes these CSV behaviors only.
- [ ] JSON export preserves Unicode and nulls. Evidence gap: run-8 covers CSV only; JSON verification remains pending.
- [ ] Export supports cancellation. Evidence gap: run-8 does not establish cancellation; verification remains pending.
- [ ] Complete the remaining applicable tests. Evidence: source checkpoint “Current tests pending,” now qualified by run-8; no complete test-suite result supplied.
- [ ] Complete the required human walkthrough. Evidence gap: walkthrough is required and missing; automated checks cannot satisfy it.

## Activation decision

Activation was reported as separately approved. Its scope and applicability are unverified. Preserve this reported decision without treating it as verified permission for an action. No activation is authorized in this request.

## Dependencies and queue context

EX-108 depends on EX-107; its implementation remains blocked while this prerequisite is unresolved. EX-109 is reported independent and ready; retrieve its outcome, requirements, and execution authority before recommending implementation. Its immediate next action is that read-only retrieval.
```

## Questions, after each version

1. What is the next action?
2. What acceptance work remains?
3. Where is the completion evidence, and what does it establish or leave unresolved?

Time in seconds or not measured? Anything confusing?
