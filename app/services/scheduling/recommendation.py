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
        Recommend a specific session within available blocks.
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

            # Default candidate: beginning of the block.
            candidate_start = block_start

            candidates.append({
                "start": candidate_start,
                "end": candidate_start + duration,
                "duration_minutes": duration_minutes,
            })

            # ------------------------------------------
            # Add evening candidate when appropriate
            # ------------------------------------------

            if preference:

                preference_lower = preference.lower()

                if (
                    "difficult" in preference_lower
                    and "night" in preference_lower
                ):
                    preferred_start = block_start.replace(
                        hour=20,
                        minute=0,
                        second=0,
                        microsecond=0,
                    )

                    # If 8 PM is before the block,
                    # start at the block beginning.
                    if preferred_start < block_start:
                        preferred_start = block_start

                    preferred_end = (
                        preferred_start + duration
                    )

                    if preferred_end <= block_end:

                        candidates.append({
                            "start": preferred_start,
                            "end": preferred_end,
                            "duration_minutes": duration_minutes,
                        })

        if not candidates:
            return None

        # ------------------------------------------
        # Prefer evening candidate
        # ------------------------------------------

        if preference:

            preference_lower = preference.lower()

            if (
                "difficult" in preference_lower
                and "night" in preference_lower
            ):

                evening_candidates = [
                    candidate
                    for candidate in candidates
                    if candidate["start"].hour >= 18
                ]

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