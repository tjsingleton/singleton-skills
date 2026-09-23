---
name: amazon-writing-style
description: >
  Audit and rewrite prose to Amazon writing rules: sentences under 30 words,
  data over adjectives, subject-verb-object, no unexplained acronyms, no clutter
  phrases, and the so-what test. Use when the user asks for Amazon writing,
  Bezos style, a so-what pass, a fluff-free memo, or an Amazon writing audit.
  Don't use when the user wants a 6-page narrative, a PR/FAQ template, or
  general copyediting without those rules.
argument-hint: "[draft path or pasted text]"
license: MIT
---

# amazon-writing-style

> **Quick usage:**
> ```
> amazon-writing-style
> amazon-writing-style <draft path>
> amazon-writing-style rewrite this memo to Amazon style
> ```
>
> If invoked with no draft, ask for the text. Do not invent a sample.

Enforce the six rules below. Do not invent a 6-page structure or a PR/FAQ
template unless the user asks for one.

## Workflow

### Step 1 — Parse arguments

Parse arguments from the active host's skill invocation:

- If empty or `--help`: show the usage hint above, then ask for the draft and
  stop until text is supplied.
- If a path is given, read that file.
- If the user pasted text, use that text.

### Step 2 — Audit

From this skill directory, pipe the draft on stdin:

```bash
python3 scripts/audit_text.py
```

Example:

```bash
python3 scripts/audit_text.py < draft.txt
```

### Step 3 — Apply rules the script cannot see

Apply every rule the script cannot see: **so what?**, unexplained jargon, and
missing actors.

### Step 4 — Report and rewrite

List violations by rule. Then output a rewrite that satisfies all six. Do not
invent numbers; mark `[NEED METRIC]`.

Done when every sentence is under 30 words, every modifier has a number or
`[NEED METRIC]`, every action has a named doer, every acronym is spelled out on
first use, clutter phrases are gone, and the opening states action, purpose,
and real-world impact.

## Core rules

Use this wording as the bar:

- **Short sentences:** Keep sentences under 30 words to force clear thinking and easy reading.
- **Data over adjectives:** Replace vague praise or modifiers with hard numbers and concrete facts.
- **Subject-verb-object structure:** Use simple, direct language featuring clear "doers" and "actions".
- **No jargon or acronyms:** Avoid internal buzzwords, and spell out any necessary acronyms on first use.
- **No clutter words:** Cut filler phrases like "due to the fact that" (use "because") or "in order to" (use "to").
- **Pass the "So what?" test:** Clearly state the action, purpose, and real-world impact of your proposal right away.

### Short sentences

Split at 30 words. Prefer two sentences over a conjunction pile-up.

### Data over adjectives

If a claim is evaluative or vague, replace the modifier with a number. Weasel
hits from the auditor (mostly, significantly, many, approximately, …) are the
same failure.

### Subject-verb-object

Name the actor. "The product team decided" beats "It was decided."

### No jargon or acronyms

Expand the first use: "press release / frequently asked questions (PR/FAQ)".
Drop buzzwords that do no work.

### No clutter words

Replace, do not decorate:

| Cut | Use |
| --- | --- |
| due to the fact that | because |
| in order to | to |
| for the purpose of | to |
| in the event that | if |
| with regard to | about |
| a number of | the count, or a number |

### So what?

The first paragraph must answer, in order: what we will do, why, and what
changes in the world if we do it. A feature list that does not change a
customer's or team's outcome fails.
