from datetime import datetime, timedelta


class Util:
    # ---------------------------------------------------------
    # Convert scraper date format into datetime objects
    #
    # Expected date and time values from the Outlook UI.
    # ---------------------------------------------------------
    @staticmethod
    def format_date(
        date: str,
        start_time: str,
        end_time: str,
    ) -> tuple[datetime, datetime]:

        if not date:
            raise ValueError(
                "Event date is empty."
            )

        try:
            event_start = datetime.strptime(
                f"{date.strip()} {start_time.strip()}",
                "%a %m/%d/%Y %I:%M %p",
            )

        except ValueError as exc:
            raise ValueError(
                "Could not parse event start date: "
                f"{date!r} {start_time!r}"
            ) from exc

        try:
            parsed_end_time = datetime.strptime(
                end_time.strip(),
                "%I:%M %p",
            ).time()

        except ValueError as exc:
            raise ValueError(
                "Could not parse event end time: "
                f"{end_time!r}"
            ) from exc

        event_end = datetime.combine(
            event_start.date(),
            parsed_end_time,
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