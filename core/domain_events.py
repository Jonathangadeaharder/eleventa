"""
Domain Events Infrastructure

Based on "Architecture Patterns with Python" (Cosmic Python)
Chapter 8: Events and the Message Bus

This module provides the foundational infrastructure for domain events,
allowing different parts of the system to react to domain model changes
without tight coupling.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Type, TYPE_CHECKING
from uuid import UUID
import logging

if TYPE_CHECKING:
    from core.models.base import DomainModel


logger = logging.getLogger(__name__)


@dataclass
class DomainEvent(ABC):
    """
    Base class for all domain events.

    Domain events represent something that happened in the domain that
    domain experts care about. They are immutable facts about the past.

    Examples:
        - ProductPriceChanged
        - SaleCompleted
        - CustomerCreditLimitExceeded
    """

    # Unique identifier for this event occurrence
    event_id: UUID = field(init=False)

    # When this event occurred
    occurred_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Generate event ID after initialization."""
        import uuid
        if not hasattr(self, 'event_id') or self.event_id is None:
            object.__setattr__(self, 'event_id', uuid.uuid4())


class EventPublisher:
    """
    Central event publisher implementing the Observer pattern.

    Services can subscribe handlers to specific event types, and when
    events are published, all registered handlers are invoked.

    This enables the Message Bus pattern from Cosmic Python, allowing
    for loose coupling between services.

    Usage:
        # Subscribe to an event
        @EventPublisher.subscribe(ProductPriceChanged)
        def on_price_changed(event: ProductPriceChanged):
            print(f"Price changed to {event.new_price}")

        # Or register directly
        EventPublisher.subscribe(ProductPriceChanged, my_handler)

        # Publish an event
        event = ProductPriceChanged(product_id=123, new_price=Decimal('99.99'))
        EventPublisher.publish(event)
    """

    _handlers: Dict[Type[DomainEvent], List[Callable[[DomainEvent], None]]] = {}
    _global_handlers: List[Callable[[DomainEvent], None]] = []

    @classmethod
    def subscribe(
        cls,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], None] = None
    ):
        """
        Subscribe a handler to a specific event type.

        Can be used as a decorator or called directly.

        Args:
            event_type: The type of event to subscribe to
            handler: The handler function (optional if used as decorator)

        Returns:
            The handler function (for decorator usage)
        """
        def decorator(func: Callable[[DomainEvent], None]):
            if event_type not in cls._handlers:
                cls._handlers[event_type] = []

            cls._handlers[event_type].append(func)
            logger.debug(
                f"Subscribed {func.__name__} to {event_type.__name__}"
            )
            return func

        if handler is not None:
            # Direct call
            return decorator(handler)
        else:
            # Decorator usage
            return decorator

    @classmethod
    def subscribe_all(cls, handler: Callable[[DomainEvent], None]):
        """
        Subscribe a handler to ALL event types.

        Useful for cross-cutting concerns like audit logging.

        Args:
            handler: Function that accepts any DomainEvent
        """
        cls._global_handlers.append(handler)
        logger.debug(f"Subscribed {handler.__name__} to all events")

    @classmethod
    def publish(cls, event: DomainEvent) -> None:
        """
        Publish a domain event to all registered handlers.

        Handlers are executed synchronously in registration order.
        If a handler raises an exception, it is logged but does not
        prevent other handlers from executing.

        Args:
            event: The domain event to publish
        """
        event_type = type(event)
        logger.info(f"Publishing event: {event_type.__name__}")

        # Execute global handlers
        for handler in cls._global_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Error in global handler {handler.__name__} "
                    f"for {event_type.__name__}: {e}",
                    exc_info=True
                )

        # Execute specific handlers
        handlers = cls._handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Error in handler {handler.__name__} "
                    f"for {event_type.__name__}: {e}",
                    exc_info=True
                )

    @classmethod
    def clear_handlers(cls) -> None:
        """
        Clear all registered handlers.

        Primarily useful for testing.
        """
        cls._handlers.clear()
        cls._global_handlers.clear()
        logger.debug("Cleared all event handlers")

    @classmethod
    def get_handlers(cls, event_type: Type[DomainEvent]) -> List[Callable]:
        """
        Get all handlers registered for a specific event type.

        Useful for debugging and testing.

        Args:
            event_type: The event type to query

        Returns:
            List of handler functions
        """
        return cls._handlers.get(event_type, []).copy()


class MessageBus:
    """
    Message Bus pattern from Cosmic Python.

    Coordinates the handling of commands and events, managing the
    Unit of Work and ensuring events are collected and dispatched.

    This is a more advanced pattern that can be used to separate
    command handling from event handling, with automatic event
    collection from aggregates.

    Usage:
        bus = MessageBus(unit_of_work)
        result = bus.handle(CreateProductCommand(...))
    """

    def __init__(self, unit_of_work):
        """
        Initialize the message bus.

        Args:
            unit_of_work: The Unit of Work to use for transactions
        """
        self.uow = unit_of_work
        self.queue: List[DomainEvent] = []

    def handle(self, message: Any) -> Any:
        """
        Handle a command or event.

        For commands, executes the command handler within a UoW context.
        For events, publishes them through the EventPublisher.

        Args:
            message: Command or Event to handle

        Returns:
            Result from command handler, or None for events
        """
        self.queue = [message]

        while self.queue:
            message = self.queue.pop(0)

            if isinstance(message, DomainEvent):
                self._handle_event(message)
            else:
                result = self._handle_command(message)
                return result

    def _handle_event(self, event: DomainEvent) -> None:
        """
        Handle a domain event by publishing it.

        Args:
            event: The event to handle
        """
        EventPublisher.publish(event)

    def _handle_command(self, command: Any) -> Any:
        """
        Handle a command by finding and executing its handler.

        Args:
            command: The command to handle

        Returns:
            Result from command handler

        Raises:
            ValueError: If no handler found for command type
        """
        # This would need to be implemented with command handlers
        # For now, this is a placeholder for future command/query separation
        raise NotImplementedError(
            "Command handling not yet implemented. "
            "Use services directly for now."
        )

    def collect_new_events(self, aggregate: DomainModel) -> List[DomainEvent]:
        """
        Collect domain events from an aggregate.

        Aggregates can accumulate events during their operations.
        This method extracts those events for processing.

        Args:
            aggregate: The aggregate to collect events from

        Returns:
            List of domain events
        """
        events = getattr(aggregate, '_domain_events', [])
        aggregate._domain_events = []  # Clear after collecting
        return events


# Audit logging handler that logs all events
@EventPublisher.subscribe_all
def audit_log_handler(event: DomainEvent) -> None:
    """
    Global event handler for audit logging.

    Logs all domain events for audit trail purposes.
    """
    logger.info(
        f"[AUDIT] {type(event).__name__} occurred at {event.occurred_at}: "
        f"{event.__dict__}"
    )
