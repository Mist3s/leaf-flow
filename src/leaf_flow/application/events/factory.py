"""Фабрика обработчиков событий."""
from leaf_flow.application.events.base import EventHandler
from leaf_flow.infrastructure.db.uow import UoW


class EventHandlerFactory:
    """
    Фабрика для создания обработчиков событий.
    
    Обработчики регистрируются при импорте модулей.
    """
    
    _handlers: dict[str, type[EventHandler]] = {}
    
    @classmethod
    def create(cls, event_type: str, uow: UoW) -> EventHandler | None:
        """
        Создать обработчик для указанного типа события.
        
        Args:
            event_type: Тип события (например, "order.created").
            uow: Unit of Work для работы с данными.
        
        Returns:
            Экземпляр обработчика или None, если обработчик не найден.
        """
        handler_class = cls._handlers.get(event_type)
        return handler_class(uow) if handler_class else None
    
    @classmethod
    def register(cls, event_type: str, handler_class: type[EventHandler]) -> None:
        """
        Зарегистрировать обработчик для типа события.
        
        Args:
            event_type: Тип события.
            handler_class: Класс обработчика.
        """
        cls._handlers[event_type] = handler_class
    
    @classmethod
    def get_registered_events(cls) -> list[str]:
        """Получить список зарегистрированных типов событий."""
        return list(cls._handlers.keys())
