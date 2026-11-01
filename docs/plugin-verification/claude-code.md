# Claude Code plugin verification

Checked on 2026-11-01 with Claude Code 2.1.314 for TJ-152.
Installation and real-host discovery passed. Representative invocation remains
blocked by an expired OAuth session that could not be refreshed. This is partial
verification, not completed behavioral acceptance or cross-host certification.

## Selected release and discovery

The selected release is version 1.5.0 at source revision
`f8859301c6c9a55056e5eae2a99320c54d0c6405`, obtained from the GitHub branch
`codex/tj-150-plugin-first`. The marketplace clone resolved to that revision.
All 98 files listed in its release manifest matched the installed cache's
SHA-256 hashes. The installed registration uses a native plugin cache and no
longer uses the development checkout through `readFromFolder`.

A real `claude --print` session in a neutral temporary directory discovered all
27 `singleton-skills:` namespaced skills, including
`singleton-skills:amazon-writing-style`. The session restricted tools to Skill,
Read, and the bundled Python auditor, disabled hooks, loaded no MCP servers,
and used a synthetic writing sample. Authentication failed before model work;
there is no successful host-produced rewrite or bundled-script invocation.
A direct local run of the installed auditor reported the expected two issues:
`significantly` and `due to the fact that`. That supporting check does not
replace execution through the host.

The read-only overlap inventory found 22 existing skill entries across the
Claude and shared skills directories. They were retained. Namespaced invocation
selects the plugin explicitly; this check does not prove an unqualified name's
precedence or authorize retiring any overlap.

## Installation and upgrade

Back up the existing Claude settings, known marketplace registration, installed
plugin registration, and previous plugin cache outside the public repository.
Record the previous marketplace source, cache identity, and any development
folder registration. Use the CLI's help for the installed version.

```sh
claude plugin marketplace add \
  'https://github.com/tjsingleton/singleton-skills.git#codex/tj-150-plugin-first' \
  --scope user --json
claude plugin update singleton-skills@singleton-skills --scope user --json
claude plugin list --json
```

If `extraKnownMarketplaces` declares a different source, update only the
Singleton Skills declaration to match the selected Git source and branch before
adding it. Verify the clone revision and installed file hashes after every
upgrade; a version label alone is insufficient. A moving branch can acquire
new commits after this check, so require the recorded revision to match.

The pre-existing registration already reported version 1.5.0 while its old
cache differed from this release in 35 files. Both update and install initially
refused to replace it because the version was unchanged. After preserving its
cache and configuration privately, the supported reinstall resolved this:

```sh
claude plugin uninstall singleton-skills@singleton-skills --scope user --keep-data --json
claude plugin install singleton-skills@singleton-skills --scope user --json
```

Do not manually delete caches or shared skill entries. Use a fresh host session
for discovery and invocation after installation. Future releases should use a
new coordinated version to avoid this same-version cache collision.

## Rollback and remaining check

To restore the prior source, add the previously recorded marketplace source
again and restore only the Singleton Skills marketplace declaration and plugin
registration from the private backup. Preserve unrelated settings changes. If
the previous cache is absent, restore its backed-up bytes before restoring its
registration. In this check the prior source was a development checkout;
restoration therefore also requires its recorded `readFromFolder` behavior.
The prior cache and all three configuration backups were preserved. Rollback
was documented but not executed.

After the operator restores Claude authentication, repeat the safe namespaced
writing audit in a neutral directory. Require evidence that the host reads the
installed skill, runs its bundled auditor on the supplied synthetic draft,
reports the two expected findings, and produces a rewrite without invented
metrics. Keep raw transcripts and local configuration evidence private. Until
that succeeds, TJ-152's invocation acceptance remains open.
