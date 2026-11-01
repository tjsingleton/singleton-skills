# Cursor verification

This records the TJ-154 checks for release 1.5.0, source revision
`f8859301c6c9a55056e5eae2a99320c54d0c6405`, on 2026-11-01.
The release contains 27 skills. Local marketplace indexing succeeded;
installed-release and Cloud Agent acceptance remain pending.

## Prerequisites and supported commands

The checked desktop was Cursor 3.27.22 on macOS arm64. The checked Cursor
Agent CLI was `2026.10.22-27dcf5f`, signed into an existing account.
`agent --help` exposes plugin marketplaces and local plugin directories.
`agent plugin --help` exposes marketplace management, with installation
available through interactive `/plugins`.

The supported command accepts a branch, tag, or commit:

```bash
agent plugin marketplace add https://github.com/tjsingleton/singleton-skills \
  --git-ref f8859301c6c9a55056e5eae2a99320c54d0c6405
agent plugin marketplace list --format json
```

Keep the intended source immutable during verification. In interactive
`/plugins`, distinguish the Installed pane from Marketplace search results.
Browsing a released skill does not prove that the installed plugin uses it.
The account's marketplace source and the installed plugin's resolved commit
must both be read back.

Cursor documents [plugins and account/team marketplace controls](https://cursor.com/docs/plugins)
and the [plugin format and component discovery](https://cursor.com/docs/reference/plugins).
Team marketplaces require Teams or Enterprise. This check used an existing
user marketplace and did not submit a public marketplace listing.

## Observed local state

Before changes, the account marketplace and installed plugin resolved commit
`0e68bdfb940e00b64bda3db7a73bc640aa9e91f7`. Their metadata was backed up
privately. Shared skill installations and existing caches were retained.

The exact-commit marketplace command reported success and materialized the
selected release locally. All 98 release-manifest files in that marketplace
checkout matched their expected SHA-256 hashes. The real interactive CLI's
Marketplace pane displayed 27 skills from Singleton Skills.

The Installed pane still displayed seven legacy skills. A fresh local CLI
startup did not advance the installed plugin. The account marketplace list
and installed cloud-plugin manifest still reported the old commit after the
successful add command. Therefore the successful command establishes local
indexing only. It does not establish an account source update, release
installation, or Cloud Agent availability.

A read-only headless discovery request produced no output after more than five
minutes and was stopped. It supplied no discovery or invocation evidence.

Installed-plugin details exposed Try in chat and Uninstall. Marketplace
details for the already installed plugin exposed no update action. Resolving
this through supported account or host controls remains required. Do not edit
internal plugin databases or delete caches to force an update.

## Upgrade and rollback

Capture the current account marketplace URL/ref and installed plugin identity
before an upgrade. Add or re-index the intended GitHub source through supported
controls, then read back both marketplace and installed identity. Start a new
agent and verify the cached release hashes before invoking a namespaced skill.
Same-version manifests can hide old source contents; version 1.5.0 alone is
insufficient evidence.

Rollback selects the previous recorded GitHub revision through supported
marketplace controls and reinstalls or selects that plugin through `/plugins`.
For this check, the previous revision is recorded above. Read back the selected
installed commit and rerun the representative invocation. Keep the private
backup until restoration is verified. Local backup restoration alone cannot
undo an account-side marketplace change.

## Cloud Agent acceptance

Cursor documents [Cloud Agent access and prerequisites](https://cursor.com/docs/cloud-agent)
and a [public Cloud Agents API](https://cursor.com/docs/cloud-agent/api/endpoints).
Repository-based cloud startup requires connected source control and an
eligible account. The API requires a generated user or service-account API
key; local CLI login is separate. No API key was configured in this check's
environment, and session credentials were not extracted.

A CLI worker registers a machine for cloud execution. It does not itself
launch a new Cloud Agent and does not prove independence from local shared
skills. No worker was started for this verification.

The remaining cloud check must start a new agent through supported Cursor
controls after the account marketplace installation resolves the selected
release. Record the remote installed revision, discover the plugin through
the host, invoke a safe synthetic input, and resolve a bundled reference or
script. Avoid repository-local skill paths as installation evidence. Record
missing platform capabilities separately from skill discovery.

## Remaining acceptance evidence

- Installed Cursor plugin hashes matching the selected release.
- Real host discovery and safe invocation from that installed plugin.
- Bundled-resource resolution through the host.
- Independent discovery, invocation, and resource resolution in a newly
  started Cloud Agent.

The checks above do not authorize shared-install retirement. They do not
certify all 27 skills or macOS-only integrations in a cloud environment.
