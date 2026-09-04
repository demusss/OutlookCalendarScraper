import os

from icalendar import Calendar, Event

from util import Util


class IcsGenerator:
    def __init__(self):
        self.calendar = Calendar()

        self.calendar.add(
            "prodid",
            "-//Outlook Calendar Scraper//EN",
        )

        self.calendar.add(
            "version",
            "2.0",
        )

    def create_event(
        self,
        title,
        date,
        desc,
    ) -> None:

        event_start_date, event_end_date = (
            Util.format_date(
                date
            )
        )

        event = Event()

        event.add(
            "summary",
            title,
        )

        if desc:
            event.add(
                "description",
                desc,
            )

        event.add(
            "dtstart",
            event_start_date,
        )

        event.add(
            "dtend",
            event_end_date,
        )

        self.calendar.add_component(
            event
        )

        os.makedirs(
            "data",
            exist_ok=True,
        )

        with open(
            "data/outlook.ics",
            "wb",
        ) as file:
            file.write(
                self.calendar.to_ical()
            )
