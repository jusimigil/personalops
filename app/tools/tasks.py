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

def create_task(title, due_date=None, priority="medium"):
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
    }

    tasks.append(new_task)
    save_tasks(tasks)

    return new_task