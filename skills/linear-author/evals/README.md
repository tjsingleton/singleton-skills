# Authoring evaluations

`evals.json` supplies user requests, controlled connector snapshots, and
independent outcome expectations. Execute the installed skill and shared
contract in a fresh agent context. Substitute the snapshot for Linear source
responses. Record the complete draft/result and ordered requested operations,
including failures, refreshes, and readback. Never connect these fixtures to a
live workspace. The declared responses are simulation; the agent's output is
an observed instruction-following run.

Judge preservation against every source requirement and authority boundary,
then inspect requested operations for duplicates, scope, and verification.
Use the snapshot's `required_items` as a review aid, not a semantic assertion.
A passing substring check cannot show that a requirement kept its meaning.

`behavior-results.md` records the executed runs and their limitations. Re-run
these scenarios when the skill or contract changes materially. Repository tests
check package integrity and portable discovery only. They do not run a model,
establish behavior quality, or certify live host compatibility.

## Implementation verification record

The first packaging slice added the candidate to the installer and discovery
contract before its package existed. Portable conformance failed with three
failures and one error, including missing skill metadata and missing README
coverage. Adding the skill, shared reference, and compatibility row made all
five portable conformance tests pass. This is a packaging red-to-green result,
not evidence of a failing model behavior corrected by instruction changes.

The full check passes with a writable temporary `PYTHONPYCACHEPREFIX`: 65
repository tests, 12 Git-triage evaluation tests, and Python compilation. The
initial default cache location was outside the process sandbox; the tests
passed but compilation could not write that cache. No browser was launched.
