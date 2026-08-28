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
        max_work_minutes=None,
        deadline_events=None,
        reference_date=None,
    ):
        """
        Build a non-overlapping multi-task schedule.

        Uses the existing recommendation score for individual
        candidates, then evaluates combinations of candidates
        to choose a better overall daily arrangement.
        """

        eligible_tasks = [
            task
            for task in tasks
            if task.get("status") in {
                "incomplete",
                "in progress",
            }
            and task.get("estimated_minutes")
            and not task.get("calendar_event_id")
        ]

        if not eligible_tasks:
            return []

        ranked_tasks = self.urgency.rank_tasks(
            eligible_tasks,
            reference_date=reference_date,
            deadline_events=deadline_events,
        )

        schedule = []
        total_scheduled_minutes = 0

        # Keep track of already-occupied intervals.
        occupied = []

        # ------------------------------------------
        # Generate candidates for each task
        # ------------------------------------------

        task_candidates = {}

        for task in ranked_tasks:

            duration = timedelta(
                minutes=task["estimated_minutes"]
            )

            candidates = []

            # --------------------------------------
            # Determine preference
            # --------------------------------------

            preferred_evening = False
            preferred_morning = False

            if preference:
                preference_lower = preference.lower()

                preferred_evening = (
                    "difficult" in preference_lower
                    and "night" in preference_lower
                )

                preferred_morning = (
                    "morning" in preference_lower
                )

            is_highly_urgent = (
                task.get("urgency_score", 0) >= 100
            )

            # --------------------------------------
            # Generate candidate slots
            # --------------------------------------

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

                    start_hour = candidate_start.hour

                    # ----------------------------------
                    # Protect preferred evening window
                    # ----------------------------------

                    if preferred_evening:

                        # Highly urgent/difficult work
                        # belongs in the evening.
                        if (
                            is_highly_urgent
                            and start_hour < 18
                        ):
                            candidate_start += timedelta(
                                minutes=30
                            )
                            continue

                        # Don't let lower-urgency tasks
                        # consume the evening window.
                        if (
                            not is_highly_urgent
                            and start_hour >= 18
                        ):
                            candidate_start += timedelta(
                                minutes=30
                            )
                            continue

                    # ----------------------------------
                    # Score candidate
                    # ----------------------------------

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

                    # ----------------------------------
                    # Whole-day placement adjustment
                    # ----------------------------------

                    if preferred_evening:

                        if (
                            start_hour >= 18
                            and is_highly_urgent
                        ):
                            score += 15

                        elif (
                            start_hour >= 18
                            and not is_highly_urgent
                        ):
                            score -= 10

                    elif (
                        preferred_morning
                        and start_hour < 12
                    ):
                        if is_highly_urgent:
                            score += 15

                    # ----------------------------------
                    # Prefer earlier placement for
                    # extremely urgent tasks
                    # ----------------------------------

                    if is_highly_urgent:

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

                    candidates.append({
                        **candidate,
                        "score": score,
                        "score_breakdown": scoring[
                            "breakdown"
                        ],
                    })

                    candidate_start += timedelta(
                        minutes=30
                    )

            candidates.sort(
                key=lambda candidate: (
                    candidate["score"],
                    candidate["start"],
                ),
                reverse=True,
            )

            if candidates:
                task_candidates[task["id"]] = candidates

        if not task_candidates:
            return []

        # ------------------------------------------
        # Search for the best combination
        # ------------------------------------------

        best_schedule = []
        best_score = float("-inf")

        def search(
            index,
            current_schedule,
            occupied,
            total_minutes,
            total_score,
        ):
            nonlocal best_schedule
            nonlocal best_score

            # --------------------------------------
            # Update best solution
            # --------------------------------------

            if total_score > best_score:
                best_score = total_score
                best_schedule = list(
                    current_schedule
                )

            if index >= len(ranked_tasks):
                return

            task = ranked_tasks[index]
            task_id = task["id"]
            task_minutes = task[
                "estimated_minutes"
            ]

            candidates = task_candidates.get(
                task_id,
                [],
            )

            # --------------------------------------
            # Option 1: leave task unscheduled
            # --------------------------------------

            search(
                index + 1,
                current_schedule,
                occupied,
                total_minutes,
                total_score,
            )

            # --------------------------------------
            # Option 2: schedule task
            # --------------------------------------

            for candidate in candidates:

                if (
                    max_work_minutes is not None
                    and (
                        total_minutes
                        + task_minutes
                        > max_work_minutes
                    )
                ):
                    continue

                overlaps = False

                for busy_start, busy_end in occupied:

                    if (
                        candidate["start"] < busy_end
                        and candidate["end"] > busy_start
                    ):
                        overlaps = True
                        break

                if overlaps:
                    continue

                new_schedule = (
                    current_schedule
                    + [{
                        "task": task,
                        "candidate": candidate,
                    }]
                )

                new_occupied = (
                    occupied
                    + [
                        (
                            candidate["start"],
                            candidate["end"],
                        ),
                        (
                            candidate["end"],
                            candidate["end"]
                            + timedelta(
                                minutes=break_minutes
                            ),
                        ),
                    ]
                )

                # ----------------------------------
                # Urgency-aware ordering bonus
                # ----------------------------------

                ordering_bonus = 0

                if task.get(
                    "urgency_score",
                    0,
                ) >= 100:

                    hours_from_midnight = (
                        candidate["start"].hour
                        + (
                            candidate["start"].minute
                            / 60
                        )
                    )

                    ordering_bonus += max(
                        0,
                        23 - hours_from_midnight,
                    ) * 2

                search(
                    index + 1,
                    new_schedule,
                    new_occupied,
                    total_minutes + task_minutes,
                    total_score
                    + candidate["score"]
                    + ordering_bonus,
                )

        search(
            index=0,
            current_schedule=[],
            occupied=[],
            total_minutes=0,
            total_score=0,
        )

        # ------------------------------------------
        # Convert best solution to public format
        # ------------------------------------------

        schedule = []

        for item in best_schedule:

            task = item["task"]
            candidate = item["candidate"]

            schedule.append({
                "task": task,
                "start": candidate["start"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "end": candidate["end"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "duration_minutes": task[
                    "estimated_minutes"
                ],
                "score": candidate["score"],
                "score_breakdown": candidate[
                    "score_breakdown"
                ],
                "reasons": self._build_reasons(
                    task=task,
                    score_breakdown=candidate[
                        "score_breakdown"
                    ],
                    preference=preference,
                ),
            })

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

        deadline_event_score = score_breakdown.get(
            "deadline_event",
            0,
        )

        if deadline_event_score > 0:
            reasons.append(
                "A matching deadline was found in "
                "your exams/assign calendar."
            )

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