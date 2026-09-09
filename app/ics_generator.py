import json
import os

from icalendar import Calendar, Event

from util import Util


class IcsGenerator:
    def __init__(self, scrape_days: int = 7):
        self.calendar = Calendar()
        self.events = []
        self.scrape_days = scrape_days

        os.makedirs(
            "data",
            exist_ok=True,
        )

        with open(
            "data/scrape_days.json",
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                {"scrape_days": self.scrape_days},
                file,
            )
            file.write("\n")

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
        start_time,
        end_time,
    ) -> None:

        event_start_date, event_end_date = (
            Util.format_date(
                date,
                start_time,
                end_time,
            )
        )

        event = Event()

        event.add(
            "summary",
            title,
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

        self.events.append(
            {
                "title": title,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
            }
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

        with open(
            "data/outlook.json",
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                self.events,
                file,
                indent=2,
            )
            file.write("\n")
