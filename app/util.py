from datetime import datetime, timedelta


class Util:
    # ---------------------------------------------------------
    # Convert scraper date format into datetime objects
    #
    # Expected:
    #
    # Thu 12/3/2026 2:00 PM - 2:00 PM
    # ---------------------------------------------------------
    @staticmethod
    def format_date(
        date: str,
    ) -> tuple[datetime, datetime]:

        if not date:
            raise ValueError(
                "Event date is empty."
            )

        if " - " not in date:
            raise ValueError(
                "Unexpected date format. "
                "Expected something like "
                "'Thu 12/3/2026 2:00 PM - 3:00 PM', "
                f"but received: {date!r}"
            )

        start_date, end_time_str = (
            date.split(
                " - ",
                1,
            )
        )

        try:
            event_start = datetime.strptime(
                start_date.strip(),
                "%a %m/%d/%Y %I:%M %p",
            )

        except ValueError as exc:
            raise ValueError(
                "Could not parse event start date: "
                f"{start_date!r}"
            ) from exc

        try:
            end_time = datetime.strptime(
                end_time_str.strip(),
                "%I:%M %p",
            ).time()

        except ValueError as exc:
            raise ValueError(
                "Could not parse event end time: "
                f"{end_time_str!r}"
            ) from exc

        event_end = datetime.combine(
            event_start.date(),
            end_time,
        )

        # -----------------------------------------------------
        # Handle events crossing midnight.
        #
        # Example:
        #
        # Start: 11:00 PM
        # End:    1:00 AM
        #
        # The end is therefore on the following day.
        #
        # Equal start/end times are left unchanged because
        # Outlook may genuinely report zero-duration events.
        # -----------------------------------------------------
        if event_end < event_start:
            event_end += timedelta(
                days=1
            )

        return (
            event_start,
            event_end,
        )

    @staticmethod
    def timestamp() -> str:
        return datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        )