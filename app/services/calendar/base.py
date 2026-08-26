from abc import ABC, abstractmethod


class CalendarProvider(ABC):
    """
    Abstract interface for calendar providers.

    PersonalOps interacts with this interface rather
    than directly interacting with Apple Calendar.
    """

    @abstractmethod
    def get_calendars(self):
        """Return available calendars."""
        pass

    @abstractmethod
    def create_event(
        self,
        title,
        start_time,
        end_time,
        calendar_name=None,
        location=None,
        description=None,
    ):
        """Create a calendar event."""
        pass