# OpenAI plugin verification

This record covers TJ-153 and the selected TJ-150 release. Codex CLI passed a
representative synthetic workflow on 2026-11-01. ChatGPT Work remains pending;
Codex installation and behavior do not establish ChatGPT Work compatibility.

## Release and installation

- Plugin: `singleton-skills@singleton-skills`, version `1.5.0`.
- Source revision: `f8859301c6c9a55056e5eae2a99320c54d0c6405`.
- Distribution branch: `codex/tj-150-plugin-first`.
- Host: Codex CLI `0.166.0` on macOS.
- The marketplace snapshot resolved to the selected revision. All 98 installed
  release files matched the release inventory's SHA-256 values.
- Native `codex plugin list --marketplace singleton-skills --json` reported the
  plugin installed and enabled, with Git marketplace provenance.

Before installing, retain a private backup of relevant Codex configuration and
existing plugin cache. Preserve shared skill installations and unrelated plugins.
Use the supported marketplace and plugin commands:

```sh
codex plugin marketplace add tjsingleton/singleton-skills --ref codex/tj-150-plugin-first --json
codex plugin add singleton-skills@singleton-skills --json
codex plugin list --marketplace singleton-skills --json
```

The branch can advance. Check the resolved Git revision and installed hashes
against the selected release before claiming an upgrade succeeded. Version alone
cannot establish the installed contents.

## Representative invocation

A fresh, ephemeral Codex session explicitly selected
`$singleton-skills:amazon-writing-style`. The test used a neutral temporary
working directory and an isolated Codex profile with the selected installed
plugin copied into its native cache layout. Its local marketplace pointed to the
verified Git snapshot. Existing account authentication supplied the model session;
no new credentials were provisioned. Unrelated MCP and app integrations were not
configured in the verification profile.

The synthetic input was:

> Our team will significantly improve the amazing checkout flow in order to help many customers.

Codex discovered the namespaced skill from the version `1.5.0` cache, read its
instructions and bundled `scripts/audit_text.py`, and executed the script from
that skill directory. The process returned exit code 0 and three violations:
`significantly`, `many`, and `in order to`. Codex also identified unsupported
praise and returned a rewrite with explicit placeholders for missing outcome and
metric information. It invented no measurement.

The first attempt could not execute reads because the parent process sandbox
prevented Codex's nested `sandbox-exec`. The successful retry launched outside the
parent sandbox while keeping Codex's own read-only sandbox. An earlier attempt
with an unsupported model alias failed before invocation; the successful attempt
used the host's configured model.

This establishes real CLI discovery and representative behavior with an isolated
verification profile. It does not establish behavior in an already-running
Codex desktop chat, automatic selection among duplicate shared skills, every
packaged workflow, or private integrations. The actual user installation and the
isolated verification copy are distinguished above. Shared skill links remain.

## Upgrade and rollback

For an upgrade, back up the relevant state, select the intended branch or revision
with `codex plugin marketplace add ... --ref ...`, refresh that marketplace using
`codex plugin marketplace upgrade singleton-skills`, and install using
`codex plugin add singleton-skills@singleton-skills`. Check native discovery,
release hashes, and a fresh safe invocation again. A successful command or unchanged
version is insufficient evidence of refreshed contents.

For rollback, reselect the previously recorded source revision and use the same
supported commands to refresh and install it. Verify hashes and fresh discovery.
If supported commands leave stale same-version contents, retain the backup and
report rollback pending rather than deleting cache directories. Restore only the
relevant backed-up configuration after checking for intervening changes. Do not
replace the entire current configuration or delete shared installations.

Private command logs, backups, and resolved local paths remain outside the public
repository. No public marketplace submission occurred.

## ChatGPT Work

On 2026-11-01, the personal plugin directory in ChatGPT's web interface did not
list Singleton Skills. Add → Upload plugin archive rejected a compressed copy of
the combined registration archive with the message:

> Marketplace archive does not include any local plugins to upload

That archive includes marketplace catalogs whose source points to the repository
root. The observed rejection concerns marketplace interpretation; it does not
establish acceptance of a standalone plugin.

`just prepare-release OUTPUT REVISION` now also generates
`singleton-skills-work.tar.gz` from the same committed source. It omits only
`.claude-plugin/marketplace.json`, `.cursor-plugin/marketplace.json`, and
`.agents/plugins/marketplace.json`. Plugin manifests, skill instructions, scripts,
and references remain included. The original `singleton-skills.tar` registration
archive is unchanged. `release.json` records the standalone archive SHA-256 and
its per-file hash inventory under `work_upload`.

A standalone upload attempt was interrupted by the browser tooling error
"native pipe closed" before acceptance could be established. Live upload remains
pending browser extension file access. Generating the archive and checking its
contents do not establish host acceptance.

Independent installation, discovery, selected invocation, bundled-resource
behavior, and runtime-capability checks remain pending in ChatGPT Work. Shared
installation state is supporting context, not evidence of a completed Work test.

The command route follows [official OpenAI plugin packaging documentation](https://developers.openai.com/plugins/build/plugins).
The installed CLI help also documents `plugin add`, `plugin list`, and the
marketplace commands used here.
