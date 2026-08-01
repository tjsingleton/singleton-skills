---
name: imessage-search
description: >
  Search and extract structured information from iMessages with a read-only,
  privacy-preserving local runner. Use for message-history queries, participant
  searches, date-bounded conversation searches, and nearby context retrieval.
argument-hint: >-
  "term" [from:"name"] [since:"date"] [before:"date"] [limit:N] [mode:members|group|both]
---

# iMessage Search

Use the bundled `scripts/search_messages_sql.py` runner. It has one versioned
request/result contract for both direct and delegated execution. The parent
agent owns interpretation, participant resolution, database policy, and any
approval to accept incomplete archive results.

This skill reads only local SQLite data. Never access a real Messages database
for tests, examples, or skill evaluation.

## Parent workflow

1. Resolve the active skill directory from this `SKILL.md`, then derive the
   runner as `<skill-directory>/scripts/search_messages_sql.py`. Do not use a
   provider-specific installation path or reconstruct a checkout path.
2. Parse the query, dates, direction, mode, and limit.
3. Resolve any requested participant locally. Remove handles configured by the
   user as their own handles. Never infer ownership from a display name.
4. Create a normalized request using the contract below. A requested name that
   cannot be resolved must use `unresolved_error`; stop and ask for a correction
   or explicit unfiltered retry. Never silently use `not_requested`.
5. Decide the database policy and archive completeness before execution.
6. Prefer a bounded executor on the smallest/fastest model that can run local
   tools when the host supports capability-based subagent routing. Otherwise,
   or if delegated live access fails, run the identical command directly.
7. Parse the result envelope and surface completeness and warnings. Do not
   expose raw handles, row IDs, chat identifiers, database paths, cache paths,
   or unrelated message bodies.

## Normalized request v1

Write request JSON with restrictive permissions and delete it in a guaranteed
cleanup path. The runner accepts it through `--request`.

```json
{
  "schema_version": "imessage-search.request.v1",
  "query": "planning",
  "query_match": "word_boundary",
  "participant_scope": {
    "state": "resolved",
    "requested_label": "Example Contact",
    "handles": ["+15550001001"]
  },
  "excluded_handles": ["+15550001999"],
  "date_range": {"since": "2026-01-01", "before": "2026-02-01"},
  "mode": "both",
  "direction": "any",
  "limit": 20,
  "database_policy": {
    "source_preference": "live_then_archive",
    "archive_fallback_authorized": false,
    "allow_incomplete_archive": false,
    "archive_cutoff": "2025-12-31T23:59:59Z",
    "archive_cutoff_source": "configured",
    "explicit_db_metadata": null
  },
  "cache_policy": {"use_display_names": true},
  "output_policy": {
    "include_messages": true,
    "include_contact_names": true,
    "include_chat_names": true
  },
  "execution_mode": "direct"
}
```

Participant states are:

- `not_requested`: the user did not request a participant filter. This is the
  only state that permits an unfiltered query.
- `resolved`: the parent supplied at least one validated, non-excluded handle.
- `unresolved_error`: a requested participant did not resolve. The runner fails
  closed before opening a database.

Source preferences are `live_only`, `live_then_archive`, `archive_only`, and
`explicit_db`. An explicit `--db` is highest priority and selects source class
`explicit`, but the path alone never implies completeness. `requested_label` is
display-only; parent-resolved handles are the sole participant authority. Group
mode matches a group thread only when its complete handle set equals the
resolved handle set, so duplicate labels and partial overlap cannot broaden it.

Every boolean in `database_policy`, `cache_policy`, and `output_policy` must be
an actual JSON `true` or `false`. Strings, numbers, nulls, missing values, and
other coercible representations fail closed.

`cache_policy.use_display_names=false` prevents both contact-cache names and
chat display names from entering records, even when the output policy permits
name fields. Those permitted fields remain null rather than carrying names.

## Database configuration and completeness

The live database defaults to `~/Library/Messages/chat.db`. Configure a static
archive explicitly:

```bash
export IMESSAGE_ARCHIVE_DB="/path/to/archive/chat.db"
export IMESSAGE_ARCHIVE_CUTOFF="2025-12-31T23:59:59Z"
export IMESSAGE_ARCHIVE_CUTOFF_SOURCE="configured"
```

The cutoff may instead come from trusted sidecar metadata, but its source must
be recorded. `live_then_archive` requires `archive_fallback_authorized=true`
before fallback. If the requested window extends after the cutoff, it also
requires `allow_incomplete_archive=true`; the result then reports
`accepted_partial`. Missing cutoff metadata, unauthorized fallback, and
unaccepted incomplete coverage are errors.

An explicit database requires `database_policy.explicit_db_metadata`:

```json
{
  "trusted": true,
  "synthetic": true,
  "completeness": "complete",
  "cutoff": null,
  "cutoff_source": null
}
```

`trusted` asserts that the parent verified the metadata source; it is not
inferred from the path. `synthetic=true` is reserved for fixture databases and
requires `completeness=complete`. A non-synthetic database may declare
`complete`, `partial` with a trusted cutoff/source pair, or `unknown`. Partial
or unknown coverage blocks unless `allow_incomplete_archive=true`; accepted
results report `accepted_partial`. A partial database reports complete only
when the requested date window is wholly within its cutoff.

The live database is opened as SQLite URI `mode=ro`, without `immutable=1`, in
a short read transaction with a one-second busy timeout. This lets SQLite see
committed WAL rows and yields a consistent snapshot while a writer is active.
The connection is rolled back and closed promptly.

## Direct execution

```bash
python3 "<skill-directory>/scripts/search_messages_sql.py" \
  --request "<private-request-file>"
```

Pass archive configuration in the environment. For an explicit synthetic or
user-approved database, add `--db "<database-path>"` and supply its metadata in
the request. The legacy CLI can express a complete fixture with
`--db-metadata-trusted --db-synthetic --db-completeness complete`, or a bounded
export with `--db-metadata-trusted --db-completeness partial --db-cutoff
<timestamp> --db-cutoff-source <source>`. The command returns only the normalized
result envelope on stdout. Request files and captured output must be mode `0600`
and removed in a `finally`/trap path on success and failure.

## Optional bounded delegation

Delegation is an optimization, never a dependency. Use it only when the host
can select a small/fast tool-capable executor without relying on a particular
provider model or role name.

Give the executor only:

- the resolved runner path and private request-file path;
- the exact command to execute;
- the `imessage-search.result.v1` return requirement;
- a prohibition on permission changes, package installation, cache rebuilding,
  participant resolution, fallback selection, query broadening, and persistence.

Do not include unrelated conversation history or raw message records. The
external adapter callback receives only the exact command and the private
request-file path—not in-memory database configuration or contact mappings—and
returns command status through the sanitized envelope only. If delegation is
unavailable, rejected, or lacks database access, the adapter changes only
`execution_mode`, runs the identical normalized query directly through the CLI,
and removes the mode-`0600` request file in all paths. Only the parent may
authorize archive fallback or retry with altered policy.

## Result v1

The result contains:

- `status` and `execution_mode`;
- `participant_scope_state`;
- selected database class (`live`, `archive`, or `explicit`) without a path;
- cutoff, metadata source, coverage, fallback authorization, and completeness;
- result count, total count, truncation, warnings, and sanitized records.

Sanitized records may contain only requested display names, requested chat
names, timestamps, direction, and requested message bodies. Raw local records
containing handles, identifiers, and row IDs remain process-local and are never
serialized into the result envelope.

## Full Disk Access

Full Disk Access belongs to the responsible host process, not generically to
Python. Name the actual host when guiding the user: Claude Code's terminal,
Codex App or CLI host, Cursor, an SSH daemon/session host, or a launch service.
After changing access, restart that responsible application or service and
retry. A delegated process can have different access from its parent, so a
delegated live-access error returns to the parent; it does not choose an
archive.

## Decoder and cache notes

`attributed_body.py` provides the standard-library baseline for modern message
bodies whose `text` field is null. Optional `pytypedstream` support is
best-effort and always falls back to the bundled decoder.

`build_contacts_cache.py` can build local display-name caches. Cache rebuilding
is a separate, parent-owned action; a bounded executor must not perform it. The
builder removes copied database/WAL/SHM files on success and failure and writes
cache files with mode `0600`.
