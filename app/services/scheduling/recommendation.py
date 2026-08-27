from datetime import datetime, timedelta


class RecommendationService:
    """
    Scores scheduling candidates based on task context
    and user preferences.
    """

    def score_candidate(
        self,
        candidate,
        task,
        preference=None,
    ):
        preferred_time_score = 0
        deadline_fit_score = 0
        priority_fit_score = 0
        workload_fit_score = 0
        reasonable_hours_score = 0

        start = candidate["start"]

        # ------------------------------------------
        # Preferred time
        # ------------------------------------------

        if preference:

            preference_lower = preference.lower()

            if (
                "difficult" in preference_lower
                and "night" in preference_lower
            ):
                if start.hour >= 18:
                    preferred_time_score = 40

            elif (
                "morning" in preference_lower
                and start.hour < 12
            ):
                preferred_time_score = 40

        # ------------------------------------------
        # Task priority
        # ------------------------------------------

        priority = task.get(
            "priority",
            "medium",
        ).lower()

        if priority == "high":
            priority_fit_score = 10

        elif priority == "medium":
            priority_fit_score = 5

        # ------------------------------------------
        # Deadline fit
        # ------------------------------------------

        due_date = task.get("due_date")

        if due_date:

            due = datetime.strptime(
                due_date,
                "%Y-%m-%d",
            ).date()

            days_remaining = (
                due - start.date()
            ).days

            if days_remaining < 0:
                deadline_fit_score = 20

            elif days_remaining == 0:
                deadline_fit_score = 15

            elif days_remaining == 1:
                deadline_fit_score = 10

            elif days_remaining <= 3:
                deadline_fit_score = 5

        # ------------------------------------------
        # Workload fit
        # ------------------------------------------

        estimated_minutes = task.get(
            "estimated_minutes"
        )

        if estimated_minutes:

            candidate_duration = candidate[
                "duration_minutes"
            ]

            if candidate_duration == estimated_minutes:
                workload_fit_score = 10

        # ------------------------------------------
        # Reasonable time of day
        # ------------------------------------------

        if 7 <= start.hour < 23:
            reasonable_hours_score = 5

        total_score = (
            preferred_time_score
            + deadline_fit_score
            + priority_fit_score
            + workload_fit_score
            + reasonable_hours_score
        )

        return {
            "score": total_score,
            "breakdown": {
                "preferred_time": preferred_time_score,
                "deadline_fit": deadline_fit_score,
                "priority_fit": priority_fit_score,
                "workload_fit": workload_fit_score,
                "reasonable_hours": reasonable_hours_score,
            },
        }

    def recommend(
        self,
        task,
        free_blocks,
        duration_minutes,
        preference=None,
    ):
        """
        Generate candidates, score them, and return
        the highest-scoring candidate.
        """

        if not free_blocks:
            return None

        duration = timedelta(
            minutes=duration_minutes
        )

        candidates = []

        candidate_interval = timedelta(
            minutes=30
        )

        for block in free_blocks:

            block_start = datetime.fromisoformat(
                block["start"]
            )

            block_end = datetime.fromisoformat(
                block["end"]
            )

            if block_end - block_start < duration:
                continue

            candidate_start = block_start

            while (
                candidate_start + duration
                <= block_end
            ):
                candidates.append({
                    "start": candidate_start,
                    "end": candidate_start + duration,
                    "duration_minutes": duration_minutes,
                })

                candidate_start += candidate_interval

            # 8 PM candidate
            evening_start = block_start.replace(
                hour=20,
                minute=0,
                second=0,
                microsecond=0,
            )

            if (
                evening_start >= block_start
                and evening_start + duration <= block_end
            ):
                candidates.append({
                    "start": evening_start,
                    "end": evening_start + duration,
                    "duration_minutes": duration_minutes,
                })

            # Noon candidate
            noon_start = block_start.replace(
                hour=12,
                minute=0,
                second=0,
                microsecond=0,
            )

            if (
                noon_start >= block_start
                and noon_start + duration <= block_end
            ):
                candidates.append({
                    "start": noon_start,
                    "end": noon_start + duration,
                    "duration_minutes": duration_minutes,
                })

        if not candidates:
            return None

        scored_candidates = []

        for candidate in candidates:

            scoring = self.score_candidate(
                candidate=candidate,
                task=task or {},
                preference=preference,
            )

            scored_candidates.append({
                **candidate,
                "score": scoring["score"],
                "score_breakdown": scoring["breakdown"],
            })

        scored_candidates.sort(
            key=lambda candidate: (
                candidate["score"],
                candidate["start"],
            ),
            reverse=True,
        )

        best = scored_candidates[0]

        return {
            "start": best["start"].strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "end": best["end"].strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "duration_minutes": best[
                "duration_minutes"
            ],
            "score": best["score"],
            "score_breakdown": best[
                "score_breakdown"
            ],
        }