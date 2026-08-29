from datetime import datetime, timedelta
from tools.memory import search_memories

from services.calendar.service import CalendarService
from services.scheduling.availability import AvailabilityService
from services.scheduling.recommendation import (
    RecommendationService,
)

from services.scheduling.urgency import UrgencyService
from tools.tasks import (
    get_tasks, 
    set_task_calendar_event,
    clear_task_calendar_event,
)

from services.scheduling.planner import PlanningService
from services.scheduling.rescheduling import ReschedulingService

SCHEDULE_CALENDAR = "term 1"
DEADLINE_CALENDAR = "exams/assign"
STUDY_CALENDAR = "study"

class SchedulingService:

    def __init__(self):
        self.calendar = CalendarService()
        self.availability = AvailabilityService()
        self.recommendation = RecommendationService()
        self.urgency = UrgencyService(
            calendar_service=self.calendar,
        )
        self.planner = PlanningService()
        self.rescheduling = ReschedulingService(
        calendar=self.calendar,
        availability=self.availability,
        recommendation=self.recommendation,
        )

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
        task=None,
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
            task=task or {},
            free_blocks=free_blocks,
            duration_minutes=duration_minutes,
            preference=preference,
        )

    def schedule_task(
        self,
        task_title=None,
        start_time=None,
        end_time=None,
        calendar_name=None,
        location=None,
        description=None,
        task_id=None,
    ):
        """
        Create a calendar event for a PersonalOps task.

        Prefer task_id when available. task_title is retained
        as a backwards-compatible fallback.
        """

        tasks = get_tasks()

        # ------------------------------------------
        # Identify the task
        # ------------------------------------------

        task = None

        if task_id is not None:
            task = next(
                (
                    existing
                    for existing in tasks
                    if existing["id"] == task_id
                ),
                None,
            )

            if task is None:
                raise ValueError(
                    f"Task {task_id} not found."
                )

        elif task_title:
            matches = [
                existing
                for existing in tasks
                if existing.get("title", "").strip().lower()
                == task_title.strip().lower()
            ]

            if not matches:
                raise ValueError(
                    f"No task found with title "
                    f"'{task_title}'."
                )

            if len(matches) > 1:
                raise ValueError(
                    f"Multiple tasks found with title "
                    f"'{task_title}'. Use task_id instead."
                )

            task = matches[0]

        else:
            raise ValueError(
                "task_id or task_title is required."
            )

        # ------------------------------------------
        # Prevent duplicate scheduling
        # ------------------------------------------

        if task.get("calendar_event_id"):
            raise ValueError(
                f"Task {task['id']} is already linked "
                "to a calendar event."
            )

        # ------------------------------------------
        # Create calendar event
        # ------------------------------------------

        event_id = self.calendar.create_event(
            title=task["title"],
            start_time=start_time,
            end_time=end_time,
            calendar_name=calendar_name,
            location=location,
            description=description,
        )

        # ------------------------------------------
        # Link task → calendar event
        # ------------------------------------------

        updated_task = set_task_calendar_event(
            task_id=task["id"],
            event_id=event_id,
            calendar_name=calendar_name,
        )

        return {
            "task": updated_task,
            "event_id": event_id,
            "start": start_time,
            "end": end_time,
        }

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
            task=task,
        )

        return {
            "task": task,
            "preference": preference,
            "recommendation": recommendation,
        }

    def plan_tasks(
        self,
        start_time,
        end_time,
        calendar_name=None,
        earliest_hour=7,
        latest_hour=23,
        break_minutes=30,
        max_work_minutes=None,
        deadline_events=None,
        reference_date=None,
    ):
        """
        Build a schedule for eligible tasks.
        """

        tasks = get_tasks()

        free_blocks = self.find_free_time(
            start_time=start_time,
            end_time=end_time,
            duration_minutes=1,
            calendar_name=calendar_name,
            earliest_hour=earliest_hour,
            latest_hour=latest_hour,
        )

        if not free_blocks:
            return []

        memories = search_memories(
            "study preferences"
        )

        preference = None

        if memories:
            preference = memories[0]["content"]

        return self.planner.plan(
            tasks=tasks,
            free_blocks=free_blocks,
            break_minutes=break_minutes,
            preference=preference,
            max_work_minutes=max_work_minutes,
            deadline_events=deadline_events,
            reference_date=reference_date,
        )

    def plan_day(
        self,
        date,
        earliest_hour=7,
        latest_hour=23,
        break_minutes=30,
        calendar_name=SCHEDULE_CALENDAR,
        max_work_minutes=360,
    ):
        """
        Build a task-aware plan for a single day.
        """

        day_start = datetime.fromisoformat(
            f"{date} 00:00:00"
        )

        day_end = datetime.fromisoformat(
            f"{date} 23:59:59"
        )

        # ------------------------------------------
        # Load tasks
        # ------------------------------------------

        tasks = get_tasks()

        # ------------------------------------------
        # Calculate scheduling window
        # ------------------------------------------

        search_start = day_start.replace(
            hour=earliest_hour,
            minute=0,
            second=0,
        )

        search_end = day_end.replace(
            hour=latest_hour,
            minute=0,
            second=0,
        )

        # ------------------------------------------
        # Load calendar events
        # ------------------------------------------
        
        events = self.calendar.get_events(
            start_time=search_start.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            end_time=search_end.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            calendar_name=calendar_name,
        )

        deadline_search_start = day_start

        deadline_search_end = day_end + timedelta(days=7)

        deadline_events = self.calendar.get_events(
            start_time=deadline_search_start.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            end_time=deadline_search_end.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            calendar_name=DEADLINE_CALENDAR,
        )

        # ------------------------------------------
        # Identify already-scheduled task sessions
        # ------------------------------------------

        scheduled_existing = []

        for task in tasks:

            event_id = task.get("calendar_event_id")

            if not event_id:
                continue

            if task.get("status") == "complete":
                continue

            task_calendar = (
                task.get("calendar_name")
                or calendar_name
            )

            if not task_calendar:
                continue

            matching_event = self.calendar.get_event_by_id(
                event_id=event_id,
                calendar_name=task_calendar,
            )

            if matching_event is None:
                continue

            event_start = datetime.fromisoformat(
                matching_event["start"]
            )

            event_end = datetime.fromisoformat(
                matching_event["end"]
            )

            if (
                event_start >= search_end
                or event_end <= search_start
            ):
                continue

            scheduled_existing.append({
                "task": task,
                "event": matching_event,
            })

        # ------------------------------------------
        # Calculate existing workload
        # ------------------------------------------

        existing_work_minutes = sum(
            int(
                (
                    datetime.fromisoformat(
                        item["event"]["end"]
                    )
                    - datetime.fromisoformat(
                        item["event"]["start"]
                    )
                ).total_seconds()
                / 60
            )
            for item in scheduled_existing
        )

        # ------------------------------------------
        # Calculate remaining workload budget
        # ------------------------------------------

        if max_work_minutes is None:
            remaining_work_minutes = None
        else:
            remaining_work_minutes = max(
                0,
                max_work_minutes - existing_work_minutes,
            )

        # ------------------------------------------
        # Build schedule using existing planner
        # ------------------------------------------

        schedule = self.plan_tasks(
            start_time=day_start.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            end_time=day_end.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            calendar_name=calendar_name,
            earliest_hour=earliest_hour,
            latest_hour=latest_hour,
            break_minutes=break_minutes,
            max_work_minutes=remaining_work_minutes,
            deadline_events=deadline_events,
            reference_date=datetime.strptime(
                date,
                "%Y-%m-%d",
            ).date(),
        )

        # ------------------------------------------
        # Identify eligible tasks
        # ------------------------------------------

        eligible_tasks = [
            task
            for task in tasks
            if task.get("status") in {
                "incomplete",
                "in progress",
            }
            and task.get("estimated_minutes")
            and not task.get("calendar_event_id")
        ]

        # ------------------------------------------
        # Determine which tasks were scheduled
        # ------------------------------------------

        scheduled_task_ids = {
            item["task"]["id"]
            for item in schedule
        }

        unscheduled_tasks = [
            task
            for task in eligible_tasks
            if task["id"] not in scheduled_task_ids
        ]

        # ------------------------------------------
        # Determine planned breaks
        # ------------------------------------------

        breaks = []

        for previous, current in zip(
            schedule,
            schedule[1:],
        ):
            previous_end = datetime.fromisoformat(
                previous["end"]
            )

            current_start = datetime.fromisoformat(
                current["start"]
            )

            gap_minutes = int(
                (
                    current_start
                    - previous_end
                ).total_seconds()
                / 60
            )

            if (
                gap_minutes >= break_minutes
                and gap_minutes <= 60
            ):
                breaks.append({
                    "start": previous["end"],
                    "end": current["start"],
                    "duration_minutes": gap_minutes,
                })

        # ------------------------------------------
        # Determine remaining free time
        # ------------------------------------------

        free_time = []

        previous_end = search_start

        for item in schedule:

            current_start = datetime.fromisoformat(
                item["start"]
            )

            if current_start > previous_end:

                gap_minutes = int(
                    (
                        current_start
                        - previous_end
                    ).total_seconds()
                    / 60
                )

                is_planned_break = any(
                    break_item["start"]
                    == previous_end.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    and break_item["end"]
                    == current_start.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    for break_item in breaks
                )

                if not is_planned_break:
                    free_time.append({
                        "start": previous_end.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "end": current_start.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "duration_minutes": gap_minutes,
                    })

            previous_end = max(
                previous_end,
                datetime.fromisoformat(
                    item["end"]
                ),
            )

        if previous_end < search_end:

            gap_minutes = int(
                (
                    search_end
                    - previous_end
                ).total_seconds()
                / 60
            )

            free_time.append({
                "start": previous_end.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "end": search_end.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "duration_minutes": gap_minutes,
            })

        # ------------------------------------------
        # Calculate workload totals
        # ------------------------------------------

        new_work_minutes = sum(
            item["duration_minutes"]
            for item in schedule
        )

        scheduled_work_minutes = (
            existing_work_minutes
            + new_work_minutes
        )

        # ------------------------------------------
        # Return complete daily plan
        # ------------------------------------------

        return {
            "date": date,
            "scheduled_existing": scheduled_existing,
            "schedule": schedule,
            "unscheduled_tasks": unscheduled_tasks,
            "breaks": breaks,
            "free_time": free_time,
            "calendar_events": events,
            "deadline_events": deadline_events,
            "calendar_name": calendar_name,
            "max_work_minutes": max_work_minutes,
            "existing_work_minutes": existing_work_minutes,
            "new_work_minutes": new_work_minutes,
            "scheduled_work_minutes": scheduled_work_minutes,
        }

    def schedule_plan(
        self,
        plan,
        calendar_name=SCHEDULE_CALENDAR,
    ):
        """
        Validate and create all events in an approved plan.

        No calendar events are created if the plan contains
        an invalid or already-linked task.
        """

        tasks = get_tasks()

        validated_items = []

        # ------------------------------------------
        # Validate entire plan first
        # ------------------------------------------

        for item in plan:

            task = item.get("task")

            if not task:
                raise ValueError(
                    "Plan item is missing its task."
                )

            task_id = task.get("id")

            if task_id is None:
                raise ValueError(
                    "Plan item is missing task ID."
                )

            current_task = next(
                (
                    existing
                    for existing in tasks
                    if existing["id"] == task_id
                ),
                None,
            )

            if current_task is None:
                raise ValueError(
                    f"Task {task_id} no longer exists."
                )

            if current_task.get("calendar_event_id"):
                raise ValueError(
                    f"Task {task_id} is already linked "
                    "to a calendar event."
                )

            start_time = item.get("start")
            end_time = item.get("end")

            if not start_time or not end_time:
                raise ValueError(
                    f"Task {task_id} is missing a start "
                    "or end time."
                )

            # Validate the time range.
            start = datetime.fromisoformat(
                start_time
            )

            end = datetime.fromisoformat(
                end_time
            )

            if end <= start:
                raise ValueError(
                    f"Invalid time range for task {task_id}."
                )

            validated_items.append({
                "task": current_task,
                "start": start_time,
                "end": end_time,
            })

        # ------------------------------------------
        # Create events
        # ------------------------------------------

        results = []

        for item in validated_items:

            task = item["task"]
            task_id = task["id"]

            event_id = self.calendar.create_event(
                title=task["title"],
                start_time=item["start"],
                end_time=item["end"],
                calendar_name=calendar_name,
            )

            updated_task = set_task_calendar_event(
                task_id=task_id,
                event_id=event_id,
                calendar_name=calendar_name,
            )

            results.append({
                "task": updated_task,
                "event_id": event_id,
                "start": item["start"],
                "end": item["end"],
            })

        return results 

    def recommend_reschedule(
        self,
        event_id,
        search_start,
        search_end,
        calendar_name=None,
        preference=None,
    ):
        """
        Recommend a new time for an existing calendar event.
        """

        event = self.calendar.get_event_by_id(
            event_id=event_id,
            calendar_name=calendar_name,
        )

        if event is None:
            return None

        return self.rescheduling.recommend_reschedule(
            event=event,
            search_start=search_start,
            search_end=search_end,
            preference=preference,
            calendar_name=calendar_name,
        )

    def reschedule_event(
        self,
        event_id,
        new_start,
        new_end,
        calendar_name=None,
    ):
        """
        Move an existing calendar event to a new time.
        """

        event = self.calendar.get_event_by_id(
            event_id=event_id,
            calendar_name=calendar_name,
        )

        if event is None:
            return None

        if event.get("recurring"):
            raise ValueError(
                "Recurring events are not supported for "
                "individual rescheduling yet."
            )

        result = self.calendar.update_event(
            event_id=event_id,
            start_time=new_start,
            end_time=new_end,
            calendar_name=calendar_name,
        )

        return {
            "event_id": event_id,
            "title": event["title"],
            "old_start": event["start"],
            "old_end": event["end"],
            "new_start": new_start,
            "new_end": new_end,
            "result": result,
        }

    def reschedule_task(
        self,
        task_id,
        new_start,
        new_end,
    ):
        """
        Reschedule the calendar event linked to a PersonalOps task.
        """

        tasks = get_tasks()

        task = next(
            (
                existing
                for existing in tasks
                if existing["id"] == task_id
            ),
            None,
        )

        if task is None:
            raise ValueError(
                f"Task {task_id} not found."
            )

        event_id = task.get("calendar_event_id")

        if not event_id:
            raise ValueError(
                f"Task {task_id} is not linked "
                "to a calendar event."
            )

        result = self.calendar.update_event(
            event_id=event_id,
            start_time=new_start,
            end_time=new_end,
        )

        return {
            "task_id": task["id"],
            "task_title": task["title"],
            "event_id": event_id,
            "new_start": new_start,
            "new_end": new_end,
            "result": result,
        }

    def remove_task_calendar_event(
        self,
        task_id,
    ):
        """
        Delete the calendar event linked to a task.
        """

        tasks = get_tasks()

        task = next(
            (
                existing
                for existing in tasks
                if existing["id"] == task_id
            ),
            None,
        )

        if task is None:
            raise ValueError(
                f"Task {task_id} not found."
            )

        event_id = task.get("calendar_event_id")
        calendar_name = task.get("calendar_name")

        if not event_id:
            raise ValueError(
                f"Task {task_id} has no linked "
                "calendar event."
            )

        result = self.calendar.delete_event(
            event_id=event_id,
            calendar_name=calendar_name,
        )

        updated_task = clear_task_calendar_event(
            task_id
        )

        return {
            "task_id": task_id,
            "task_title": task["title"],
            "event_id": event_id,
            "calendar_name": calendar_name,
            "result": result,
            "task": updated_task,
        }

    
