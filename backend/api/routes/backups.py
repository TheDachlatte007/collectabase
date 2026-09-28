from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from ...services.backup_service import (
    BackupError,
    cleanup_backup,
    create_backup,
    restore_backup,
    stage_restore,
)
from ..schemas import BackupCreateRequest, BackupRestoreRequest
from ..security import require_admin_access


router = APIRouter()


def _bad_backup_request(exc: BackupError) -> HTTPException:
    return HTTPException(status_code=400, detail={"code": "bad_backup", "message": str(exc)})


@router.post("/api/backups/create")
async def create_full_backup(payload: BackupCreateRequest, _admin: None = Depends(require_admin_access)):
    try:
        archive_path, filename, _ = create_backup(
            include_secrets=payload.include_provider_credentials,
            password=payload.backup_password or "",
        )
    except BackupError as exc:
        raise _bad_backup_request(exc) from exc

    return FileResponse(
        archive_path,
        media_type="application/zip",
        filename=filename,
        background=BackgroundTask(cleanup_backup, archive_path),
    )


@router.post("/api/backups/inspect")
async def inspect_full_backup(file: UploadFile = File(...), _admin: None = Depends(require_admin_access)):
    if not (file.filename or "").lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail={"code": "bad_request", "message": "Select a ZIP backup file."})
    try:
        return stage_restore(file)
    except BackupError as exc:
        raise _bad_backup_request(exc) from exc


@router.post("/api/backups/restore")
async def restore_full_backup(payload: BackupRestoreRequest, _admin: None = Depends(require_admin_access)):
    try:
        return restore_backup(
            token=payload.restore_token,
            confirmation=payload.confirmation,
            password=payload.backup_password or "",
        )
    except BackupError as exc:
        raise _bad_backup_request(exc) from exc
