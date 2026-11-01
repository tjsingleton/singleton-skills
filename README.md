# singleton-skills

A portable collection of [Agent Skills](https://agentskills.io/) with native
plugin distribution for released use and a contract-tested shared route for
development and compatibility. The repository also packages its skills using the
[Agent Plugins standard](https://agent-plugins.org/).

The repository contains more skills than the current portable-core candidate.
The skills in `supported-skills.txt` are contract-tested candidates for the
intended hosts below; the remaining skills are available for use and development
but are not yet portability-certified.

## Support matrix

| Skill | Portable-core status | Hosts | Notes |
| --- | --- | --- | --- |
| `agentic-harness-designer` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Designs agent harnesses around tools, authority, execution, context, evaluation, and operator visibility. |
| `amazon-writing-style` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Audits and rewrites prose against six Amazon writing rules. |
| `current-info-search` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Uses Perplexity Agent API for time-sensitive answers, with source and date discipline. |
| `git-triage` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Network-free local snapshot by default; remote refresh and mutations require explicit approval. |
| `heavy-file-ingestion` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Converts large or binary local documents into hash-versioned, source-anchored artifacts before analysis. |
| `html-artifacts` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Creates self-contained offline HTML deliverables with accessible, responsive layouts. |
| `imessage-search` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | macOS Messages access and Full Disk Access are environmental requirements. Small-model delegation is optional; direct execution is the guaranteed fallback. |
| `linear-author` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Drafts and rewrites issues with a shared preservation and mutation contract; connected Linear capabilities are optional. |
| `linear-triage` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Read-only actionable frontier and inconsistency findings; requires the sibling linear-author shared contract. |
| `linear-update` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Reconciles progress and evidence with minimal verified edits; requires the bundled linear-author shared contract. |
| `visible-delegation` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Delegates bounded work through named, attachable tmux sessions and independently verifies results before cleanup. |
| `organize-screenshots` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Organizes screenshot collections into chronological, deduplicated groups. |
| `pdf-document-ingestion` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Ingests PDF documents into searchable, structured text. |
| `plain-english-docs` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Writes reader-facing documentation and instructions in plain English. |
| `self-pr-merge` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Reviews a user's own PR before a separately authorized squash merge. |
| `voice-profile` | Candidate; contract-tested | Intended: Claude Code, Codex, Cursor | Routes TJ's writing jobs to no-ai-slop, Amazon memos, and plain-English how-tos. |
| All other repository skills | Available, not certified | Varies | Installed only with the explicit `all` selection or exposed by a native plugin. |

The automated suite verifies the portable contracts and simulates both shared
and Claude discovery in temporary roots. Live Claude Code, Codex, and Cursor
discovery and behavior smokes remain pending. Until those pass, this matrix
expresses intended portable support, not certified live cross-host support or
evidence that every repository skill has cross-agent parity.

## Installation

### Recommended: Agent Plugins CLI

Install the plugin into detected supported agent tools at user scope:

```bash
npx plugins@latest tjsingleton/singleton-skills -
```

The CLI defaults to user scope and auto-detects installed targets. This route
exposes every skill in the repository, including skills outside the
portable-core candidate set. To inspect the package without installing it, run
`npx plugins discover tjsingleton/singleton-skills`.

The ownership-safe symlink installer refuses foreign files, directories, and
links. It records checkout-specific provenance in
`.singleton-skills-links.json`, allowing uninstall to remove only links owned by
this checkout.

### Shared route: explicit development and compatibility

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

### Claude Code supported-only compatibility route

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

### Host-native plugin routes: all skills

The native plugin manifests expose every skill under `skills/`. They are an
all-skills route and do not expand the portable-core certification claim.

Claude Code:

```text
/plugin marketplace add tjsingleton/singleton-skills
/plugin install singleton-skills@singleton-skills
```

Codex:

```bash
codex plugin marketplace add https://github.com/tjsingleton/singleton-skills
codex plugin add singleton-skills@singleton-skills
```

Cursor marketplaces are Git-backed. Register this repository, then install the
plugin interactively from Cursor's Marketplace panel:

```bash
cursor-agent plugin marketplace add https://github.com/tjsingleton/singleton-skills
```

For local development, Cursor Agent can load the checkout directly for a
session without registering a marketplace:

```bash
cursor-agent --plugin-dir /path/to/singleton-skills
```

Do not combine a host's native plugin route with a symlink route containing the
same skills. The host may discover duplicate skill names.

#### Clean-break migration from `singleton-skills-dev`

The marketplace and plugin IDs are now both `singleton-skills`. Before using
the following separately authorized removal commands, inventory affected
consumers and verify their replacements and restoration information. Preserve
unproven installations and direct-only skills.

Claude Code:

```text
/plugin uninstall singleton-skills@singleton-skills-dev
/plugin marketplace remove singleton-skills-dev
/plugin marketplace add tjsingleton/singleton-skills
/plugin install singleton-skills@singleton-skills
```

Codex:

```bash
codex plugin remove singleton-skills@singleton-skills-dev
codex plugin marketplace remove singleton-skills-dev
codex plugin marketplace add https://github.com/tjsingleton/singleton-skills
codex plugin add singleton-skills@singleton-skills
```

Cursor Agent, if the old marketplace was previously registered:

```bash
cursor-agent plugin marketplace remove singleton-skills-dev
cursor-agent plugin marketplace add https://github.com/tjsingleton/singleton-skills
```

This repository only supplies manifests and prints registration commands. It
does not publish a marketplace or modify Claude Code, Codex, Cursor, or shell
configuration. Run `just register` to print the export and registration commands
without applying them.

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
├── plugin.json             # Agent Plugins portable manifest
├── .claude-plugin/          # Native Claude plugin metadata
├── .cursor-plugin/          # Native Cursor plugin and marketplace metadata
├── .codex-plugin/           # Native Codex plugin metadata
├── .agents/plugins/         # Repo-local Codex marketplace metadata
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

## Prepare a release and migration inventory

Run `just bump ver=1.5.0` to coordinate the version-bearing manifests, review
and commit the intended release, then run:

```bash
just check
just prepare-release /tmp/singleton-skills-release HEAD
```

Preparation reads committed Git contents only, including all tracked skill
references and scripts. Uncommitted edits are excluded. Select an explicit
commit instead of `HEAD` when preparing an older release. The output directory
must not already exist. `release.json` records the resolved source commit,
coordinated version, skill inventory, SHA-256 of every packaged file, and archive
hash. The same archive contains Claude, OpenAI and Cursor registration files.
Review those contents before separately authorizing publication. Preparation
publishes nothing and changes no installed host configuration.

Before migration, generate a private read-only inventory:

```bash
just inventory all /tmp/example-shared /tmp/example-claude /tmp/consumers.json > /tmp/migration-inventory.json
```

Run the inventory script from the owning checkout: another worktree has distinct
provenance and conservatively reports the original links as unproven.
Omit root overrides to inspect the installer's configured shared and Claude
roots. The optional consumers file maps root kinds to observed consumers, for
example `{"shared": ["Cursor local", "other compatible host"], "claude": ["Claude Code"]}`.
The inventory enumerates existing entries, including broken links, foreign
content and names absent from the current package. Names present in the package
are overlap candidates, not proof that a replacement is installed. Only matching
checkout provenance establishes ownership; legacy links remain unproven.
Foreign file contents are never read or copied into the report.

Keep this output private and outside Git: it contains machine paths and
provenance. Consumer names are operator observations; completeness remains
unverified, and unknown roots remain unresolved. Inventory always retains every
entry and grants no cleanup authority. It records exact link values and existing
provenance for restoration, plus backup and replacement-verification requirements.
Before cleanup, retain source revisions and provenance backups, back up non-link
content, establish all consumers, and verify each replacement and restoration.

Verify Claude Code, Codex, ChatGPT Work, Cursor local, Cursor Cloud Agents, and
Grok Bot separately against the intended release. Cursor Cloud Agents and Grok
Bot use GitHub-backed Cursor marketplace distribution; local links cannot supply
remote installations. Record installed version/revision, selected discovery,
safe invocation, bundled-resource resolution, and dependency availability for
each target. Pending host checks remain pending; automated packaging tests and
marketplace registration do not certify live behavior. Use an explicit checkout
for development (`cursor-agent --plugin-dir /path/to/singleton-skills`, or local
marketplace registration where supported). Retain shared installations for any
consumer without a verified replacement.
