#!/usr/bin/env python3
"""
Process raw messages_fetch API responses into structured JSON.

Handles single responses, multiple pages (pagination), and contact name resolution.

Usage:
    # Single response
    python process_messages.py raw.json [options]

    # Merge multiple paginated responses
    python process_messages.py page1.json page2.json page3.json --merge [options]

Options:
    --output, -o    Write structured JSON to file (default: stdout)
    --contacts      JSON file mapping handle -> display name {"handle": "Name"}
    --filter-sent   Only include messages you sent
    --filter-recv   Only include messages you received
    --query         Post-filter keyword (case-insensitive; uses word-boundary match by default)
    --query-substr  Use substring matching instead of word-boundary for --query
    --limit         Cap output at N records (oldest first by default)
    --limit-recent  When --limit is set, keep most recent instead of oldest
    --table         Print markdown table to stderr
    --summary       Print summary line to stderr (count, truncation notice)

Input JSON shapes accepted:
    1. mcpproxy envelope: {"content": [{"type": "text", "text": "<json>"}]}
    2. schema.org Conversation: {"@type": "Conversation", "hasPart": [...]}
    3. Array of either of the above (when using --merge)

Output per record:
    {
      "id": "UUID",
      "timestamp": "2026-03-21T16:24:13Z",
      "direction": "sent" | "received",
      "contact": "Jane Smith" | "+12035551234" | null,
      "contact_handle": "+12035551234" | null,
      "message": "Can you sing tomorrow morning?"
    }
"""

import json
import sys
import argparse
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def unwrap_response(raw: dict | list) -> dict:
    """Strip the mcpproxy content envelope if present."""
    if isinstance(raw, list):
        # Shouldn't happen at top-level, but handle gracefully
        return {"hasPart": [part for item in raw for part in _extract_parts(item)]}
    if "content" in raw and isinstance(raw["content"], list):
        text = raw["content"][0].get("text", "{}")
        return json.loads(text)
    return raw


def _extract_parts(data: dict) -> list:
    data = unwrap_response(data)
    return data.get("hasPart", [])


def merge_responses(raws: list[dict]) -> list:
    """Flatten multiple paginated API responses into one list of message parts."""
    parts = []
    for raw in raws:
        parts.extend(_extract_parts(raw))
    return parts


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

def process_parts(parts: list, contacts: dict = None) -> list:
    """
    Convert schema.org message parts into structured records.

    For sent messages (sender.@id = "me"), the recipient is not available from
    the API — contact will be None; contact_handle will be None.

    For received messages, contact is resolved via the contacts map (handle → name)
    with the raw handle as fallback.
    """
    contacts = contacts or {}
    results = []

    seen_ids = set()
    for msg in parts:
        msg_id = msg.get("@id")
        if msg_id in seen_ids:
            continue  # deduplicate across paginated pages
        seen_ids.add(msg_id)

        sender_id = msg.get("sender", {}).get("@id", "")
        is_sent = sender_id == "me"
        handle = None if is_sent else sender_id
        contact = None if is_sent else contacts.get(sender_id, sender_id)

        results.append({
            "id": msg_id,
            "timestamp": msg.get("createdAt"),
            "direction": "sent" if is_sent else "received",
            "contact": contact,
            "contact_handle": handle,
            "message": (msg.get("text") or "").strip(),
        })

    results.sort(key=lambda x: x["timestamp"] or "")
    return results


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def apply_filters(
    records: list,
    *,
    sent_only: bool = False,
    recv_only: bool = False,
    query: str = "",
    query_substr: bool = False,
) -> list:
    import re
    if sent_only:
        records = [r for r in records if r["direction"] == "sent"]
    if recv_only:
        records = [r for r in records if r["direction"] == "received"]
    if query:
        if query_substr:
            q = query.lower()
            records = [r for r in records if q in (r["message"] or "").lower()]
        else:
            # Word-boundary match with common inflections: "sing" matches "sing", "singing",
            # "singer", "sings" but NOT "choosing", "missing", or proper nouns like "Singmehgg".
            # Builds: \bsing(?:ing|er|ers|s|ed|along)?\b
            suffixes = r'(?:ing|er|ers|ed|s|along)?'
            pattern = re.compile(r'\b' + re.escape(query) + suffixes + r'\b', re.IGNORECASE)
            records = [r for r in records if pattern.search(r["message"] or "")]
    return records


def apply_limit(records: list, limit: int, most_recent: bool = False) -> tuple[list, int]:
    """
    Return (trimmed_records, total_before_trim).
    If most_recent=True, return the last N records (sorted ascending, newest at end).
    """
    total = len(records)
    if limit and total > limit:
        if most_recent:
            return records[-limit:], total
        return records[:limit], total
    return records, total


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def format_table(records: list, total_fetched: int = None) -> str:
    if not records:
        return "No messages found."

    shown = len(records)
    header = f"Showing {shown} message(s)"
    if total_fetched and total_fetched > shown:
        header += f" (of {total_fetched} fetched — {total_fetched - shown} more available)"

    lines = [
        header + "\n",
        "| Timestamp | Dir | Contact | Message |",
        "|-----------|-----|---------|---------|",
    ]
    for r in records:
        ts = r["timestamp"] or ""
        direction = "→" if r["direction"] == "sent" else "←"
        contact = r["contact"] or r["contact_handle"] or "(unknown)"
        text = (r["message"] or "").replace("\n", " ")
        msg = text[:80] + ("…" if len(text) > 80 else "")
        lines.append(f"| {ts} | {direction} | {contact} | {msg} |")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Process messages_fetch API response(s) into structured JSON."
    )
    parser.add_argument("inputs", nargs="+", help="Raw API response JSON file(s)")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    parser.add_argument("--contacts", help="JSON file: {handle: display_name}")
    parser.add_argument("--filter-sent", action="store_true")
    parser.add_argument("--filter-recv", action="store_true")
    parser.add_argument("--query", help="Post-filter keyword (word-boundary match by default)")
    parser.add_argument("--query-substr", action="store_true",
                        help="Use substring matching instead of word-boundary for --query")
    parser.add_argument("--limit", type=int, help="Cap output at N records")
    parser.add_argument("--limit-recent", action="store_true",
                        help="With --limit, keep most recent instead of oldest")
    parser.add_argument("--table", action="store_true",
                        help="Print markdown table to stderr")
    parser.add_argument("--summary", action="store_true",
                        help="Print one-line summary to stderr")
    args = parser.parse_args()

    # Load all input files
    raws = []
    for path in args.inputs:
        with open(path) as f:
            raws.append(json.load(f))

    # Flatten pages
    parts = merge_responses(raws)

    # Load contacts map
    contacts = {}
    if args.contacts:
        with open(args.contacts) as f:
            contacts = json.load(f)

    # Process
    records = process_parts(parts, contacts)
    records = apply_filters(
        records,
        sent_only=args.filter_sent,
        recv_only=args.filter_recv,
        query=args.query or "",
        query_substr=args.query_substr,
    )

    total_fetched = len(records)
    if args.limit:
        records, _ = apply_limit(records, args.limit, args.limit_recent)

    # Output
    if args.table:
        print(format_table(records, total_fetched), file=sys.stderr)
    if args.summary:
        remaining = total_fetched - len(records)
        note = f" ({remaining} more available)" if remaining > 0 else ""
        print(f"{len(records)} messages{note}", file=sys.stderr)

    output = json.dumps(records, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output + "\n")
        print(f"Written {len(records)} records to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
