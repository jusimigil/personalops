import json

from pathlib import Path
from tools.courses import get_courses

BASE_DIR = Path(__file__).resolve().parents[2]

ASSIGNMENTS_FILE = (
    BASE_DIR / "data" / "assignments.json"
)

def load_assignments():
    """Load assignments from the local JSON database."""

    if not ASSIGNMENTS_FILE.exists():
        return []

    with open(
        ASSIGNMENTS_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_assignments(assignments):
    """Save assignments to the local JSON database."""

    ASSIGNMENTS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        ASSIGNMENTS_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            assignments,
            file,
            indent=2,
        )

def get_assignment_tasks(assignment_id):
    """
    Return all tasks associated with an assignment.
    """

    from tools.tasks import get_tasks

    return [
        task
        for task in get_tasks()
        if task.get("assignment_id") == assignment_id
    ]

def get_assignment_progress(assignment_id):
    """
    Return progress information for an assignment.
    """

    assignments = load_assignments()

    assignment = next(
        (
            assignment
            for assignment in assignments
            if assignment["id"] == assignment_id
        ),
        None,
    )

    if assignment is None:
        raise ValueError(
            f"Assignment {assignment_id} does not exist."
        )

    from tools.tasks import get_tasks

    tasks = [
        task
        for task in get_tasks()
        if task.get("assignment_id") == assignment_id
    ]

    total_task_minutes = sum(
        task.get("estimated_minutes") or 0
        for task in tasks
    )

    completed_tasks = [
        task
        for task in tasks
        if task.get("status") == "complete"
    ]

    remaining_task_minutes = sum(
        task.get("estimated_minutes") or 0
        for task in tasks
        if task.get("status") != "complete"
    )

    assignment_estimated_minutes = (
        assignment.get("estimated_minutes") or 0
    )

    completed_task_minutes = sum(
        task.get("estimated_minutes") or 0
        for task in tasks
        if task.get("status") == "complete"
    )

    if assignment_estimated_minutes > 0:
        completion_percentage = min(
            100,
            max(
                0,
                (
                    completed_task_minutes
                    / assignment_estimated_minutes
                )
                * 100,
            ),
        )
    elif tasks:
        completion_percentage = (
            len(completed_tasks)
            / len(tasks)
        ) * 100
    else:
        completion_percentage = 0

    return {
        "assignment_id": assignment_id,
        "assignment_estimated_minutes": (
            assignment_estimated_minutes
        ),
        "task_estimated_minutes": total_task_minutes,
        "remaining_estimated_minutes": (
            remaining_task_minutes
        ),
        "completed_tasks": len(completed_tasks),
        "total_tasks": len(tasks),
        "completion_percentage": (
            round(completion_percentage, 1)
        ),
        "completed_task_minutes": completed_task_minutes,
    }

def get_assignments():
    """Return all assignments."""

    return load_assignments()


def create_assignment(
    course_id,
    title,
    due_date=None,
    estimated_minutes=None,
    status="incomplete",
):
    """
    Create a new assignment.
    """

    course = next(
        (
            course
            for course in get_courses()
            if course["id"] == course_id
        ),
        None,
    )

    if course is None:
        raise ValueError(
            f"Course {course_id} does not exist."
        )

    assignments = load_assignments()

    if assignments:
        new_id = max(
            assignment["id"]
            for assignment in assignments
        ) + 1
    else:
        new_id = 1

    new_assignment = {
        "id": new_id,
        "course_id": course_id,
        "title": title,
        "due_date": due_date,
        "estimated_minutes": estimated_minutes,
        "status": status,
    }

    assignments.append(new_assignment)

    save_assignments(assignments)

    return new_assignment


def update_assignment(
    assignment_id,
    course_id=None,
    title=None,
    due_date=None,
    estimated_minutes=None,
    status=None,
):
    """
    Update an existing assignment.

    Only provided fields are changed.
    """

    assignments = load_assignments()

    for assignment in assignments:

        if assignment["id"] != assignment_id:
            continue

        if course_id is not None:

            course = next(
                (
                    course
                    for course in get_courses()
                    if course["id"] == course_id
                ),
                None,
            )

            if course is None:
                raise ValueError(
                    f"Course {course_id} does not exist."
                )

            assignment["course_id"] = course_id

        if title is not None:
            assignment["title"] = title

        if due_date is not None:
            assignment["due_date"] = due_date

        if estimated_minutes is not None:
            assignment["estimated_minutes"] = (
                estimated_minutes
            )

        if status is not None:
            assignment["status"] = status

        save_assignments(assignments)

        return assignment

    return None


def delete_assignment(assignment_id):
    """
    Delete an assignment by ID.
    """

    assignments = load_assignments()

    remaining_assignments = [
        assignment
        for assignment in assignments
        if assignment["id"] != assignment_id
    ]

    if len(remaining_assignments) == len(assignments):
        return None

    save_assignments(remaining_assignments)

    return {
        "id": assignment_id,
        "deleted": True,
    }

def create_assignment_task(
    assignment_id,
    title=None,
    priority="medium",
    estimated_minutes=None,
    due_date=None,
):
    """
    Create a task associated with an existing assignment.

    The task inherits the assignment's course.
    The assignment remains the source of the academic deadline
    unless an explicit task due date is supplied.
    """

    assignments = load_assignments()

    assignment = next(
        (
            assignment
            for assignment in assignments
            if assignment["id"] == assignment_id
        ),
        None,
    )

    if assignment is None:
        raise ValueError(
            f"Assignment {assignment_id} does not exist."
        )

    from tools.tasks import create_task

    task_title = title or assignment["title"]

    task_due_date = (
        due_date
        if due_date is not None
        else assignment.get("due_date")
    )

    return create_task(
        title=task_title,
        due_date=task_due_date,
        priority=priority,
        estimated_minutes=estimated_minutes,
        assignment_id=assignment_id,
    )

def get_upcoming_assignments(
    start_date,
    end_date,
):
    """
    Return assignments and their associated tasks
    whose effective deadlines fall within a date range.
    """

    assignments = load_assignments()

    from tools.tasks import get_tasks

    tasks = get_tasks()

    results = []

    for assignment in assignments:

        due_date = assignment.get("due_date")

        if not due_date:
            continue

        if due_date < start_date or due_date > end_date:
            continue

        assignment_tasks = [
            task
            for task in tasks
            if task.get("assignment_id")
            == assignment["id"]
        ]

        results.append({
            "assignment": assignment,
            "tasks": assignment_tasks,
        })

    results.sort(
        key=lambda item: item["assignment"]["due_date"]
    )

    return results

def get_academic_workload(
    start_date,
    end_date,
):
    """
    Calculate academic workload for assignments and
    standalone tasks within a date range.

    Assignment workload is counted once using the
    assignment's estimated_minutes.

    Tasks associated with assignments are used for
    progress tracking but are not added again to the
    overall academic workload.

    Standalone tasks are counted independently.
    """

    assignments = load_assignments()

    from tools.tasks import get_tasks
    from tools.courses import get_courses

    tasks = get_tasks()
    courses = get_courses()

    workload = []

    total_assignment_minutes = 0
    total_task_minutes = 0
    total_completed_task_minutes = 0
    total_remaining_task_minutes = 0
    standalone_task_minutes = 0
    standalone_completed_task_minutes = 0
    standalone_remaining_task_minutes = 0

    # ------------------------------------------
    # Assignment workload
    # ------------------------------------------

    for assignment in assignments:

        due_date = assignment.get("due_date")

        if not due_date:
            continue

        if due_date < start_date or due_date > end_date:
            continue

        course = next(
            (
                course
                for course in courses
                if course["id"] == assignment["course_id"]
            ),
            None,
        )

        assignment_tasks = [
            task
            for task in tasks
            if task.get("assignment_id")
            == assignment["id"]
        ]

        assignment_task_minutes = sum(
            task.get("estimated_minutes") or 0
            for task in assignment_tasks
        )

        completed_task_minutes = sum(
            task.get("estimated_minutes") or 0
            for task in assignment_tasks
            if task.get("status") == "complete"
        )

        remaining_task_minutes = sum(
            task.get("estimated_minutes") or 0
            for task in assignment_tasks
            if task.get("status") != "complete"
        )

        assignment_estimated_minutes = (
            assignment.get("estimated_minutes") or 0
        )

        total_assignment_minutes += (
            assignment_estimated_minutes
        )

        total_task_minutes += (
            assignment_task_minutes
        )

        total_completed_task_minutes += (
            completed_task_minutes
        )

        total_remaining_task_minutes += (
            remaining_task_minutes
        )

        workload.append({
            "type": "assignment",
            "assignment": assignment,
            "course": course,
            "task_estimated_minutes": (
                assignment_task_minutes
            ),
            "completed_task_minutes": (
                completed_task_minutes
            ),
            "remaining_task_minutes": (
                remaining_task_minutes
            ),
        })

    # ------------------------------------------
    # Standalone task workload
    # ------------------------------------------

    for task in tasks:

        if task.get("assignment_id"):
            continue

        if task.get("course_id") is None:
            continue

        due_date = task.get("due_date")

        if not due_date:
            continue

        if due_date < start_date or due_date > end_date:
            continue

        if task.get("status") not in {
            "incomplete",
            "in progress",
        }:
            continue

        estimated_minutes = (
            task.get("estimated_minutes") or 0
        )

        if estimated_minutes <= 0:
            continue

        standalone_task_minutes += (
            estimated_minutes
        )

        standalone_remaining_task_minutes += (
            estimated_minutes
        )

        course = None

        if task.get("course_id") is not None:
            course = next(
                (
                    course
                    for course in courses
                    if course["id"] == task["course_id"]
                ),
                None,
            )

        workload.append({
            "type": "standalone_task",
            "task": task,
            "course": course,
            "task_estimated_minutes": (
                estimated_minutes
            ),
            "completed_task_minutes": 0,
            "remaining_task_minutes": (
                estimated_minutes
            ),
        })

    # ------------------------------------------
    # Totals
    # ------------------------------------------

    total_academic_minutes = (
        total_assignment_minutes
        + standalone_task_minutes
    )

    total_remaining_academic_minutes = (
        total_remaining_task_minutes
        + standalone_remaining_task_minutes
    )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "assignments": [
            item
            for item in workload
            if item["type"] == "assignment"
        ],
        "standalone_tasks": [
            item
            for item in workload
            if item["type"] == "standalone_task"
        ],
        "total_assignments": len([
            item
            for item in workload
            if item["type"] == "assignment"
        ]),
        "total_academic_minutes": (
            total_academic_minutes
        ),
        "total_assignment_minutes": (
            total_assignment_minutes
        ),
        "total_standalone_task_minutes": (
            standalone_task_minutes
        ),
        "total_task_minutes": (
            total_task_minutes
        ),
        "total_completed_task_minutes": (
            total_completed_task_minutes
            + standalone_completed_task_minutes
        ),
        "total_remaining_task_minutes": (
            total_remaining_academic_minutes
        ),
    }