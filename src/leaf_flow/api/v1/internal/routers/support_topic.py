from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, Response

from leaf_flow.api.deps import uow_dep, require_internal_auth
from leaf_flow.api.v1.internal.schemas.support_topic import (
    SupportTopicPublic,
    SupportTopicEnsureRequest,
    SupportTopicByThreadResponse,
)
from leaf_flow.infrastructure.db.uow import UoW
from leaf_flow.services import support_topic_service


router = APIRouter(prefix="/internal/support-topics", tags=["internal"])


@router.get(
    "/by-telegram/{user_telegram_id}",
    response_model=SupportTopicPublic,
    responses={404: {"description": "Not Found"}},
)
async def get_by_telegram(
    user_telegram_id: int = Path(...),
    _: None = Depends(require_internal_auth),
    uow: UoW = Depends(uow_dep),
) -> SupportTopicPublic:
    topic = await support_topic_service.get_by_telegram(user_telegram_id, uow)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support topic not found")
    return SupportTopicPublic(
        id=topic.id,
        user_telegram_id=topic.user_telegram_id,
        admin_chat_id=topic.admin_chat_id,
        thread_id=topic.thread_id,
    )


@router.post(
    "/ensure",
    response_model=SupportTopicPublic,
)
async def ensure_support_topic(
    payload: SupportTopicEnsureRequest,
    response: Response,
    _: None = Depends(require_internal_auth),
    uow: UoW = Depends(uow_dep),
) -> SupportTopicPublic:
    try:
        topic, created = await support_topic_service.ensure_support_topic(
            user_telegram_id=payload.user_telegram_id,
            admin_chat_id=payload.admin_chat_id,
            thread_id=payload.thread_id,
            uow=uow,
        )
    except ValueError as e:
        if str(e) == "CONFLICT_USER":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="user_telegram_id is already bound to another thread",
            )
        if str(e) == "CONFLICT_THREAD":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="(admin_chat_id, thread_id) is already bound to another user",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bad request",
        )
    if created:
        response.status_code = status.HTTP_201_CREATED
    return SupportTopicPublic(
        id=topic.id,
        user_telegram_id=topic.user_telegram_id,
        admin_chat_id=topic.admin_chat_id,
        thread_id=topic.thread_id,
    )


@router.get(
    "/by-thread",
    response_model=SupportTopicByThreadResponse,
    responses={404: {"description": "Not Found"}},
)
async def get_by_thread(
    admin_chat_id: int = Query(...),
    thread_id: int = Query(...),
    _: None = Depends(require_internal_auth),
    uow: UoW = Depends(uow_dep),
) -> SupportTopicByThreadResponse:
    topic = await support_topic_service.get_by_thread(admin_chat_id, thread_id, uow)
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Support topic not found")
    return SupportTopicByThreadResponse(
        user_telegram_id=topic.user_telegram_id,
        thread_id=topic.thread_id,
        admin_chat_id=topic.admin_chat_id,
    )
