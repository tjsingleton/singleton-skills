# Changelog

All notable changes to the **imessage-search** skill are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [Unreleased]

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
- Open `chat.db` read-only + immutable (`mode=ro&immutable=1`) — reads `chat.db-wal` without
  locking Messages.app, fixing "database is locked" and stale-result failure modes.

## [1.0.0] - 2026-04-12

### Added
- Initial skill: search and extract structured information from iMessages via imcp MCP
- Support for filters: from, since, before, limit, mode (members/group/both)
- argument-hint field for autocomplete display
- Moved from repo root to skills/imessage-search/ in singleton-skills plugin structure
