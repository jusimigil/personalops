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

    def update_event(
        self,
        event_id,
        title=None,
        start_time=None,
        end_time=None,
        calendar_name=None,
        location=None,
        description=None,
    ):
        raise NotImplementedError

    def get_event_by_id(
        self,
        event_id,
        calendar_name=None,
    ):
        raise NotImplementedError

    def find_events_by_title(
        self,
        title,
        calendar_name=None,
    ):
        raise NotImplementedError