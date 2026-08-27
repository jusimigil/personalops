from services.calendar.service import CalendarService
from services.scheduling.service import SchedulingService
from services.approval import request_confirmation

calendar_service = CalendarService()
scheduling_service = SchedulingService()


def get_calendars():
    """
    Return the user's available Apple Calendars.
    """

    return calendar_service.get_calendars()


def create_calendar_event(
    title,
    start_time,
    end_time,
    calendar_name=None,
    location=None,
    description=None,
):
    """
    Create an event in Apple Calendar.
    """

    return calendar_service.create_event(
        title=title,
        start_time=start_time,
        end_time=end_time,
        calendar_name=calendar_name,
        location=location,
        description=description,
    )

def get_calendar_events(
    start_time,
    end_time,
    calendar_name=None,
):
    """
    Retrieve Apple Calendar events within a time range.
    """

    return calendar_service.get_events(
        start_time=start_time,
        end_time=end_time,
        calendar_name=calendar_name,
    )

def schedule_task(
    task_title=None,
    start_time=None,
    end_time=None,
    calendar_name=None,
    location=None,
    description=None,
    task_id=None,
):
    action_description = (
        "Create calendar event:\n\n"
        f"  Title: {task_title}\n"
        f"  Start: {start_time}\n"
        f"  End: {end_time}"
    )

    if calendar_name:
        action_description += (
            f"\n  Calendar: {calendar_name}"
        )

    approved = request_confirmation(
        action_description
    )

    if not approved:
        return {
            "success": False,
            "message": "Calendar event creation cancelled.",
        }

    return scheduling_service.schedule_task(
        task_title=task_title,
        start_time=start_time,
        end_time=end_time,
        calendar_name=calendar_name,
        location=location,
        description=description,
        task_id=task_id,
    )

def find_free_time(
    start_time,
    end_time,
    duration_minutes,
    calendar_name=None,
    earliest_hour=7,
    latest_hour=23,
):
    """
    Find available time blocks in Apple Calendar.
    """

    return scheduling_service.find_free_time(
        start_time=start_time,
        end_time=end_time,
        duration_minutes=duration_minutes,
        calendar_name=calendar_name,
        earliest_hour=earliest_hour,
        latest_hour=latest_hour,
    )

def recommend_task_time(
    task_title,
    start_time,
    end_time,
    duration_minutes=120,
    calendar_name=None,
    earliest_hour=7,
    latest_hour=23,
):
    return scheduling_service.recommend_for_task(
        task_title=task_title,
        start_time=start_time,
        end_time=end_time,
        duration_minutes=duration_minutes,
        calendar_name=calendar_name,
        earliest_hour=earliest_hour,
        latest_hour=latest_hour,
    )

def plan_tasks(
    start_time,
    end_time,
    calendar_name=None,
    earliest_hour=7,
    latest_hour=23,
    break_minutes=30,
):
    """
    Build a proposed schedule for multiple tasks.
    """

    return scheduling_service.plan_tasks(
        start_time=start_time,
        end_time=end_time,
        calendar_name=calendar_name,
        earliest_hour=earliest_hour,
        latest_hour=latest_hour,
        break_minutes=break_minutes,
    )

def schedule_plan(
    plan,
    calendar_name=None,
):
    """
    Schedule an entire approved plan.
    """

    return scheduling_service.schedule_plan(
        plan=plan,
        calendar_name=calendar_name,
    )

def recommend_reschedule(
    event_id,
    search_start,
    search_end,
    calendar_name=None,
    preference=None,
):
    """
    Recommend a new time for an existing calendar event.
    """

    return scheduling_service.recommend_reschedule(
        event_id=event_id,
        search_start=search_start,
        search_end=search_end,
        calendar_name=calendar_name,
        preference=preference,
    )


def reschedule_event(
    event_id,
    new_start,
    new_end,
    calendar_name=None,
):
    """
    Move an existing calendar event to a new time.
    """

    return scheduling_service.reschedule_event(
        event_id=event_id,
        new_start=new_start,
        new_end=new_end,
        calendar_name=calendar_name,
    )

def find_calendar_event(
    title,
    calendar_name=None,
):
    return calendar_service.find_event(
        title=title,
        calendar_name=calendar_name,
    )

def reschedule_task(
    task_id,
    new_start,
    new_end,
):
    """
    Reschedule the calendar event linked to a PersonalOps task.
    """

    return scheduling_service.reschedule_task(
        task_id=task_id,
        new_start=new_start,
        new_end=new_end,
    )