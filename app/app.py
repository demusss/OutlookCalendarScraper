from dotenv import load_dotenv

import logging
import os

from scraper import CalendarScraper
from ics_generator import IcsGenerator
from util import Util


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class App:
    def __init__(self):
        load_dotenv(
            ".env"
        )

        self.url = os.getenv(
            "CALENDAR_URL"
        )

        if not self.url:
            raise ValueError(
                "CALENDAR_URL is not set in .env"
            )

    def runApp(self) -> None:
        events = CalendarScraper(
            self.url
        ).run()

        logger.info(
            f"Scraped {len(events)} events."
        )

        ics_gen_inst = IcsGenerator()

        for event_number, event in enumerate(
            events,
            start=1,
        ):
            if len(event) < 3:
                logger.warning(
                    "Skipping malformed event "
                    f"#{event_number}: {event!r}"
                )
                continue

            e_title = event[0]
            e_date = event[1]
            e_desc = event[2]

            logger.info(
                f"Adding event #{event_number}: "
                f"title={e_title!r}, "
                f"date={e_date!r}"
            )

            ics_gen_inst.create_event(
                e_title,
                e_date,
                e_desc,
            )


if __name__ == "__main__":
    app = App()

    app.runApp()

    logger.info(
        f"[{Util.timestamp()}] - "
        "Scraping finished :)"
    )