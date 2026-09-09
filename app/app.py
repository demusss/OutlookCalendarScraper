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
            "OUTLOOK_URL"
        )

        if not self.url:
            raise ValueError(
                "OUTLOOK_URL is not set in .env"
            )

        try:
            self.scrape_days = int(
                os.getenv("SCRAPE_DAYS", "7")
            )
        except ValueError as exc:
            raise ValueError(
                "SCRAPE_DAYS must be a positive integer"
            ) from exc

        if self.scrape_days <= 0:
            raise ValueError(
                "SCRAPE_DAYS must be a positive integer"
            )

    def runApp(self) -> None:
        events = CalendarScraper(
            self.url,
            self.scrape_days,
        ).run()

        logger.info(
            f"Scraped {len(events)} events."
        )

        valid_events = []

        for event_number, event in enumerate(
            events,
            start=1,
        ):
            if len(event) < 4:
                logger.warning(
                    "Skipping malformed event "
                    f"#{event_number}: {event!r}"
                )
                continue

            valid_events.append(event)

        valid_events.sort(
            key=lambda event: Util.format_date(
                event[1],
                event[2],
                event[3],
            )[0]
        )

        ics_gen_inst = IcsGenerator(
            self.scrape_days
        )

        for event_number, event in enumerate(
            valid_events,
            start=1,
        ):
            e_title = event[0]
            e_date = event[1]
            e_start_time = event[2]
            e_end_time = event[3]

            logger.info(
                f"Adding event #{event_number}: "
                f"title={e_title!r}, "
                f"date={e_date!r}, "
                f"start={e_start_time!r}, "
                f"end={e_end_time!r}"
            )

            ics_gen_inst.create_event(
                e_title,
                e_date,
                e_start_time,
                e_end_time,
            )


if __name__ == "__main__":
    app = App()

    app.runApp()

    logger.info(
        f"[{Util.timestamp()}] - "
        "Scraping finished :)"
    )