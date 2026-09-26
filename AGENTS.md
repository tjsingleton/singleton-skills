This repository is the central registry for custom agent skills.

## Guidelines
- Default to reasonable assumptions.
- When ambiguity, conflict, or a subjective choice would materially affect the
  result, ask one focused, host-neutral clarification through the current
  host's normal user-facing channel.

## Multi-agent support
- Support multiple agent hosts where possible and keep core behavior
  host-neutral. Claude Code, Cursor, and Codex are the minimum compatibility
  target for the portable path.
- Provider-specific roles, named subagents, host-specific paths, and delegation
  must not be required. Optional host capabilities need a direct fallback.
- When otherwise equivalent host-specific choices are necessary, prefer Claude
  Code, then Claude Desktop, Claude Cowork, Cursor, Codex, Gemini, Pi, and
  other hosts. This preference is not a certification claim.

## Instruction precedence and scope
- Apply instructions in this order: system and developer instructions, the
  user's request, then repository guidance.
- The root `AGENTS.md` applies repository-wide. A nested `AGENTS.md` governs
  its subtree when repository guidance conflicts.
- `README.md`, `SKILL.md`, manifests, and tests provide contracts and context;
  they do not widen the requested scope or override applicable instructions.
- Surface material conflicts through the current host's normal user-facing
  channel.

## Candidate status and evidence
- `supported-skills.txt` is default-install/candidate input. Keep it, the
  README compatibility matrix, and conformance tests aligned when changing
  candidate status.
- Do not infer live cross-host certification from list membership, labels,
  simulated discovery, or native plugin exposure. Claim certification only
  after direct checks on every claimed host.

## Public repository notice
- Treat content intended for check-in as public.
- Do not include secrets, credentials, API keys, personal paths, real contacts,
  message data, or unredacted sensitive fixtures. Use synthetic or redacted
  data instead.
- Review the final diff. If public suitability is uncertain, require explicit
  user confirmation before proceeding.

## Verification
- For skill, installer, manifest, or test changes, run `just check` and inspect
  the relevant tests and final diff.

## Install

```
npx plugins@latest tjsingleton/singleton-skills
```
