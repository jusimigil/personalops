from datetime import date, datetime


class UrgencyService:
    """
    Deterministically calculates how urgently a task
    should be considered for scheduling.
    """

    PRIORITY_WEIGHTS = {
        "low": 10,
        "medium": 30,
        "high": 50,
    }

    STATUS_WEIGHTS = {
        "incomplete": 0,
        "in progress": 10,
    }

    def calculate(self, task, reference_date=None):
        """
        Calculate an urgency score for a task.

        Higher score = more urgent.
        """

        if reference_date is None:
            reference_date = date.today()

        score = 0

        # ------------------------------------------
        # Priority
        # ------------------------------------------

        priority = task.get(
            "priority",
            "medium",
        ).lower()

        score += self.PRIORITY_WEIGHTS.get(
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

        score += self.STATUS_WEIGHTS.get(
            status,
            0,
        )

        # ------------------------------------------
        # Due date
        # ------------------------------------------

        due_date_string = task.get(
            "due_date"
        )

        if due_date_string:

            due_date = datetime.strptime(
                due_date_string,
                "%Y-%m-%d",
            ).date()

            days_remaining = (
                due_date - reference_date
            ).days

            if days_remaining < 0:
                # Overdue
                score += 50

            elif days_remaining == 0:
                # Due today
                score += 40

            elif days_remaining == 1:
                # Due tomorrow
                score += 30

            elif days_remaining <= 3:
                # Due within three days
                score += 20

            elif days_remaining <= 7:
                # Due within a week
                score += 10

        # ------------------------------------------
        # Estimated workload
        # ------------------------------------------

        estimated_minutes = task.get(
            "estimated_minutes"
        )

        if estimated_minutes:

            if estimated_minutes >= 240:
                score += 20

            elif estimated_minutes >= 180:
                score += 15

            elif estimated_minutes >= 120:
                score += 10

            elif estimated_minutes >= 60:
                score += 5

        return {
            "task_id": task.get("id"),
            "title": task.get("title"),
            "score": score,
        }

    def rank_tasks(self, tasks, reference_date=None):
        """
        Return tasks sorted from most urgent to least urgent.
        """

        ranked = []

        for task in tasks:
            urgency = self.calculate(
                task,
                reference_date=reference_date,
            )

            ranked.append({
                **task,
                "urgency_score": urgency["score"],
            })

        ranked.sort(
            key=lambda task: task["urgency_score"],
            reverse=True,
        )

        return ranked