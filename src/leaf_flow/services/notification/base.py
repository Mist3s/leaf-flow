"""Базовый класс обработчика событий."""
from abc import ABC, abstractmethod
from typing import Any

from leaf_flow.infrastructure.db.uow import UoW


class EventHandler(ABC):
    """
    Базовый класс для обработчиков событий.
    
    Каждый обработчик получает UoW для подгрузки
    дополнительных данных (user, support_topic и т.д.).
    """
    
    def __init__(self, uow: UoW):
        self._uow = uow
    
    @abstractmethod
    async def handle(self, payload: dict[str, Any]) -> None:
        """
        Обработать событие.
        
        Args:
            payload: Данные события из outbox.
        """
        ...
