from datetime import datetime, timedelta

from services.scheduling.urgency import UrgencyService
from services.scheduling.recommendation import RecommendationService

class PlanningService:
    """
    Builds a schedule for multiple tasks using
    urgency and available time.
    """

    def __init__(self):
        self.urgency = UrgencyService()
        self.recommendation = RecommendationService()

    def plan(
        self,
        tasks,
        free_blocks,
        break_minutes=30,
        preference=None,
    ):
        """
        Build a non-overlapping multi-task schedule.
        """

        eligible_tasks = [
            task
            for task in tasks
            if task.get("status") in {
                "incomplete",
                "in progress",
            }
            and task.get("estimated_minutes")
        ]

        if not eligible_tasks:
            return []

        ranked_tasks = self.urgency.rank_tasks(
            eligible_tasks
        )

        schedule = []

        # Keep track of already-occupied intervals.
        occupied = []

        for task in ranked_tasks:

            duration = timedelta(
                minutes=task["estimated_minutes"]
            )

            best_candidate = None
            best_score = float("-inf")
            best_breakdown = {}

            for block in free_blocks:

                block_start = datetime.fromisoformat(
                    block["start"]
                )

                block_end = datetime.fromisoformat(
                    block["end"]
                )

                candidate_start = block_start

                while (
                    candidate_start + duration
                    <= block_end
                ):

                    candidate_end = (
                        candidate_start + duration
                    )

                    # ----------------------------------
                    # Check for overlap
                    # ----------------------------------

                    overlaps = False

                    for busy_start, busy_end in occupied:

                        if (
                            candidate_start < busy_end
                            and candidate_end > busy_start
                        ):
                            overlaps = True
                            break

                    if overlaps:
                        candidate_start += timedelta(
                            minutes=30
                        )
                        continue

                    candidate = {
                        "start": candidate_start,
                        "end": candidate_end,
                        "duration_minutes": task[
                            "estimated_minutes"
                        ],
                    }

                    scoring = self.recommendation.score_candidate(
                        candidate=candidate,
                        task=task,
                        preference=preference,
                    )

                    score = scoring["score"]

                    # Slightly favor earlier placement for
                    # very urgent tasks.
                    if task["urgency_score"] >= 100:

                        hours_from_start = (
                            candidate_start
                            - datetime.fromisoformat(
                                free_blocks[0]["start"]
                            )
                        ).total_seconds() / 3600

                        score -= hours_from_start

                    # Avoid ending at or after midnight.
                    if candidate_end.hour == 0:
                        score -= 10

                    if score > best_score:

                        best_score = score
                        best_candidate = candidate
                        best_breakdown = scoring["breakdown"]

                    candidate_start += timedelta(
                        minutes=30
                    )

            if best_candidate is None:
                continue

            task_start = best_candidate["start"]
            task_end = best_candidate["end"]

            schedule.append({
                "task": task,
                "start": task_start.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "end": task_end.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "duration_minutes": task[
                    "estimated_minutes"
                ],
                "score": best_score,
                "score_breakdown": best_breakdown,
                "reasons": self._build_reasons(
                    task=task,
                    score_breakdown=best_breakdown,
                    preference=preference,
                ),
            })

            # Reserve the task itself.
            occupied.append(
                (task_start, task_end)
            )

            # Reserve the break immediately after it.
            occupied.append(
                (
                    task_end,
                    task_end + timedelta(
                        minutes=break_minutes
                    ),
                )
            )

        schedule.sort(
            key=lambda item: item["start"]
        )

        return schedule

    def _build_reasons(
        self,
        task,
        score_breakdown,
        preference=None,
    ):
        reasons = []

        if score_breakdown.get("preferred_time", 0) > 0:
            reasons.append(
                "Matches your preferred study time."
            )

        deadline_score = score_breakdown.get(
            "deadline_fit",
            0,
        )

        if deadline_score > 0:

            due_date = task.get("due_date")

            if due_date:
                reasons.append(
                    f"Deadline is {due_date}."
                )

        if score_breakdown.get("priority_fit", 0) > 0:
            reasons.append(
                f"The task is {task.get('priority', 'medium')} priority."
            )

        if score_breakdown.get("workload_fit", 0) > 0:
            reasons.append(
                "The session matches the estimated workload."
            )

        if score_breakdown.get("reasonable_hours", 0) > 0:
            reasons.append(
                "The session falls within your normal scheduling hours."
            )

        return reasons