import json

from pathlib import Path


# Find the project root
BASE_DIR = Path(__file__).resolve().parents[2]

# Location of our course database
COURSES_FILE = BASE_DIR / "data" / "courses.json"


def load_courses():
    """Load courses from the local JSON database."""

    if not COURSES_FILE.exists():
        return []

    with open(
        COURSES_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_courses(courses):
    """Save courses to the local JSON database."""

    COURSES_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        COURSES_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            courses,
            file,
            indent=2,
        )


def get_courses():
    """Return all courses."""

    return load_courses()

def get_course_tasks(course_id):
    """
    Return all tasks associated with a course.
    """

    from tools.tasks import get_tasks

    return [
        task
        for task in get_tasks()
        if task.get("course_id") == course_id
    ]

def get_course_overview(course_id):
    """
    Return a summary of a course, including its assignments
    and associated tasks.
    """

    courses = load_courses()

    course = next(
        (
            course
            for course in courses
            if course["id"] == course_id
        ),
        None,
    )

    if course is None:
        raise ValueError(
            f"Course {course_id} does not exist."
        )

    from tools.assignments import get_assignments
    from tools.tasks import get_tasks

    assignments = [
        assignment
        for assignment in get_assignments()
        if assignment["course_id"] == course_id
    ]

    tasks = [
        task
        for task in get_tasks()
        if task.get("course_id") == course_id
    ]

    incomplete_tasks = [
        task
        for task in tasks
        if task.get("status") != "complete"
    ]

    completed_tasks = [
        task
        for task in tasks
        if task.get("status") == "complete"
    ]

    return {
        "course": course,
        "assignments": assignments,
        "tasks": tasks,
        "total_assignments": len(assignments),
        "total_tasks": len(tasks),
        "incomplete_tasks": len(incomplete_tasks),
        "completed_tasks": len(completed_tasks),
    }

def create_course(
    code,
    name,
    term,
):
    """
    Create a new course.
    """

    courses = load_courses()

    if courses:
        new_id = max(
            course["id"]
            for course in courses
        ) + 1
    else:
        new_id = 1

    new_course = {
        "id": new_id,
        "code": code,
        "name": name,
        "term": term,
    }

    courses.append(new_course)

    save_courses(courses)

    return new_course


def update_course(
    course_id,
    code=None,
    name=None,
    term=None,
):
    """
    Update an existing course.

    Only provided fields are changed.
    """

    courses = load_courses()

    for course in courses:

        if course["id"] != course_id:
            continue

        if code is not None:
            course["code"] = code

        if name is not None:
            course["name"] = name

        if term is not None:
            course["term"] = term

        save_courses(courses)

        return course

    return None


def delete_course(course_id):
    """
    Delete a course by ID.
    """

    courses = load_courses()

    remaining_courses = [
        course
        for course in courses
        if course["id"] != course_id
    ]

    if len(remaining_courses) == len(courses):
        return None

    save_courses(remaining_courses)

    return {
        "id": course_id,
        "deleted": True,
    }