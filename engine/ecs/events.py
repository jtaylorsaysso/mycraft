"""
Event Bus for decoupled game logic interaction.
"""
from typing import Callable, Any, Dict, List
from dataclasses import dataclass
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Base class for all game events."""
    pass

class EventBus:
    """
    Publish-subscribe event system for decoupling game logic.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = defaultdict(list)
        self._history: List[Event] = []

    def subscribe(self, event_type: str, handler: Callable[[Any], None]):
        """
        Register a handler for a specific event type.
        
        Args:
            event_type: Name of the event to listen for
            handler: Function to call when event is published
        """
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed {handler.__name__} to {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable[[Any], None]):
        """Unregister a handler."""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    def publish(self, event_name: str, **kwargs):
        """
        Trigger an event, calling all subscribers.
        
        Args:
            event_name: Name of the event
            **kwargs: Data to pass to handlers
        """
        # Create lightweight object if not already an object
        event_data = type("EventData", (), kwargs)()
        
        handlers = self._subscribers[event_name]
        for handler in handlers:
            try:
                handler(event_data)
            except Exception as e:
                logger.error(f"Error handling event {event_name}: {e}", exc_info=True)

    def emit(self, event: Event):
        """Emit a typed event object."""
        event_type = event.__class__.__name__
        handlers = self._subscribers[event_type]
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event_type}: {e}", exc_info=True)
