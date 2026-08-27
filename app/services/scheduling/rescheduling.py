from datetime import datetime, timedelta

from services.scheduling.recommendation import RecommendationService


class ReschedulingService:
    """
    Finds alternative times for existing calendar events.
    """

    def __init__(
        self,
        calendar,
        availability,
        recommendation,
    ):
        self.calendar = calendar
        self.availability = availability
        self.recommendation = recommendation

    def find_event(
        self,
        event_id=None,
        title=None,
        start_time=None,
        end_time=None,
        calendar_name=None,
    ):
        """
        Find an existing calendar event.

        Preference order:
        1. event_id
        2. title + optional time range
        """

        # ------------------------------------------
        # Direct UID lookup
        # ------------------------------------------

        if event_id:
            return self.calendar.get_event_by_id(
                event_id=event_id,
                calendar_name=calendar_name,
            )

        # ------------------------------------------
        # Title lookup
        # ------------------------------------------

        if not title:
            raise ValueError(
                "event_id or title is required."
            )

        if start_time is None or end_time is None:
            raise ValueError(
                "start_time and end_time are required "
                "when searching by title."
            )

        events = self.calendar.get_events(
            start_time=start_time,
            end_time=end_time,
            calendar_name=calendar_name,
        )

        matching_events = [
            event
            for event in events
            if event.get("title", "").lower()
            == title.lower()
        ]

        if not matching_events:
            return None

        return matching_events[0]

    def recommend_reschedule(
        self,
        event,
        search_start,
        search_end,
        preference=None,
        calendar_name=None,
    ):
        """
        Find and score alternative times for an event.
        """

        old_start = datetime.fromisoformat(
            event["start"]
        )
        old_end = datetime.fromisoformat(
            event["end"]
        )

        duration_minutes = int(
            (old_end - old_start).total_seconds() / 60
        )

        # Get calendar events for the search window.
        calendar_events = self.calendar.get_events(
            start_time=search_start,
            end_time=search_end,
            calendar_name=calendar_name,
        )

        # Don't treat the event being rescheduled
        # as a conflict with itself.
        blocking_events = [
            existing
            for existing in calendar_events
            if existing.get("event_id")
            != event.get("event_id")
        ]

        # Find free time while treating the original
        # event as removed.
        free_blocks = self.availability.find_free_blocks(
            search_start,
            search_end,
            duration_minutes,
            blocking_events,
        )

        if not free_blocks:
            return None

        task_context = {
            "title": event["title"],
            "priority": "medium",
            "estimated_minutes": duration_minutes,
        }

        recommendation = self.recommendation.recommend(
            task=task_context,
            free_blocks=free_blocks,
            duration_minutes=duration_minutes,
            preference=preference,
        )

        if recommendation is None:
            return None

        return {
            "event": event,
            "current_start": event["start"],
            "current_end": event["end"],
            "duration_minutes": duration_minutes,
            "recommendation": recommendation,
        }