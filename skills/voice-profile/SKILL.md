---
name: voice-profile
description: >
  Writes, rewrites, or reviews prose in TJ's registers. Use when drafting
  emails, posts, docs, feedback, recipes, READMEs, or anything in my voice.
  Uses no-ai-slop when installed, with a bundled clean-prose fallback; Amazon
  writing style for memos and proposals; plain-English how-tos for human-facing
  instructions. Don't use when the user only wants a grammar pass, a 6-page
  narrative, or to humanize copy.
argument-hint: "[draft path or pasted text]"
license: MIT
---

# voice-profile

> **Quick usage:**
> ```
> voice-profile
> voice-profile <draft path>
> voice-profile make this sound like me
> ```
>
> If invoked with no draft, ask for the text. Do not invent a sample.

Compose existing writing skills. Do not invent a personality. Do not bend facts
to sound like the writer.

## Workflow

### Step 1 — Parse arguments

Parse arguments from the active host's skill invocation:

- If empty or `--help`: show the usage hint above, then ask for the draft and
  stop until text is supplied.
- If a path is given, read that file.
- If the user pasted text, use that text.

### Step 2 — Confirm the job

Confirm audience, surface, and register before editing.

### Step 3 — Load companion skills

1. If `no-ai-slop` is installed, read and apply it. Otherwise, apply the
   [built-in clean-prose fallback](#built-in-clean-prose-fallback). After a
   rewrite, run the fallback self-check below in either case.
2. If the piece is a proposal, decision, hiring memo, or "why we should do X,"
   also read and apply the sibling `amazon-writing-style` skill. From that skill
   directory, run `python3 scripts/audit_text.py`. How-tos and reference docs
   skip the Amazon auditor unless the user asked for it.
3. If the piece is human-facing instructions (docs, setup, README, recipe),
   apply [plain-english how-tos](plain-english.md) in this folder. Code comments
   and commit messages are excluded.
4. Do not load `humanizer` unless the user asked to humanize. It adds
   personality this profile does not authorize.

### Step 4 — Edit, then stop

Minimum change that helps. Do not full-rewrite strong copy to prove the skill
ran. One polish pass against confirmed rules and the clean-prose self-check.
Stop.

Zero process residue in the deliverable: no "per the voice profile," no rule
names, no edit narration. If the user asks, put that in a short **What changed**
section only.

## Accuracy first

For technical content, contracts, evaluator results, and interview evidence:
accuracy beats voice. Never change a count, verdict, file path, or who did what
to improve the sentence.

## Registers (draft)

Personal registers are **draft**. Do not treat quality-words ("direct," "warm")
as rules. Confirmed observable rules live in [registers.md](registers.md) only
after a verdict. Until then, use the routing table:

| Audience / stakes | Register | Skills |
| --- | --- | --- |
| Interviewer how-to, README, recipe | How-to | clean prose + plain-English |
| Evaluator policy, contracts | Reference | clean prose; define terms at first use |
| `feedback.md`, discussed-eval | Interview evidence | [feedback packet](feedback-recipe.md); clean prose; no hire-score theater |
| Memo / "we should ship this" | Amazon | clean prose + amazon-writing-style |
| Email, Slack, public post | Personal | stop and ask for samples if [registers.md](registers.md) has no confirmed rule for that surface |

One register per section. If a how-to needs background, put the explanation in
a skippable block. Do not mix tutorial, how-to, reference, and explanation in
the same section.

## Built-in clean-prose fallback

Preserve the writer's meaning, facts, vocabulary, cadence, bluntness, humor,
and real uncertainty. Make the minimum effective edit. Cut generic setup,
repetition, empty qualifiers, tangled sentences, and unsupported attribution.
Prefer concrete nouns, direct verbs, and active voice when they improve
clarity. Keep a distinctive sentence when it is already clear. Never invent a
claim, example, number, source, opinion, or personal detail.

Before delivery, check that:

1. Meaning, facts, and uncertainty match the source.
2. The point is clear and every changed sentence earns its place.
3. No unsupported detail or attribution was added.
4. The anti-patterns below are absent unless the source uses one deliberately
   as part of the writer's voice.
5. Strong, distinctive lines were left alone.

Fix any failed check, then run the list again.

## Anti-patterns

Use this list with either `no-ai-slop` or the bundled fallback. When the user
catches a new one, add it here:

- delve, foster, leverage, utilize, facilitate, empower, streamline, robust,
  cutting-edge, paradigm, tapestry, realm, beacon, multifaceted, meticulous,
  intricate, paramount, transformative, elevate, embark, supercharge, harness
- simply, just, easy, please (in instructions)
- "note that", "it's important to", "as mentioned above", "in order to",
  "prior to", "going forward"
- Binary contrast openers ("This is not X. It's Y.")
- Em dashes in short copy. Prefer a full stop.
- Claiming to detect that a human "wrote like AI." Name patterns, do not guess
  authorship.
- Inventing typos, biography, or hesitation to fake a person.

## Discovery tracks (not auto-run)

Do not invent samples. If the user wants a real personal-voice model, authorship
profile, publication system, or a standalone docs skill, follow
[discovery.md](discovery.md) and stop for their input.
