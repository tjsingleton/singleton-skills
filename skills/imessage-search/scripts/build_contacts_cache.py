#!/usr/bin/env python3
"""
Build a contacts cache from an Address Book .abbu backup.

Reads all Sources/*.abbu SQLite databases, resolves contacts and group membership,
normalises phone numbers to E.164, and writes a JSON cache used by search_messages_sql.py.

Usage:
    python build_contacts_cache.py [options]

Options:
    --abbu          Path to .abbu directory (default: auto-detect in ~/Documents)
    --output, -o    Output JSON path (default: ~/.cache/imessage-contacts.json)
    --groups        Also write a groups JSON: {group_name: [handle, ...]}
    --verbose       Print all contacts and groups found

Output format (~/.cache/imessage-contacts.json):
    {
      "+17703771812": "TJ Singleton",
      "+14706401297": "Larry Elrod",
      ...
    }

Groups output (--groups flag):
    {
      "NC Worship Team": ["+14706401297", "+17705242011", ...],
      ...
    }
"""

import json
import os
import re
import shutil
import sqlite3
import sys
import argparse
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Phone normalisation
# ---------------------------------------------------------------------------

def normalise_e164(raw: str, default_country="1") -> str | None:
    """
    Strip formatting and produce E.164 (+1XXXXXXXXXX for US numbers).
    Returns None if the number looks invalid.
    """
    if not raw:
        return None
    # Keep only digits and leading +
    digits = re.sub(r"[^\d+]", "", raw)
    # Already E.164 with country code
    if digits.startswith("+"):
        digits = "+" + re.sub(r"\D", "", digits[1:])
        if len(digits) >= 10:
            return digits
        return None
    # Strip any leading "1" for 11-digit US numbers
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"+{default_country}{digits}"
    return None


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def open_source_db(db_path: Path) -> sqlite3.Connection | None:
    """Copy db + WAL to temp dir and open — avoids locking the original."""
    tmp = tempfile.mkdtemp(prefix="abbu_")
    try:
        shutil.copy2(db_path, f"{tmp}/ab.db")
        wal = Path(str(db_path) + "-wal")
        shm = Path(str(db_path) + "-shm")
        if wal.exists():
            shutil.copy2(wal, f"{tmp}/ab.db-wal")
        if shm.exists():
            shutil.copy2(shm, f"{tmp}/ab.db-shm")
        conn = sqlite3.connect(f"{tmp}/ab.db")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"  Warning: could not open {db_path}: {e}", file=sys.stderr)
        return None


def read_source(db_path: Path, verbose: bool = False) -> tuple[dict, dict]:
    """
    Read one source database.
    Returns:
        contacts: {pk: {"name": str, "handles": [e164, ...]}}
        groups:   {pk: {"name": str, "member_pks": [int, ...]}}
    """
    conn = open_source_db(db_path)
    if not conn:
        return {}, {}

    contacts: dict[int, dict] = {}
    groups: dict[int, dict] = {}

    try:
        # Load all records
        cur = conn.execute(
            "SELECT Z_PK, Z_ENT, ZFIRSTNAME, ZLASTNAME, ZORGANIZATION, ZNAME FROM ZABCDRECORD"
        )
        ent_counts: dict[int, int] = {}
        for row in cur:
            ent = row["Z_ENT"]
            ent_counts[ent] = ent_counts.get(ent, 0) + 1

        # Determine which Z_ENT is contacts vs groups
        # Groups have ZNAME set but no ZFIRSTNAME/ZLASTNAME
        cur = conn.execute(
            "SELECT Z_PK, Z_ENT, ZFIRSTNAME, ZLASTNAME, ZORGANIZATION, ZNAME FROM ZABCDRECORD"
        )
        for row in cur:
            pk = row["Z_PK"]
            first = row["ZFIRSTNAME"] or ""
            last = row["ZLASTNAME"] or ""
            org = row["ZORGANIZATION"] or ""
            name = row["ZNAME"] or ""

            if first or last or org:
                # It's a contact
                display = " ".join(filter(None, [first, last])) or org
                contacts[pk] = {"name": display, "handles": []}
            elif name:
                # It's a group
                groups[pk] = {"name": name, "member_pks": []}

        # Load phone numbers
        cur = conn.execute(
            "SELECT ZOWNER, ZFULLNUMBER FROM ZABCDPHONENUMBER WHERE ZFULLNUMBER IS NOT NULL"
        )
        for row in cur:
            owner = row["ZOWNER"]
            handle = normalise_e164(row["ZFULLNUMBER"])
            if handle and owner in contacts:
                if handle not in contacts[owner]["handles"]:
                    contacts[owner]["handles"].append(handle)

        # Load email addresses
        cur = conn.execute(
            "SELECT ZOWNER, ZADDRESS FROM ZABCDEMAILADDRESS WHERE ZADDRESS IS NOT NULL"
        )
        for row in cur:
            owner = row["ZOWNER"]
            email = (row["ZADDRESS"] or "").strip().lower()
            if email and owner in contacts:
                if email not in contacts[owner]["handles"]:
                    contacts[owner]["handles"].append(email)

        # Load group membership — try both junction table names
        for table, contact_col, group_col in [
            ("Z_22PARENTGROUPS", "Z_22CONTACTS", "Z_19PARENTGROUPS1"),
            ("Z_18PARENTGROUPS", "Z_18CHILDGROUPS", "Z_19PARENTGROUPS"),
        ]:
            try:
                cur = conn.execute(f"SELECT {contact_col}, {group_col} FROM {table}")
                for row in cur:
                    contact_pk = row[0]
                    group_pk = row[1]
                    if group_pk in groups and contact_pk in contacts:
                        if contact_pk not in groups[group_pk]["member_pks"]:
                            groups[group_pk]["member_pks"].append(contact_pk)
            except sqlite3.OperationalError:
                pass  # Table or column doesn't exist in this source

    finally:
        conn.close()

    if verbose:
        print(f"  {len(contacts)} contacts, {len(groups)} groups", file=sys.stderr)

    return contacts, groups


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def find_abbu(search_dir: Path) -> Path | None:
    """Auto-detect the most recent .abbu in search_dir."""
    matches = sorted(search_dir.glob("*.abbu"), key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def build_cache(abbu: Path, verbose: bool = False) -> tuple[dict, dict]:
    """
    Read all Sources in the .abbu and merge into flat handle→name and group→handles maps.
    """
    handle_to_name: dict[str, str] = {}
    group_to_handles: dict[str, list[str]] = {}

    sources_dir = abbu / "Sources"
    if not sources_dir.exists():
        print(f"No Sources/ directory in {abbu}", file=sys.stderr)
        return {}, {}

    for source_dir in sorted(sources_dir.iterdir()):
        db_path = source_dir / "AddressBook-v22.abcddb"
        if not db_path.exists():
            continue
        if verbose:
            print(f"Reading {source_dir.name}...", file=sys.stderr)

        contacts, groups = read_source(db_path, verbose=verbose)

        # Build handle→name
        for pk, contact in contacts.items():
            name = contact["name"]
            for handle in contact["handles"]:
                if handle not in handle_to_name:
                    handle_to_name[handle] = name

        # Build group→handles
        for gk, group in groups.items():
            name = group["name"]
            handles = []
            for member_pk in group["member_pks"]:
                if member_pk in contacts:
                    handles.extend(contacts[member_pk]["handles"])
            if name not in group_to_handles:
                group_to_handles[name] = []
            for h in handles:
                if h not in group_to_handles[name]:
                    group_to_handles[name].append(h)

    return handle_to_name, group_to_handles


def main():
    parser = argparse.ArgumentParser(description="Build iMessage contacts cache from .abbu")
    parser.add_argument("--abbu", help="Path to .abbu directory (auto-detected if omitted)")
    parser.add_argument("--output", "-o",
                        default=str(Path.home() / ".cache/imessage-contacts.json"),
                        help="Output handle→name JSON (default: ~/.cache/imessage-contacts.json)")
    parser.add_argument("--groups", help="Output group→handles JSON file")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    # Find .abbu
    if args.abbu:
        abbu = Path(args.abbu)
    else:
        abbu = find_abbu(Path.home() / "Documents")
        if not abbu:
            print("No .abbu found in ~/Documents. Use --abbu to specify a path.", file=sys.stderr)
            sys.exit(1)
        print(f"Using: {abbu}", file=sys.stderr)

    handle_to_name, group_to_handles = build_cache(abbu, verbose=args.verbose)

    # Write handle cache
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(handle_to_name, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {len(handle_to_name)} handles → {out}", file=sys.stderr)

    # Write groups cache
    if args.groups:
        gout = Path(args.groups)
        gout.parent.mkdir(parents=True, exist_ok=True)
        gout.write_text(json.dumps(group_to_handles, indent=2, ensure_ascii=False) + "\n")
        print(f"Wrote {len(group_to_handles)} groups → {gout}", file=sys.stderr)
    else:
        # Always print groups to stdout for quick inspection
        if args.verbose:
            for gname, handles in sorted(group_to_handles.items()):
                names = [handle_to_name.get(h, h) for h in handles]
                print(f"  [{gname}]: {', '.join(names)}", file=sys.stderr)

    print(f"\nDone. {len(handle_to_name)} handles, {len(group_to_handles)} groups.", file=sys.stderr)


if __name__ == "__main__":
    main()
