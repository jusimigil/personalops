from datetime import date, timedelta

from services.academics.study_config import (
    MAX_DAILY_STUDY_MINUTES,
    MAX_TOPIC_SESSION_MINUTES,
    PREFERRED_SESSION_MINUTES,
    MIN_SESSION_MINUTES,
)

from tools.exams import get_exams
from tools.exam_topics import rank_exam_topics

def get_session_objective(topic, phase):
    """
    Return a practical objective for a study session.
    """

    if phase == "learn":
        return (
            f"Build a solid understanding of {topic} "
            "and work through representative examples."
        )

    if phase == "practice":
        return (
            f"Practice {topic} by solving representative "
            "problems with minimal help from notes."
        )

    if phase == "final_review":
        return (
            "Recall the key concepts across all exam topics "
            "without relying on notes."
        )

    return None


def generate_study_plan(
    exam_id,
    reference_date=None,
):
    """
    Generate a deterministic study plan for an exam.

    The plan has three stages:

    1. Coverage:
       Initial learning for every topic.

    2. Reinforcement:
       Practice for topics that need additional attention.

    3. Consolidation:
       Active recall / mixed review near the exam.
    """

    if reference_date is None:
        reference_date = date.today()

    exams = get_exams()

    exam = next(
        (
            exam
            for exam in exams
            if exam["id"] == exam_id
        ),
        None,
    )

    if exam is None:
        raise ValueError(
            f"Exam {exam_id} does not exist."
        )

    exam_date = date.fromisoformat(
        exam["exam_date"]
    )

    days_remaining = (
        exam_date - reference_date
    ).days

    if days_remaining < 0:
        raise ValueError(
            "Cannot generate a study plan for an exam "
            "that has already occurred."
        )

    topics = rank_exam_topics(
        exam_id=exam_id,
        days_remaining=days_remaining,
    )

    if not topics:
        raise ValueError(
            f"Exam {exam_id} has no study topics."
        )

    total_study_minutes = sum(
        topic["estimated_minutes"]
        for topic in topics
    )

    # ------------------------------------------
    # Available study days
    # ------------------------------------------

    available_days = []

    current_date = reference_date

    while current_date < exam_date:
        available_days.append(current_date)
        current_date += timedelta(days=1)

    if not available_days:
        available_days = [reference_date]

    # ------------------------------------------
    # Reserve final day before exam for review
    # ------------------------------------------

    if len(available_days) >= 2:
        review_date = available_days[-1]
        learning_days = available_days[:-1]
    else:
        review_date = available_days[0]
        learning_days = available_days

    sessions = []

    # Track how much topic time remains.
    remaining_topic_minutes = {
        topic["id"]: topic["estimated_minutes"]
        for topic in topics
    }

    # ------------------------------------------
    # Stage 1: Coverage / Learn
    # ------------------------------------------

    day_index = 0

    for topic in topics:

        topic_id = topic["id"]

        remaining = remaining_topic_minutes[
            topic_id
        ]

        if remaining <= 0:
            continue

        if not learning_days:
            break

        study_date = learning_days[
            day_index % len(learning_days)
        ]

        # Keep the first exposure reasonably substantial.
        session_minutes = min(
            PREFERRED_SESSION_MINUTES,
            MAX_TOPIC_SESSION_MINUTES,
            remaining,
        )

        if session_minutes < MIN_SESSION_MINUTES:
            session_minutes = remaining

        sessions.append({
            "date": study_date.isoformat(),
            "topic_id": topic_id,
            "topic": topic["name"],
            "duration_minutes": session_minutes,
            "priority_score": topic["priority_score"],
            "phase": "learn",
            "objective": get_session_objective(
                topic["name"],
                "learn",
            ),
        })

        remaining_topic_minutes[
            topic_id
        ] -= session_minutes

        day_index += 1

    # ------------------------------------------
    # Stage 2: Reinforcement / Practice
    # ------------------------------------------

    day_minutes = {
        study_date: 0
        for study_date in available_days
    }

    for session in sessions:

        session_date = date.fromisoformat(
            session["date"]
        )

        day_minutes[session_date] += (
            session["duration_minutes"]
        )

    # Practice highest-priority topics first.
    practice_topics = sorted(
        topics,
        key=lambda topic: topic["priority_score"],
        reverse=True,
    )

    for topic in practice_topics:

        topic_id = topic["id"]

        remaining = remaining_topic_minutes[
            topic_id
        ]

        if remaining <= 0:
            continue

        candidate_days = [
            study_date
            for study_date in learning_days
            if (
                day_minutes[study_date]
                < MAX_DAILY_STUDY_MINUTES
            )
        ]

        candidate_days.sort(
            key=lambda study_date: day_minutes[
                study_date
            ]
        )

        while (
            remaining > 0
            and candidate_days
        ):

            selected_day = candidate_days[0]

            available_today = (
                MAX_DAILY_STUDY_MINUTES
                - day_minutes[selected_day]
            )

            session_minutes = min(
                PREFERRED_SESSION_MINUTES,
                MAX_TOPIC_SESSION_MINUTES,
                remaining,
                available_today,
            )

            if session_minutes < MIN_SESSION_MINUTES:
                break

            sessions.append({
                "date": selected_day.isoformat(),
                "topic_id": topic_id,
                "topic": topic["name"],
                "duration_minutes": session_minutes,
                "priority_score": topic["priority_score"],
                "phase": "practice",
                "objective": get_session_objective(
                    topic["name"],
                    "practice",
                ),
            })

            remaining_topic_minutes[
                topic_id
            ] -= session_minutes

            remaining -= session_minutes

            day_minutes[selected_day] += (
                session_minutes
            )

            candidate_days = [
                study_date
                for study_date in candidate_days
                if (
                    day_minutes[study_date]
                    < MAX_DAILY_STUDY_MINUTES
                )
            ]

            candidate_days.sort(
                key=lambda study_date: day_minutes[
                    study_date
                ]
            )

    # ------------------------------------------
    # Stage 3: Final consolidation
    # ------------------------------------------

    if review_date:

        available_review_minutes = (
            MAX_DAILY_STUDY_MINUTES
            - day_minutes[review_date]
        )

        if available_review_minutes >= MIN_SESSION_MINUTES:

            # Use remaining review capacity for
            # the highest-priority unresolved topic.
            unresolved_topics = [
                topic
                for topic in topics
                if remaining_topic_minutes[
                    topic["id"]
                ] > 0
            ]

            unresolved_topics.sort(
                key=lambda topic: topic["priority_score"],
                reverse=True,
            )

            review_minutes = min(
                30,
                available_review_minutes,
            )

            if review_minutes >= MIN_SESSION_MINUTES:

                if unresolved_topics:

                    topic = unresolved_topics[0]

                    sessions.append({
                        "date": review_date.isoformat(),
                        "topic_id": topic["id"],
                        "topic": topic["name"],
                        "duration_minutes": review_minutes,
                        "priority_score": topic[
                            "priority_score"
                        ],
                        "phase": "final_review",
                        "objective": get_session_objective(
                            "Mixed Review",
                            "final_review",
                        ),
                    })

                    remaining_topic_minutes[
                        topic["id"]
                    ] -= min(
                        review_minutes,
                        remaining_topic_minutes[
                            topic["id"]
                        ],
                    )

                else:

                    sessions.append({
                        "date": review_date.isoformat(),
                        "topic_id": None,
                        "topic": "Mixed Review",
                        "duration_minutes": review_minutes,
                        "priority_score": 0,
                        "phase": "final_review",
                        "objective": get_session_objective(
                            "Mixed Review",
                            "final_review",
                        ),
                    })

                day_minutes[review_date] += (
                    review_minutes
                )

    # ------------------------------------------
    # Results
    # ------------------------------------------

    unscheduled_minutes = sum(
        remaining_topic_minutes.values()
    )

    sessions.sort(
        key=lambda session: (
            session["date"],
            -session["priority_score"],
        )
    )

    return {
        "exam": exam,
        "reference_date": (
            reference_date.isoformat()
        ),
        "exam_date": exam_date.isoformat(),
        "days_remaining": days_remaining,
        "total_study_minutes": total_study_minutes,
        "scheduled_study_minutes": (
            total_study_minutes
            - unscheduled_minutes
        ),
        "unscheduled_study_minutes": (
            unscheduled_minutes
        ),
        "sessions": sessions,
    }