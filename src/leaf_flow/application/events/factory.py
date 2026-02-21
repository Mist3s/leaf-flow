"""Фабрика обработчиков событий."""
from leaf_flow.application.events.base import EventHandler
from leaf_flow.infrastructure.db.uow import UoW


class EventHandlerFactory:
    """
    Фабрика для создания обработчиков событий.
    
    Обработчики регистрируются при импорте модулей.
    """
    
    _handlers: dict[str, list[type[EventHandler]]] = {}
    
    @classmethod
    def create_all(cls, event_type: str, uow: UoW) -> list[EventHandler]:
        """
        Создать все зарегистрированные обработчики для указанного типа события.
        
        Args:
            event_type: Тип события (например, "order.created").
            uow: Unit of Work для работы с данными.
        
        Returns:
            Список экземпляров обработчиков (может быть пустым).
        """
        handler_classes = cls._handlers.get(event_type, [])
        return [handler_class(uow) for handler_class in handler_classes]
    
    @classmethod
    def register(cls, event_type: str, handler_class: type[EventHandler]) -> None:
        """
        Зарегистрировать обработчик для типа события.
        
        Args:
            event_type: Тип события.
            handler_class: Класс обработчика.
        """
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        
        if handler_class not in cls._handlers[event_type]:
            cls._handlers[event_type].append(handler_class)
    
    @classmethod
    def get_registered_events(cls) -> list[str]:
        """Получить список зарегистрированных типов событий."""
        return list(cls._handlers.keys())
