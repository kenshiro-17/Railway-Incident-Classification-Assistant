from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from jwt import InvalidTokenError
from jwt import PyJWKClient

from app.core.config import settings

Role = Literal["worker", "supervisor", "admin"]


@dataclass
class UserContext:
    user_id: str
    role: Role


def _parse_bearer_token(token: str) -> UserContext:
    # Demo token shape: user:<id>|role:<worker|supervisor|admin>
    parts = dict(item.split(":", 1) for item in token.split("|") if ":" in item)
    user_id = parts.get("user", "").strip()
    role = parts.get("role", "").strip()
    if not user_id or role not in {"worker", "supervisor", "admin"}:
        raise ValueError("Invalid token")
    return UserContext(user_id=user_id, role=role)  # type: ignore[arg-type]


_jwks_client: PyJWKClient | None = None


def _jwt_user_context(token: str) -> UserContext:
    global _jwks_client
    if not settings.sso_jwks_url or not settings.sso_issuer or not settings.sso_audience:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="SSO JWT configuration missing")
    if _jwks_client is None:
        _jwks_client = PyJWKClient(settings.sso_jwks_url)

    signing_key = _jwks_client.get_signing_key_from_jwt(token)
    claims = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256", "ES256"],
        audience=settings.sso_audience,
        issuer=settings.sso_issuer,
    )
    user_id = str(claims.get(settings.sso_user_claim, "")).strip()
    role_value = claims.get(settings.sso_role_claim, "worker")
    if isinstance(role_value, list):
        role = next((r for r in role_value if r in {"worker", "supervisor", "admin"}), "worker")
    else:
        role = str(role_value).strip()
    if not user_id or role not in {"worker", "supervisor", "admin"}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid SSO JWT claims")
    return UserContext(user_id=user_id, role=role)  # type: ignore[arg-type]


def require_user(authorization: str = Header(default="")) -> UserContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SSO bearer token required")
    token = authorization.split(" ", 1)[1]
    try:
        if settings.require_jwt_in_prod and settings.environment.lower() == "prod" and settings.sso_mode != "jwt":
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="SSO JWT mode required in prod")
        if settings.sso_mode == "jwt":
            return _jwt_user_context(token)
        return _parse_bearer_token(token)
    except HTTPException:
        raise
    except (ValueError, InvalidTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid SSO token")


def require_supervisor_or_admin(user: UserContext = Depends(require_user)) -> UserContext:
    if user.role not in {"supervisor", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Supervisor/admin access required")
    return user


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require_internal_client(
    request: Request,
    x_internal_token: str = Header(default="", alias="X-Internal-Token"),
) -> None:
    if not settings.internal_api_token:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal API token not configured")
    if x_internal_token != settings.internal_api_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal API token")
    mtls_header_value = request.headers.get(settings.mtls_verified_header, "")
    if settings.require_mtls_for_internal and mtls_header_value.lower() not in {"1", "true", "yes"}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="mTLS verification required")
