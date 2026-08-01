#!/usr/bin/env python3
"""Ownership-safe symlink installer for singleton-skills."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Mapping


SCHEMA_VERSION = 1
PROVENANCE_NAME = ".singleton-skills-links.json"
LOCK_NAME = ".singleton-skills-links.lock"
SUPPORTED_MANIFEST = "supported-skills.txt"


class InstallerError(RuntimeError):
    """A safe, user-facing installer refusal."""


@dataclass(frozen=True)
class TargetRoot:
    kind: str
    path: Path


@dataclass(frozen=True)
class DesiredLink:
    skill_name: str
    target_kind: str
    target_root: Path
    source_path: Path
    target_path: Path
    target_root_identity: tuple[int, int] | None = None

    def record(self, checkout_realpath: Path) -> dict[str, object]:
        link_value = str(self.source_path)
        return {
            "checkout_realpath": str(checkout_realpath),
            "skill_name": self.skill_name,
            "target_path": str(self.target_path),
            "target_kind": self.target_kind,
            "target_root": str(self.target_root),
            "source_path": str(self.source_path),
            "installed_link_value": link_value,
        }


@dataclass
class RootHandle:
    path: Path
    fd: int
    identity: tuple[int, int]

    def verify(self) -> None:
        try:
            path_stat = self.path.stat()
            fd_stat = os.fstat(self.fd)
        except OSError as exc:
            raise InstallerError(f"cannot verify installation root: {self.path}: {exc}") from exc
        observed = (path_stat.st_dev, path_stat.st_ino)
        opened = (fd_stat.st_dev, fd_stat.st_ino)
        if observed != self.identity or opened != self.identity:
            raise InstallerError(f"installation root identity changed: {self.path}")

    def exists(self, name: str) -> bool:
        try:
            os.stat(name, dir_fd=self.fd, follow_symlinks=False)
        except FileNotFoundError:
            return False
        return True

    def readlink(self, name: str) -> str | None:
        try:
            return os.readlink(name, dir_fd=self.fd)
        except (FileNotFoundError, OSError):
            return None

    def symlink(self, source: str, name: str) -> None:
        os.symlink(source, name, dir_fd=self.fd)

    def unlink(self, name: str) -> None:
        os.unlink(name, dir_fd=self.fd)


@contextmanager
def _transaction_lock(checkout_realpath: Path) -> Iterator[None]:
    lock_path = checkout_realpath / LOCK_NAME
    flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(lock_path, flags, 0o600)
    except OSError as exc:
        raise InstallerError(f"cannot open installer transaction lock: {exc}") from exc
    with os.fdopen(fd, "a+b") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        except OSError as exc:
            raise InstallerError(f"cannot acquire installer transaction lock: {exc}") from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@contextmanager
def _open_root_handles(
    desired_links: Iterable[DesiredLink], *, create_missing: bool = True
) -> Iterator[dict[Path, RootHandle]]:
    expected_by_root: dict[Path, tuple[int, int] | None] = {}
    for desired in desired_links:
        expected_by_root.setdefault(desired.target_root, desired.target_root_identity)
    handles: dict[Path, RootHandle] = {}
    created_roots: list[Path] = []
    completed = False
    try:
        for path, expected in expected_by_root.items():
            if expected is None:
                if not create_missing:
                    raise InstallerError(f"installation root is missing: {path}")
                try:
                    path.mkdir(parents=True, exist_ok=False)
                except FileExistsError as exc:
                    raise InstallerError(
                        f"installation root appeared during transaction: {path}"
                    ) from exc
                created_roots.append(path)
            else:
                try:
                    current = path.stat()
                except OSError as exc:
                    raise InstallerError(f"installation root changed: {path}: {exc}") from exc
                if (current.st_dev, current.st_ino) != expected:
                    raise InstallerError(f"installation root identity changed: {path}")
            try:
                fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
            except OSError as exc:
                raise InstallerError(f"cannot open installation root: {path}: {exc}") from exc
            fd_stat = os.fstat(fd)
            identity = (fd_stat.st_dev, fd_stat.st_ino)
            if expected is not None and identity != expected:
                os.close(fd)
                raise InstallerError(f"installation root identity changed: {path}")
            handle = RootHandle(path, fd, identity)
            handle.verify()
            handles[path] = handle
        yield handles
        completed = True
    finally:
        for handle in handles.values():
            os.close(handle.fd)
        if not completed:
            for path in reversed(created_roots):
                try:
                    path.rmdir()
                except OSError:
                    pass


def _resolved(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def resolve_roots(
    shared_dir: str | None,
    claude_dir: str | None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Path]:
    env = os.environ if environ is None else environ
    home = _resolved(env.get("HOME") or Path.home())
    shared = shared_dir or env.get("SINGLETON_SHARED_SKILLS_DIR")
    claude = claude_dir or env.get("SINGLETON_CLAUDE_SKILLS_DIR")
    return {
        "shared": _resolved(shared) if shared else home / ".agents" / "skills",
        "claude": _resolved(claude) if claude else home / ".claude" / "skills",
    }


def selected_roots(target: str, roots: Mapping[str, Path]) -> list[TargetRoot]:
    kinds = ("shared", "claude") if target == "all" else (target,)
    selected = [TargetRoot(kind, _resolved(roots[kind])) for kind in kinds]
    if len({root.path for root in selected}) != len(selected):
        raise InstallerError("shared and Claude targets resolve to the same directory")
    return selected


def load_supported(repo_root: Path) -> list[str]:
    manifest = repo_root / SUPPORTED_MANIFEST
    try:
        names = [
            line.strip()
            for line in manifest.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    except OSError as exc:
        raise InstallerError(f"cannot read supported-skill manifest: {exc}") from exc
    if not names or len(names) != len(set(names)):
        raise InstallerError("supported-skill manifest must contain unique skill names")
    for name in names:
        _validate_skill_name(name)
    return names


def _validate_skill_name(name: str) -> None:
    candidate = Path(name)
    if (
        name in {".", ".."}
        or candidate.is_absolute()
        or candidate.name != name
        or "/" in name
        or "\\" in name
    ):
        raise InstallerError(
            f"supported-skill manifest contains an unsafe skill name: {name!r}"
        )


def _confined_child(parent: Path, name: str, *, strict: bool) -> Path:
    parent_realpath = parent.resolve(strict=strict)
    child = (parent_realpath / name).resolve(strict=strict)
    try:
        child.relative_to(parent_realpath)
    except ValueError as exc:
        raise InstallerError(f"path escapes its required root: {child}") from exc
    return child


def load_skill_names(repo_root: Path, selection: str) -> list[str]:
    supported = load_supported(repo_root)
    if selection == "default":
        names = supported
    else:
        skills_dir = repo_root / "skills"
        names = sorted(path.name for path in skills_dir.iterdir() if path.is_dir())
    for name in names:
        _validate_skill_name(name)
        source = _confined_child(repo_root / "skills", name, strict=True)
        if not source.is_dir():
            raise InstallerError(f"skill source is missing: {name}")
    return names


def _empty_provenance(checkout_realpath: Path) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "checkout_realpath": str(checkout_realpath),
        "records": [],
    }


def _load_provenance(path: Path, checkout_realpath: Path) -> tuple[dict[str, object], bytes | None]:
    if path.is_symlink():
        raise InstallerError("installer provenance must not be a symlink")
    if not path.exists():
        return _empty_provenance(checkout_realpath), None
    try:
        raw = path.read_bytes()
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallerError(f"cannot read installer provenance: {exc}") from exc
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != SCHEMA_VERSION
        or data.get("checkout_realpath") != str(checkout_realpath)
        or not isinstance(data.get("records"), list)
        or any(not isinstance(record, dict) for record in data["records"])
    ):
        raise InstallerError("installer provenance has an unsupported or foreign schema")
    required_record_fields = {
        "checkout_realpath",
        "skill_name",
        "target_path",
        "target_kind",
        "target_root",
        "source_path",
        "installed_link_value",
    }
    for record in data["records"]:
        if (
            set(record) != required_record_fields
            or any(not isinstance(record[field], str) for field in required_record_fields)
            or record["checkout_realpath"] != str(checkout_realpath)
            or record["target_kind"] not in {"shared", "claude"}
        ):
            raise InstallerError("installer provenance contains an invalid ownership record")
    target_paths = [record["target_path"] for record in data["records"]]
    if any(not isinstance(path_value, str) for path_value in target_paths) or len(
        target_paths
    ) != len(set(target_paths)):
        raise InstallerError("installer provenance contains invalid or duplicate targets")
    return data, raw


def _serialize_provenance(data: Mapping[str, object]) -> bytes:
    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_bytes_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _restore_provenance(path: Path, raw: bytes | None) -> None:
    if raw is None:
        if path.exists():
            path.unlink()
    else:
        _write_bytes_atomic(path, raw)


def _actual_link_value(path: Path) -> str | None:
    return os.readlink(path) if path.is_symlink() else None


def _record_for(
    records: Iterable[dict[str, object]], target_path: Path
) -> dict[str, object] | None:
    target = str(target_path)
    return next((record for record in records if record.get("target_path") == target), None)


def _is_owned(
    desired: DesiredLink,
    record: dict[str, object] | None,
    checkout_realpath: Path,
) -> bool:
    return record == desired.record(checkout_realpath) and _actual_link_value(
        desired.target_path
    ) == str(desired.source_path)


def _desired_links(
    repo_root: Path,
    selection: str,
    target: str,
    roots: Mapping[str, Path],
) -> list[DesiredLink]:
    names = load_skill_names(repo_root, selection)
    skills_root = (repo_root / "skills").resolve(strict=True)
    desired_links: list[DesiredLink] = []
    for root in selected_roots(target, roots):
        root_path = root.path.resolve(strict=False)
        try:
            root_stat = root_path.stat()
        except FileNotFoundError:
            root_identity = None
        except OSError as exc:
            raise InstallerError(f"cannot inspect installation root: {root_path}: {exc}") from exc
        else:
            if not root_path.is_dir():
                raise InstallerError(f"installation root is not a directory: {root_path}")
            root_identity = (root_stat.st_dev, root_stat.st_ino)
        for name in names:
            source_path = _confined_child(skills_root, name, strict=True)
            target_parent = (root_path / name).parent.resolve(strict=False)
            if target_parent != root_path:
                raise InstallerError(
                    f"install target escapes its required root: {root_path / name}"
                )
            desired_links.append(
                DesiredLink(
                    skill_name=name,
                    target_kind=root.kind,
                    target_root=root_path,
                    source_path=source_path,
                    target_path=target_parent / name,
                    target_root_identity=root_identity,
                )
            )
    return desired_links


def _preflight_install(
    desired_links: Iterable[DesiredLink],
    records: list[dict[str, object]],
    checkout_realpath: Path,
    handles: Mapping[Path, RootHandle],
) -> None:
    for desired in desired_links:
        handle = handles[desired.target_root]
        handle.verify()
        record = _record_for(records, desired.target_path)
        exists = handle.exists(desired.skill_name)
        owned = record == desired.record(checkout_realpath) and handle.readlink(
            desired.skill_name
        ) == str(desired.source_path)
        if exists and not owned:
            raise InstallerError(f"refusing foreign install target: {desired.target_path}")
        if not exists and record is not None and record != desired.record(checkout_realpath):
            raise InstallerError(f"refusing conflicting ownership record: {desired.target_path}")


def install(
    repo_root: Path,
    selection: str,
    target: str,
    roots: Mapping[str, Path],
) -> list[DesiredLink]:
    checkout_realpath = repo_root.resolve(strict=True)
    with _transaction_lock(checkout_realpath):
        provenance_path = checkout_realpath / PROVENANCE_NAME
        provenance, prior_provenance = _load_provenance(
            provenance_path, checkout_realpath
        )
        records = list(provenance["records"])
        desired_links = _desired_links(checkout_realpath, selection, target, roots)
        with _open_root_handles(desired_links) as handles:
            _preflight_install(desired_links, records, checkout_realpath, handles)
            created: list[DesiredLink] = []
            try:
                for desired in desired_links:
                    handle = handles[desired.target_root]
                    handle.verify()
                    if handle.exists(desired.skill_name):
                        existing = _record_for(records, desired.target_path)
                        owned = existing == desired.record(
                            checkout_realpath
                        ) and handle.readlink(desired.skill_name) == str(
                            desired.source_path
                        )
                        if not owned:
                            raise InstallerError(
                                "install target changed after preflight: "
                                f"{desired.target_path}"
                            )
                    else:
                        try:
                            handle.symlink(
                                str(desired.source_path), desired.skill_name
                            )
                        except FileExistsError as exc:
                            raise InstallerError(
                                "install target appeared after preflight: "
                                f"{desired.target_path}"
                            ) from exc
                        created.append(desired)
                    existing = _record_for(records, desired.target_path)
                    if existing is not None:
                        records.remove(existing)
                    records.append(desired.record(checkout_realpath))
                for desired in desired_links:
                    handle = handles[desired.target_root]
                    handle.verify()
                    if handle.readlink(desired.skill_name) != str(desired.source_path):
                        raise InstallerError(
                            "install target changed before provenance write: "
                            f"{desired.target_path}"
                        )
                provenance["records"] = sorted(
                    records, key=lambda item: str(item["target_path"])
                )
                _write_bytes_atomic(
                    provenance_path, _serialize_provenance(provenance)
                )
                for handle in handles.values():
                    handle.verify()
            except Exception as exc:
                rollback_errors: list[str] = []
                for desired in reversed(created):
                    handle = handles[desired.target_root]
                    try:
                        if handle.readlink(desired.skill_name) == str(
                            desired.source_path
                        ):
                            handle.unlink(desired.skill_name)
                        elif handle.exists(desired.skill_name):
                            rollback_errors.append(
                                f"{desired.target_path}: created link changed "
                                "during installation"
                            )
                    except OSError as rollback_exc:
                        rollback_errors.append(
                            f"{desired.target_path}: {rollback_exc}"
                        )
                try:
                    _restore_provenance(provenance_path, prior_provenance)
                except OSError as rollback_exc:
                    rollback_errors.append(f"{provenance_path}: {rollback_exc}")
                if rollback_errors:
                    raise InstallerError(
                        f"installation failed ({exc}); rollback also failed: "
                        f"{'; '.join(rollback_errors)}"
                    ) from exc
                raise InstallerError(
                    f"installation failed and was rolled back: {exc}"
                ) from exc
        return desired_links


def uninstall(
    repo_root: Path,
    selection: str,
    target: str,
    roots: Mapping[str, Path],
) -> list[DesiredLink]:
    checkout_realpath = repo_root.resolve(strict=True)
    with _transaction_lock(checkout_realpath):
        provenance_path = checkout_realpath / PROVENANCE_NAME
        provenance, prior_provenance = _load_provenance(
            provenance_path, checkout_realpath
        )
        records = list(provenance["records"])
        desired_links = _desired_links(checkout_realpath, selection, target, roots)
        candidates = [
            desired
            for desired in desired_links
            if _record_for(records, desired.target_path) is not None
        ]
        if not candidates:
            return []
        with _open_root_handles(candidates, create_missing=False) as handles:
            owned: list[DesiredLink] = []
            for desired in candidates:
                handle = handles[desired.target_root]
                handle.verify()
                record = _record_for(records, desired.target_path)
                if record != desired.record(
                    checkout_realpath
                ) or handle.readlink(desired.skill_name) != str(desired.source_path):
                    raise InstallerError(
                        "refusing to uninstall changed or foreign target: "
                        f"{desired.target_path}"
                    )
                owned.append(desired)
            removed: list[tuple[DesiredLink, str]] = []
            try:
                for desired in owned:
                    handle = handles[desired.target_root]
                    handle.verify()
                    prior_link = handle.readlink(desired.skill_name)
                    if prior_link is None:
                        raise InstallerError(
                            f"uninstall target changed: {desired.target_path}"
                        )
                    handle.unlink(desired.skill_name)
                    removed.append((desired, prior_link))
                    record = _record_for(records, desired.target_path)
                    if record is not None:
                        records.remove(record)
                for handle in handles.values():
                    handle.verify()
                provenance["records"] = sorted(
                    records, key=lambda item: str(item["target_path"])
                )
                if records or prior_provenance is not None:
                    _write_bytes_atomic(
                        provenance_path, _serialize_provenance(provenance)
                    )
                for handle in handles.values():
                    handle.verify()
            except Exception as exc:
                rollback_errors: list[str] = []
                for desired, prior_link in reversed(removed):
                    handle = handles[desired.target_root]
                    try:
                        if handle.exists(desired.skill_name):
                            rollback_errors.append(
                                f"{desired.target_path}: rollback target reappeared"
                            )
                        else:
                            handle.symlink(prior_link, desired.skill_name)
                    except OSError as rollback_exc:
                        rollback_errors.append(
                            f"{desired.target_path}: {rollback_exc}"
                        )
                try:
                    _restore_provenance(provenance_path, prior_provenance)
                except OSError as rollback_exc:
                    rollback_errors.append(f"{provenance_path}: {rollback_exc}")
                if rollback_errors:
                    raise InstallerError(
                        f"uninstall failed ({exc}); rollback also failed: "
                        f"{'; '.join(rollback_errors)}"
                    ) from exc
                raise InstallerError(
                    f"uninstall failed and was rolled back: {exc}"
                ) from exc
            return owned


def list_status(repo_root: Path, target: str, roots: Mapping[str, Path]) -> list[str]:
    checkout_realpath = repo_root.resolve(strict=True)
    provenance, _ = _load_provenance(
        checkout_realpath / PROVENANCE_NAME, checkout_realpath
    )
    records = list(provenance["records"])
    supported = set(load_supported(checkout_realpath))
    names = load_skill_names(checkout_realpath, "all")
    lines: list[str] = []
    for root in selected_roots(target, roots):
        for name in names:
            desired = DesiredLink(
                skill_name=name,
                target_kind=root.kind,
                target_root=root.path,
                source_path=(checkout_realpath / "skills" / name).resolve(strict=True),
                target_path=root.path / name,
            )
            installed = os.path.lexists(desired.target_path)
            record = _record_for(records, desired.target_path)
            owned = installed and _is_owned(desired, record, checkout_realpath)
            lines.append(
                f"{root.kind:<6} {name:<24} supported={'yes' if name in supported else 'no':<3} "
                f"installed={'yes' if installed else 'no':<3} owned={'yes' if owned else 'no'}"
            )
    return lines


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("install", "list", "uninstall"))
    parser.add_argument("--set", dest="selection", choices=("default", "all"), default="default")
    parser.add_argument("--target", choices=("shared", "claude", "all"), default="shared")
    parser.add_argument("--shared-dir")
    parser.add_argument("--claude-dir")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parent.parent
    roots = resolve_roots(args.shared_dir, args.claude_dir)
    try:
        if args.command == "install":
            changed = install(repo_root, args.selection, args.target, roots)
            for item in changed:
                print(f"Linked [{item.target_kind}]: {item.skill_name} -> {item.target_path}")
            if args.target in {"claude", "all"}:
                print(
                    "Warning: do not enable the Claude native plugin and Claude symlink "
                    "installation together; that can discover skills twice."
                )
        elif args.command == "uninstall":
            changed = uninstall(repo_root, args.selection, args.target, roots)
            for item in changed:
                print(f"Removed [{item.target_kind}]: {item.skill_name}")
            if not changed:
                print("No owned links selected.")
        else:
            for line in list_status(repo_root, args.target, roots):
                print(line)
    except InstallerError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
