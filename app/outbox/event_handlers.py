from abc import ABC, abstractmethod
from typing import Any, Dict


class EventHandler(ABC):
    """Abstract base class for event handlers"""

    @abstractmethod
    async def handle(self, payload: Dict[str, Any]) -> None:
        """
        Handle the event with the given payload

        Args:
            payload: Data associated with the event

        Raises:
            Exception: If handling fails , the exception will be propagated
        """
        pass

    @abstractmethod
    def supports(self, event_type: str) -> bool:
        """
        Check if the handler supports the given event type

        Args:
            event_type: Type of the event (USER_CREATED, TRANSACTION_CREATED)

        Returns:
            True if the handler supports the event type, False otherwise
        """
        pass
