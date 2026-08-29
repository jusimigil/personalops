import json

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

EXAM_TOPICS_FILE = (
    BASE_DIR / "data" / "exam_topics.json"
)


def load_exam_topics():
    """Load exam topics from the local JSON database."""

    if not EXAM_TOPICS_FILE.exists():
        return []

    with open(
        EXAM_TOPICS_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def save_exam_topics(topics):
    """Save exam topics to the local JSON database."""

    EXAM_TOPICS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        EXAM_TOPICS_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            topics,
            file,
            indent=2,
        )


def get_exam_topics(exam_id=None):
    """
    Return exam topics.

    When exam_id is provided, return only topics
    associated with that exam.
    """

    topics = load_exam_topics()

    if exam_id is None:
        return topics

    return [
        topic
        for topic in topics
        if topic["exam_id"] == exam_id
    ]


def create_exam_topic(
    exam_id,
    name,
    estimated_minutes,
    importance="medium",
    confidence="medium",
):
    """
    Create a topic for an existing exam.
    """

    from tools.exams import get_exams

    valid_levels = {
        "low",
        "medium",
        "high",
    }

    if importance not in valid_levels:
        raise ValueError(
            "importance must be low, medium, or high."
        )

    if confidence not in valid_levels:
        raise ValueError(
            "confidence must be low, medium, or high."
        )

    exam = next(
        (
            exam
            for exam in get_exams()
            if exam["id"] == exam_id
        ),
        None,
    )

    if exam is None:
        raise ValueError(
            f"Exam {exam_id} does not exist."
        )

    if estimated_minutes <= 0:
        raise ValueError(
            "estimated_minutes must be greater than 0."
        )

    topics = load_exam_topics()

    if topics:
        new_id = max(
            topic["id"]
            for topic in topics
        ) + 1
    else:
        new_id = 1

    new_topic = {
        "id": new_id,
        "exam_id": exam_id,
        "name": name,
        "estimated_minutes": estimated_minutes,
        "importance": importance,
        "confidence": confidence,
    }

    topics.append(new_topic)

    save_exam_topics(topics)

    return new_topic


def update_exam_topic(
    topic_id,
    name=None,
    estimated_minutes=None,
    importance=None,
    confidence=None,
):
    """
    Update an existing exam topic.
    """

    topics = load_exam_topics()

    for topic in topics:

        if topic["id"] != topic_id:
            continue

        if name is not None:
            topic["name"] = name

        if estimated_minutes is not None:

            if estimated_minutes <= 0:
                raise ValueError(
                    "estimated_minutes must be greater than 0."
                )

            topic["estimated_minutes"] = (
                estimated_minutes
            )

        valid_levels = {
            "low",
            "medium",
            "high",
        }

        if importance is not None:

            if importance not in valid_levels:
                raise ValueError(
                    "importance must be low, medium, or high."
                )

            topic["importance"] = importance

        if confidence is not None:

            if confidence not in valid_levels:
                raise ValueError(
                    "confidence must be low, medium, or high."
                )

            topic["confidence"] = confidence

        save_exam_topics(topics)

        return topic

    return None


def delete_exam_topic(topic_id):
    """
    Delete an exam topic by ID.
    """

    topics = load_exam_topics()

    remaining_topics = [
        topic
        for topic in topics
        if topic["id"] != topic_id
    ]

    if len(remaining_topics) == len(topics):
        return None

    save_exam_topics(remaining_topics)

    return {
        "id": topic_id,
        "deleted": True,
    }

def calculate_topic_priority(
    topic,
    days_remaining,
):
    """
    Calculate a deterministic study priority score
    for an exam topic.
    """

    importance_scores = {
        "low": 10,
        "medium": 20,
        "high": 30,
    }

    confidence_scores = {
        "high": 0,
        "medium": 10,
        "low": 20,
    }

    importance_score = importance_scores.get(
        topic.get("importance", "medium"),
        20,
    )

    confidence_score = confidence_scores.get(
        topic.get("confidence", "medium"),
        10,
    )

    if days_remaining <= 0:
        proximity_score = 30
    elif days_remaining == 1:
        proximity_score = 25
    elif days_remaining <= 3:
        proximity_score = 20
    elif days_remaining <= 7:
        proximity_score = 15
    elif days_remaining <= 14:
        proximity_score = 10
    else:
        proximity_score = 5

    estimated_minutes = (
        topic.get("estimated_minutes") or 0
    )

    if estimated_minutes >= 180:
        workload_score = 15
    elif estimated_minutes >= 120:
        workload_score = 10
    elif estimated_minutes >= 60:
        workload_score = 5
    else:
        workload_score = 0

    total_score = (
        importance_score
        + confidence_score
        + proximity_score
        + workload_score
    )

    return {
        "topic_id": topic.get("id"),
        "name": topic.get("name"),
        "score": total_score,
        "breakdown": {
            "importance": importance_score,
            "confidence": confidence_score,
            "proximity": proximity_score,
            "workload": workload_score,
        },
    }

def rank_exam_topics(
    exam_id,
    days_remaining,
):
    """
    Return exam topics ranked from highest to lowest
    study priority.
    """

    topics = get_exam_topics(exam_id)

    ranked = []

    for topic in topics:

        priority = calculate_topic_priority(
            topic=topic,
            days_remaining=days_remaining,
        )

        ranked.append({
            **topic,
            "priority_score": priority["score"],
            "priority_breakdown": priority["breakdown"],
        })

    ranked.sort(
        key=lambda topic: topic["priority_score"],
        reverse=True,
    )

    return ranked
