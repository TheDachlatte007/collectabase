import hmac
import ipaddress
import os

from fastapi import Header, HTTPException, Request


def _env_any(*names: str) -> str:
    env = os.environ
    for name in names:
        for candidate in (name, name.lower(), name.upper()):
            value = env.get(candidate, "").strip()
            if value:
                return value
    lowered = {k.lower(): v for k, v in env.items()}
    for name in names:
        value = str(lowered.get(name.lower(), "")).strip()
        if value:
            return value
    return ""


def _admin_api_key() -> str:
    return _env_any("ADMIN_API_KEY", "COLLECTABASE_ADMIN_KEY")


def _trust_proxy_headers() -> bool:
    return _env_any("TRUST_PROXY_HEADERS", "TRUST_X_FORWARDED_FOR", "TRUST_FORWARDED_IP") in {
        "1",
        "true",
        "yes",
        "on",
    }


def _extract_client_ip(request: Request) -> str:
    if _trust_proxy_headers():
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return str(request.client.host).strip()
    return ""


def _is_private_or_loopback(ip_value: str) -> bool:
    if not ip_value:
        return False
    host = ip_value.strip().lower()
    if host in {"localhost", "testclient"}:
        return True
    try:
        ip_obj = ipaddress.ip_address(ip_value.split("%")[0])
    except ValueError:
        return False
    return bool(ip_obj.is_private or ip_obj.is_loopback)


def _is_local_host_header(request: Request) -> bool:
    host = (request.headers.get("host") or "").strip().lower()
    if not host:
        return False
    host_no_port = host.split(":", 1)[0]
    return host_no_port in {"localhost", "127.0.0.1", "[::1]", "testserver"}


def admin_protection_status() -> dict:
    key_set = bool(_admin_api_key())
    return {
        "admin_key_configured": key_set,
        "admin_mode": "api_key" if key_set else "local_only",
    }


async def require_admin_access(
    request: Request,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
    authorization: str | None = Header(default=None),
):
    configured_key = _admin_api_key()
    presented_key = (x_admin_key or "").strip()

    if not presented_key and authorization:
        auth_value = authorization.strip()
        if auth_value.lower().startswith("bearer "):
            presented_key = auth_value[7:].strip()

    if configured_key:
        if presented_key and hmac.compare_digest(presented_key, configured_key):
            return
        raise HTTPException(
            status_code=401,
            detail={
                "code": "unauthorized",
                "message": "Missing or invalid admin API key.",
            },
        )

    client_ip = _extract_client_ip(request)
    if _is_private_or_loopback(client_ip) or _is_local_host_header(request):
        return

    raise HTTPException(
        status_code=403,
        detail={
            "code": "forbidden",
            "message": "Admin actions are blocked for remote clients. Set ADMIN_API_KEY to enable secure remote access.",
        },
    )
