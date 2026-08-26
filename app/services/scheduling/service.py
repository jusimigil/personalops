from datetime import datetime, time
from tools.tasks import get_tasks
from tools.memory import search_memories

from services.calendar.service import CalendarService
from services.scheduling.availability import AvailabilityService
from services.scheduling.recommendation import (
    RecommendationService,
)

from services.scheduling.urgency import UrgencyService
from tools.tasks import get_tasks

class SchedulingService:

    def __init__(self):
        self.calendar = CalendarService()
        self.availability = AvailabilityService()
        self.recommendation = RecommendationService()
        self.urgency = UrgencyService()

    def find_free_time(
        self,
        start_time,
        end_time,
        duration_minutes,
        calendar_name=None,
        earliest_hour=7,
        latest_hour=23,
    ):
        """
        Find usable free blocks in Apple Calendar.

        Defaults to 7 AM - 11 PM.
        """

        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)

        # Restrict search to reasonable hours.
        search_start = max(
            start,
            start.replace(
                hour=earliest_hour,
                minute=0,
                second=0,
            ),
        )

        search_end = min(
            end,
            end.replace(
                hour=latest_hour,
                minute=0,
                second=0,
            ),
        )

        if search_end <= search_start:
            return []

        events = self.calendar.get_events(
            start_time=search_start.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            end_time=search_end.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            calendar_name=calendar_name,
        )

        return self.availability.find_free_blocks(
            start_time=search_start.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            end_time=search_end.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            duration_minutes=duration_minutes,
            events=events,
        )

    def recommend_time(
        self,
        start_time,
        end_time,
        duration_minutes,
        preference=None,
        calendar_name=None,
        earliest_hour=7,
        latest_hour=23,
    ):
        """
        Find available time and recommend the best block.
        """

        free_blocks = self.find_free_time(
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            calendar_name=calendar_name,
            earliest_hour=earliest_hour,
            latest_hour=latest_hour,
        )

        if not free_blocks:
            return None

        return self.recommendation.recommend(
            task=None,
            free_blocks=free_blocks,
            preference=preference,
            duration_minutes=duration_minutes,
        )

    def schedule_task(
        self,
        task_title,
        start_time,
        end_time,
        calendar_name=None,
        location=None,
        description=None,
    ):
        """
        Create a calendar event for a previously recommended
        task time.
        """

        return self.calendar.create_event(
            title=task_title,
            start_time=start_time,
            end_time=end_time,
            calendar_name=calendar_name,
            location=location,
            description=description,
    )

    def recommend_for_task(
        self,
        task_title,
        start_time,
        end_time,
        duration_minutes=120,
        calendar_name=None,
        earliest_hour=7,
        latest_hour=23,
    ):
        """
        Find the best available time for a task using
        the user's saved preferences.
        """

        # ------------------------------------------
        # Find the requested task
        # ------------------------------------------

        tasks = get_tasks()

        matching_tasks = [
            task
            for task in tasks
            if task_title.lower() in task["title"].lower()
        ]

        task = (
            matching_tasks[0]
            if matching_tasks
            else {
                "title": task_title
            }
        )

        # ------------------------------------------
        # Find relevant preferences
        # ------------------------------------------

        memories = search_memories(
            "study preferences"
        )

        preference = None

        if memories:
            preference = memories[0]["content"]

        # ------------------------------------------
        # Find available time
        # ------------------------------------------

        free_blocks = self.find_free_time(
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            calendar_name=calendar_name,
            earliest_hour=earliest_hour,
            latest_hour=latest_hour,
        )

        if not free_blocks:
            return None

        # ------------------------------------------
        # Recommend the best block
        # ------------------------------------------

        recommendation = self.recommendation.recommend(
            task=task,
            free_blocks=free_blocks,
            duration_minutes=duration_minutes,
            preference=preference,
        )

        if recommendation is None:
            return None

        return {
            "task": task,
            "preference": preference,
            "recommendation": recommendation,
        }

    def get_next_task_to_schedule(self):
        """
        Return the incomplete task with the highest urgency score.

        In-progress tasks are also considered.
        """

        tasks = get_tasks()

        eligible_tasks = [
            task
            for task in tasks
            if task.get("status") in {
                "incomplete",
                "in progress",
            }
        ]

        if not eligible_tasks:
            return None

        ranked_tasks = self.urgency.rank_tasks(
            eligible_tasks
        )

        return ranked_tasks[0]

    def get_next_task_recommendation(
        self,
        start_time,
        end_time,
        calendar_name=None,
        earliest_hour=7,
        latest_hour=23,
    ):
        """
        Identify the most urgent task and recommend a
        specific time to work on it.
        """

        task = self.get_next_task_to_schedule()

        if task is None:
            return None

        duration_minutes = task.get(
            "estimated_minutes"
        )

        if duration_minutes is None:
            return {
                "task": task,
                "error": (
                    "The task does not have an "
                    "estimated duration."
                ),
            }

        memories = search_memories(
            "study preferences"
        )

        preference = None

        if memories:
            preference = memories[0]["content"]

        recommendation = self.recommend_time(
            start_time=start_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            preference=preference,
            calendar_name=calendar_name,
            earliest_hour=earliest_hour,
            latest_hour=latest_hour,
        )

        return {
            "task": task,
            "preference": preference,
            "recommendation": recommendation,
        }