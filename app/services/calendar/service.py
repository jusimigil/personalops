from services.calendar.apple_script import (
    AppleScriptCalendarProvider,
)

from datetime import datetime, timedelta


class CalendarService:
    """
    High-level calendar interface used by PersonalOps.

    The rest of the application does not need to know
    which calendar provider is being used.
    """

    def __init__(self, provider=None):

        if provider is None:
            provider = AppleScriptCalendarProvider()

        self.provider = provider

    def get_calendars(self):
        return self.provider.get_calendars()

    def create_event(
        self,
        title,
        start_time,
        end_time,
        calendar_name=None,
        location=None,
        description=None,
    ):
        return self.provider.create_event(
            title=title,
            start_time=start_time,
            end_time=end_time,
            calendar_name=calendar_name,
            location=location,
            description=description,
        )

    def get_events(
        self,
        start_time,
        end_time,
        calendar_name=None,
    ):
        return self.provider.get_events(
            start_time=start_time,
            end_time=end_time,
            calendar_name=calendar_name,
        )

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
        return self.provider.update_event(
            event_id=event_id,
            title=title,
            start_time=start_time,
            end_time=end_time,
            calendar_name=calendar_name,
            location=location,
            description=description,
        )

    def get_event_by_id(
        self,
        event_id,
        calendar_name=None,
    ):
        return self.provider.get_event_by_id(
            event_id=event_id,
            calendar_name=calendar_name,
        )

    def find_event(
        self,
        title,
        calendar_name=None,
    ):
        return self.find_events_by_title(
            title=title,
            calendar_name=calendar_name,
        )

    def find_events_by_title(
        self,
        title,
        calendar_name=None,
    ):
        return self.provider.find_events_by_title(
            title=title,
            calendar_name=calendar_name,
        )