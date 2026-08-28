from datetime import date, datetime

DEADLINE_CALENDAR = "exams/assign"


class UrgencyService:
    """
    Deterministically calculates how urgently a task
    should be considered for scheduling.
    """
    def __init__(self, calendar_service=None):
        self.calendar = calendar_service

    DEADLINE_EVENT_BONUS = 15

    PRIORITY_WEIGHTS = {
        "low": 10,
        "medium": 30,
        "high": 50,
    }

    STATUS_WEIGHTS = {
        "incomplete": 0,
        "in progress": 10,
    }

    def calculate(
        self,
        task,
        reference_date=None,
        effective_due_date=None,
    ):
        """
        Calculate an urgency score and its breakdown.
        """

        if reference_date is None:
            reference_date = date.today()

        priority_score = 0
        status_score = 0
        deadline_score = 0
        workload_score = 0

        # ------------------------------------------
        # Priority
        # ------------------------------------------

        priority = task.get(
            "priority",
            "medium",
        ).lower()

        priority_score = self.PRIORITY_WEIGHTS.get(
            priority,
            30,
        )

        # ------------------------------------------
        # Status
        # ------------------------------------------

        status = task.get(
            "status",
            "incomplete",
        ).lower()

        status_score = self.STATUS_WEIGHTS.get(
            status,
            0,
        )

        # ------------------------------------------
        # Due date
        # ------------------------------------------

        due_date = effective_due_date

        if due_date is None:

            due_date_string = task.get(
                "due_date"
            )

            if due_date_string:
                due_date = datetime.strptime(
                    due_date_string,
                    "%Y-%m-%d",
                ).date()

        if due_date:

            days_remaining = (
                due_date - reference_date
            ).days

            if days_remaining < 0:
                deadline_score = 50

            elif days_remaining == 0:
                deadline_score = 40

            elif days_remaining == 1:
                deadline_score = 30

            elif days_remaining <= 3:
                deadline_score = 20

            elif days_remaining <= 7:
                deadline_score = 10

        # ------------------------------------------
        # Workload
        # ------------------------------------------

        estimated_minutes = task.get(
            "estimated_minutes"
        )

        if estimated_minutes:

            if estimated_minutes >= 240:
                workload_score = 20

            elif estimated_minutes >= 180:
                workload_score = 15

            elif estimated_minutes >= 120:
                workload_score = 10

            elif estimated_minutes >= 60:
                workload_score = 5

        total_score = (
            priority_score
            + status_score
            + deadline_score
            + workload_score
        )

        return {
            "task_id": task.get("id"),
            "title": task.get("title"),
            "score": total_score,
            "breakdown": {
                "priority": priority_score,
                "status": status_score,
                "deadline": deadline_score,
                "workload": workload_score,
            },
        }

    def match_deadline_event(
        self,
        task,
        events,
    ):
        """
        Find an exams/assign event that appears to correspond
        to the task.

        Matching is intentionally conservative:
        - Exact normalized title match is accepted.
        - A known deadline suffix after the task title is accepted.
        - Arbitrary extra words are not enough for a match.
        """

        task_title = task.get("title")

        if not task_title:
            return None

        deadline_suffixes = {
            "deadline",
            "due",
            "due date",
            "assignment",
            "assignment due",
            "submission",
            "submission due",
            "submit",
            "exam",
            "test",
            "project",
            "requirement",
        }

        def normalize(text):
            return " ".join(
                text.lower()
                .replace("-", " ")
                .split()
            )

        normalized_task = normalize(task_title)

        for event in events:

            event_title = normalize(
                event.get("title", "")
            )

            # --------------------------------------
            # Exact match
            # --------------------------------------

            if event_title == normalized_task:
                return event

            # --------------------------------------
            # Task title + recognized deadline suffix
            # --------------------------------------

            for suffix in deadline_suffixes:

                expected_title = (
                    f"{normalized_task} {suffix}"
                )

                if event_title == expected_title:
                    return event

        return None

    def calculate_deadline_event_bonus(
        self,
        event,
        reference_date=None,
    ):
        """
        Calculate urgency bonus based on the deadline
        date represented by an exams/assign event.
        """

        if event is None:
            return 0

        if reference_date is None:
            reference_date = date.today()

        event_start = datetime.fromisoformat(
            event["start"]
        )

        deadline_date = event_start.date()

        days_remaining = (
            deadline_date - reference_date
        ).days

        if days_remaining < 0:
            return 25

        if days_remaining == 0:
            return 25

        if days_remaining == 1:
            return 20

        if days_remaining <= 3:
            return 15

        if days_remaining <= 7:
            return 10

        return 5

    def get_effective_due_date(
        self,
        task,
        deadline_event=None,
    ):
        """
        Return the task's explicit due date when available.
        Otherwise use the matching exams/assign deadline date.
        """

        task_due_date = task.get("due_date")

        if task_due_date:
            return datetime.strptime(
                task_due_date,
                "%Y-%m-%d",
            ).date()

        if deadline_event:
            event_start = datetime.fromisoformat(
                deadline_event["start"]
            )

            return event_start.date()

        return None

    def rank_tasks(
        self,
        tasks,
        reference_date=None,
        deadline_events=None,
    ):
        """
        Return tasks sorted from most urgent to least urgent.
        """

        ranked = []

        for task in tasks:

            deadline_event = None

            # ------------------------------------------
            # Match exams/assign deadline event
            # ------------------------------------------

            if deadline_events:
                deadline_event = self.match_deadline_event(
                    task=task,
                    events=deadline_events,
                )

            # ------------------------------------------
            # Determine effective due date
            # ------------------------------------------

            effective_due_date = self.get_effective_due_date(
                task=task,
                deadline_event=deadline_event,
            )

            # ------------------------------------------
            # Calculate base urgency
            # ------------------------------------------

            urgency = self.calculate(
                task,
                reference_date=reference_date,
                effective_due_date=effective_due_date,
            )

            # ------------------------------------------
            # Calculate deadline-event bonus
            # ------------------------------------------

            deadline_event_score = 0

            if deadline_event is not None:
                deadline_event_score = (
                    self.calculate_deadline_event_bonus(
                        event=deadline_event,
                        reference_date=reference_date,
                    )
                )

            # ------------------------------------------
            # Store ranked task
            # ------------------------------------------

            ranked.append({
                **task,
                "urgency_score": (
                    urgency["score"]
                    + deadline_event_score
                ),
                "urgency_breakdown": {
                    **urgency["breakdown"],
                    "deadline_event": deadline_event_score,
                },
                "deadline_event": deadline_event,
                "effective_due_date": (
                    effective_due_date.isoformat()
                    if effective_due_date
                    else None
                ),
            })

        ranked.sort(
            key=lambda task: task["urgency_score"],
            reverse=True,
        )

        return ranked

