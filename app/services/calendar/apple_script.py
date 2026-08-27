import subprocess
from datetime import datetime, timedelta
import re

from dateutil.rrule import rrulestr

from services.calendar.base import CalendarProvider


class AppleScriptCalendarProvider(CalendarProvider):
    """
    Calendar provider using macOS AppleScript.
    """

    def _run_script(self, script):
        """Execute an AppleScript command."""

        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
            )

        return result.stdout.strip()

    def _escape_text(self, text):
        """Escape text for use inside an AppleScript string."""

        if text is None:
            return ""

        return (
            str(text)
            .replace("\\", "\\\\")
            .replace('"', '\\"')
        )

    def get_calendars(self):
        """Return available Apple Calendar calendars."""

        script = """
        tell application "Calendar"
            get name of calendars
        end tell
        """

        output = self._run_script(script)

        if not output:
            return []

        return [
            name.strip()
            for name in output.split(",")
        ]

    def get_events(
        self,
        start_time,
        end_time,
        calendar_name=None,
    ):
        """Return calendar events within a time range."""

        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)

        if end <= start:
            raise ValueError(
                "End time must be after start time."
            )

        today = datetime.now().date()

        start_day_offset = (
            start.date() - today
        ).days

        end_day_offset = (
            end.date() - today
        ).days

        start_seconds = (
            start.hour * 3600
            + start.minute * 60
            + start.second
        )

        end_seconds = (
            end.hour * 3600
            + end.minute * 60
            + end.second
        )

        if calendar_name:
            calendars = [calendar_name]
        else:
            calendars = self.get_calendars()

        events = []

        for current_calendar in calendars:

            escaped_calendar = self._escape_text(
                current_calendar
            )

            script = f'''
            set rangeStart to current date
            set time of rangeStart to 0
            set rangeStart to rangeStart + ({start_day_offset} * days)
            set rangeStart to rangeStart + {start_seconds}

            set rangeEnd to current date
            set time of rangeEnd to 0
            set rangeEnd to rangeEnd + ({end_day_offset} * days)
            set rangeEnd to rangeEnd + {end_seconds}

            tell application "Calendar"
                tell calendar "{escaped_calendar}"

                    set allEvents to every event
                    set outputText to ""

                    repeat with currentEvent in allEvents

                        set eventStart to start date of currentEvent
                        set eventEnd to end date of currentEvent

                        set eventTitle to summary of currentEvent

                        set eventRecurrence to recurrence of currentEvent

                        if eventRecurrence is missing value then
                            set eventRecurrence to ""
                        end if

                        set eventTitle to summary of currentEvent

                        set startYear to year of eventStart
                        set startMonth to month of eventStart as integer
                        set startDay to day of eventStart
                        set startHour to hours of eventStart
                        set startMinute to minutes of eventStart
                        set startSecond to seconds of eventStart

                        set endYear to year of eventEnd
                        set endMonth to month of eventEnd as integer
                        set endDay to day of eventEnd
                        set endHour to hours of eventEnd
                        set endMinute to minutes of eventEnd
                        set endSecond to seconds of eventEnd

                        set eventUID to uid of currentEvent

                        set outputText to outputText & eventUID
                        set outputText to outputText & "\t"
                        set outputText to outputText & eventTitle
                        set outputText to outputText & "\t"

                        set outputText to outputText & startYear
                        set outputText to outputText & "-"
                        set outputText to outputText & startMonth
                        set outputText to outputText & "-"
                        set outputText to outputText & startDay
                        set outputText to outputText & " "
                        set outputText to outputText & startHour
                        set outputText to outputText & ":"
                        set outputText to outputText & startMinute
                        set outputText to outputText & ":"
                        set outputText to outputText & startSecond

                        set outputText to outputText & "\t"

                        set outputText to outputText & endYear
                        set outputText to outputText & "-"
                        set outputText to outputText & endMonth
                        set outputText to outputText & "-"
                        set outputText to outputText & endDay
                        set outputText to outputText & " "
                        set outputText to outputText & endHour
                        set outputText to outputText & ":"
                        set outputText to outputText & endMinute
                        set outputText to outputText & ":"
                        set outputText to outputText & endSecond

                        set outputText to outputText & "\t"
                        set outputText to outputText & eventRecurrence
                        set outputText to outputText & "\n"

                    end repeat

                    return outputText

                end tell
            end tell
            '''

            output = self._run_script(script)

            for line in output.splitlines():

                parts = line.split("\t")

                if len(parts) != 5:
                    continue

                event_id = parts[0]
                title = parts[1]

                event_start = datetime.strptime(
                    parts[2],
                    "%Y-%m-%d %H:%M:%S"
                )

                event_end = datetime.strptime(
                    parts[3],
                    "%Y-%m-%d %H:%M:%S"
                )

                recurrence = parts[4].strip()
                recurrence = self._normalize_recurrence(
                    recurrence
                )

                duration = event_end - event_start

                # ------------------------------------------
                # Non-recurring event
                # ------------------------------------------

                if not recurrence:

                    if event_start < end and event_end > start:

                        events.append({
                            "calendar": current_calendar,
                            "event_id": event_id,
                            "title": title,
                            "start": event_start.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "end": event_end.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                            "recurring": False,
                        })

                    continue

                # ------------------------------------------
                # Recurring event
                # ------------------------------------------

                try:

                    naive_start = event_start.replace(
                        tzinfo=None
                    )

                    naive_query_start = start.replace(
                        tzinfo=None
                    )

                    naive_query_end = end.replace(
                        tzinfo=None
                    )

                    rule = rrulestr(
                        recurrence,
                        dtstart=naive_start,
                    )

                    occurrences = rule.between(
                        naive_query_start,
                        naive_query_end,
                        inc=True,
                    )

                    for occurrence in occurrences:

                        occurrence_end = (
                            occurrence + duration
                        )

                        if (
                            occurrence < end
                            and occurrence_end > start
                        ):

                            events.append({
                                "calendar": current_calendar,
                                "event_id": event_id,
                                "title": title,
                                "start": occurrence.strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "end": occurrence_end.strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                "recurring": True,
                            })

                except Exception as error:

                    print(
                        f"[WARNING] Could not expand recurrence "
                        f"for '{title}': {error}"
                    )

        return events

    def get_event_by_id(
        self,
        event_id,
        calendar_name=None,
    ):
        """Return a single Apple Calendar event by UID."""

        if not event_id:
            raise ValueError("event_id is required.")

        if calendar_name is None:
            calendars = self.get_calendars()

            if not calendars:
                raise RuntimeError(
                    "No Apple Calendar calendars found."
                )

            calendar_name = calendars[0]

        escaped_event_id = self._escape_text(event_id)
        escaped_calendar = self._escape_text(calendar_name)

        script = f"""
        tell application "Calendar"
            tell calendar "{escaped_calendar}"
                set matchingEvents to every event whose uid is "{escaped_event_id}"

                if (count of matchingEvents) is 0 then
                    return ""
                end if

                set targetEvent to item 1 of matchingEvents

                set eventTitle to summary of targetEvent
                set eventStart to start date of targetEvent
                set eventEnd to end date of targetEvent
                set eventRecurrence to recurrence of targetEvent

                if eventRecurrence is missing value then
                    set eventRecurrence to ""
                end if

                set eventYear to year of eventStart
                set eventMonth to month of eventStart as integer
                set eventDay to day of eventStart
                set eventHour to hours of eventStart
                set eventMinute to minutes of eventStart
                set eventSecond to seconds of eventStart

                set endYear to year of eventEnd
                set endMonth to month of eventEnd as integer
                set endDay to day of eventEnd
                set endHour to hours of eventEnd
                set endMinute to minutes of eventEnd
                set endSecond to seconds of eventEnd

                set outputText to eventTitle
                set outputText to outputText & "\t"
                set outputText to outputText & eventYear
                set outputText to outputText & "-"
                set outputText to outputText & eventMonth
                set outputText to outputText & "-"
                set outputText to outputText & eventDay
                set outputText to outputText & " "
                set outputText to outputText & eventHour
                set outputText to outputText & ":"
                set outputText to outputText & eventMinute
                set outputText to outputText & ":"
                set outputText to outputText & eventSecond
                set outputText to outputText & "\t"
                set outputText to outputText & endYear
                set outputText to outputText & "-"
                set outputText to outputText & endMonth
                set outputText to outputText & "-"
                set outputText to outputText & endDay
                set outputText to outputText & " "
                set outputText to outputText & endHour
                set outputText to outputText & ":"
                set outputText to outputText & endMinute
                set outputText to outputText & ":"
                set outputText to outputText & endSecond
                set outputText to outputText & "\t"
                set outputText to outputText & eventRecurrence

                return outputText
            end tell
        end tell
        """

        output = self._run_script(script)

        if not output:
            return None

        parts = output.split("\t")

        if len(parts) != 3:
            raise RuntimeError(
                "Unexpected Apple Calendar event output."
            )

        event_title = parts[0]

        event_start = datetime.strptime(
            parts[1],
            "%Y-%m-%d %H:%M:%S",
        )

        event_end = datetime.strptime(
            parts[2],
            "%Y-%m-%d %H:%M:%S",
        )

        return {
            "calendar": calendar_name,
            "event_id": event_id,
            "title": event_title,
            "start": event_start.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "end": event_end.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "recurrence": "",
            "recurring": False,
        }

    def update_event(
        self,
        event_id,
        title=None,
        start_time=None,
        end_time=None,
        calendar_name=None,
        location=None,
        description=None,
    ):
        """Update an existing Apple Calendar event."""

        if not event_id:
            raise ValueError("event_id is required.")

        if all(
            value is None
            for value in (
                title,
                start_time,
                end_time,
                location,
                description,
            )
        ):
            raise ValueError(
                "At least one event field must be provided."
            )

        start = (
            datetime.fromisoformat(start_time)
            if start_time is not None
            else None
        )

        end = (
            datetime.fromisoformat(end_time)
            if end_time is not None
            else None
        )

        if (
            start is not None
            and end is not None
            and end <= start
        ):
            raise ValueError(
                "End time must be after start time."
            )

        if calendar_name is None:
            calendars = self.get_calendars()

            if not calendars:
                raise RuntimeError(
                    "No Apple Calendar calendars found."
                )

            calendar_name = calendars[0]

        today = datetime.now().date()

        setup_lines = []

        if start is not None:
            start_offset = (
                start.date() - today
            ).days

            start_seconds = (
                start.hour * 3600
                + start.minute * 60
                + start.second
            )

            setup_lines.extend([
                "set startDate to current date",
                "set time of startDate to 0",
                f"set startDate to startDate + ({start_offset} * days)",
                f"set startDate to startDate + {start_seconds}",
            ])

        if end is not None:
            end_offset = (
                end.date() - today
            ).days

            end_seconds = (
                end.hour * 3600
                + end.minute * 60
                + end.second
            )

            setup_lines.extend([
                "set endDate to current date",
                "set time of endDate to 0",
                f"set endDate to endDate + ({end_offset} * days)",
                f"set endDate to endDate + {end_seconds}",
            ])

        update_lines = []

        if title is not None:
            update_lines.append(
                f'set summary of targetEvent to "{self._escape_text(title)}"'
            )

        if start is not None and end is not None:
            update_lines.append(
                "set end date of targetEvent to endDate"
            )
            update_lines.append(
                "set start date of targetEvent to startDate"
            )
        elif start is not None:
            update_lines.append(
                "set start date of targetEvent to startDate"
            )
        elif end is not None:
            update_lines.append(
                "set end date of targetEvent to endDate"
            )

        if location is not None:
            update_lines.append(
                f'set location of targetEvent to "{self._escape_text(location)}"'
            )

        if description is not None:
            update_lines.append(
                f'set description of targetEvent to "{self._escape_text(description)}"'
            )

        setup_text = "\n".join(setup_lines)
        update_text = "\n".join(update_lines)

        escaped_event_id = self._escape_text(event_id)
        escaped_calendar = self._escape_text(calendar_name)

        script = f"""
    {setup_text}

    tell application "Calendar"
        tell calendar "{escaped_calendar}"
            set matchingEvents to every event whose uid is "{escaped_event_id}"

            if (count of matchingEvents) is 0 then
                error "Calendar event not found."
            end if

            set targetEvent to item 1 of matchingEvents

            {update_text}

            save targetEvent

            return uid of targetEvent
        end tell
    end tell
    """
        return self._run_script(script)

    def create_event(
        self,
        title,
        start_time,
        end_time,
        calendar_name=None,
        location=None,
        description=None,
    ):
        """Create an event in Apple Calendar."""

        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)

        if end <= start:
            raise ValueError(
                "End time must be after start time."
            )

        if calendar_name is None:
            calendars = self.get_calendars()

            if not calendars:
                raise RuntimeError(
                    "No Apple Calendar calendars found."
                )

            calendar_name = calendars[0]

        title = self._escape_text(title)
        calendar_name = self._escape_text(calendar_name)
        location = self._escape_text(location)
        description = self._escape_text(description)

    # ------------------------------------------
    # Calculate date offsets
    # ------------------------------------------

        today = datetime.now().date()

        start_day_offset = (
            start.date() - today
        ).days

        end_day_offset = (
           end.date() - today
        ).days

        # Seconds since midnight.
        start_seconds = (
            start.hour * 3600
            + start.minute * 60
            + start.second
        )

        end_seconds = (
            end.hour * 3600
            + end.minute * 60
            + end.second
        )

    # ------------------------------------------
    # AppleScript
    # ------------------------------------------

        script = f'''
        set eventStart to current date
        set time of eventStart to 0
        set eventStart to eventStart + ({start_day_offset} * days)
        set eventStart to eventStart + {start_seconds}

        set eventEnd to current date
        set time of eventEnd to 0
        set eventEnd to eventEnd + ({end_day_offset} * days)
        set eventEnd to eventEnd + {end_seconds}

        tell application "Calendar"
            tell calendar "{calendar_name}"
                set newEvent to make new event with properties {{summary:"{title}", start date:eventStart, end date:eventEnd}}

                set location of newEvent to "{location}"
                set description of newEvent to "{description}"

                return uid of newEvent
            end tell
        end tell
        '''

        return self._run_script(script)

    def find_events_by_title(
        self,
        title,
        calendar_name=None,
    ):
        """Find calendar events directly by title."""

        if not title:
            raise ValueError("title is required.")

        if calendar_name is None:
            calendars = self.get_calendars()
        else:
            calendars = [calendar_name]

        matches = []

        escaped_title = self._escape_text(title)

        for current_calendar in calendars:
            escaped_calendar = self._escape_text(
                current_calendar
            )

            script = f'''
            tell application "Calendar"
                tell calendar "{escaped_calendar}"
                    set matchingEvents to every event whose summary is "{escaped_title}"

                    set outputText to ""

                    repeat with currentEvent in matchingEvents
                        set eventUID to uid of currentEvent
                        set eventTitle to summary of currentEvent
                        set eventStart to start date of currentEvent
                        set eventEnd to end date of currentEvent

                        set startYear to year of eventStart
                        set startMonth to month of eventStart as integer
                        set startDay to day of eventStart
                        set startHour to hours of eventStart
                        set startMinute to minutes of eventStart
                        set startSecond to seconds of eventStart

                        set endYear to year of eventEnd
                        set endMonth to month of eventEnd as integer
                        set endDay to day of eventEnd
                        set endHour to hours of eventEnd
                        set endMinute to minutes of eventEnd
                        set endSecond to seconds of eventEnd

                        set outputText to outputText & eventUID
                        set outputText to outputText & "\t"
                        set outputText to outputText & eventTitle
                        set outputText to outputText & "\t"

                        set outputText to outputText & startYear
                        set outputText to outputText & "-"
                        set outputText to outputText & startMonth
                        set outputText to outputText & "-"
                        set outputText to outputText & startDay
                        set outputText to outputText & " "
                        set outputText to outputText & startHour
                        set outputText to outputText & ":"
                        set outputText to outputText & startMinute
                        set outputText to outputText & ":"
                        set outputText to outputText & startSecond

                        set outputText to outputText & "\t"

                        set outputText to outputText & endYear
                        set outputText to outputText & "-"
                        set outputText to outputText & endMonth
                        set outputText to outputText & "-"
                        set outputText to outputText & endDay
                        set outputText to outputText & " "
                        set outputText to outputText & endHour
                        set outputText to outputText & ":"
                        set outputText to outputText & endMinute
                        set outputText to outputText & ":"
                        set outputText to outputText & endSecond

                        set outputText to outputText & "\n"
                    end repeat

                    return outputText
                end tell
            end tell
            '''

            output = self._run_script(script)

            for line in output.splitlines():
                parts = line.split("\t")

                if len(parts) != 4:
                    continue

                event_id = parts[0]

                event_start = datetime.strptime(
                    parts[2],
                    "%Y-%m-%d %H:%M:%S",
                )

                event_end = datetime.strptime(
                    parts[3],
                    "%Y-%m-%d %H:%M:%S",
                )

                matches.append({
                    "calendar": current_calendar,
                    "event_id": event_id,
                    "title": parts[1],
                    "start": event_start.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "end": event_end.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "recurring": False,
                })

        return matches

    def _normalize_recurrence(self, recurrence):
        """
        Normalize an Apple Calendar RRULE so dateutil can
        evaluate it against naive local datetimes.
        """

        if not recurrence:
            return recurrence

        # Apple Calendar commonly returns UTC UNTIL values:
        #
        #   UNTIL=20261214T155959Z
        #
        # Because our DTSTART/query datetimes are naive local
        # times, remove the trailing Z so dateutil treats UNTIL
        # as a naive datetime as well.
        recurrence = re.sub(
            r"UNTIL=(\d{8}T\d{6})Z",
            r"UNTIL=\1",
            recurrence,
        )

        return recurrence
        