from fastapi import HTTPException


def api_error(status_code: int, message: str, code: str):
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


def not_found(message: str = "Resource not found"):
    return api_error(404, message, "not_found")


def bad_request(message: str = "Bad request"):
    return api_error(400, message, "bad_request")


def conflict(message: str = "Conflict", extra: dict | None = None):
    payload = {"code": "conflict", "message": message}
    if extra:
        payload.update(extra)
    return HTTPException(status_code=409, detail=payload)

