import json
from pathlib import Path


# Find the project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Location of our task database
TASKS_FILE = BASE_DIR / "data" / "tasks.json"


def load_tasks():
    """Load tasks from the local JSON database."""

    if not TASKS_FILE.exists():
        return []

    with open(TASKS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_tasks(tasks):
    """Save tasks to the local JSON database."""

    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(TASKS_FILE, "w", encoding="utf-8") as file:
        json.dump(tasks, file, indent=2)


def get_tasks():
    """
    Get the user's current tasks.

    Returns:
        A list of tasks with their ID, title, due date,
        priority, and status.
    """

    return load_tasks()

def create_task(
    title,
    due_date=None,
    priority="medium",
    estimated_minutes=None,
    ):
    """
    Create a new task.

    Args:
        title: The task title.
        due_date: Optional due date in YYYY-MM-DD format.
        priority: Task priority: low, medium, or high.

    Returns:
        The newly created task.
    """

    tasks = load_tasks()

    # Generate a new ID
    if tasks:
        new_id = max(task["id"] for task in tasks) + 1
    else:
        new_id = 1

    new_task = {
        "id": new_id,
        "title": title,
        "due_date": due_date,
        "priority": priority,
        "status": "incomplete",
        "estimated_minutes": estimated_minutes,
        "calendar_event_id": None,
        "calendar_name": None,
    }

    tasks.append(new_task)
    save_tasks(tasks)

    return new_task

def update_task(
    task_id,
    title=None,
    due_date=None,
    priority=None,
    status=None,
    estimated_minutes=None,
):
    """
    Update an existing task.

    Only provided fields are changed.
    """

    tasks = load_tasks()

    for task in tasks:
        if task["id"] != task_id:
            continue

        if title is not None:
            task["title"] = title

        if due_date is not None:
            task["due_date"] = due_date

        if priority is not None:
            task["priority"] = priority

        if status is not None:
            task["status"] = status

        if estimated_minutes is not None:
            task["estimated_minutes"] = estimated_minutes

        save_tasks(tasks)
        return task

    return None

def set_task_calendar_event(
    task_id,
    event_id,
    calendar_name=None,
):
    """
    Associate a task with a calendar event.
    """

    tasks = load_tasks()

    for task in tasks:
        if task["id"] != task_id:
            continue

        task["calendar_event_id"] = event_id
        task["calendar_name"] = calendar_name

        save_tasks(tasks)
        return task

    return None

def clear_task_calendar_event(task_id):
    """
    Remove the calendar event association from a task.
    """

    tasks = load_tasks()

    for task in tasks:
        if task["id"] != task_id:
            continue

        task["calendar_event_id"] = None
        task["calendar_name"] = None

        save_tasks(tasks)
        return task

    return None

def delete_task(task_id):
    """
    Delete a task by ID.
    """

    tasks = load_tasks()

    remaining_tasks = [
        task
        for task in tasks
        if task["id"] != task_id
    ]

    if len(remaining_tasks) == len(tasks):
        return None

    save_tasks(remaining_tasks)

    return {
        "id": task_id,
        "deleted": True,
    }

def complete_task(task_id):
    """
    Mark an existing task as complete.
    """

    return update_task(
        task_id=task_id,
        status="complete",
    )

