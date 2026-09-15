---
name: plain-english-docs
description: >
  Write plain-English documentation when a reader needs to understand or complete
  work: setup guides, READMEs, instructions, and explanations. Exclude code
  comments and commit messages.
license: MIT
---

# plain-english-docs

Make the reader's next action clear. Apply this skill automatically to any
reader-facing documentation or explanation. Skip code comments and commit
messages.

## Choose the section's job

Choose one mode before writing each section.

| Mode | Use it to |
| --- | --- |
| Tutorial | Teach a beginner by doing. |
| How-to | Help the reader finish one task. |
| Reference | Help the reader look up a fact. |
| Explanation | Give background and reasons. |

Use one mode in each section. Never switch between instructions and reasons in
the same section. When a how-to needs background, put it in a clearly named,
skippable explanation block.

## Draft for the reader

- Define each term a non-expert may not know in the sentence where it first
  appears. Do not send the reader to a glossary. For example: "Open the
  repository, the folder that holds this project's files."
- Write steps as commands. Give one action per step. Name the place before the
  action: "In Settings, click Publish." Use the visible label or menu name, not a
  screen direction.
- Put reasons in their own sentence or paragraph. Do not hide a reason inside a
  step.
- Use full stops. Do not use em dashes. Cut an aside that cannot stand as its own
  sentence.
- Use plain words: "wrong," not "suboptimal"; "use," not "leverage" or
  "utilize"; "before," not "prior to"; "to," not "in order to."
- Never write "simply," "just," "easy," or "please" in an instruction.

## Keep agent English out

Write the direct word instead. The banned words and phrases are:

- leverage
- utilize
- robust
- seamless
- streamline
- delve
- comprehensive
- note that
- it's important to
- as mentioned above

Treat close forms as banned. When the user identifies another agent-English word
or phrase, add it to this list and remove it from the current delivery.

## Give every failing step a way forward

After every step that can fail, say what failure looks like and what the reader
should do next. For example: "If the repository is not in the list, you do not
have permission to use it. Ask the repository owner to grant you access, then open
the list again."

## Check before delivery

Deliver only after all four checks pass:

1. The em-dash count is zero.
2. Every unfamiliar term is defined where it first appears.
3. Each section has one mode. Split any section that alternates between what and
   why.
4. Read the weakest sentence aloud. Rewrite it if it needs a second read.
