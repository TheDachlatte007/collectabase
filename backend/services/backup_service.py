"""Create and restore portable, self-contained Collectabase backups."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import time
import uuid
import zipfile
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from threading import RLock
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.engine import make_url

from ..db.session import engine, get_database_url
from ..version import APP_VERSION


BACKUP_FORMAT_VERSION = 1
MAX_ARCHIVE_BYTES = int(os.getenv("COLLECTABASE_BACKUP_MAX_MB", "1024")) * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = int(os.getenv("COLLECTABASE_BACKUP_MAX_UNCOMPRESSED_MB", "4096")) * 1024 * 1024
MAX_ARCHIVE_FILES = int(os.getenv("COLLECTABASE_BACKUP_MAX_FILES", "20000"))
RESTORE_TOKEN_TTL_SECONDS = 60 * 60
SECRET_PREFIX = "cfg:"

_BACKUP_LOCK = RLock()
_RESTORE_STAGING: dict[str, "StagedRestore"] = {}


class BackupError(ValueError):
    """Raised when a backup cannot be created, inspected, or restored safely."""


@dataclass
class StagedRestore:
    token: str
    archive_path: Path
    manifest: dict[str, Any]
    created_at: float


def _sqlite_database_path() -> Path:
    url = make_url(get_database_url())
    if url.get_backend_name() != "sqlite" or not url.database:
        raise BackupError("Full backups currently require a SQLite database.")
    return Path(url.database).resolve()


def _uploads_path() -> Path:
    default = Path("/app/uploads") if Path("/app").exists() else Path(__file__).resolve().parents[2] / "uploads"
    return Path(os.getenv("UPLOADS_DIR", str(default))).resolve()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot_database(source: Path, destination: Path) -> None:
    if not source.exists():
        raise BackupError("Collection database was not found.")
    with closing(sqlite3.connect(source)) as source_db, closing(sqlite3.connect(destination)) as destination_db:
        source_db.backup(destination_db)


def _table_count(connection: sqlite3.Connection, table: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row else 0


def _read_secret_values(connection: sqlite3.Connection) -> dict[str, str]:
    try:
        rows = connection.execute(
            "SELECT key, value FROM app_meta WHERE key LIKE ? AND TRIM(COALESCE(value, '')) != ''",
            (f"{SECRET_PREFIX}%",),
        ).fetchall()
    except sqlite3.OperationalError:
        return {}
    return {str(key): str(value) for key, value in rows}


def _sanitize_snapshot(snapshot: Path, include_secrets: bool) -> tuple[dict[str, int], dict[str, str]]:
    with closing(sqlite3.connect(snapshot)) as db:
        db.execute("PRAGMA foreign_keys = ON")
        secrets = _read_secret_values(db) if include_secrets else {}
        try:
            db.execute("DELETE FROM app_meta WHERE key LIKE ?", (f"{SECRET_PREFIX}%",))
        except sqlite3.OperationalError:
            pass
        # The catalog is an updatable scrape cache, not collection data. Excluding it keeps
        # portable backups small while current values and price history remain intact.
        try:
            db.execute("DELETE FROM price_catalog")
        except sqlite3.OperationalError:
            pass
        counts = {
            table: _table_count(db, table)
            for table in ("games", "item_images", "price_history", "lots", "lot_items", "lot_sales")
        }
        db.commit()
        db.execute("VACUUM")
    return counts, secrets


def _encrypt_secrets(secrets: dict[str, str], password: str) -> bytes:
    if len(password) < 12:
        raise BackupError("Use a password with at least 12 characters to include provider credentials.")
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
    ciphertext = AESGCM(key).encrypt(nonce, json.dumps(secrets, sort_keys=True).encode("utf-8"), None)
    return json.dumps(
        {
            "version": 1,
            "kdf": "scrypt",
            "salt": base64.b64encode(salt).decode("ascii"),
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        },
        separators=(",", ":"),
    ).encode("utf-8")


def _decrypt_secrets(payload: bytes, password: str) -> dict[str, str]:
    if not password:
        raise BackupError("This backup contains provider credentials. Enter its backup password.")
    try:
        envelope = json.loads(payload.decode("utf-8"))
        salt = base64.b64decode(envelope["salt"])
        nonce = base64.b64decode(envelope["nonce"])
        ciphertext = base64.b64decode(envelope["ciphertext"])
        key = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
        values = json.loads(AESGCM(key).decrypt(nonce, ciphertext, None).decode("utf-8"))
    except Exception as exc:
        raise BackupError("The backup password is incorrect or its encrypted credentials are damaged.") from exc
    if not isinstance(values, dict) or any(not str(key).startswith(SECRET_PREFIX) for key in values):
        raise BackupError("The encrypted credential payload is invalid.")
    return {str(key): str(value) for key, value in values.items()}


def _iter_upload_files(uploads_dir: Path):
    if not uploads_dir.exists():
        return
    for path in uploads_dir.rglob("*"):
        if path.is_file() and not path.is_symlink():
            yield path


def _backup_filename() -> str:
    return f"collectabase-backup-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.zip"


def _automatic_backup_filename() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%SZ")
    return f"collectabase-auto-backup-{timestamp}.zip"


def create_backup(include_secrets: bool = False, password: str = "") -> tuple[Path, str, dict[str, Any]]:
    """Create a temporary ZIP archive that the route can stream to the browser."""
    with _BACKUP_LOCK:
        work_dir = Path(tempfile.mkdtemp(prefix="collectabase_backup_"))
        snapshot = work_dir / "collection.sqlite"
        archive_path = work_dir / _backup_filename()
        _snapshot_database(_sqlite_database_path(), snapshot)
        counts, secrets = _sanitize_snapshot(snapshot, include_secrets)

        uploads_dir = _uploads_path()
        upload_files = list(_iter_upload_files(uploads_dir) or [])
        upload_bytes = sum(path.stat().st_size for path in upload_files)
        encrypted_secrets = _encrypt_secrets(secrets, password) if secrets else None
        manifest = {
            "format": "collectabase-backup",
            "format_version": BACKUP_FORMAT_VERSION,
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "app_version": APP_VERSION,
            "includes": {
                "database": True,
                "uploads": True,
                "provider_credentials": bool(encrypted_secrets),
                "price_catalog_cache": False,
            },
            "counts": counts,
            "uploads": {"files": len(upload_files), "bytes": upload_bytes},
            "checksums": {"collection.sqlite": _sha256(snapshot)},
        }

        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
            archive.write(snapshot, "collection.sqlite")
            if encrypted_secrets:
                archive.writestr("encrypted-secrets.json", encrypted_secrets)
            for upload in upload_files:
                archive.write(upload, PurePosixPath("uploads") / upload.relative_to(uploads_dir))

        return archive_path, archive_path.name, manifest


def cleanup_backup(path: Path) -> None:
    shutil.rmtree(path.parent, ignore_errors=True)


def create_automatic_backup(retention: int = 14) -> dict[str, Any]:
    """Persist a credential-free daily backup and retain only recent automatic archives."""
    if retention < 1:
        raise BackupError("Automatic backup retention must be at least one archive.")

    archive_path, _filename, manifest = create_backup(include_secrets=False)
    destination_dir = _sqlite_database_path().parent / "backups"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / _automatic_backup_filename()
    try:
        shutil.move(str(archive_path), destination)
    finally:
        cleanup_backup(archive_path)

    archives = sorted(
        destination_dir.glob("collectabase-auto-backup-*.zip"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for expired in archives[retention:]:
        try:
            expired.unlink()
        except OSError:
            # A failed cleanup must not invalidate the newly-created backup.
            continue

    retained = list(destination_dir.glob("collectabase-auto-backup-*.zip"))
    return {
        "filename": destination.name,
        "path": str(destination),
        "retained": len(retained),
        "created_at": manifest["created_at"],
    }


def _validate_member_name(name: str) -> None:
    if "\\" in name:
        raise BackupError("Backup contains an unsafe file path.")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise BackupError("Backup contains an unsafe file path.")


def _read_manifest(archive: zipfile.ZipFile) -> dict[str, Any]:
    try:
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BackupError("Backup is missing a valid manifest.") from exc
    if manifest.get("format") != "collectabase-backup" or manifest.get("format_version") != BACKUP_FORMAT_VERSION:
        raise BackupError("This backup format is not supported by this Collectabase version.")
    if "collection.sqlite" not in archive.namelist():
        raise BackupError("Backup is missing its collection database.")
    return manifest


def _validate_archive(archive_path: Path) -> dict[str, Any]:
    if not zipfile.is_zipfile(archive_path):
        raise BackupError("Select a Collectabase backup ZIP file.")
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_ARCHIVE_FILES:
            raise BackupError("Backup contains too many files.")
        uncompressed = 0
        for info in infos:
            _validate_member_name(info.filename)
            uncompressed += info.file_size
            if uncompressed > MAX_UNCOMPRESSED_BYTES:
                raise BackupError("Backup expands beyond the configured safety limit.")
        manifest = _read_manifest(archive)
        expected_hash = str(manifest.get("checksums", {}).get("collection.sqlite", ""))
        actual_hash = hashlib.sha256(archive.read("collection.sqlite")).hexdigest()
        if not expected_hash or actual_hash != expected_hash:
            raise BackupError("Backup database checksum does not match its manifest.")
    return manifest


def stage_restore(upload) -> dict[str, Any]:
    """Persist an uploaded archive only after basic ZIP and checksum validation."""
    with _BACKUP_LOCK:
        _cleanup_stale_restore_tokens()
        work_dir = Path(tempfile.mkdtemp(prefix="collectabase_restore_"))
        archive_path = work_dir / "restore.zip"
        total = 0
        try:
            with archive_path.open("wb") as destination:
                while chunk := upload.file.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_ARCHIVE_BYTES:
                        raise BackupError("Backup exceeds the configured upload limit.")
                    destination.write(chunk)
            manifest = _validate_archive(archive_path)
        except Exception:
            shutil.rmtree(work_dir, ignore_errors=True)
            raise

        token = uuid.uuid4().hex
        _RESTORE_STAGING[token] = StagedRestore(token, archive_path, manifest, time.time())
        return {
            "token": token,
            "created_at": manifest.get("created_at"),
            "app_version": manifest.get("app_version"),
            "counts": manifest.get("counts", {}),
            "uploads": manifest.get("uploads", {}),
            "includes_provider_credentials": bool(manifest.get("includes", {}).get("provider_credentials")),
            "price_catalog_cache_included": bool(manifest.get("includes", {}).get("price_catalog_cache")),
        }


def _extract_restore_archive(archive_path: Path, target_dir: Path, password: str) -> tuple[Path, Path, dict[str, str]]:
    with zipfile.ZipFile(archive_path) as archive:
        manifest = _read_manifest(archive)
        database_path = target_dir / "collection.sqlite"
        with archive.open("collection.sqlite") as source, database_path.open("wb") as destination:
            shutil.copyfileobj(source, destination)

        uploads_target = target_dir / "uploads"
        uploads_target.mkdir()
        for info in archive.infolist():
            if not info.filename.startswith("uploads/") or info.is_dir():
                continue
            relative = PurePosixPath(info.filename).relative_to("uploads")
            destination = uploads_target.joinpath(*relative.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, destination.open("wb") as output:
                shutil.copyfileobj(source, output)

        expected_hash = str(manifest.get("checksums", {}).get("collection.sqlite", ""))
        if _sha256(database_path) != expected_hash:
            raise BackupError("Restored database checksum does not match its manifest.")

        secret_values: dict[str, str] = {}
        if manifest.get("includes", {}).get("provider_credentials"):
            try:
                secret_values = _decrypt_secrets(archive.read("encrypted-secrets.json"), password)
            except KeyError as exc:
                raise BackupError("Backup declares credentials but the encrypted payload is missing.") from exc
    return database_path, uploads_target, secret_values


def _validate_database(path: Path) -> None:
    with closing(sqlite3.connect(path)) as db:
        integrity = db.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            raise BackupError("Backup database integrity check failed.")
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        missing = {"games", "platforms", "app_meta"} - tables
        if missing:
            raise BackupError("Backup is missing required collection tables.")


def _apply_secret_values(path: Path, values: dict[str, str]) -> None:
    if not values:
        return
    with closing(sqlite3.connect(path)) as db:
        for key, value in values.items():
            db.execute(
                """
                INSERT INTO app_meta (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                (key, value),
            )
        db.commit()


def _upgrade_database(path: Path) -> None:
    from alembic import command
    from alembic.config import Config

    alembic_ini = Path(__file__).resolve().parents[1] / "alembic.ini"
    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str((alembic_ini.parent / "alembic").resolve()))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{path.as_posix()}")
    command.upgrade(config, "head")


def _current_secret_values() -> dict[str, str]:
    current_db = _sqlite_database_path()
    with closing(sqlite3.connect(current_db)) as db:
        return _read_secret_values(db)


def _create_pre_restore_backup() -> str:
    archive_path, filename, _ = create_backup(include_secrets=False)
    destination_dir = _sqlite_database_path().parent / "backups"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"pre-restore-{filename}"
    shutil.move(str(archive_path), destination)
    cleanup_backup(archive_path)
    return destination.name


def restore_backup(token: str, confirmation: str, password: str = "") -> dict[str, Any]:
    if confirmation.strip().upper() != "RESTORE":
        raise BackupError("Type RESTORE to confirm replacing the current collection.")

    with _BACKUP_LOCK:
        _cleanup_stale_restore_tokens()
        staged = _RESTORE_STAGING.get(token)
        if not staged:
            raise BackupError("Restore session expired. Inspect the backup again before restoring.")

        database_path = _sqlite_database_path()
        uploads_path = _uploads_path()
        stage_dir = Path(tempfile.mkdtemp(prefix=".collectabase_restore_", dir=database_path.parent))
        previous_uploads = uploads_path.parent / f".uploads-pre-restore-{uuid.uuid4().hex}"
        restore_completed = False
        try:
            restored_db, restored_uploads, encrypted_secrets = _extract_restore_archive(
                staged.archive_path, stage_dir, password
            )
            _validate_database(restored_db)
            _upgrade_database(restored_db)
            _validate_database(restored_db)

            # A backup without encrypted credentials never erases credentials already configured on this instance.
            _apply_secret_values(restored_db, encrypted_secrets or _current_secret_values())
            safety_backup = _create_pre_restore_backup()

            from ..scheduler import init_scheduler, shutdown_scheduler

            shutdown_scheduler()
            try:
                engine.dispose()
                uploads_were_moved = False
                try:
                    if uploads_path.exists():
                        os.replace(uploads_path, previous_uploads)
                        uploads_were_moved = True
                    os.replace(restored_uploads, uploads_path)
                    os.replace(restored_db, database_path)
                except Exception:
                    if uploads_path.exists() and uploads_were_moved:
                        shutil.rmtree(uploads_path, ignore_errors=True)
                    if uploads_were_moved and previous_uploads.exists():
                        os.replace(previous_uploads, uploads_path)
                    raise
                finally:
                    if previous_uploads.exists() and uploads_path.exists():
                        shutil.rmtree(previous_uploads, ignore_errors=True)
                restore_completed = True
            finally:
                init_scheduler()
            return {
                "ok": True,
                "message": "Collection restored successfully. Reload the app to see the restored data.",
                "safety_backup": safety_backup,
            }
        finally:
            shutil.rmtree(stage_dir, ignore_errors=True)
            if restore_completed:
                _RESTORE_STAGING.pop(token, None)
                cleanup_backup(staged.archive_path)


def _cleanup_stale_restore_tokens() -> None:
    cutoff = time.time() - RESTORE_TOKEN_TTL_SECONDS
    for token, staged in list(_RESTORE_STAGING.items()):
        if staged.created_at < cutoff:
            _RESTORE_STAGING.pop(token, None)
            cleanup_backup(staged.archive_path)
