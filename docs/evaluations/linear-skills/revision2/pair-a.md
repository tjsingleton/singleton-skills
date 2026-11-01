# Pair A, revision 2

Synthetic comparison. Original uses formatting assistance (headings and line
breaks) while preserving the controlled source semantics. It is not a natural
issue archive. Revised is verbatim fresh skill execution. Present only one
version at a time. Keep the separate facilitator key withheld.

## Original with formatting assistance

```markdown
# EX-101 — Reliable export

Workspace: Example / team: Example / project: Export.
Native status: Done.

Outcome: reliable export.
Current statement: implementation not started (2026-01-02).

Criteria:
- Preserve ordering.
- Support cancellation.
- Tests.
- Human walkthrough.

New report: tests pass at build-9. Artifact read confirms tests cover
ordering and cancellation only. Walkthrough absent.

Team status definitions: In Progress means work or acceptance outstanding;
Done means all issue criteria met.
Separate activation approval required. No writes authorized.
Comments, parent, and dependencies read: none.
```

## Revised

```markdown
# EX-101 — Reliable export

Outcome: provide a reliable export that preserves ordering and supports cancellation.

Current position: build-9 was inspected and verifies ordering and cancellation tests only. Overall acceptance remains incomplete because broader test completion is not established and the required human walkthrough is absent. The native Done status conflicts with those outstanding gates; propose In Progress under the team's definitions.

Next action: establish the remaining test scope and evidence, then complete and record the required human walkthrough. Obtain separate activation approval before activation.

Acceptance criteria:
- [x] Preserve ordering — inspected build-9 test artifact verifies ordering coverage and passing results; this establishes that tested behavior only.
- [x] Support cancellation — inspected build-9 test artifact verifies cancellation coverage and passing results; this establishes that tested behavior only.
- [ ] Complete required tests — the new report says tests pass at build-9, but the inspected artifact covers ordering and cancellation only; broader completion remains unverified.
- [ ] Complete the human walkthrough — no walkthrough evidence is available.

Authority: activation requires separate approval. Test results and issue acceptance do not grant activation authority.

History: the 2026-01-02 checkpoint said implementation had not started. Retain it as historical context; the inspected build-9 results provide later, bounded evidence of progress without establishing full implementation or acceptance.
```

## Questions, after each version

1. What is the next action?
2. What acceptance work remains?
3. Where is the completion evidence, and what does it establish or leave unresolved?

Time in seconds or not measured? Anything confusing?
