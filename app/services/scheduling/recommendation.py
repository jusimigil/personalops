from datetime import datetime, timedelta


class RecommendationService:

    def recommend(
        self,
        task,
        free_blocks,
        duration_minutes,
        preference=None,
    ):
        """
        Recommend a specific study/work session
        within the available blocks.
        """

        if not free_blocks:
            return None

        duration = timedelta(
            minutes=duration_minutes
        )

        candidates = []

        for block in free_blocks:

            block_start = datetime.fromisoformat(
                block["start"]
            )

            block_end = datetime.fromisoformat(
                block["end"]
            )

            if block_end - block_start < duration:
                continue

            # Default candidate starts at the
            # beginning of the free block.
            candidate_start = block_start
            candidate_end = (
                candidate_start + duration
            )

            candidates.append({
                "start": candidate_start,
                "end": candidate_end,
                "duration_minutes": duration_minutes,
            })

        if not candidates:
            return None

        # Prefer evening sessions when the user
        # prefers studying difficult subjects at night.
        if preference:

            preference_lower = preference.lower()

            if (
                "difficult" in preference_lower
                and "night" in preference_lower
            ):

                evening_candidates = []

                for candidate in candidates:

                    if candidate["start"].hour >= 18:
                        evening_candidates.append(
                            candidate
                        )

                if evening_candidates:
                    candidates = evening_candidates

        best = candidates[0]

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
        }