#!/usr/bin/env python3
"""Read an iMessage SQLite database through a private-safe request contract.

The runner never resolves people, chooses an unauthorized fallback, or exposes
database paths and raw identifiers in its result envelope.  Its only required
dependency is the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
from attributed_body import message_text


REQUEST_SCHEMA = "imessage-search.request.v1"
RESULT_SCHEMA = "imessage-search.result.v1"
APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)
DEFAULT_LIVE_DB = Path.home() / "Library/Messages/chat.db"
PARTICIPANT_STATES = {"not_requested", "resolved", "unresolved_error"}
SOURCE_PREFERENCES = {"live_only", "live_then_archive", "archive_only", "explicit_db"}
MODES = {"members", "group", "both"}
DIRECTIONS = {"any", "sent", "received"}
EXPLICIT_COMPLETENESS = {"complete", "partial", "unknown"}


class RequestError(ValueError):
    """The parent supplied a request that cannot safely be executed."""


class DatabasePolicyError(RuntimeError):
    """No database can be selected without violating the request policy."""


@dataclass(frozen=True)
class DatabaseConfig:
    explicit_db: Path | None = None
    live_db: Path | None = DEFAULT_LIVE_DB
    archive_db: Path | None = None


@dataclass(frozen=True)
class DatabaseSelection:
    path: Path
    source_class: str
    archive_cutoff: str | None
    cutoff_source: str | None
    coverage: str
    fallback_authorized: bool
    completeness: str
    warnings: tuple[str, ...] = ()


def parse_date(value: str) -> datetime:
    value = value.strip().lower()
    now = datetime.now(timezone.utc)
    if value == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if value == "yesterday":
        return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    if value == "last week":
        return now - timedelta(weeks=1)
    if value == "last month":
        return (now.replace(day=1) - timedelta(days=1)).replace(day=1)
    if value == "last year":
        return now.replace(year=now.year - 1, month=1, day=1)
    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?", value)
    if match:
        month, day = int(match.group(1)), int(match.group(2))
        year = int(match.group(3)) if match.group(3) else now.year
        return datetime(year + (2000 if year < 100 else 0), month, day, tzinfo=timezone.utc)
    normalized = value[:-1] + "+00:00" if value.endswith("z") else value
    parsed = datetime.fromisoformat(normalized)
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)


def to_apple_ns(value: datetime) -> int:
    return int((value - APPLE_EPOCH).total_seconds() * 1_000_000_000)


def apple_timestamp_to_iso(value: int | None) -> str | None:
    if value is None:
        return None
    return (APPLE_EPOCH + timedelta(seconds=value / 1_000_000_000)).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise RequestError("cache files must contain a JSON object")
    return loaded


def _required_bool(container: dict[str, Any], key: str, prefix: str) -> bool:
    if key not in container or type(container[key]) is not bool:
        raise RequestError(f"{prefix}.{key} must be a JSON boolean")
    return container[key]


def normalize_request(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise RequestError("request must be a JSON object")
    if raw.get("schema_version") != REQUEST_SCHEMA:
        raise RequestError(f"schema_version must be {REQUEST_SCHEMA!r}")

    participant = raw.get("participant_scope")
    if not isinstance(participant, dict):
        raise RequestError("participant_scope must be a JSON object")
    state = participant.get("state")
    if state not in PARTICIPANT_STATES:
        raise RequestError("participant_scope.state is invalid")
    handles = participant.get("handles") or []
    if not isinstance(handles, list) or not all(isinstance(item, str) and item for item in handles):
        raise RequestError("participant_scope.handles must be a list of non-empty strings")
    excluded = raw.get("excluded_handles") or []
    if not isinstance(excluded, list) or not all(isinstance(item, str) and item for item in excluded):
        raise RequestError("excluded_handles must be a list of non-empty strings")
    excluded_set = set(excluded)
    handles = list(dict.fromkeys(item for item in handles if item not in excluded_set))
    if state == "unresolved_error":
        raise RequestError("requested participant was unresolved; refusing an unfiltered search")
    if state == "resolved" and not handles:
        raise RequestError("resolved participant scope requires at least one non-excluded handle")
    if state == "not_requested" and handles:
        raise RequestError("not_requested participant scope cannot contain handles")

    mode = raw.get("mode", "both")
    direction = raw.get("direction", "any")
    if mode not in MODES:
        raise RequestError("mode must be members, group, or both")
    if direction not in DIRECTIONS:
        raise RequestError("direction must be any, sent, or received")
    limit = raw.get("limit", 20)
    if limit is not None and (not isinstance(limit, int) or isinstance(limit, bool) or limit < 1):
        raise RequestError("limit must be a positive integer or null")

    date_range = raw.get("date_range")
    if not isinstance(date_range, dict):
        raise RequestError("date_range must be a JSON object")
    since = date_range.get("since")
    before = date_range.get("before")
    if since:
        parse_date(since)
    if before:
        parse_date(before)
    if since and before and parse_date(since) >= parse_date(before):
        raise RequestError("date_range.since must be before date_range.before")

    policy = raw.get("database_policy")
    if not isinstance(policy, dict):
        raise RequestError("database_policy must be a JSON object")
    preference = policy.get("source_preference")
    if preference not in SOURCE_PREFERENCES:
        raise RequestError("database_policy.source_preference is invalid")
    cutoff = policy.get("archive_cutoff")
    cutoff_source = policy.get("archive_cutoff_source")
    if cutoff:
        parse_date(cutoff)
    if bool(cutoff) != bool(cutoff_source):
        raise RequestError("archive cutoff and its metadata source must be supplied together")

    archive_fallback_authorized = _required_bool(
        policy, "archive_fallback_authorized", "database_policy"
    )
    allow_incomplete_archive = _required_bool(
        policy, "allow_incomplete_archive", "database_policy"
    )
    explicit_metadata = policy.get("explicit_db_metadata")
    if explicit_metadata is not None:
        if not isinstance(explicit_metadata, dict):
            raise RequestError("database_policy.explicit_db_metadata must be a JSON object or null")
        allowed_metadata_keys = {"trusted", "synthetic", "completeness", "cutoff", "cutoff_source"}
        if set(explicit_metadata) - allowed_metadata_keys:
            raise RequestError("database_policy.explicit_db_metadata contains unsupported fields")
        trusted = _required_bool(explicit_metadata, "trusted", "database_policy.explicit_db_metadata")
        synthetic = _required_bool(explicit_metadata, "synthetic", "database_policy.explicit_db_metadata")
        explicit_completeness = explicit_metadata.get("completeness")
        if explicit_completeness not in EXPLICIT_COMPLETENESS:
            raise RequestError(
                "database_policy.explicit_db_metadata.completeness must be complete, partial, or unknown"
            )
        explicit_cutoff = explicit_metadata.get("cutoff")
        explicit_cutoff_source = explicit_metadata.get("cutoff_source")
        if explicit_cutoff:
            parse_date(explicit_cutoff)
        if bool(explicit_cutoff) != bool(explicit_cutoff_source):
            raise RequestError("explicit database cutoff and its metadata source must be supplied together")
        if explicit_completeness == "partial" and not explicit_cutoff:
            raise RequestError("partial explicit database metadata requires cutoff metadata")
        if explicit_completeness != "partial" and explicit_cutoff:
            raise RequestError("explicit database cutoff metadata is valid only for partial completeness")
        if synthetic and explicit_completeness != "complete":
            raise RequestError("synthetic explicit databases must declare complete fixture coverage")
        explicit_metadata = {
            "trusted": trusted,
            "synthetic": synthetic,
            "completeness": explicit_completeness,
            "cutoff": explicit_cutoff,
            "cutoff_source": explicit_cutoff_source,
        }

    cache_policy = raw.get("cache_policy")
    if not isinstance(cache_policy, dict):
        raise RequestError("cache_policy must be a JSON object")
    if set(cache_policy) != {"use_display_names"}:
        raise RequestError("cache_policy must contain only use_display_names")
    use_display_names = _required_bool(cache_policy, "use_display_names", "cache_policy")

    output_policy = raw.get("output_policy")
    if not isinstance(output_policy, dict):
        raise RequestError("output_policy must be a JSON object")
    allowed_output_keys = {"include_messages", "include_contact_names", "include_chat_names"}
    if set(output_policy) != allowed_output_keys:
        raise RequestError("output_policy must contain exactly the supported boolean fields")
    normalized_output_policy = {
        key: _required_bool(output_policy, key, "output_policy") for key in sorted(allowed_output_keys)
    }
    query = raw.get("query") or ""
    if not isinstance(query, str):
        raise RequestError("query must be a string")
    execution_mode = raw.get("execution_mode", "direct")
    if execution_mode not in {"direct", "delegated"}:
        raise RequestError("execution_mode must be direct or delegated")

    return {
        "schema_version": REQUEST_SCHEMA,
        "query": query,
        "query_match": raw.get("query_match", "word_boundary"),
        "participant_scope": {
            "state": state,
            "requested_label": participant.get("requested_label"),
            "handles": handles,
        },
        "excluded_handles": list(dict.fromkeys(excluded)),
        "date_range": {"since": since, "before": before},
        "mode": mode,
        "direction": direction,
        "limit": limit,
        "database_policy": {
            "source_preference": preference,
            "archive_fallback_authorized": archive_fallback_authorized,
            "allow_incomplete_archive": allow_incomplete_archive,
            "archive_cutoff": cutoff,
            "archive_cutoff_source": cutoff_source,
            "explicit_db_metadata": explicit_metadata,
        },
        "cache_policy": {"use_display_names": use_display_names},
        "output_policy": normalized_output_policy,
        "execution_mode": execution_mode,
    }


def _sqlite_uri(path: Path) -> str:
    return "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro"


def open_readonly(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(_sqlite_uri(path), uri=True, timeout=1.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout=1000")
    connection.execute("BEGIN")
    return connection


def _probe(path: Path | None) -> bool:
    if path is None:
        return False
    connection = None
    try:
        connection = open_readonly(path)
        connection.execute("SELECT 1").fetchone()
        return True
    except (OSError, sqlite3.Error):
        return False
    finally:
        if connection is not None:
            connection.rollback()
            connection.close()


def cutoff_coverage(request: dict[str, Any], cutoff_text: str | None) -> str:
    if not cutoff_text:
        return "unknown_cutoff"
    cutoff = parse_date(cutoff_text)
    since_text = request["date_range"]["since"]
    before_text = request["date_range"]["before"]
    since = parse_date(since_text) if since_text else None
    before = parse_date(before_text) if before_text else None
    if before is not None and before <= cutoff:
        return "within_archive"
    if since is not None and since >= cutoff:
        return "after_cutoff"
    return "overlaps_after_cutoff"


def archive_coverage(request: dict[str, Any]) -> str:
    return cutoff_coverage(request, request["database_policy"]["archive_cutoff"])


def _select_archive(request: dict[str, Any], config: DatabaseConfig, fallback: bool) -> DatabaseSelection:
    policy = request["database_policy"]
    if fallback and not policy["archive_fallback_authorized"]:
        raise DatabasePolicyError("live database unavailable and archive fallback is not authorized")
    archive_path = config.archive_db
    if archive_path is None or not _probe(archive_path):
        raise DatabasePolicyError("configured archive database is unavailable")
    coverage = archive_coverage(request)
    if coverage == "unknown_cutoff":
        raise DatabasePolicyError("archive cutoff metadata is required")
    incomplete = coverage != "within_archive"
    if incomplete and not policy["allow_incomplete_archive"]:
        raise DatabasePolicyError("archive cannot cover the requested window; explicit partial-result acceptance is required")
    warnings = ("Results are limited by the configured archive cutoff.",) if incomplete else ()
    return DatabaseSelection(
        path=archive_path,
        source_class="archive",
        archive_cutoff=policy["archive_cutoff"],
        cutoff_source=policy["archive_cutoff_source"],
        coverage=coverage,
        fallback_authorized=policy["archive_fallback_authorized"],
        completeness="accepted_partial" if incomplete else "complete",
        warnings=warnings,
    )


def select_database(request: dict[str, Any], config: DatabaseConfig) -> DatabaseSelection:
    policy = request["database_policy"]
    preference = policy["source_preference"]
    if config.explicit_db is not None:
        if not _probe(config.explicit_db):
            raise DatabasePolicyError("explicit database is unavailable")
        metadata = policy["explicit_db_metadata"]
        if metadata is None:
            raise DatabasePolicyError("explicit database requires trusted completeness metadata")
        if not metadata["trusted"]:
            raise DatabasePolicyError("explicit database completeness metadata is not trusted")
        declared = metadata["completeness"]
        cutoff = metadata["cutoff"]
        if metadata["synthetic"]:
            coverage = "synthetic_complete"
        elif declared == "complete":
            coverage = "asserted_complete"
        else:
            coverage = cutoff_coverage(request, cutoff)
        incomplete = declared == "unknown" or (declared == "partial" and coverage != "within_archive")
        if incomplete and not policy["allow_incomplete_archive"]:
            raise DatabasePolicyError(
                "explicit database coverage is incomplete or unknown; explicit partial-result acceptance is required"
            )
        warnings = ("Results are limited by explicit database coverage metadata.",) if incomplete else ()
        return DatabaseSelection(
            config.explicit_db,
            "explicit",
            cutoff,
            metadata["cutoff_source"],
            coverage,
            False,
            "accepted_partial" if incomplete else "complete",
            warnings,
        )
    if preference == "explicit_db":
        raise DatabasePolicyError("source preference explicit_db requires --db")
    live_path = config.live_db
    if preference in {"live_only", "live_then_archive"} and live_path is not None and _probe(live_path):
        return DatabaseSelection(live_path, "live", None, None, "live", False, "complete")
    if preference == "live_only":
        raise DatabasePolicyError("live database is unavailable to the responsible host process")
    if preference == "archive_only":
        return _select_archive(request, config, fallback=False)
    return _select_archive(request, config, fallback=True)


BASE_SELECT = """
SELECT m.rowid, m.date, m.is_from_me, m.text, m.attributedBody,
       h.id AS sender_handle, c.display_name AS chat_name, c.chat_identifier
FROM message m
LEFT JOIN handle h ON m.handle_id = h.rowid
LEFT JOIN chat_message_join cmj ON m.rowid = cmj.message_id
LEFT JOIN chat c ON cmj.chat_id = c.rowid
"""


def _base_conditions(request: dict[str, Any]) -> tuple[list[str], list[Any]]:
    conditions: list[str] = []
    params: list[Any] = []
    since = request["date_range"]["since"]
    before = request["date_range"]["before"]
    if since:
        conditions.append("m.date >= ?")
        params.append(to_apple_ns(parse_date(since)))
    if before:
        conditions.append("m.date < ?")
        params.append(to_apple_ns(parse_date(before)))
    if request["direction"] == "sent":
        conditions.append("m.is_from_me = 1")
    elif request["direction"] == "received":
        conditions.append("m.is_from_me = 0")
    excluded = request["excluded_handles"]
    if excluded:
        placeholders = ",".join("?" for _ in excluded)
        conditions.append(f"COALESCE(h.id, '') NOT IN ({placeholders})")
        params.extend(excluded)
    return conditions, params


def _participant_condition(handles: list[str]) -> tuple[str, list[str]]:
    placeholders = ",".join("?" for _ in handles)
    return f"""m.rowid IN (
        SELECT cmj2.message_id FROM chat_message_join cmj2
        JOIN chat_handle_join chj ON cmj2.chat_id = chj.chat_id
        JOIN handle ph ON chj.handle_id = ph.rowid
        WHERE ph.id IN ({placeholders})
    )""", handles


def build_members_query(request: dict[str, Any]) -> tuple[str, list[Any]]:
    conditions, params = _base_conditions(request)
    handles = request["participant_scope"]["handles"]
    if handles:
        clause, values = _participant_condition(handles)
        conditions.append(clause)
        params.extend(values)
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    return f"{BASE_SELECT} {where} ORDER BY m.date DESC", params


def build_group_query(request: dict[str, Any]) -> tuple[str, list[Any]]:
    conditions, params = _base_conditions(request)
    handles = request["participant_scope"]["handles"]
    if handles:
        placeholders = ",".join("?" for _ in handles)
        conditions.append(f"""cmj.chat_id IN (
            SELECT chj.chat_id FROM chat_handle_join chj
            JOIN handle ph ON chj.handle_id = ph.rowid
            JOIN chat gc ON chj.chat_id = gc.rowid
            WHERE gc.chat_identifier LIKE 'chat%'
            GROUP BY chj.chat_id
            HAVING COUNT(DISTINCT ph.id) = ?
               AND COUNT(DISTINCT CASE WHEN ph.id IN ({placeholders}) THEN ph.id END) = ?
        )""")
        params.extend([len(handles), *handles, len(handles)])
    else:
        conditions.append("c.chat_identifier LIKE 'chat%'")
    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    return f"{BASE_SELECT} {where} ORDER BY m.date DESC", params


def _fetch_rows(connection: sqlite3.Connection, request: dict[str, Any]) -> list[sqlite3.Row]:
    queries = [build_members_query(request)]
    if request["mode"] == "group":
        queries = [build_group_query(request)]
    elif request["mode"] == "both":
        queries.append(build_group_query(request))
    rows: dict[int, sqlite3.Row] = {}
    for sql, params in queries:
        for row in connection.execute(sql, params).fetchall():
            rows.setdefault(row["rowid"], row)
    return sorted(rows.values(), key=lambda row: row["date"] or 0, reverse=True)


def _raw_records(
    rows: list[sqlite3.Row], contacts: dict[str, Any], use_display_names: bool
) -> list[dict[str, Any]]:
    records = []
    for row in rows:
        sent = bool(row["is_from_me"])
        handle = (row["chat_identifier"] if sent else row["sender_handle"]) or None
        records.append({
            "local_id": str(row["rowid"]),
            "timestamp": apple_timestamp_to_iso(row["date"]),
            "direction": "sent" if sent else "received",
            "contact_name": contacts.get(handle) if use_display_names and handle else None,
            "contact_handle": handle,
            "chat_name": (row["chat_name"] or None) if use_display_names else None,
            "chat_identifier": row["chat_identifier"] or None,
            "message": message_text(row["text"], row["attributedBody"]).strip(),
        })
    return records


def _filter_keyword(records: list[dict[str, Any]], query: str, match: str) -> list[dict[str, Any]]:
    if not query:
        return records
    if match == "substring":
        needle = query.casefold()
        return [record for record in records if needle in record["message"].casefold()]
    if match != "word_boundary":
        raise RequestError("query_match must be word_boundary or substring")
    pattern = re.compile(r"\b" + re.escape(query) + r"(?:ing|er|ers|ed|s)?\b", re.IGNORECASE)
    return [record for record in records if pattern.search(record["message"])]


def sanitize_records(records: list[dict[str, Any]], output_policy: dict[str, bool]) -> list[dict[str, Any]]:
    sanitized = []
    for record in records:
        item: dict[str, Any] = {
            "timestamp": record["timestamp"],
            "direction": record["direction"],
        }
        if output_policy["include_contact_names"]:
            item["contact"] = record["contact_name"]
        if output_policy["include_chat_names"]:
            item["chat"] = record["chat_name"]
        if output_policy["include_messages"]:
            item["message"] = record["message"]
        sanitized.append(item)
    return sanitized


def execute_request(
    raw_request: dict[str, Any],
    config: DatabaseConfig,
    contacts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    request = normalize_request(raw_request)
    selection = select_database(request, config)
    connection = open_readonly(selection.path)
    try:
        rows = _fetch_rows(connection, request)
    finally:
        connection.rollback()
        connection.close()
    raw = _filter_keyword(
        _raw_records(rows, contacts or {}, request["cache_policy"]["use_display_names"]),
        request["query"],
        request["query_match"],
    )
    total = len(raw)
    limit = request["limit"]
    shown = raw if limit is None else raw[:limit]
    return {
        "schema_version": RESULT_SCHEMA,
        "status": "ok",
        "execution_mode": request["execution_mode"],
        "participant_scope_state": request["participant_scope"]["state"],
        "database": {
            "selected_source_class": selection.source_class,
            "archive_cutoff": selection.archive_cutoff,
            "archive_cutoff_source": selection.cutoff_source,
            "query_coverage": selection.coverage,
            "archive_fallback_authorized": selection.fallback_authorized,
            "completeness": selection.completeness,
        },
        "summary": {"result_count": len(shown), "total_count": total, "truncated": total > len(shown)},
        "records": sanitize_records(shown, request["output_policy"]),
        "warnings": list(selection.warnings),
    }


DelegatedExecutor = Callable[[tuple[str, ...], Path], dict[str, Any]]


def _write_private_request(path: Path, request: dict[str, Any]) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_TRUNC)
    try:
        os.fchmod(descriptor, 0o600)
        payload = json.dumps(request, ensure_ascii=False).encode("utf-8")
        while payload:
            written = os.write(descriptor, payload)
            payload = payload[written:]
    finally:
        os.close(descriptor)


def _cli_command(request_path: Path, config: DatabaseConfig, runner_path: Path) -> tuple[str, ...]:
    command = [sys.executable, str(runner_path), "--request", str(request_path)]
    if config.explicit_db is not None:
        command.extend(["--db", str(config.explicit_db)])
    elif config.live_db is None:
        command.append("--no-live-db")
    elif config.live_db != DEFAULT_LIVE_DB:
        command.extend(["--live-db", str(config.live_db)])
    if config.archive_db is not None:
        command.extend(["--archive-db", str(config.archive_db)])
    return tuple(command)


def _validate_result_envelope(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise RequestError("executor must return a JSON result object")
    status = result.get("status")
    required_keys = {
        "schema_version", "status", "execution_mode", "participant_scope_state",
        "database", "summary", "records", "warnings",
    }
    if status == "error":
        required_keys.add("error")
    if set(result) != required_keys:
        raise RequestError("executor returned an incomplete or extended result envelope")
    if result["schema_version"] != RESULT_SCHEMA or status not in {"ok", "error"}:
        raise RequestError("executor returned an invalid result schema or status")
    if result["execution_mode"] not in {"direct", "delegated"}:
        raise RequestError("executor returned an invalid execution mode")
    if result["participant_scope_state"] not in PARTICIPANT_STATES | {"unknown"}:
        raise RequestError("executor returned an invalid participant scope state")

    warnings = result["warnings"]
    if not isinstance(warnings, list) or not all(isinstance(item, str) for item in warnings):
        raise RequestError("executor returned invalid warnings")

    records = result.get("records")
    if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
        raise RequestError("executor returned invalid records")
    allowed_record_keys = {"timestamp", "direction", "contact", "chat", "message"}
    for record in records:
        if not {"timestamp", "direction"}.issubset(record) or set(record) - allowed_record_keys:
            raise RequestError("executor returned incomplete or unsanitized records")
        if record["timestamp"] is not None and not isinstance(record["timestamp"], str):
            raise RequestError("executor returned an invalid record timestamp")
        if record["direction"] not in {"sent", "received"}:
            raise RequestError("executor returned an invalid record direction")
        if "contact" in record and record["contact"] is not None and not isinstance(record["contact"], str):
            raise RequestError("executor returned an invalid contact name")
        if "chat" in record and record["chat"] is not None and not isinstance(record["chat"], str):
            raise RequestError("executor returned an invalid chat name")
        if "message" in record and not isinstance(record["message"], str):
            raise RequestError("executor returned an invalid message")

    database = result.get("database")
    database_keys = {
        "selected_source_class",
        "archive_cutoff",
        "archive_cutoff_source",
        "query_coverage",
        "archive_fallback_authorized",
        "completeness",
    }
    if not isinstance(database, dict) or set(database) != database_keys:
        raise RequestError("executor returned incomplete or unsanitized database metadata")
    source_class = database["selected_source_class"]
    if source_class not in {None, "live", "archive", "explicit"}:
        raise RequestError("executor returned an invalid database source class")
    cutoff = database["archive_cutoff"]
    cutoff_source = database["archive_cutoff_source"]
    if cutoff is not None and not isinstance(cutoff, str):
        raise RequestError("executor returned an invalid database cutoff")
    if cutoff_source is not None and not isinstance(cutoff_source, str):
        raise RequestError("executor returned an invalid database cutoff source")
    if (cutoff is None) != (cutoff_source is None):
        raise RequestError("executor returned incomplete database cutoff metadata")
    if type(database["archive_fallback_authorized"]) is not bool:
        raise RequestError("executor returned an invalid fallback authorization")
    coverage = database["query_coverage"]
    if coverage not in {
        "live", "within_archive", "after_cutoff", "overlaps_after_cutoff",
        "unknown_cutoff", "synthetic_complete", "asserted_complete", "blocked",
    }:
        raise RequestError("executor returned an invalid query coverage")
    completeness = database["completeness"]
    if completeness not in {"complete", "accepted_partial", "blocked_incomplete"}:
        raise RequestError("executor returned an invalid database completeness")

    summary = result.get("summary")
    if not isinstance(summary, dict) or set(summary) != {"result_count", "total_count", "truncated"}:
        raise RequestError("executor returned an invalid summary")
    if any(type(summary[key]) is not int or summary[key] < 0 for key in ("result_count", "total_count")):
        raise RequestError("executor returned invalid summary counts")
    if type(summary["truncated"]) is not bool:
        raise RequestError("executor returned an invalid truncation flag")
    if summary["result_count"] != len(records) or summary["total_count"] < summary["result_count"]:
        raise RequestError("executor returned inconsistent summary counts")
    if summary["truncated"] != (summary["total_count"] > summary["result_count"]):
        raise RequestError("executor returned an inconsistent truncation flag")

    if status == "ok":
        if source_class not in {"live", "archive", "explicit"}:
            raise RequestError("successful result requires a selected database source")
        complete_coverages = {"live", "within_archive", "synthetic_complete", "asserted_complete"}
        partial_coverages = {"after_cutoff", "overlaps_after_cutoff", "unknown_cutoff"}
        if completeness == "complete" and coverage not in complete_coverages:
            raise RequestError("complete result has inconsistent database coverage")
        if completeness == "accepted_partial" and coverage not in partial_coverages:
            raise RequestError("partial result has inconsistent database coverage")
        if completeness == "blocked_incomplete" or coverage == "blocked":
            raise RequestError("successful result cannot report blocked coverage")
        if source_class == "live" and (coverage != "live" or cutoff is not None):
            raise RequestError("live result has inconsistent database metadata")
        if source_class == "archive" and (cutoff is None or coverage not in {"within_archive", "after_cutoff", "overlaps_after_cutoff"}):
            raise RequestError("archive result has inconsistent database metadata")
    else:
        error = result["error"]
        if not isinstance(error, dict) or set(error) != {"type", "message"}:
            raise RequestError("executor returned invalid structured error metadata")
        if not all(isinstance(error[key], str) and error[key] for key in ("type", "message")):
            raise RequestError("executor returned invalid structured error values")
        if source_class is not None or coverage != "blocked" or completeness != "blocked_incomplete":
            raise RequestError("error result has inconsistent database status")
        if records or summary != {"result_count": 0, "total_count": 0, "truncated": False}:
            raise RequestError("error result must have empty records and summary")
    return result


def _invoke_cli(command: tuple[str, ...]) -> dict[str, Any]:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RequestError("runner did not return a JSON result envelope") from error
    validated = _validate_result_envelope(result)
    if (completed.returncode == 0) != (validated["status"] == "ok"):
        raise RequestError("runner return code is inconsistent with its result status")
    return validated


def _is_delegated_access_error(result: dict[str, Any]) -> bool:
    if result.get("status") != "error":
        return False
    error = result.get("error") or {}
    error_type = error.get("type")
    message = str(error.get("message", "")).casefold()
    return error_type in {"PermissionError", "OperationalError", "OSError"} or (
        error_type == "DatabasePolicyError" and ("unavailable" in message or "access" in message)
    )


def execute_with_delegation_fallback(
    raw_request: dict[str, Any],
    config: DatabaseConfig,
    delegated_executor: DelegatedExecutor | None = None,
    runner_path: Path | None = None,
) -> dict[str, Any]:
    """Run the CLI contract, retrying locally after delegated access failure."""
    request = normalize_request(raw_request)
    descriptor, name = tempfile.mkstemp(prefix="imessage-search-request-", suffix=".json")
    os.fchmod(descriptor, 0o600)
    os.close(descriptor)
    request_path = Path(name)
    try:
        _write_private_request(request_path, request)
        command = _cli_command(request_path, config, runner_path or Path(__file__).resolve())
        if request["execution_mode"] == "delegated" and delegated_executor is not None:
            try:
                delegated_result = _validate_result_envelope(delegated_executor(command, request_path))
            except (PermissionError, sqlite3.OperationalError, OSError):
                delegated_result = None
            if delegated_result is not None and not _is_delegated_access_error(delegated_result):
                return delegated_result
        elif request["execution_mode"] != "delegated":
            return _invoke_cli(command)

        request["execution_mode"] = "direct"
        _write_private_request(request_path, request)
        result = _invoke_cli(command)
        result["warnings"] = [
            "Delegated database access failed or was unavailable; the identical request ran directly.",
            *result.get("warnings", []),
        ]
        return result
    finally:
        request_path.unlink(missing_ok=True)


def run_with_temporary_output(
    raw_request: dict[str, Any], config: DatabaseConfig, contacts: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Exercise the file-output boundary and always remove sensitive output."""
    descriptor, name = tempfile.mkstemp(prefix="imessage-search-", suffix=".json")
    os.fchmod(descriptor, 0o600)
    os.close(descriptor)
    path = Path(name)
    try:
        result = execute_request(raw_request, config, contacts)
        path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        os.chmod(path, 0o600)
        return json.loads(path.read_text(encoding="utf-8"))
    finally:
        path.unlink(missing_ok=True)


def _legacy_request(args: argparse.Namespace, contacts: dict[str, Any], groups: dict[str, Any]) -> dict[str, Any]:
    state = "not_requested"
    handles: list[str] = []
    if args.from_name:
        state = "resolved"
        label = args.from_name.casefold()
        handles = [handle for handle, name in contacts.items() if str(name).casefold() == label]
        for group_name, group_handles in groups.items():
            if group_name.casefold() == label:
                handles.extend(group_handles)
        handles = list(dict.fromkeys(handle for handle in handles if handle not in set(args.exclude_handle)))
        if not handles:
            state = "unresolved_error"
    preference = "explicit_db" if args.db else args.source_preference
    direction = "any"
    if args.sent:
        direction = "sent"
    elif args.received:
        direction = "received"
    return {
        "schema_version": REQUEST_SCHEMA,
        "query": args.query or "",
        "query_match": "substring" if args.query_substr else "word_boundary",
        "participant_scope": {"state": state, "requested_label": args.from_name, "handles": handles},
        "excluded_handles": args.exclude_handle,
        "date_range": {"since": args.since, "before": args.before},
        "mode": args.mode,
        "direction": direction,
        "limit": None if args.all else args.limit,
        "database_policy": {
            "source_preference": preference,
            "archive_fallback_authorized": args.authorize_archive_fallback,
            "allow_incomplete_archive": args.accept_partial_archive,
            "archive_cutoff": args.archive_cutoff,
            "archive_cutoff_source": args.archive_cutoff_source,
            "explicit_db_metadata": {
                "trusted": args.db_metadata_trusted,
                "synthetic": args.db_synthetic,
                "completeness": args.db_completeness,
                "cutoff": args.db_cutoff,
                "cutoff_source": args.db_cutoff_source,
            } if args.db else None,
        },
        "cache_policy": {"use_display_names": True},
        "output_policy": {"include_messages": True, "include_contact_names": True, "include_chat_names": True},
        "execution_mode": args.execution_mode,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, help="versioned normalized request JSON")
    parser.add_argument("--db", type=Path, help="explicit read-only database; highest priority")
    parser.add_argument("--db-metadata-trusted", action="store_true")
    parser.add_argument("--db-synthetic", action="store_true")
    parser.add_argument("--db-completeness", choices=sorted(EXPLICIT_COMPLETENESS), default="unknown")
    parser.add_argument("--db-cutoff")
    parser.add_argument("--db-cutoff-source")
    parser.add_argument("--live-db", type=Path, default=DEFAULT_LIVE_DB)
    parser.add_argument("--no-live-db", action="store_true")
    parser.add_argument("--archive-db", type=Path, default=os.environ.get("IMESSAGE_ARCHIVE_DB"))
    parser.add_argument("--archive-cutoff", default=os.environ.get("IMESSAGE_ARCHIVE_CUTOFF"))
    parser.add_argument("--archive-cutoff-source", default=os.environ.get("IMESSAGE_ARCHIVE_CUTOFF_SOURCE"))
    parser.add_argument("--source-preference", choices=sorted(SOURCE_PREFERENCES), default="live_only")
    parser.add_argument("--authorize-archive-fallback", action="store_true")
    parser.add_argument("--accept-partial-archive", action="store_true")
    parser.add_argument("--execution-mode", choices=["direct", "delegated"], default="direct")
    parser.add_argument("--contacts", type=Path)
    parser.add_argument("--groups", type=Path)
    parser.add_argument("--exclude-handle", action="append", default=[])
    parser.add_argument("--query", "-q")
    parser.add_argument("--query-substr", action="store_true")
    parser.add_argument("--from", dest="from_name")
    parser.add_argument("--mode", choices=sorted(MODES), default="both")
    parser.add_argument("--since")
    parser.add_argument("--before")
    parser.add_argument("--sent", action="store_true")
    parser.add_argument("--received", action="store_true")
    parser.add_argument("--limit", "-n", type=int, default=20)
    parser.add_argument("--all", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.sent and args.received:
        raise SystemExit("--sent and --received are mutually exclusive")
    contacts = load_json(args.contacts)
    groups = load_json(args.groups)
    config = DatabaseConfig(args.db, None if args.no_live_db else args.live_db, args.archive_db)
    raw_request: Any = {}
    try:
        raw_request = (
            json.loads(args.request.read_text(encoding="utf-8"))
            if args.request
            else _legacy_request(args, contacts, groups)
        )
        result = execute_request(raw_request, config, contacts)
    except (RequestError, DatabasePolicyError, json.JSONDecodeError, sqlite3.Error, OSError) as error:
        request_object = raw_request if isinstance(raw_request, dict) else {}
        participant = request_object.get("participant_scope")
        participant = participant if isinstance(participant, dict) else {}
        policy = request_object.get("database_policy")
        policy = policy if isinstance(policy, dict) else {}
        participant_state = participant.get("state", "unknown")
        if participant_state not in PARTICIPANT_STATES:
            participant_state = "unknown"
        execution_mode = request_object.get("execution_mode", args.execution_mode)
        if execution_mode not in {"direct", "delegated"}:
            execution_mode = args.execution_mode
        cutoff = policy.get("archive_cutoff")
        cutoff_source = policy.get("archive_cutoff_source")
        if not (
            isinstance(cutoff, str) and cutoff and isinstance(cutoff_source, str) and cutoff_source
        ):
            cutoff = None
            cutoff_source = None
        result = {
            "schema_version": RESULT_SCHEMA,
            "status": "error",
            "execution_mode": execution_mode,
            "participant_scope_state": participant_state,
            "database": {
                "selected_source_class": None,
                "archive_cutoff": cutoff,
                "archive_cutoff_source": cutoff_source,
                "query_coverage": "blocked",
                "archive_fallback_authorized": (
                    policy.get("archive_fallback_authorized") is True
                ),
                "completeness": "blocked_incomplete",
            },
            "summary": {"result_count": 0, "total_count": 0, "truncated": False},
            "error": {"type": error.__class__.__name__, "message": str(error)},
            "records": [],
            "warnings": [],
        }
        print(json.dumps(result, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
