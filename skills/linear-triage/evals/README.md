# Triage evaluations

Execute the skill and its linked contract in a fresh agent context against each
`prompt` and controlled `snapshot` in `evals.json`. Withhold `expected_output`
and `expectations` until the agent has produced its findings. Substitute the
snapshot for connector responses; never connect these fixtures to a live
workspace. Record the complete findings and ordered requested operations,
including reads that fail and any attempted mutations. Assess actual next
actions, dependency reasoning, source limits, and authority independently
against the oracle. A mention of an issue ID is insufficient evidence.

`behavior-results.md` records observed instruction-following runs and their
limitations. Re-run when the skill or shared contract changes materially.
Repository tests check packaging and candidate discovery; they do not execute
a model or prove live compatibility across hosts. These fixtures test bounded
read-only assessments, including a mixed request asking for easy fixes.

## Packaging red-to-green

Adding the candidate before its package and README row existed produced three
portable conformance failures and one error. Adding the package and discovery
row resolves that packaging failure. This is separate from model behavior:
there is no claim that a failing model behavior was repaired by those edits.
