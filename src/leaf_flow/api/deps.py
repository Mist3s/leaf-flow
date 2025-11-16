from fastapi import Depends, Header, HTTPException, status
from typing import Annotated, Optional

from leaf_flow.infrastructure.db.uow import UoW, get_uow
from leaf_flow.services.security import decode_access_token
from leaf_flow.domain.entities.user import UserEntity
from leaf_flow.domain.mappers import map_user_model_to_entity

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
    user_id = payload.get("sub", {}).get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = await uow.users.get(int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return map_user_model_to_entity(user)
