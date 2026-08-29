import json

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

EXAMS_FILE = BASE_DIR / "data" / "exams.json"


def load_exams():
    """Load exams from the local JSON database."""

    if not EXAMS_FILE.exists():
        return []

    with open(
        EXAMS_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_exams(exams):
    """Save exams to the local JSON database."""

    EXAMS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        EXAMS_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            exams,
            file,
            indent=2,
        )


def get_exams():
    """Return all exams."""

    return load_exams()


def create_exam(
    course_id,
    title,
    exam_date,
    coverage=None,
    status="upcoming",
):
    """
    Create an exam for an existing course.
    """

    from tools.courses import get_courses

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

    exams = load_exams()

    if exams:
        new_id = max(
            exam["id"]
            for exam in exams
        ) + 1
    else:
        new_id = 1

    new_exam = {
        "id": new_id,
        "course_id": course_id,
        "title": title,
        "exam_date": exam_date,
        "coverage": coverage,
        "status": status,
    }

    exams.append(new_exam)

    save_exams(exams)

    return new_exam


def update_exam(
    exam_id,
    course_id=None,
    title=None,
    exam_date=None,
    coverage=None,
    status=None,
):
    """
    Update an existing exam.

    Only provided fields are changed.
    """

    exams = load_exams()

    for exam in exams:

        if exam["id"] != exam_id:
            continue

        if course_id is not None:

            from tools.courses import get_courses

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

            exam["course_id"] = course_id

        if title is not None:
            exam["title"] = title

        if exam_date is not None:
            exam["exam_date"] = exam_date

        if coverage is not None:
            exam["coverage"] = coverage

        if status is not None:
            exam["status"] = status

        save_exams(exams)

        return exam

    return None


def delete_exam(exam_id):
    """
    Delete an exam by ID.
    """

    exams = load_exams()

    remaining_exams = [
        exam
        for exam in exams
        if exam["id"] != exam_id
    ]

    if len(remaining_exams) == len(exams):
        return None

    save_exams(remaining_exams)

    return {
        "id": exam_id,
        "deleted": True,
    }


def get_course_exams(course_id):
    """
    Return all exams associated with a course.
    """

    from tools.courses import get_courses

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

    return [
        exam
        for exam in load_exams()
        if exam["course_id"] == course_id
    ]