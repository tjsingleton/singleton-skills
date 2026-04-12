#!/usr/bin/env python3
"""
Search iMessages directly from a chat.db SQLite database.

Faster and more complete than the iMCP path — provides full recipient context
for sent messages, group chat names, and attachment info.

Works against:
  - Live DB: ~/Library/Messages/chat.db  (requires Full Disk Access for Terminal)
  - Archive: /Volumes/DataDock/Users/tjsingleton/Archives/OldArchives/Messages/chat.db

Usage:
    python search_messages_sql.py [options]

Options:
    --db            Path to chat.db (auto-detects live then archive)
    --query, -q     Keyword to search (word-boundary match by default)
    --query-substr  Use substring match instead
    --from          Filter by contact name or group name (uses contacts/groups cache)
    --since         Start date (ISO, natural: "2026-01-01", "last month", "1/1")
    --before        End date
    --sent          Only sent messages
    --received      Only received messages
    --limit, -n     Max results to show (default: 20)
    --all           Show all results (no limit)
    --contacts      Contacts cache JSON (default: ~/.cache/imessage-contacts.json)
    --groups        Groups cache JSON  (default: ~/.cache/imessage-groups.json)
    --output, -o    Write JSON to file (default: stdout)
    --table         Print markdown table to stderr
    --summary       Print one-line summary to stderr

Output per record (same schema as process_messages.py):
    {
      "id": "rowid",
      "timestamp": "2025-01-23T23:32:00Z",
      "direction": "sent" | "received",
      "contact": "Larry Elrod",
      "contact_handle": "+14706401297",
      "chat_name": "NC Worship Team",     # group display_name or null
      "chat_identifier": "+14706401297",  # raw chat identifier
      "message": "Can you lead singing?"
    }
"""

import json
import os
import re
import sqlite3
import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# DB discovery
# ---------------------------------------------------------------------------

LIVE_DB = Path.home() / "Library/Messages/chat.db"
ARCHIVE_DB = Path("/Volumes/DataDock/Users/tjsingleton/Archives/OldArchives/Messages/chat.db")


def find_db(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    if LIVE_DB.exists():
        return LIVE_DB
    if ARCHIVE_DB.exists():
        return ARCHIVE_DB
    raise FileNotFoundError(
        "No chat.db found. Use --db to specify path, or grant Terminal Full Disk Access."
    )


# ---------------------------------------------------------------------------
# Date parsing
# ---------------------------------------------------------------------------

APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)

def apple_timestamp_to_iso(ts: int | None) -> str | None:
    if ts is None:
        return None
    dt = APPLE_EPOCH + timedelta(seconds=ts / 1_000_000_000)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_date(s: str) -> datetime:
    """Parse natural-ish date strings into UTC datetime."""
    s = s.strip().lower().lstrip("since").strip()
    now = datetime.now(timezone.utc)

    # Relative
    if s == "today":         return now.replace(hour=0, minute=0, second=0)
    if s == "yesterday":     return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)
    if s == "last week":     return now - timedelta(weeks=1)
    if s == "last month":    return (now.replace(day=1) - timedelta(days=1)).replace(day=1)
    if s == "last year":     return now.replace(year=now.year - 1, month=1, day=1)

    # M/D or M/D/YY or M/D/YYYY
    m = re.match(r'^(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$', s)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        year = int(m.group(3)) if m.group(3) else now.year
        if year < 100:
            year += 2000
        return datetime(year, month, day, tzinfo=timezone.utc)

    # ISO
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    raise ValueError(f"Cannot parse date: {s!r}")


def to_apple_ns(dt: datetime) -> int:
    """Convert datetime to Apple nanosecond timestamp."""
    return int((dt - APPLE_EPOCH).total_seconds() * 1_000_000_000)


# ---------------------------------------------------------------------------
# Contact / group cache
# ---------------------------------------------------------------------------

def load_cache(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def my_handles(contacts: dict) -> set[str]:
    """Return all handles that belong to the user (mapped to 'TJ Singleton' in contacts cache)."""
    return {h for h, n in contacts.items() if n == "TJ Singleton"}


def resolve_from(name: str, contacts: dict, groups: dict, exclude_me: bool = True) -> list[str] | None:
    """
    Resolve a contact/group name to a list of E.164 phone handles.
    Excludes own handles by default (they don't appear in chat_handle_join as participants).
    Returns None if not found.
    """
    own = my_handles(contacts) if exclude_me else set()

    # Exact group match
    if name in groups:
        phones = [h for h in groups[name] if re.match(r'^\+\d+$', h) and h not in own]
        return phones or None

    # Case-insensitive group match
    for gname, handles in groups.items():
        if gname.lower() == name.lower():
            phones = [h for h in handles if re.match(r'^\+\d+$', h) and h not in own]
            return phones or None

    # Contact name match (handle → name, invert)
    name_lower = name.lower()
    matches = [h for h, n in contacts.items()
               if n.lower() == name_lower and re.match(r'^\+\d+$', h) and h not in own]
    return matches or None


# ---------------------------------------------------------------------------
# Query builder
# ---------------------------------------------------------------------------

BASE_SELECT = """
    SELECT
        m.rowid,
        m.date,
        m.is_from_me,
        m.text,
        h.id AS sender_handle,
        c.display_name AS chat_name,
        c.chat_identifier
    FROM message m
    LEFT JOIN handle h ON m.handle_id = h.rowid
    LEFT JOIN chat_message_join cmj ON m.rowid = cmj.message_id
    LEFT JOIN chat c ON cmj.chat_id = c.rowid
"""


def _base_conditions(keyword, word_boundary, since_ns, before_ns, sent_only, recv_only):
    """Build the conditions and params shared across both query modes."""
    conditions = ["m.text IS NOT NULL"]
    params = []

    if keyword:
        conditions.append("LOWER(m.text) LIKE ?")
        params.append(f"%{keyword.lower()}%")

    if since_ns is not None:
        conditions.append("m.date >= ?")
        params.append(since_ns)
    if before_ns is not None:
        conditions.append("m.date < ?")
        params.append(before_ns)

    if sent_only:
        conditions.append("m.is_from_me = 1")
    elif recv_only:
        conditions.append("m.is_from_me = 0")

    return conditions, params


def build_members_query(
    keyword, word_boundary, participant_handles,
    since_ns, before_ns, sent_only, recv_only,
) -> tuple[str, list]:
    """
    Members mode: any message to/from any member of the group,
    across all 1:1 and group conversations.
    """
    conditions, params = _base_conditions(keyword, word_boundary, since_ns, before_ns, sent_only, recv_only)

    if participant_handles:
        placeholders = ",".join("?" * len(participant_handles))
        conditions.append(f"""
            m.rowid IN (
                SELECT cmj2.message_id FROM chat_message_join cmj2
                JOIN chat_handle_join chj ON cmj2.chat_id = chj.chat_id
                JOIN handle ph ON chj.handle_id = ph.rowid
                WHERE ph.id IN ({placeholders})
            )
        """)
        params.extend(participant_handles)

    where = " AND ".join(conditions)
    return BASE_SELECT + f"WHERE {where} ORDER BY m.date DESC", params


def build_group_chat_query(
    keyword, word_boundary, group_name, participant_handles,
    since_ns, before_ns, sent_only, recv_only,
) -> tuple[str, list]:
    """
    Group chat mode: messages within the named group thread itself.

    Strategy:
      1. Match by chat.display_name (works when FDA available or name is set)
      2. Fall back to finding chats that contain the most group members
         (handles archived DBs where display_name is NULL)
    """
    conditions, params = _base_conditions(keyword, word_boundary, since_ns, before_ns, sent_only, recv_only)

    group_conditions = []
    group_params = []

    # Strategy 1: by display_name
    if group_name:
        group_conditions.append("""
            cmj.chat_id IN (
                SELECT rowid FROM chat WHERE display_name LIKE ?
            )
        """)
        group_params.append(f"%{group_name}%")

    # Strategy 2: group chats (chat_identifier starts with 'chat') that contain ANY member.
    # Group threads always have a UUID-style identifier vs a phone/email for 1:1s.
    if participant_handles:
        placeholders = ",".join("?" * len(participant_handles))
        group_conditions.append(f"""
            cmj.chat_id IN (
                SELECT chj.chat_id
                FROM chat_handle_join chj
                JOIN handle ph ON chj.handle_id = ph.rowid
                JOIN chat gc ON chj.chat_id = gc.rowid
                WHERE ph.id IN ({placeholders})
                  AND gc.chat_identifier LIKE 'chat%'
            )
        """)
        group_params.extend(participant_handles)

    if group_conditions:
        conditions.append("(" + " OR ".join(group_conditions) + ")")
        params.extend(group_params)

    where = " AND ".join(conditions)
    return BASE_SELECT + f"WHERE {where} ORDER BY m.date DESC", params


def build_query(
    keyword, word_boundary, participant_handles, group_name,
    since_ns, before_ns, sent_only, recv_only, mode,
) -> tuple[str, list]:
    """
    mode: "members" | "group" | "both"
      members — any message to/from any member across all convos
      group   — messages within the group thread itself
      both    — union of both (deduplicated by rowid in Python)
    """
    if mode == "group":
        return build_group_chat_query(
            keyword, word_boundary, group_name, participant_handles,
            since_ns, before_ns, sent_only, recv_only,
        )
    # members or both — caller runs members query; "both" runs group query separately
    return build_members_query(
        keyword, word_boundary, participant_handles,
        since_ns, before_ns, sent_only, recv_only,
    )


# ---------------------------------------------------------------------------
# Word-boundary post-filter
# ---------------------------------------------------------------------------

def word_boundary_filter(records: list, keyword: str) -> list:
    pattern = re.compile(
        r'\b' + re.escape(keyword) + r'(?:ing|er|ers|ed|s|along)?\b',
        re.IGNORECASE
    )
    return [r for r in records if pattern.search(r["message"] or "")]


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def format_table(records: list, total: int) -> str:
    if not records:
        return "No messages found."
    shown = len(records)
    header = f"Showing {shown} of {total} message(s)"
    if total > shown:
        header += f" ({total - shown} more — use --all or increase --limit)"
    lines = [
        header + "\n",
        "| Timestamp | Dir | Contact | Chat | Message |",
        "|-----------|-----|---------|------|---------|",
    ]
    for r in records:
        ts = r["timestamp"] or ""
        d = "→" if r["direction"] == "sent" else "←"
        contact = r["contact"] or r["contact_handle"] or "(unknown)"
        chat = r.get("chat_name") or ""
        msg = (r["message"] or "").replace("\n", " ")
        msg = msg[:70] + ("…" if len(msg) > 70 else "")
        lines.append(f"| {ts} | {d} | {contact} | {chat} | {msg} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Search iMessages directly from chat.db")
    parser.add_argument("--db", help="Path to chat.db")
    parser.add_argument("--query", "-q", help="Keyword (word-boundary match by default)")
    parser.add_argument("--query-substr", action="store_true", help="Use substring match")
    parser.add_argument("--from", dest="from_name", help="Contact or group name")
    parser.add_argument("--mode", choices=["members", "group", "both"], default="members",
                        help="members=any convo with any member; group=group thread only; both=union (default: members)")
    parser.add_argument("--since", help="Start date (ISO or natural)")
    parser.add_argument("--before", help="End date")
    parser.add_argument("--sent", action="store_true")
    parser.add_argument("--received", action="store_true")
    parser.add_argument("--limit", "-n", type=int, default=20)
    parser.add_argument("--all", action="store_true", help="No limit")
    parser.add_argument("--contacts", default=str(Path.home() / ".cache/imessage-contacts.json"))
    parser.add_argument("--groups", default=str(Path.home() / ".cache/imessage-groups.json"))
    parser.add_argument("--output", "-o", help="Write JSON output to file")
    parser.add_argument("--table", action="store_true", help="Print markdown table to stderr")
    parser.add_argument("--summary", action="store_true", help="Print one-line summary to stderr")
    args = parser.parse_args()

    db_path = find_db(args.db)
    print(f"Using: {db_path}", file=sys.stderr)

    contacts = load_cache(Path(args.contacts))
    groups = load_cache(Path(args.groups))

    # Resolve --from
    participant_handles = None
    if args.from_name:
        participant_handles = resolve_from(args.from_name, contacts, groups)
        if participant_handles:
            print(f"Resolved '{args.from_name}' → {len(participant_handles)} handles", file=sys.stderr)
        else:
            print(f"Warning: could not resolve '{args.from_name}' — searching without participant filter", file=sys.stderr)

    # Parse dates
    since_ns = to_apple_ns(parse_date(args.since)) if args.since else None
    before_ns = to_apple_ns(parse_date(args.before)) if args.before else None

    # Build and run query
    common = dict(
        keyword=args.query,
        word_boundary=not args.query_substr,
        participant_handles=participant_handles,
        since_ns=since_ns,
        before_ns=before_ns,
        sent_only=args.sent,
        recv_only=args.received,
    )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    if args.mode == "both":
        sql_m, params_m = build_members_query(**common)
        sql_g, params_g = build_group_chat_query(
            group_name=args.from_name, **common
        )
        rows_m = conn.execute(sql_m, params_m).fetchall()
        rows_g = conn.execute(sql_g, params_g).fetchall()
        # Deduplicate by rowid, members results first
        seen = set()
        rows = []
        for r in list(rows_m) + list(rows_g):
            if r["rowid"] not in seen:
                seen.add(r["rowid"])
                rows.append(r)
        rows.sort(key=lambda r: r["date"] or 0, reverse=True)
    else:
        sql, params = build_query(group_name=args.from_name, mode=args.mode, **common)
        rows = conn.execute(sql, params).fetchall()

    conn.close()

    # Build records
    records = []
    for row in rows:
        is_sent = bool(row["is_from_me"])
        if is_sent:
            raw_handle = row["chat_identifier"] or ""
            # For group chats the identifier is a chat UUID, not a phone
            is_group = raw_handle.startswith("chat") or not re.match(r'^[\+\d@]', raw_handle)
            contact_handle = None if is_group else raw_handle
            contact = contacts.get(contact_handle, None) if contact_handle else None
        else:
            raw_handle = row["sender_handle"] or ""
            contact_handle = raw_handle or None
            contact = contacts.get(raw_handle, None)

        records.append({
            "id": str(row["rowid"]),
            "timestamp": apple_timestamp_to_iso(row["date"]),
            "direction": "sent" if is_sent else "received",
            "contact": contact,
            "contact_handle": contact_handle,
            "chat_name": row["chat_name"] or None,
            "chat_identifier": row["chat_identifier"] or None,
            "message": (row["text"] or "").strip(),
        })

    # Word-boundary post-filter
    if args.query and not args.query_substr:
        records = word_boundary_filter(records, args.query)

    total = len(records)
    limit = None if args.all else args.limit
    shown = records[:limit] if limit else records

    if args.table:
        print(format_table(shown, total), file=sys.stderr)
    if args.summary:
        extra = f" ({total - len(shown)} more)" if total > len(shown) else ""
        print(f"{len(shown)} messages{extra}", file=sys.stderr)

    output = json.dumps(shown, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output + "\n")
        print(f"Written {len(shown)} records to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
