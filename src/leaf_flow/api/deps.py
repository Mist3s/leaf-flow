from fastapi import Depends, Header, HTTPException, Security, status
from typing import Annotated, Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from leaf_flow.infrastructure.db.uow import UoW, get_uow
from leaf_flow.services.security import decode_access_token
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.domain.mappers import map_user_model_to_entity
from leaf_flow.config import settings

_internal_http_bearer = HTTPBearer(auto_error=False)
_admin_http_bearer = HTTPBearer(auto_error=False)

def uow_dep(uow: UoW = Depends(get_uow)) -> UoW:
    return uow


async def get_current_user(
    authorization: Annotated[Optional[str], Header(alias="Authorization")] = None,
    uow: UoW = Depends(uow_dep),
) -> UserEntity:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = int(payload.get("sub"))
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = await uow.users.get(int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return map_user_model_to_entity(user)


async def require_internal_auth(
    credentials: HTTPAuthorizationCredentials | None = Security(_internal_http_bearer),
) -> None:
    if not credentials or not credentials.scheme or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    token = credentials.credentials
    if token != settings.INTERNAL_BOT_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


async def require_admin_auth(
    credentials: HTTPAuthorizationCredentials | None = Security(_admin_http_bearer),
) -> None:
    if not credentials or not credentials.scheme or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    token = credentials.credentials
    if token != settings.ADMIN_API_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
