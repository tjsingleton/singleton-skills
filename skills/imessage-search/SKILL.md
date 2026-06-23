---
name: imessage-search
description: >
  Search and extract structured information from iMessages.
  Use this skill whenever the user wants to search their messages, find past conversations, extract
  structured data from texts (e.g., "who did I ask to sing?", "when did I last text about X?",
  "find messages from Jane about the project"), fetch conversation context around a specific message,
  or analyze message history. Trigger on any request involving iMessages, texts, message history,
  or conversation search — even if the user doesn't say "iMessage" explicitly.
  Supports query syntax: "term" from:"name" since:"date" before:"date" limit:N mode:members|group|both
argument-hint: >-
  "term" [from:"name"] [since:"date"] [before:"date"] [limit:N] [mode:members|group|both]
---

# iMessage Search

> **Quick usage:**
> ```
> "term" [from:"Name or Group"] [since:"date"] [before:"date"] [limit:N] [mode:members|group|both]
> ```
> Examples:
> - `"sing" from:"NC Worship Team" since:"1/1" limit:5`
> - `from:"Larry" since:"last week" --sent`
> - `"Johnson proposal" since:"last month" mode:group`
>
> If invoked with no arguments, show this hint and wait for a query.

Two search paths — use the best available:

| Path | When available | Speed | Capabilities |
|------|---------------|-------|--------------|
| **SQLite direct** (`search_messages_sql.py`) | Always (live DB needs FDA; archive always) | Fast | Full recipient context, group chat detection, no MCP round-trips |
| **iMCP fallback** (`process_messages.py`) | iMCP server available | Slower | No recipient for sent msgs, no group names |

**Default DB paths** (auto-detected in priority order):
1. `~/Library/Messages/chat.db` — live (needs Full Disk Access for the process that runs the script)
2. `/Volumes/DataDock/Users/tjsingleton/Archives/OldArchives/Messages/chat.db` — archive (always accessible)

---

## Message body decoding (attributedBody)

On modern macOS (Ventura+), `message.text` is NULL for ~99% of messages — the body
lives in the `attributedBody` BLOB as an Apple "typedstream" `NSAttributedString`.
A search that reads only `text` finds almost nothing. `search_messages_sql.py` selects
both columns and decodes the body via `attributed_body.py` (`message_text()`):

- **Default: pure standard library.** A dependency-free byte-scan heuristic — zero
  supply-chain exposure. Validated at 99.95% coverage and 100% accuracy against rows
  that carry both `text` and `attributedBody`.
- **Optional upgrade: `pytypedstream`.** If `pip install pytypedstream` is present it is
  used first (best-effort), else the heuristic runs. It is **not** a declared dependency.
  Security review: MEDIUM (known-good author, pure-Python, no network/eval, no CVEs; but
  crashes on multiline strings and is single-maintainer). Our wrapper catches its failures
  and falls back to the heuristic, so installing it can only help, never break. Pin it
  (`pytypedstream==0.1.0`) with a hash if you adopt it.

> Note on FDA: Full Disk Access is granted to the **responsible process** (the app at the
> top of the process tree — your terminal, or whatever launched Claude Code), not to
> `python3`/`sqlite3`. Granting "Terminal" FDA does nothing for an SSH/launchd/cron/Electron
> context with a different responsible process. The DB is opened read-only + immutable, so it
> reads `chat.db-wal` and never locks Messages.app.

---

## Query Syntax

| Field | Example | Meaning |
|-------|---------|---------|
| positional | `"sing"` | keyword search |
| `from:` | `from:"NC Worship Team"` | contact or group name |
| `since:` / `filter:` | `since:"1/1"` | start date (natural language ok) |
| `before:` | `before:"March"` | end date |
| `limit:` | `limit:5` | max results shown |
| `mode:` | `mode:both` | `members` \| `group` \| `both` (default: `both`) |

---

## Search Modes

**`members`** — any message to/from any member of the group, across all 1:1 and group conversations  
**`group`** — messages within group threads only (chats where `chat_identifier LIKE 'chat%'` and contains any group member)  
**`both`** — union of both, deduplicated. **Use this as the default.**

> Note: group mode uses `chat_identifier LIKE 'chat%'` to distinguish group threads from 1:1s — no member-count threshold needed.

---

## Pre-flight Check

**Before dispatching to a subagent**, run this check whenever the query window may extend past **2025-09-04** (the archive DB cutoff):

### 1. Does the query need the live DB?

If `since:` is absent OR `before:` is after 2025-09-04, the query may cover post-cutoff messages. The archive only holds data through 2025-09-04 — any messages after that date require the live DB (`~/Library/Messages/chat.db`), which needs Full Disk Access (FDA).

### 2. Test live DB access

Run in a shell:
```bash
sqlite3 ~/Library/Messages/chat.db "SELECT 1" 2>/dev/null && echo "ACCESSIBLE" || echo "NOT_ACCESSIBLE"
```

Or, equivalently, `find_db()` in `search_messages_sql.py` now tests actual connectivity and emits a warning to stderr if FDA is missing.

### 3. Branch on result

**If live DB IS accessible** → proceed normally (script auto-selects live DB first).

**If live DB is NOT accessible AND query window extends past 2025-09-04**:

> **Full Disk Access required for complete results**
>
> Messages after **2025-09-04** are only in the live iMessage database
> (`~/Library/Messages/chat.db`), which requires Terminal Full Disk Access.
>
> **To grant FDA:**
> 1. Open **System Settings → Privacy & Security → Full Disk Access**
> 2. Enable the toggle next to **Terminal** (or the app you're running Claude Code from)
> 3. Restart Terminal, then retry your search
>
> **To search anyway with archive-only results** (data through 2025-09-04 only):
> Confirm and the search will run against the archive — results will be
> **truncated** and will not include any messages after 2025-09-04.

Do not proceed to the subagent dispatch until the user confirms (archive fallback) or grants FDA.

---

## Workflow

### Step 1 — Parse & Resolve (in parallel)

Simultaneously:
1. Parse query syntax → keyword, date range, user limit, mode
2. Resolve `from:` name via local cache (no MCP needed):
   - `~/.cache/imessage-groups.json` — group name → phone handles
   - `~/.cache/imessage-contacts.json` — contact name → phone handles
   - Own handles (TJ Singleton) are **automatically excluded** — they don't appear in participant joins
   - If cache miss → fall back to `imcp:contacts_search`; if still not found → search without participant filter and note it

**Cache rebuild:** `python build_contacts_cache.py --groups ~/.cache/imessage-groups.json`

### Step 2 — Delegate to Subagent

Spawn a `general-purpose` subagent:

```
Search iMessages and return structured results.

## Parameters
keyword: "<term>"
from_name: "<group or contact name>"    # already resolved to handles below
participant_handles: [<e164 phones>]    # from cache lookup, own handle excluded
since: "<ISO date or null>"
before: "<ISO date or null>"
mode: "both"                            # members | group | both
sent_only: false
limit: <N or null>

## Steps

1. Run search_messages_sql.py (primary):
   python ~/.claude/skills/imessage-search/scripts/search_messages_sql.py \
     --query "<keyword>" \
     --from "<group_name>" \
     --since "<date>" \
     --mode both \
     [--sent | --received] \
     --limit <N> \
     --contacts ~/.cache/imessage-contacts.json \
     --groups ~/.cache/imessage-groups.json \
     --output /tmp/messages_out.json \
     --table --summary

2. If chat.db is inaccessible (auth error), fall back to iMCP path:
   a. Call imcp:messages_fetch via mcpproxy call_tool_read
   b. Save raw response to /tmp/messages_page_1.json
   c. Paginate: if results == 100, set end = oldest createdAt, fetch again
   d. Resolve sender handles via contacts cache (not contacts_search)
   e. Run process_messages.py on accumulated pages

3. Return: table output, JSON contents, total count, any truncation notice
```

### Step 3 — Fetch Context Around a Message

For surrounding conversation context:

```bash
python search_messages_sql.py \
  --db <path> \
  --from "<other party handle or name>" \
  --since "<message_timestamp - 30min>" \
  --before "<message_timestamp + 30min>" \
  --limit 50
```

---

## Scripts

### `scripts/search_messages_sql.py` — primary search

```
python search_messages_sql.py [options]

  --db            Path to chat.db (auto-detects live → archive)
  --query, -q     Keyword (word-boundary match by default)
  --query-substr  Use substring match instead
  --from          Contact or group name (resolved via cache)
  --mode          members | group | both  (default: members)
  --since         Start date
  --before        End date
  --sent          Only sent messages
  --received      Only received messages
  --limit, -n     Max results (default: 20)
  --all           No limit
  --contacts      ~/.cache/imessage-contacts.json
  --groups        ~/.cache/imessage-groups.json
  --output, -o    Write JSON to file
  --table         Print markdown table to stderr
  --summary       Print count line to stderr
```

### `scripts/process_messages.py` — iMCP fallback

```
python process_messages.py page1.json [page2.json ...] [options]

  --output, -o     Write JSON to file
  --contacts       JSON map {handle: name}
  --filter-sent / --filter-recv
  --query          Post-filter keyword (word-boundary)
  --query-substr   Use substring match
  --limit N        Cap results
  --limit-recent   Keep most recent (default: oldest)
  --table          Markdown table to stderr
  --summary        Count line to stderr
```

### `scripts/build_contacts_cache.py` — build/refresh cache

```
python build_contacts_cache.py [--abbu <path>] [--groups <output>] [-v]

Reads all Sources in the .abbu, writes:
  ~/.cache/imessage-contacts.json   {handle: "Display Name"}  (565 handles)
  ~/.cache/imessage-groups.json     {group: [handle, ...]}    (8 groups)
```

---

## Output Schema

Both scripts produce the same record shape:

```json
{
  "id": "1121",
  "timestamp": "2025-01-23T23:22:21Z",
  "direction": "sent",
  "contact": "Gay Stewart",
  "contact_handle": "+14045698507",
  "chat_name": "NC Worship Team",
  "chat_identifier": "+14045698507",
  "message": "Can you sing Amazing God on Sunday morning?"
}
```

`chat_name` is populated when `chat.display_name` is set (live DB with FDA). `chat_identifier` is always present — group threads start with `chat`, 1:1s are a phone/email.

---

## Example

> `/search-messages "sing" from:"NC Worship Team" since:"1/1" limit:5`

1. **Resolve**: `NC Worship Team` → 12 handles (TJ excluded), `since:"1/1"` → `2026-01-01`
2. **Subagent**:
   ```
   python search_messages_sql.py \
     --query sing --from "NC Worship Team" --since 2026-01-01 \
     --mode both --limit 5 --table --summary
   ```
3. **Output**: table + `"5 of 10 messages (5 more)"`

---

## Notes

- **Full Disk Access** unlocks the live DB: System Settings → Privacy & Security → Full Disk Access → Terminal
- Without FDA, the archive at `/Volumes/DataDock/.../Messages/chat.db` is used automatically
- Group threads: `chat_identifier LIKE 'chat%'`; 1:1s: phone or email
- `chat_name` is null in the archive (pre-dates named groups); live DB has it
- Own handles (TJ Singleton) are excluded from participant queries automatically
- Cache files: `~/.cache/imessage-contacts.json`, `~/.cache/imessage-groups.json`

---

## FDA and the 2025-09-04 archive cutoff

### The two databases

| Database | Path | Coverage | Access |
|----------|------|----------|--------|
| **Live** | `~/Library/Messages/chat.db` | All messages (continuously updated) | Requires FDA |
| **Archive** | `/Volumes/DataDock/Users/tjsingleton/Archives/OldArchives/Messages/chat.db` | Through **2025-09-04** only | Always readable |

### Why this matters

The archive DB is a snapshot taken on or before 2025-09-04. Any iMessage sent or received after that date exists **only** in the live DB. Without FDA, searches that span post-cutoff dates will silently miss recent messages or return no results at all.

### How the script handles it

`find_db()` in `search_messages_sql.py` tests actual read access (not just file existence) before selecting the live DB. If FDA is not granted:
- A warning is printed to stderr: `"live DB exists but is not readable (FDA not granted). Falling back to archive."`
- The archive is used automatically
- Results are silently truncated at 2025-09-04

### Granting FDA

1. **System Settings → Privacy & Security → Full Disk Access**
2. Click **+** and add **Terminal** (or the app running Claude Code)
3. Toggle it **on**
4. **Restart Terminal** — the change takes effect on next launch

### Quick access test

```bash
sqlite3 ~/Library/Messages/chat.db "SELECT 1" 2>/dev/null && echo "FDA: granted" || echo "FDA: NOT granted (archive only)"
```

### When to surface the pre-flight warning

Always run the pre-flight check (see **Pre-flight Check** section above) when:
- The query has no `since:` bound (may span all time, including recent)
- The `since:` or `before:` range overlaps or extends past 2025-09-04
- The user asks about "recent" messages or the current year
