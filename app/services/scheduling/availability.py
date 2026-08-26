from datetime import datetime, timedelta


class AvailabilityService:

    def find_free_blocks(
        self,
        start_time,
        end_time,
        duration_minutes,
        events,
    ):
        """
        Find available blocks within a time range.

        Events must contain:
            start: YYYY-MM-DD HH:MM:SS
            end:   YYYY-MM-DD HH:MM:SS
        """

        start = datetime.fromisoformat(
            start_time
        )

        end = datetime.fromisoformat(
            end_time
        )

        duration = timedelta(
            minutes=duration_minutes
        )

        if end <= start:
            raise ValueError(
                "End time must be after start time."
            )

        if duration <= timedelta(0):
            raise ValueError(
                "Duration must be greater than zero."
            )

        # Convert events into datetime intervals.
        busy = []

        for event in events:

            event_start = datetime.fromisoformat(
                event["start"]
            )

            event_end = datetime.fromisoformat(
                event["end"]
            )

            # Ignore events completely outside
            # our requested range.
            if event_end <= start:
                continue

            if event_start >= end:
                continue

            # Clamp events to our search window.
            event_start = max(
                event_start,
                start,
            )

            event_end = min(
                event_end,
                end,
            )

            busy.append(
                (event_start, event_end)
            )

        # Sort events chronologically.
        busy.sort(
            key=lambda interval: interval[0]
        )

        # Merge overlapping events.
        merged = []

        for event_start, event_end in busy:

            if not merged:
                merged.append(
                    [event_start, event_end]
                )
                continue

            previous_start, previous_end = (
                merged[-1]
            )

            if event_start <= previous_end:

                merged[-1][1] = max(
                    previous_end,
                    event_end,
                )

            else:

                merged.append(
                    [event_start, event_end]
                )

        # Find gaps.
        free_blocks = []

        cursor = start

        for busy_start, busy_end in merged:

            if busy_start > cursor:

                gap = busy_start - cursor

                if gap >= duration:

                    free_blocks.append({
                        "start": cursor.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "end": busy_start.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "duration_minutes": int(
                            gap.total_seconds() / 60
                        ),
                    })

            cursor = max(
                cursor,
                busy_end,
            )

        # Check time after the final event.
        if cursor < end:

            gap = end - cursor

            if gap >= duration:

                free_blocks.append({
                    "start": cursor.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "end": end.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "duration_minutes": int(
                        gap.total_seconds() / 60
                    ),
                })

        return free_blocks