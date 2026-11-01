# Grok Bot marketplace verification

TJ-155 remains blocked after the November 1, 2026 live check.
The selected release is version 1.5.0 at commit
`f8859301c6c9a55056e5eae2a99320c54d0c6405`.

## Direct observations

The native Grok Bot app exposes account plugins through **Connect apps → Your
plugins**. The installed list shows Singleton Skills with 27 skills. Its detail
view lists the expected skill names, including `amazon-writing-style`,
`dev-skill`, and `session-operating-map`.

The detail view exposes an Uninstall action but no version, source revision,
update action, or per-Bot enabled state. The displayed count and names do not
prove that the selected release is installed or usable by a Bot.

The primary Bot's Library tab contains generated pages, files, and apps. It does
not expose plugin configuration. Account settings and composer actions also
provided no observed plugin enablement control. This is a record of the checked
controls, not a claim that no supported control exists elsewhere.

## Invocation result

A bounded read-only task asked the primary Bot to load `amazon-writing-style`,
resolve a bundled reference or evaluation resource, and rewrite this synthetic
sentence:

> We are excited to leverage our amazing solution to foster better outcomes.

The Bot replied that Singleton Skills was unavailable in its conversation. It
reported that exact-name lookup and search failed, that version and source
revision were unknown, and that it could not load a bundled resource. Its plain
rewrite was explicitly attributed to its own writing rather than skill use.
Those lookup results are Bot claims. The native transcript verifies the request
and reply, but did not expose the underlying tool trace.

Invocation and bundled-resource resolution therefore failed this check. An
installed account listing is insufficient evidence for per-Bot availability.

## Installation, update, and rollback

This native UI check made no installation, uninstallation, routine, schedule,
or shared-skill changes. The installed account entry remained present. No
rollback is needed for this lane. The only persistent change was the bounded
verification exchange in the primary Bot conversation.

The Cursor account marketplace lane owns source registration and update work.
Any later retry must record the selected source revision and the actual installed
revision independently, then repeat the Bot invocation. If the host cannot expose
or establish that identity, retain the blocker. Do not substitute another
Cursor target's success or a marketplace listing for Grok Bot evidence.

Before a future supported reinstall, record the existing source and installation
state and its supported restoration route. Preserve unrelated plugins, shared
skill directories, caches, and Bot routines. This check did not validate an
update or rollback flow and does not certify Grok Bot compatibility.
