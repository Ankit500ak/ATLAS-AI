from typing import Dict, Any, Type, TypeVar, Callable, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceContainer:
    """Dependency injection container with singleton and factory support."""

    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[[], Any]] = {}
        self._scoped: Dict[Type, Any] = {}
        self._in_scope = False

    def register_singleton(self, interface: Type[T], implementation: Type[T] | Callable[[], T]) -> None:
        """Register a singleton service."""
        if callable(implementation) and not isinstance(implementation, type):
            self._factories[interface] = implementation
        else:
            self._factories[interface] = lambda: implementation()
        logger.debug(f"Registered singleton: {interface.__name__}")

    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory for creating new instances."""
        self._factories[interface] = factory
        logger.debug(f"Registered factory: {interface.__name__}")

    def register_scoped(self, interface: Type[T], implementation: Type[T] | Callable[[], T]) -> None:
        """Register a scoped service (per request/lifecycle)."""
        self.register_singleton(interface, implementation)

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service instance."""
        if interface in self._singletons:
            return self._singletons[interface]

        if interface in self._factories:
            instance = self._factories[interface]()
            self._singletons[interface] = instance
            return instance

        raise ValueError(f"Service not registered: {interface.__name__}")

    def try_resolve(self, interface: Type[T]) -> Optional[T]:
        """Try to resolve a service, return None if not registered."""
        try:
            return self.resolve(interface)
        except ValueError:
            return None

    def scope(self):
        """Create a new scope for scoped services."""
        return ServiceScope(self)

    def clear(self) -> None:
        """Clear all registrations (mainly for testing)."""
        self._singletons.clear()
        self._factories.clear()
        self._scoped.clear()


class ServiceScope:
    """Context manager for scoped service resolution."""

    def __init__(self, container: ServiceContainer):
        self._container = container
        self._previous_scope = container._in_scope
        self._scoped_instances: Dict[Type, Any] = {}

    def __enter__(self):
        self._container._in_scope = True
        self._container._scoped = self._scoped_instances
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._container._in_scope = self._previous_scope
        self._container._scoped = {}
        self._scoped_instances.clear()

    def resolve(self, interface: Type[T]) -> T:
        if interface in self._scoped_instances:
            return self._scoped_instances[interface]

        if interface in self._container._factories:
            instance = self._container._factories[interface]()
            self._scoped_instances[interface] = instance
            return instance

        raise ValueError(f"Service not registered: {interface.__name__}")


_container: Optional[ServiceContainer] = None


def get_container() -> ServiceContainer:
    """Get the global service container."""
    global _container
    if _container is None:
        _container = ServiceContainer()
    return _container


def configure_container(config: Optional[Dict[str, Any]] = None) -> ServiceContainer:
    """Configure and return the service container with all registrations."""
    container = get_container()
    container.clear()

    from app.config import settings

    from app.infrastructure.database.repositories import (
        SQLAlchemyUserRepository,
        SQLAlchemyConversationRepository,
        SQLAlchemyDocumentRepository,
        SQLAlchemyAlertRepository,
    )
    from app.domain.repositories import (
        UserRepository,
        ConversationRepository,
        DocumentRepository,
        AlertRepository,
    )
    from app.infrastructure.ai.service import AIServiceImpl
    from app.domain.services import AIService
    from app.infrastructure.financial.stock_service import StockServiceImpl
    from app.infrastructure.financial.news_service import NewsServiceImpl
    from app.infrastructure.financial.market_service import MarketServiceImpl
    from app.infrastructure.financial.sec_service import SECFilingServiceImpl
    from app.infrastructure.financial.earnings_calendar import EarningsCalendarImpl
    from app.infrastructure.financial.cache_service import CacheServiceImpl
    from app.domain.services import (
        StockService,
        NewsService,
        MarketService,
        SECFilingService,
        EarningsCalendarService,
        CacheService,
    )
    from app.infrastructure.messaging.telegram_bot import TelegramBotImpl
    from app.domain.services import TelegramBotService

    container.register_singleton(UserRepository, lambda: SQLAlchemyUserRepository())
    container.register_singleton(ConversationRepository, lambda: SQLAlchemyConversationRepository())
    container.register_singleton(DocumentRepository, lambda: SQLAlchemyDocumentRepository())
    container.register_singleton(AlertRepository, lambda: SQLAlchemyAlertRepository())

    container.register_singleton(AIService, lambda: AIServiceImpl())
    container.register_singleton(StockService, lambda: StockServiceImpl())
    container.register_singleton(NewsService, lambda: NewsServiceImpl())
    container.register_singleton(MarketService, lambda: MarketServiceImpl())
    container.register_singleton(SECFilingService, lambda: SECFilingServiceImpl())
    container.register_singleton(EarningsCalendarService, lambda: EarningsCalendarImpl())
    container.register_singleton(CacheService, lambda: CacheServiceImpl())

    container.register_singleton(TelegramBotService, lambda: TelegramBotImpl())

    logger.info("Service container configured successfully")
    return container


def inject(interface: Type[T]) -> Callable[[], T]:
    """Dependency injection decorator for FastAPI dependencies."""
    def dependency():
        return get_container().resolve(interface)
    return dependency