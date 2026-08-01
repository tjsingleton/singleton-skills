# singleton-skills

A portable collection of [Agent Skills](https://agentskills.io/) with shared
discovery for Codex and Cursor, an explicit Claude Code route, and an optional
native Claude plugin.

The repository contains more skills than the current portable-core candidate.
The skills in `supported-skills.txt` are contract-tested candidates for the
intended hosts below; the remaining skills are available for use and development
but are not yet portability-certified.

## Support matrix

| Skill | Portable-core status | Hosts | Notes |
| --- | --- | --- | --- |
| `git-triage` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Network-free local snapshot by default; remote refresh and mutations require explicit approval. |
| `imessage-search` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | macOS Messages access and Full Disk Access are environmental requirements. Small-model delegation is optional; direct execution is the guaranteed fallback. |
| All other repository skills | Available, not certified | Varies | Installed only with the explicit `all` selection or exposed by the native Claude plugin. |

The automated suite verifies the portable contracts and simulates both shared
and Claude discovery in temporary roots. Live Claude Code, Codex, and Cursor
discovery and behavior smokes remain pending. Until those pass, this matrix
expresses intended portable support, not certified live cross-host support or
evidence that every repository skill has cross-agent parity.

## Installation

The ownership-safe symlink installer refuses foreign files, directories, and
links. It records checkout-specific provenance in
`.singleton-skills-links.json`, allowing uninstall to remove only links owned by
this checkout.

### Shared route: Codex and Cursor

`just install` installs only the supported set into the shared Agent Skills
directory:

```bash
just install
# equivalent to: just install set=default target=shared
```

The shared destination is resolved in this order:

1. the `shared_dir` argument;
2. `SINGLETON_SHARED_SKILLS_DIR`;
3. `$HOME/.agents/skills`.

Install every available skill only when that broader, uncertified set is
intentional:

```bash
just install set=all target=shared
```

### Claude Code supported-only route

Install the supported set into Claude's explicit skill directory:

```bash
just install set=default target=claude
```

The Claude destination is resolved from `claude_dir`, then
`SINGLETON_CLAUDE_SKILLS_DIR`, then `$HOME/.claude/skills`.

To install into both shared and Claude destinations atomically:

```bash
just install set=default target=all
```

Inspect support, installation, and ownership independently with `just list`, or
remove only installer-owned links with `just uninstall`. Both accept the same
`target`, `shared_dir`, and `claude_dir` parameters; uninstall also accepts
`set=default|all`.

### Native Claude plugin: all skills

The existing Claude Code plugin exposes all repository skills and is therefore
an all-skills, not-yet-portability-certified route:

```text
/plugin marketplace add /path/to/singleton-skills
/plugin install singleton-skills@singleton-skills-dev
```

Do not enable the native plugin and Claude symlink installation at the same
time. Claude may discover the same skill twice.

## iMessage environment and privacy

`imessage-search` runs only on macOS systems with a local Messages database. The
application or service that actually reads the database—such as the terminal
hosting Claude Code or Codex CLI, Codex App, Cursor, an SSH host process, or a
launch service—must have Full Disk Access. Restart that responsible process
after changing access.

The live database is read-only. A static archive is optional and must be
configured explicitly; no personal path or cutoff is inferred:

```bash
export IMESSAGE_ARCHIVE_DB="/path/to/archive/chat.db"
export IMESSAGE_ARCHIVE_CUTOFF="2025-12-31T23:59:59Z"
export IMESSAGE_ARCHIVE_CUTOFF_SOURCE="configured"
```

Archive fallback and acceptance of results that extend beyond the cutoff remain
explicit decisions. The standard-library decoder is the baseline;
`pytypedstream` is an optional enhancement.

When a host supports capability-based subagents, the parent may delegate only
the bounded runner step to the smallest/fastest model capable of local tool
execution. Delegation is not required. If routing is unavailable, rejected, or
cannot access Messages, the parent runs the identical normalized request
directly and preserves the same privacy and completeness checks.

## Dependencies

Environmental dependencies are separate from agent dependencies:

- Both supported skills require the local tools they invoke: Git for
  `git-triage`, and Python 3 plus macOS Messages data for `imessage-search`.
- GitHub CLI (`gh`) and `pytypedstream` are optional enhancements.
- No OMX, OMC, provider-specific role, named subagent, or Claude-specific path
  is required by the supported portable core.
- Capability-based iMessage delegation is optional; direct parent execution is
  always the fallback.

## Repository structure

```text
singleton-skills/
├── .claude-plugin/          # Native Claude plugin metadata
├── skills/<skill-name>/
│   ├── SKILL.md             # Portable skill definition and discovery metadata
│   ├── scripts/             # Optional bundled helpers
│   └── evals/               # Optional evaluations and contract tests
├── scripts/                 # Repository tooling and installer
├── tests/                   # Repository conformance and regression tests
├── supported-skills.txt     # Contract-tested/default candidate set
├── AGENTS.md
├── justfile
└── README.md
```

Every discoverable skill has a `SKILL.md` with YAML frontmatter whose `name`
matches its directory and whose `description` states when to use the skill.

## Development and verification

Create a skill with `just new name=my-skill`. The default install remains
limited to `supported-skills.txt`; use `set=all` while intentionally testing an
uncertified skill.

Run the full public-safe suite with one command:

```bash
just check
```

The check runs repository unit/conformance tests, Git triage contract tests, and
Python bytecode compilation. Fixtures and discovery simulations use temporary
directories and synthetic data; they never inspect or modify real home skill
installations, contacts, or Messages databases.

## Public repository notice

This repository is public. Never commit secrets, credentials, API keys,
personal paths, real contacts, or message data. Review every change before
publishing.
