# Changelog

All notable changes to the **imessage-search** skill are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [Unreleased]

### Changed
- Added a versioned private-safe request/result contract shared by optional bounded
  delegation and direct execution.
- Made archive path, cutoff metadata, fallback authorization, and excluded handles
  explicit configuration.
- Live databases now use WAL-aware read-only access without SQLite's immutable flag.
- Boolean policy fields reject non-JSON-boolean values instead of coercing them.
- Explicit databases require trusted synthetic/completeness/cutoff metadata.
- Group searches use only the exact parent-resolved handle set; labels are display-only.
- Contact cache temporary SQLite/WAL/SHM copies are cleaned and outputs are `0600`.
- Delegated database-access failure can retry the identical request directly.
- Disabling display-name cache use now suppresses contact and chat names even when
  name fields are enabled for output.
- The delegation seam now passes only a CLI command and private request path, validates
  sanitized envelopes, preserves structured errors, and cleans request files.

## [1.2.0] - 2026-06-23

### Removed
- iMCP fallback path (`process_messages.py`). The iMCP/mcpproxy server crashed often,
  and the SQLite-direct path now covers all messages (including `attributedBody`), so the
  fallback added crash surface with no remaining benefit. The skill is SQLite-only.

## [1.1.0] - 2026-06-23

### Fixed
- **Decode `attributedBody`** — on Ventura+ macOS `message.text` is NULL for ~99% of
  messages (body is an Apple typedstream blob in `attributedBody`). `search_messages_sql.py`
  read only `text` and hard-filtered `m.text IS NOT NULL`, so it silently missed almost
  everything (e.g. "coffee": 0 hits → 65; "love": 1 → 759). This presented as "FDA trouble"
  but was not a permissions problem. Now selects and decodes `attributedBody`.

### Added
- `attributed_body.py` — typedstream decoder. Default is a dependency-free stdlib heuristic
  (99.95% coverage, 100% accuracy vs ground truth); optional `pytypedstream` used best-effort
  if installed (not a declared dependency; security-reviewed MEDIUM, see SKILL.md).

### Changed
- Keyword matching moved from SQL (`LOWER(m.text) LIKE`) into Python after decoding — SQL
  cannot reliably match a typedstream BLOB. SQL now filters only date/participant/direction.
- Open `chat.db` read-only. The portable runner later replaced the immutable connection
  with a WAL-aware short read transaction for changing live databases.

## [1.0.0] - 2026-04-12

### Added
- Initial skill: search and extract structured information from iMessages via imcp MCP
- Support for filters: from, since, before, limit, mode (members/group/both)
- argument-hint field for autocomplete display
- Moved from repo root to skills/imessage-search/ in singleton-skills plugin structure
