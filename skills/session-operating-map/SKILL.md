---
name: session-operating-map
description: >
  Maintain a repo-local operating map for parallel agent sessions. Use when
  coordinating multi-session work or asking "what's in flight" in a project.
  Skip a single independent task.
argument-hint: "[setup|status|update]"
license: MIT
---

# session-operating-map

> **Quick usage:**
> ```
> session-operating-map setup
> session-operating-map status
> session-operating-map update
> ```
>
> Examples: “Set up coordination for this repo,” “What’s in flight?”, or “Mark
> the API lane blocked on credentials.”

## Operating map

An operating map is a compact, current snapshot of parallel work. It answers
which concern each lane owns, its objective, session, state, blocker, and the
decisions that constrain multiple lanes. Keep it separate from issue trackers,
implementation plans, and handoff detail.

Use this skill when the user starts parallel work, asks what is in flight or who
owns work, or asks to establish or maintain project coordination. Select the
least invasive action: `setup` when the map is absent, `status` for a question,
and `update` for a reported state change. For a single independent task, proceed
without a map.

## Read first

Every session joining a repository that has an operating map reads
`docs/operating-map.md` before investigating, planning, editing, delegating, or
claiming a lane. The map supplies coordination context; changing an owner or
scope still requires a coordinated handoff.

## Workflow

### 1. Locate and read

Resolve the repository root and use exactly `docs/operating-map.md`. If it
exists, read it in full before project work; identify active lanes, owners,
blockers, and current decisions relevant to the request. For `status`, report
only that evidence and call out unknown or stale entries.

**Complete when:** the existing map has been read, or its absence is confirmed.

### 2. Set up the snapshot

For `setup`, inspect the assigned work and active sessions. Add only work that
is actually in flight; record unknown ownership or state as unknown rather than
inferring it. Create the map with this structure when it is absent:

```md
# Operating Map

> Coordination state for parallel work in this repository. Read this file
> before starting a session or claiming a lane.

## Active lanes

| Lane | Objective | Owning session | Current state | Blockers |
| --- | --- | --- | --- | --- |
| example-api-contract | Define and verify the API contract | api-contract session | in progress | None |

## Current decisions

| Decision | Rationale | Affects |
| --- | --- | --- |
| Keep the wire format backward compatible | Existing clients depend on it | api-contract, client-migration |

## Done lanes

| Lane | Outcome |
| --- | --- |
| example-discovery | Located the relevant integration boundary |
```

Use short, recognizable session labels, concise states such as `in progress`,
`blocked`, or `handoff`, and one obvious kebab-case lane name per independently
owned concern. Capture decisions only when they constrain multiple lanes or
materially change how work proceeds.

**Complete when:** one map exists and every active lane has a short name,
objective, owning session, current state, and blocker.

### 3. Update by state transition

Refresh a lane only when it starts, blocks, resumes, hands off, or finishes.
Keep the row current by replacing the state, owner, and blocker together when
they change. The map remains a snapshot, not a journal: routine progress,
timestamps, chat narration, and resolved blockers stay out of it. Record a new
or changed decision only when it has coordination impact beyond one lane.

**Complete when:** every requested state transition is reflected once, with no
history appended to an active row.

### 4. Archive and promote

When a lane finishes, remove it from **Active lanes** and add a one-line outcome
to **Done lanes**. Promote a durable, reusable lesson to the relevant project
documentation or project skill; leave transient detail and unverified
conclusions out of the map.

**Complete when:** the finished lane has one outcome line and any reusable
lesson has a durable home outside the map.

## Reporting

State the map path and summarize changed lanes, current blockers, and changed
decisions. A status response lists active lanes and blockers, then identifies
unknown ownership or state that needs clarification.
