# Facilitator key: withhold until answers are recorded

## Provenance

The instruction revisions were committed before execution. A and C ran at
d2576cf; B finally ran at f52f67c. The author/update/shared instructions used by
A/C are byte-identical at the latter revision; only triage changed. Fresh contexts read the
three skills and shared contract, with previous outputs, eval oracles, and this
packet withheld. Source selection and later judging were performed by an agent
that knew expected behavior. Source snapshots stand in for connector responses;
artifact inspection claims therefore mean supplied synthetic observations, not
actual inspection of a real build. Execution records contain full exact outputs,
proposed fields, findings, and empty requested-operation/simulated-return arrays.
No live writes occurred. The short revision identifier in the executor's metadata
was expanded to its full Git SHA when packaging; response text was unchanged.

The initial B execution is retained as failure in execution-initial.json: its
queue finding recommends starting supposedly scoped EX-109 work, although the
snapshot supplies neither actual scope nor authority. The issue display preserves
requirements but cannot make that triage recommendation valid. Existing triage
steps 4–5 already require those facts; this is an instruction-following failure,
not evidence that a ready label grants authority. A second fresh B execution also called EX-109 an implementation frontier despite
missing details, so it is retained as failure in execution-rerun-before-fix.json.
The repeated failure warranted an explicit snapshot-only readiness clarification
in linear-triage. The final fresh B execution follows that committed repair.
Retain all attempts when judging reliability.

## Preservation and task ledger

| Case | Required interpretation | Exact output location |
|---|---|---|
| A | Reliable export, ordering, cancellation retained | outcome and checklist |
| A | build-9 supports ordering/cancellation only, not all tests | checked-item limits and unchecked tests |
| A | Human walkthrough missing; next action includes completing it and resolving test scope | current position, next action, unchecked walkthrough |
| A | Done conflicts with team's outstanding-acceptance semantics; In Progress proposed, unsaved | current position and proposed_fields |
| A | 2026-01-02 checkpoint retained as history | History |
| A | Separate activation approval required; no writes authorized | Authority and operation accounting |
| B | CSV/JSON, Unicode/nulls, cancellation preserved | outcome and checklist |
| B | run-8 supports only CSV Unicode/null behavior | checked-item pointers and unchecked JSON/cancellation/tests |
| B | Required walkthrough remains missing | current position and unchecked walkthrough |
| B | Existing separate approval retained as reported with applicability unverified | Authority |
| B | EX-108 depends on incomplete EX-107; EX-109 independent and reported ready | dependency context and triage findings |
| B | Unknown EX-109 scope/authority limits next action to retrieving those facts | rerun triage findings; initial execution fails this row |
| B | Fresh read unchanged, no version preconditions; future save needs refresh and race disclosure | full response findings |
| C | Only ordering checked; cancellation denied; full regression and walkthrough unsupported | checklist and findings |
| C | Dated tests-pending checkpoint retained | History |
| C | Staging-only approval reported/unverified, production absent, no activation | Authority |

A broader generic tests item stays unchecked even when its named behavioral
subsets have passing evidence. Evidence pointers are synthetic artifact identifiers;
no public accessible build URL was supplied. Draft-only proposals need no simulated
write/readback. B has one author-owned rewrite incorporating update reconciliation,
with triage findings reused separately and no duplicate operation. Other metadata
and native relationships are unchanged. A's status proposal is update-owned.

The facilitator's preservation assessment is agent judgment, separate from human
responses. Human evidence, timing, re-evaluation, and adoption remain pending.

## Results and limits

Initial synthetic set: A and C pass the reviewed preservation/checklist checks;
B fails the unsupported implementation-readiness recommendation. A second B
attempt before the clarification also fails that boundary. Final B preserves
the approval, checklist evidence limits, dependencies, and explicitly requires
read-only scope/authority retrieval for EX-109. No implementation frontier or
execution permission is inferred. Three final selected case outputs pass these
bounded semantic checks; the two earlier B failures remain part of the record.
This judgment is not a benchmark estimate or human pilot result.

The pin-integrity test first failed because revision2/pins.json did not exist.
It checks hashes, committed instruction bytes, and verbatim display inclusion;
it does not judge comprehension or semantic preservation.
