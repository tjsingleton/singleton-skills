---
name: learn-from-context
description: >
  Extract valuable learnings, patterns, and insights from the current agent session
  and integrate them with your knowledge systems (PKB, OpenBrain, workflows).
  Use when you want to capture and persist discoveries from a conversation.
  Trigger on: "extract learning", "learn from this", "capture insight", "add to knowledge",
  "extract pattern", "record finding".
  Don't use for generic lookups or when you need to act on information within the current conversation.
argument-hint: "[topic] [--target knowledge-system]"
license: MIT
---

# learn-from-context

> **Quick usage:**
> ```
> /singleton-skills:learn-from-context <argument>
> ```
>
> If invoked with no arguments, show this hint and wait for input.

## Overview

This skill extracts actionable insights and patterns from the current conversation context,
then routes them to your knowledge systems for persistent storage and cross-system integration.

**Why it exists:** Enable continuous learning loops where each agent session surfaces discoveries
that compound across your PKB, OpenBrain, tooling, homelab, and AI workflows. Instead of losing
context when a session ends, this skill bridges current insights into your persistent knowledge graph.

## Workflow

### Step 1 — Parse arguments

Parse `$ARGUMENTS`:
- If empty or `--help`: show usage hint above and stop
- Extract optional `[topic]` (e.g., "architecture", "debugging pattern", "tool integration")
- Extract optional `--target` flag (default: auto-route to appropriate system)
  - `openbrain`: Capture as a thought in OpenBrain
  - `pkb`: Add to Personal Knowledge Base
  - `both`: Route to both systems

### Step 2 — Analyze current context

Scan the conversation to identify:
- Key insights discovered or validated
- Patterns or anti-patterns encountered
- Tool/workflow improvements
- Architectural decisions or trade-offs
- Lessons learned or gotchas

Frame learnings as actionable, reusable knowledge that will be useful in future contexts.

### Step 3 — Route to knowledge systems

**For OpenBrain (default):**
- Call `open-brain:capture_thought` with the extracted learning
- Include metadata: domain, confidence, source session

**For PKB:**
- Format as a structured knowledge entry
- Link to related existing knowledge
- Update cross-references if applicable

### Step 4 — Report results

Output what was captured, which systems it was added to, and provide IDs/references
for future lookup and cross-linking.

## Output

```
✓ Captured learning: [summary]
  Domain: [topic]
  Stored in: OpenBrain (ID: xxx) | PKB | Both
  Linkage: [related concepts/prior sessions]
```

## Notes

- Learnings are most valuable when they reflect patterns across multiple sessions
- Include "why" context so future-you understands the decision rationale
- OpenBrain captures are automatically indexed and searchable across all future sessions
