from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/imessage-search/scripts/search_messages_sql.py"
SPEC = importlib.util.spec_from_file_location("imessage_search_runner", SCRIPT)
runner = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)

CACHE_SCRIPT = ROOT / "skills/imessage-search/scripts/build_contacts_cache.py"
CACHE_SPEC = importlib.util.spec_from_file_location("imessage_contacts_cache", CACHE_SCRIPT)
cache_builder = importlib.util.module_from_spec(CACHE_SPEC)
assert CACHE_SPEC and CACHE_SPEC.loader
sys.modules[CACHE_SPEC.name] = cache_builder
CACHE_SPEC.loader.exec_module(cache_builder)


def attributed_blob(text: str) -> bytes:
    encoded = text.encode("utf-8")
    return b"prefixNSString" + b"\x01\x94\x84\x01\x2b" + bytes([len(encoded)]) + encoded


def request(**overrides):
    value = {
        "schema_version": runner.REQUEST_SCHEMA,
        "query": "planning",
        "query_match": "word_boundary",
        "participant_scope": {
            "state": "resolved",
            "requested_label": "Example Group",
            "handles": ["+15550001001"],
        },
        "excluded_handles": ["+15550001999"],
        "date_range": {"since": "2026-01-01", "before": "2026-02-01"},
        "mode": "both",
        "direction": "any",
        "limit": 20,
        "database_policy": {
            "source_preference": "explicit_db",
            "archive_fallback_authorized": False,
            "allow_incomplete_archive": False,
            "archive_cutoff": None,
            "archive_cutoff_source": None,
            "explicit_db_metadata": {
                "trusted": True,
                "synthetic": True,
                "completeness": "complete",
                "cutoff": None,
                "cutoff_source": None,
            },
        },
        "cache_policy": {"use_display_names": True},
        "output_policy": {
            "include_messages": True,
            "include_contact_names": True,
            "include_chat_names": True,
        },
        "execution_mode": "direct",
    }
    for key, item in overrides.items():
        if key in {"participant_scope", "date_range", "database_policy", "output_policy"}:
            value[key] = {**value[key], **item}
        else:
            value[key] = item
    return value


class SyntheticMessages:
    def __init__(self, root: Path):
        self.path = root / "synthetic-chat.db"
        self.writer = sqlite3.connect(self.path)
        self.writer.execute("PRAGMA journal_mode=WAL")
        self.writer.execute("PRAGMA wal_autocheckpoint=0")
        self.writer.executescript(
            """
            CREATE TABLE message (
                rowid INTEGER PRIMARY KEY, date INTEGER, is_from_me INTEGER,
                text TEXT, attributedBody BLOB, handle_id INTEGER
            );
            CREATE TABLE handle (rowid INTEGER PRIMARY KEY, id TEXT);
            CREATE TABLE chat (rowid INTEGER PRIMARY KEY, display_name TEXT, chat_identifier TEXT);
            CREATE TABLE chat_message_join (chat_id INTEGER, message_id INTEGER);
            CREATE TABLE chat_handle_join (chat_id INTEGER, handle_id INTEGER);
            INSERT INTO handle VALUES (1, '+15550001001');
            INSERT INTO handle VALUES (2, '+15550001002');
            INSERT INTO handle VALUES (3, '+15550001999');
            INSERT INTO chat VALUES (1, 'Example Group', 'chat-synthetic-group');
            INSERT INTO chat VALUES (2, NULL, '+15550001002');
            INSERT INTO chat_handle_join VALUES (1, 1);
            INSERT INTO chat_handle_join VALUES (1, 2);
            INSERT INTO chat_handle_join VALUES (2, 2);
            """
        )
        self.writer.commit()
        self.writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def add(self, rowid, timestamp, sent, text, blob, handle_id, chat_id):
        self.writer.execute(
            "INSERT INTO message VALUES (?, ?, ?, ?, ?, ?)",
            (rowid, runner.to_apple_ns(runner.parse_date(timestamp)), int(sent), text, blob, handle_id),
        )
        self.writer.execute("INSERT INTO chat_message_join VALUES (?, ?)", (chat_id, rowid))
        self.writer.commit()

    def close(self):
        self.writer.close()


class IMessageSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = SyntheticMessages(self.root)
        self.db.add(1, "2026-01-05T10:00:00Z", False, "Planning note", None, 1, 1)
        self.db.add(2, "2026-01-06T10:00:00Z", False, None, attributed_blob("Planning follow-up"), 1, 1)
        self.db.add(3, "2026-01-07T10:00:00Z", False, "Unrelated private text", None, 2, 2)
        self.db.add(4, "2026-01-08T10:00:00Z", False, "Planning local copy", None, 3, 1)
        self.config = runner.DatabaseConfig(explicit_db=self.db.path, live_db=None, archive_db=None)

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def invoke_cli_payload(self, payload):
        descriptor, name = tempfile.mkstemp(prefix="request-", suffix=".json", dir=self.root)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as request_file:
            request_file.write(payload)
        request_path = Path(name)
        self.assertEqual(request_path.stat().st_mode & 0o777, 0o600)
        command = (
            sys.executable,
            str(SCRIPT),
            "--request",
            str(request_path),
            "--db",
            str(self.db.path),
        )
        try:
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
        finally:
            request_path.unlink(missing_ok=True)
        self.assertFalse(request_path.exists())
        return completed, json.loads(completed.stdout)

    def invoke_cli(self, raw_request):
        return self.invoke_cli_payload(json.dumps(raw_request))

    def test_plain_attributed_group_direction_dates_limit_and_privacy(self):
        result = runner.execute_request(
            request(limit=1), self.config, {"+15550001001": "Example Contact"}
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["summary"], {"result_count": 1, "total_count": 2, "truncated": True})
        self.assertEqual(result["records"][0]["message"], "Planning follow-up")
        serialized = json.dumps(result)
        self.assertNotIn("+15550001001", serialized)
        self.assertNotIn("+15550001999", serialized)
        self.assertNotIn(str(self.db.path), serialized)
        self.assertNotIn("Unrelated private text", serialized)
        self.assertNotIn("local_id", serialized)
        self.assertNotIn("chat_identifier", serialized)

        sent_only = runner.execute_request(request(direction="sent"), self.config)
        self.assertEqual(sent_only["summary"]["total_count"], 0)
        bounded = runner.execute_request(
            request(date_range={"since": "2026-01-06T12:00:00Z"}), self.config
        )
        self.assertEqual(bounded["summary"]["total_count"], 0)

    def test_committed_uncheckpointed_wal_row_is_visible(self):
        wal_path = Path(str(self.db.path) + "-wal")
        self.assertTrue(wal_path.exists())
        self.assertGreater(wal_path.stat().st_size, 0)
        result = runner.execute_request(request(query="follow-up"), self.config)
        self.assertEqual(result["summary"]["total_count"], 1)
        self.assertEqual(result["records"][0]["message"], "Planning follow-up")

    def test_short_read_transaction_has_consistent_snapshot_during_write(self):
        reader = runner.open_readonly(self.db.path)
        try:
            before = reader.execute("SELECT COUNT(*) FROM message").fetchone()[0]
            self.db.add(5, "2026-01-09T10:00:00Z", False, "Planning newly committed", None, 1, 1)
            during = reader.execute("SELECT COUNT(*) FROM message").fetchone()[0]
        finally:
            reader.rollback()
            reader.close()
        self.assertEqual(before, during)
        fresh = runner.execute_request(request(), self.config)
        self.assertEqual(fresh["summary"]["total_count"], 3)

    def test_unresolved_participant_fails_closed_before_database_probe(self):
        unresolved = request(participant_scope={"state": "unresolved_error", "handles": []})
        with mock.patch.object(runner, "select_database") as select:
            with self.assertRaisesRegex(runner.RequestError, "refusing an unfiltered search"):
                runner.execute_request(unresolved, self.config)
        select.assert_not_called()

    def test_not_requested_is_the_only_unfiltered_state(self):
        unfiltered = request(
            participant_scope={"state": "not_requested", "requested_label": None, "handles": []},
            excluded_handles=[],
        )
        result = runner.execute_request(unfiltered, self.config)
        self.assertEqual(result["summary"]["total_count"], 3)
        with self.assertRaises(runner.RequestError):
            runner.normalize_request(request(participant_scope={"state": "resolved", "handles": []}))

    def test_excluded_handles_are_configuration_not_identity(self):
        result = runner.execute_request(
            request(
                participant_scope={"handles": ["+15550001001", "+15550001999"]},
                excluded_handles=["+15550001999"],
            ),
            self.config,
        )
        self.assertEqual(result["summary"]["total_count"], 2)

    def test_cache_policy_false_suppresses_contact_and_chat_display_names(self):
        result = runner.execute_request(
            request(cache_policy={"use_display_names": False}),
            self.config,
            {"+15550001001": "Example Contact"},
        )
        self.assertTrue(result["records"])
        self.assertTrue(all(record["contact"] is None for record in result["records"]))
        self.assertTrue(all(record["chat"] is None for record in result["records"]))
        serialized = json.dumps(result)
        self.assertNotIn("Example Contact", serialized)
        self.assertNotIn("Example Group", serialized)

    def test_policy_and_output_booleans_reject_non_json_booleans(self):
        cases = [
            ("database_policy", "archive_fallback_authorized"),
            ("database_policy", "allow_incomplete_archive"),
            ("cache_policy", "use_display_names"),
            ("output_policy", "include_messages"),
            ("output_policy", "include_contact_names"),
            ("output_policy", "include_chat_names"),
        ]
        for section, field in cases:
            for malformed in ("false", 0, 1, None, []):
                candidate = request()
                candidate[section][field] = malformed
                with self.subTest(section=section, field=field, malformed=malformed):
                    with self.assertRaisesRegex(runner.RequestError, "must be a JSON boolean"):
                        runner.normalize_request(candidate)
            candidate = request()
            del candidate[section][field]
            with self.subTest(section=section, field=field, malformed="missing"):
                with self.assertRaises(runner.RequestError):
                    runner.normalize_request(candidate)

        for field in ("trusted", "synthetic"):
            candidate = request()
            candidate["database_policy"]["explicit_db_metadata"][field] = "true"
            with self.assertRaisesRegex(runner.RequestError, "must be a JSON boolean"):
                runner.normalize_request(candidate)

    def test_explicit_database_requires_trusted_completeness_metadata(self):
        missing = request(database_policy={"explicit_db_metadata": None})
        with self.assertRaisesRegex(runner.DatabasePolicyError, "trusted completeness metadata"):
            runner.execute_request(missing, self.config)

        untrusted = request()
        untrusted["database_policy"]["explicit_db_metadata"]["trusted"] = False
        with self.assertRaisesRegex(runner.DatabasePolicyError, "not trusted"):
            runner.execute_request(untrusted, self.config)

        unknown = request()
        unknown["database_policy"]["explicit_db_metadata"].update(
            {"synthetic": False, "completeness": "unknown"}
        )
        with self.assertRaisesRegex(runner.DatabasePolicyError, "partial-result acceptance"):
            runner.execute_request(unknown, self.config)
        unknown["database_policy"]["allow_incomplete_archive"] = True
        accepted = runner.execute_request(unknown, self.config)
        self.assertEqual(accepted["database"]["query_coverage"], "unknown_cutoff")
        self.assertEqual(accepted["database"]["completeness"], "accepted_partial")

    def test_legacy_cli_can_declare_a_complete_synthetic_fixture(self):
        args = runner._parser().parse_args([
            "--db", str(self.db.path),
            "--db-metadata-trusted",
            "--db-synthetic",
            "--db-completeness", "complete",
            "--query", "planning",
        ])
        raw = runner._legacy_request(args, {}, {})
        result = runner.execute_request(raw, runner.DatabaseConfig(explicit_db=self.db.path))
        self.assertEqual(result["database"]["query_coverage"], "synthetic_complete")
        self.assertEqual(result["database"]["completeness"], "complete")

    def test_group_scope_uses_exact_parent_handles_not_requested_label(self):
        self.db.writer.executescript(
            """
            INSERT INTO chat VALUES (3, 'Example Group', 'chat-duplicate-label');
            INSERT INTO chat VALUES (4, 'Different Label', 'chat-partial-overlap');
            INSERT INTO chat_handle_join VALUES (3, 1);
            INSERT INTO chat_handle_join VALUES (3, 3);
            INSERT INTO chat_handle_join VALUES (4, 1);
            """
        )
        self.db.writer.commit()
        self.db.add(5, "2026-01-09T10:00:00Z", False, "Planning duplicate label", None, 1, 3)
        self.db.add(6, "2026-01-10T10:00:00Z", False, "Planning partial overlap", None, 1, 4)

        result = runner.execute_request(
            request(
                mode="group",
                participant_scope={
                    "requested_label": "Example Group",
                    "handles": ["+15550001001", "+15550001002"],
                },
            ),
            self.config,
        )
        self.assertEqual(result["summary"]["total_count"], 2)
        messages = {record["message"] for record in result["records"]}
        self.assertNotIn("Planning duplicate label", messages)
        self.assertNotIn("Planning partial overlap", messages)

        sql, params = runner.build_group_query(runner.normalize_request(request(mode="group")))
        self.assertNotIn("WHERE display_name", sql)
        self.assertNotIn("Example Group", params)

    def test_archive_policy_blocks_unknown_unauthorized_and_incomplete(self):
        archive_config = runner.DatabaseConfig(live_db=self.root / "missing.db", archive_db=self.db.path)
        base_policy = {
            "source_preference": "live_then_archive",
            "archive_fallback_authorized": False,
            "archive_cutoff": "2026-01-06T00:00:00Z",
            "archive_cutoff_source": "configured",
            "explicit_db_metadata": None,
        }
        with self.assertRaisesRegex(runner.DatabasePolicyError, "not authorized"):
            runner.execute_request(request(database_policy=base_policy), archive_config)

        authorized = {**base_policy, "archive_fallback_authorized": True}
        with self.assertRaisesRegex(runner.DatabasePolicyError, "partial-result acceptance"):
            runner.execute_request(request(database_policy=authorized), archive_config)

        accepted = {**authorized, "allow_incomplete_archive": True}
        result = runner.execute_request(request(database_policy=accepted), archive_config)
        self.assertEqual(result["database"]["selected_source_class"], "archive")
        self.assertEqual(result["database"]["completeness"], "accepted_partial")
        self.assertEqual(result["database"]["query_coverage"], "overlaps_after_cutoff")

        missing_cutoff = {**accepted, "archive_cutoff": None, "archive_cutoff_source": None}
        with self.assertRaisesRegex(runner.DatabasePolicyError, "cutoff metadata"):
            runner.execute_request(request(database_policy=missing_cutoff), archive_config)

    def test_direct_and_delegated_contracts_are_equivalent(self):
        direct = runner.execute_request(request(execution_mode="direct"), self.config)

        observed = []

        def delegated(command, request_path):
            observed.append((command, request_path))
            self.assertEqual(request_path.stat().st_mode & 0o777, 0o600)
            self.assertNotIn("--contacts", command)
            self.assertNotIn("--groups", command)
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            return json.loads(completed.stdout)

        delegated = runner.execute_with_delegation_fallback(
            request(execution_mode="delegated"),
            self.config,
            delegated_executor=delegated,
        )
        self.assertEqual(len(observed), 1)
        self.assertFalse(observed[0][1].exists())
        self.assertEqual(direct["execution_mode"], "direct")
        self.assertEqual(delegated["execution_mode"], "delegated")
        direct.pop("execution_mode")
        delegated.pop("execution_mode")
        self.assertEqual(direct, delegated)

    def test_delegation_access_failure_retries_identical_request_directly(self):
        delegated_request = request(execution_mode="delegated")
        observed = []
        created = []
        real_mkstemp = tempfile.mkstemp

        def recording_mkstemp(*args, **kwargs):
            descriptor, name = real_mkstemp(dir=self.root, *args, **kwargs)
            created.append(Path(name))
            return descriptor, name

        def denied(command, request_path):
            observed.append((command, json.loads(request_path.read_text(encoding="utf-8"))))
            self.assertEqual(request_path.stat().st_mode & 0o777, 0o600)
            return {
                "schema_version": runner.RESULT_SCHEMA,
                "status": "error",
                "execution_mode": "delegated",
                "participant_scope_state": "resolved",
                "database": {
                    "selected_source_class": None,
                    "archive_cutoff": None,
                    "archive_cutoff_source": None,
                    "query_coverage": "blocked",
                    "archive_fallback_authorized": False,
                    "completeness": "blocked_incomplete",
                },
                "summary": {"result_count": 0, "total_count": 0, "truncated": False},
                "error": {"type": "PermissionError", "message": "delegated host lacks access"},
                "records": [],
                "warnings": [],
            }

        with mock.patch.object(runner.tempfile, "mkstemp", side_effect=recording_mkstemp):
            fallback = runner.execute_with_delegation_fallback(
                delegated_request,
                self.config,
                delegated_executor=denied,
            )
        direct = runner.execute_request(request(execution_mode="direct"), self.config)
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0][1]["participant_scope"]["handles"], ["+15550001001"])
        self.assertEqual(observed[0][1]["execution_mode"], "delegated")
        self.assertNotIn("--contacts", observed[0][0])
        self.assertEqual(fallback["execution_mode"], "direct")
        self.assertIn("Delegated database access failed", fallback["warnings"][0])
        self.assertTrue(created)
        self.assertTrue(all(not path.exists() for path in created))
        fallback["warnings"] = direct["warnings"]
        self.assertEqual(fallback, direct)

    def test_cli_direct_success_returns_normalized_sanitized_envelope(self):
        completed, result = self.invoke_cli(request(execution_mode="direct"))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(result["schema_version"], runner.RESULT_SCHEMA)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["execution_mode"], "direct")
        self.assertEqual(result["participant_scope_state"], "resolved")
        self.assertEqual(result["database"]["selected_source_class"], "explicit")
        self.assertEqual(result["summary"]["total_count"], 2)
        self.assertTrue(result["records"])
        self.assertFalse(
            {"local_id", "contact_handle", "chat_identifier"}.intersection(result["records"][0])
        )

    def test_cli_structured_error_for_malformed_request(self):
        malformed = request()
        malformed["output_policy"]["include_messages"] = "true"
        completed, result = self.invoke_cli(malformed)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(result["schema_version"], runner.RESULT_SCHEMA)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["type"], "RequestError")
        self.assertIn("JSON boolean", result["error"]["message"])
        self.assertEqual(result["records"], [])

        syntax_completed, syntax_result = self.invoke_cli_payload('{"schema_version":')
        self.assertEqual(syntax_completed.returncode, 2)
        self.assertEqual(syntax_result["status"], "error")
        self.assertEqual(syntax_result["error"]["type"], "JSONDecodeError")
        self.assertEqual(syntax_result["records"], [])

        self.assertEqual(runner._validate_result_envelope(result), result)
        self.assertEqual(runner._validate_result_envelope(syntax_result), syntax_result)

    def test_result_envelope_rejects_incomplete_wrong_type_and_enum_values(self):
        base = runner.execute_request(request(execution_mode="direct"), self.config)
        cases = []

        candidate = json.loads(json.dumps(base))
        candidate.pop("warnings")
        cases.append(("missing top-level key", candidate))
        candidate = json.loads(json.dumps(base))
        candidate["unexpected"] = True
        cases.append(("extra top-level key", candidate))
        candidate = json.loads(json.dumps(base))
        candidate["execution_mode"] = "remote"
        cases.append(("execution enum", candidate))
        candidate = json.loads(json.dumps(base))
        candidate["participant_scope_state"] = "maybe"
        cases.append(("participant enum", candidate))
        candidate = json.loads(json.dumps(base))
        candidate["warnings"] = "warning"
        cases.append(("warnings type", candidate))
        candidate = json.loads(json.dumps(base))
        candidate["database"].pop("archive_cutoff_source")
        cases.append(("database missing key", candidate))
        candidate = json.loads(json.dumps(base))
        candidate["database"]["archive_fallback_authorized"] = 0
        cases.append(("database boolean type", candidate))
        candidate = json.loads(json.dumps(base))
        candidate["database"]["completeness"] = "probably_complete"
        cases.append(("completeness enum", candidate))
        candidate = json.loads(json.dumps(base))
        candidate["database"]["archive_cutoff"] = "2026-01-01T00:00:00Z"
        cases.append(("cutoff pair", candidate))
        candidate = json.loads(json.dumps(base))
        candidate["summary"]["result_count"] = True
        cases.append(("summary count type", candidate))
        candidate = json.loads(json.dumps(base))
        candidate["summary"]["truncated"] = not candidate["summary"]["truncated"]
        cases.append(("summary consistency", candidate))
        candidate = json.loads(json.dumps(base))
        candidate["records"][0].pop("timestamp")
        cases.append(("record missing key", candidate))
        candidate = json.loads(json.dumps(base))
        candidate["records"][0]["direction"] = "sideways"
        cases.append(("record enum", candidate))
        candidate = json.loads(json.dumps(base))
        candidate["error"] = {"type": "Error", "message": "not allowed on success"}
        cases.append(("error on success", candidate))
        candidate = json.loads(json.dumps(base))
        candidate["status"] = "error"
        cases.append(("missing error on failure", candidate))

        for label, candidate in cases:
            with self.subTest(label=label):
                with self.assertRaises(runner.RequestError):
                    runner._validate_result_envelope(candidate)

    def test_cli_return_code_must_match_structured_status(self):
        success = runner.execute_request(request(execution_mode="direct"), self.config)
        malformed = request()
        malformed["output_policy"]["include_messages"] = "true"
        _, structured_error = self.invoke_cli(malformed)

        with mock.patch.object(
            runner.subprocess,
            "run",
            return_value=mock.Mock(returncode=7, stdout=json.dumps(success), stderr="failed"),
        ):
            with self.assertRaisesRegex(runner.RequestError, "return code"):
                runner._invoke_cli(("synthetic-runner",))

        with mock.patch.object(
            runner.subprocess,
            "run",
            return_value=mock.Mock(returncode=0, stdout=json.dumps(structured_error), stderr=""),
        ):
            with self.assertRaisesRegex(runner.RequestError, "return code"):
                runner._invoke_cli(("synthetic-runner",))

        with mock.patch.object(
            runner.subprocess,
            "run",
            return_value=mock.Mock(returncode=2, stdout=json.dumps(structured_error), stderr=""),
        ):
            self.assertEqual(runner._invoke_cli(("synthetic-runner",)), structured_error)

    def test_temporary_output_is_restrictive_and_cleaned_on_success_and_failure(self):
        created = []
        real_mkstemp = tempfile.mkstemp

        def recording_mkstemp(*args, **kwargs):
            descriptor, name = real_mkstemp(dir=self.root, *args, **kwargs)
            created.append(Path(name))
            return descriptor, name

        with (
            mock.patch.object(runner.tempfile, "mkstemp", side_effect=recording_mkstemp),
            mock.patch.object(runner.os, "chmod", wraps=os.chmod) as chmod,
        ):
            result = runner.run_with_temporary_output(request(), self.config)
            self.assertEqual(result["status"], "ok")
            chmod.assert_called_with(created[0], 0o600)
        self.assertTrue(created)
        self.assertTrue(all(not path.exists() for path in created))

        with mock.patch.object(runner.tempfile, "mkstemp", side_effect=recording_mkstemp):
            with self.assertRaises(runner.RequestError):
                runner.run_with_temporary_output(
                    request(participant_scope={"state": "unresolved_error", "handles": []}), self.config
                )
        self.assertTrue(all(not path.exists() for path in created))

    def test_public_artifacts_contain_no_private_examples_or_portability_dependencies(self):
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ROOT / "skills/imessage-search").rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
        forbidden = [
            "general-purpose",
            "~/.claude/skills",
        ]
        for token in forbidden:
            self.assertNotIn(token, text)
        self.assertNotRegex(text, r"/Users/[^/]+/")
        self.assertNotRegex(text, r"/Volumes/[^/]+/Users/")
        self.assertNotRegex(text, r"\+1(?!555)\d{10}")


class ContactsCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_source_copy_removes_temp_db_wal_and_shm(self):
        source = self.root / "AddressBook-v22.abcddb"
        sqlite3.connect(source).close()
        Path(str(source) + "-wal").write_bytes(b"synthetic wal")
        Path(str(source) + "-shm").write_bytes(b"synthetic shm")
        copied = self.root / "copied-source"
        copied.mkdir()

        with mock.patch.object(cache_builder.tempfile, "mkdtemp", return_value=str(copied)):
            with cache_builder.open_source_db(source) as connection:
                self.assertIsNotNone(connection)
                self.assertTrue((copied / "ab.db").exists())
                self.assertTrue((copied / "ab.db-wal").exists())
                self.assertTrue((copied / "ab.db-shm").exists())
        self.assertFalse(copied.exists())

    def test_source_copy_cleans_up_after_open_failure(self):
        copied = self.root / "failed-source"
        copied.mkdir()
        with mock.patch.object(cache_builder.tempfile, "mkdtemp", return_value=str(copied)):
            with cache_builder.open_source_db(self.root / "missing.db") as connection:
                self.assertIsNone(connection)
        self.assertFalse(copied.exists())

    def test_cache_outputs_are_owner_only_including_existing_files(self):
        output = self.root / "contacts.json"
        output.write_text("old", encoding="utf-8")
        os.chmod(output, 0o644)
        cache_builder.write_private_json(output, {"+15550001001": "Example Contact"})
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(output.read_text(encoding="utf-8")), {
            "+15550001001": "Example Contact"
        })


if __name__ == "__main__":
    unittest.main()
