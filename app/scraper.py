from datetime import datetime
import logging
import re

from selenium import webdriver
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class CalendarScraper:
    def __init__(self, url):
        self.url = url

    # ---------------------------------------------------------
    # Initialise Chrome
    # ---------------------------------------------------------
    def init_driver(self) -> webdriver:
        options = Options()

        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=2560,1440")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--start-maximized")

        options.add_argument(
            "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        )

        driver = webdriver.Chrome(options=options)

        driver.execute_script(
            "Object.defineProperty("
            "navigator, 'webdriver', "
            "{get: () => undefined}"
            ")"
        )

        return driver

    # ---------------------------------------------------------
    # Convert Outlook aria-label into the format expected by
    # Util.format_date()
    #
    # Example aria-label:
    #
    # Private Appointment, 2:00 PM to 2:00 PM,
    # Thursday, December 3, 2026,
    # Free, Recurring event, Private
    #
    # Returns:
    #
    # Thu 12/3/2026 2:00 PM - 2:00 PM
    # ---------------------------------------------------------
    def parse_aria_date(self, aria_label: str) -> str:
        if not aria_label:
            raise ValueError(
                "Outlook event does not contain an aria-label."
            )

        #logger.info(
        #    f"Parsing Outlook aria-label: {aria_label!r}"
        #)

        match = re.search(
            r"(\d{1,2}:\d{2}\s*[AP]M)"
            r"\s+to\s+"
            r"(\d{1,2}:\d{2}\s*[AP]M)"
            r",\s*"
            r"("
            r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
            r",\s*"
            r"(?:January|February|March|April|May|June|July|August|"
            r"September|October|November|December)"
            r"\s+\d{1,2},\s+\d{4}"
            r")",
            aria_label,
            re.IGNORECASE,
        )

        if not match:
            raise ValueError(
                "Could not extract start/end date from Outlook "
                f"aria-label: {aria_label!r}"
            )

        start_time = match.group(1).strip().upper()
        end_time = match.group(2).strip().upper()
        full_date = match.group(3).strip()

        #logger.info(
        #    f"Extracted Outlook date={full_date!r}, "
        #    f"start={start_time!r}, "
        #    f"end={end_time!r}"
        #)

        try:
            parsed_date = datetime.strptime(
                full_date,
                "%A, %B %d, %Y",
            )

        except ValueError as exc:
            raise ValueError(
                f"Could not parse Outlook date {full_date!r}"
            ) from exc

        date = (
            f"{parsed_date.strftime('%a')} "
            f"{parsed_date.month}/"
            f"{parsed_date.day}/"
            f"{parsed_date.year} "
            f"{start_time} - {end_time}"
        )

        #logger.info(
        #    f"Final parsed date for ICS: {date!r}"
        #)

        return date

    # ---------------------------------------------------------
    # Re-find an event if Selenium marks the original element
    # as stale.
    # ---------------------------------------------------------
    def refind_event(self, driver, item_index):
        if item_index:
            return driver.find_element(
                By.CSS_SELECTOR,
                f'div[data-itemindex="{item_index}"]',
            )

        raise StaleElementReferenceException(
            "Could not re-find Outlook event because "
            "data-itemindex was unavailable."
        )

    # ---------------------------------------------------------
    # Extract one event
    # ---------------------------------------------------------
    def get_event_data(
        self,
        driver,
        event,
        timeout: int = 10,
        event_count: int = 0,
    ) -> list:

        wait = WebDriverWait(driver, timeout)

        # -----------------------------------------------------
        # Save Outlook's event identifier before doing anything
        # that could make the WebElement stale.
        # -----------------------------------------------------
        item_index = event.get_attribute(
            "data-itemindex"
        )

        #logger.info(
        #    f"EVENT HTML:\n"
        #    f"{event.get_attribute('outerHTML')}"
        #)

        # -----------------------------------------------------
        # IMPORTANT:
        #
        # aria-label is NOT on div[data-itemindex].
        # It is on the nested div[role="button"].
        # -----------------------------------------------------
        try:
            event_button = event.find_element(
                By.CSS_SELECTOR,
                'div[role="button"]',
            )

            aria_label = event_button.get_attribute(
                "aria-label"
            )

        except StaleElementReferenceException:
            event = self.refind_event(
                driver,
                item_index,
            )

            event_button = event.find_element(
                By.CSS_SELECTOR,
                'div[role="button"]',
            )

            aria_label = event_button.get_attribute(
                "aria-label"
            )

        #logger.info(
        #    f"Event aria-label: {aria_label!r}"
        #)

        # -----------------------------------------------------
        # Parse date BEFORE opening the popup.
        #
        # Opening Outlook's popup can cause calendar elements
        # to become stale.
        # -----------------------------------------------------
        date = self.parse_aria_date(
            aria_label
        )

        # -----------------------------------------------------
        # Click event
        # -----------------------------------------------------
        try:
            event_button.click()

        except StaleElementReferenceException:
            event = self.refind_event(
                driver,
                item_index,
            )

            event_button = event.find_element(
                By.CSS_SELECTOR,
                'div[role="button"]',
            )

            driver.execute_script(
                "arguments[0].click();",
                event_button,
            )

        # -----------------------------------------------------
        # Wait for Outlook event popup
        # -----------------------------------------------------
        popup = wait.until(
            EC.visibility_of_element_located(
                (
                    By.CSS_SELECTOR,
                    'div[role="dialog"], '
                    'div[role="region"]',
                )
            )
        )

        # -----------------------------------------------------
        # Get title
        # -----------------------------------------------------
        try:
            title = WebDriverWait(
                popup,
                5,
            ).until(
                EC.visibility_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        'span[aria-label="Title"]',
                    )
                )
            ).text.strip()

        except TimeoutException:
            title = ""

        # -----------------------------------------------------
        # If popup title isn't available, get title from
        # aria-label as a fallback.
        # -----------------------------------------------------
        if not title and aria_label:
            time_match = re.search(
                r",\s*\d{1,2}:\d{2}\s*[AP]M"
                r"\s+to\s+"
                r"\d{1,2}:\d{2}\s*[AP]M",
                aria_label,
                re.IGNORECASE,
            )

            if time_match:
                title = aria_label[
                    :time_match.start()
                ].strip()

        if not title:
            title = "Outlook Event"

        # -----------------------------------------------------
        # Initialise description/location variables
        # -----------------------------------------------------
        meet_link = None
        classroom = ""

        # -----------------------------------------------------
        # Try to get Teams meeting link
        # -----------------------------------------------------
        try:
            desc_element = WebDriverWait(
                popup,
                5,
            ).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        'div[visibility="hidden"]',
                    )
                )
            )

            description_text = (
                desc_element.get_attribute(
                    "textContent"
                )
                or ""
            ).strip()

            meet_url_pattern = (
                r"https://teams\.microsoft\.com/"
                r"meet/\S+"
            )

            match = re.search(
                meet_url_pattern,
                description_text,
            )

            if match:
                meet_link = match.group(0)

        except TimeoutException:
            pass

        # -----------------------------------------------------
        # If no Teams link, try to get classroom/location
        # -----------------------------------------------------
        if not meet_link:
            try:
                loc = WebDriverWait(
                    popup,
                    5,
                ).until(
                    EC.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            'span[class="QI7ov"]',
                        )
                    )
                ).text.strip()

                classroom_pattern = (
                    r"Sala:\s*\d+"
                )

                match = re.search(
                    classroom_pattern,
                    loc,
                )

                if match:
                    classroom = match.group(0)

            except TimeoutException:
                pass

        # -----------------------------------------------------
        # Close popup
        # -----------------------------------------------------
        try:
            popup.send_keys(
                Keys.ESCAPE
            )

        except Exception:
            driver.switch_to.active_element.send_keys(
                Keys.ESCAPE
            )

        # -----------------------------------------------------
        # Wait for Outlook overlay to disappear.
        # -----------------------------------------------------
        try:
            wait.until(
                EC.invisibility_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "div.ms-Overlay",
                    )
                )
            )

        except TimeoutException:
            logger.warning(
                "Popup overlay did not disappear "
                "in time"
            )

        # -----------------------------------------------------
        # Create returned event data
        # -----------------------------------------------------
        if meet_link:
            event_data = [
                "[Remote] " + title,
                date,
                meet_link,
            ]

        else:
            event_data = [
                "[OnSite] " + title,
                date,
                classroom,
            ]

        logger.info(
            f"Event scraped #{event_count}: "
            f"{event_data}"
        )

        return event_data

    # ---------------------------------------------------------
    # Parse all visible months/events
    # ---------------------------------------------------------
    def parse_all_events(
        self,
        driver,
        timeout: int = 10,
    ) -> list:

        event_locator = (
            "div[data-itemindex]"
        )

        button_locator = (
            'i[data-icon-name="Down"]'
        )

        wait = WebDriverWait(
            driver,
            timeout,
        )

        parsed_events_data = []

        # =====================================================
        # Initial month + next 3 months
        #
        # month_number:
        # 0 = currently displayed month
        # 1-3 = following months
        # =====================================================
        for month_number in range(4):

            if month_number > 0:
                logger.info(
                    "Moving to next month "
                    f"({month_number}/3)"
                )

                # ---------------------------------------------
                # Ensure any previous popup/overlay is gone.
                # ---------------------------------------------
                try:
                    wait.until(
                        EC.invisibility_of_element_located(
                            (
                                By.CSS_SELECTOR,
                                "div.ms-Overlay",
                            )
                        )
                    )

                except TimeoutException:
                    logger.warning(
                        "Overlay still visible before "
                        "clicking next month"
                    )

                # ---------------------------------------------
                # Find next-month button
                # ---------------------------------------------
                next_button = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.CSS_SELECTOR,
                            button_locator,
                        )
                    )
                )

                # Save current event identifiers so we can
                # detect that Outlook actually changed month.
                old_elements = driver.find_elements(
                    By.CSS_SELECTOR,
                    event_locator,
                )

                old_ids = {
                    element.get_attribute(
                        "data-itemindex"
                    )
                    for element in old_elements
                }

                next_button.click()

                # ---------------------------------------------
                # Wait for events for the new month.
                # ---------------------------------------------
                wait.until(
                    EC.presence_of_all_elements_located(
                        (
                            By.CSS_SELECTOR,
                            event_locator,
                        )
                    )
                )

                # Best-effort wait for calendar contents
                # to actually change.
                try:
                    wait.until(
                        lambda d: {
                            element.get_attribute(
                                "data-itemindex"
                            )
                            for element in d.find_elements(
                                By.CSS_SELECTOR,
                                event_locator,
                            )
                        }
                        != old_ids
                    )

                except TimeoutException:
                    logger.warning(
                        "Could not confirm that calendar "
                        "event IDs changed after moving "
                        "to next month."
                    )

            # ---------------------------------------------
            # Find current month's events
            # ---------------------------------------------
            wait.until(
                EC.presence_of_all_elements_located(
                    (
                        By.CSS_SELECTOR,
                        event_locator,
                    )
                )
            )

            events = driver.find_elements(
                By.CSS_SELECTOR,
                event_locator,
            )

            logger.info(
                f"Found {len(events)} events "
                f"in displayed month #{month_number + 1}"
            )

            # ---------------------------------------------
            # IMPORTANT:
            #
            # Re-find the list before each event because
            # Outlook can rebuild its DOM after a popup
            # opens/closes.
            # ---------------------------------------------
            event_total = len(events)

            for event_position in range(
                event_total
            ):
                current_events = driver.find_elements(
                    By.CSS_SELECTOR,
                    event_locator,
                )

                if event_position >= len(
                    current_events
                ):
                    logger.warning(
                        "Event list changed while "
                        "processing month; skipping "
                        f"position {event_position}."
                    )
                    continue

                event = current_events[
                    event_position
                ]

                try:
                    event_data = self.get_event_data(
                        driver,
                        event,
                        timeout,
                        event_position + 1,
                    )

                    parsed_events_data.append(
                        event_data
                    )

                except Exception:
                    logger.exception(
                        "Failed to scrape event "
                        f"#{event_position + 1}"
                    )
                    raise

        return parsed_events_data

    # ---------------------------------------------------------
    # Main scraper entry point
    # ---------------------------------------------------------
    def run(self) -> list:
        driver = self.init_driver()

        try:
            driver.get(
                self.url
            )

            parsed_events = (
                self.parse_all_events(
                    driver
                )
            )

            return parsed_events

        finally:
            driver.quit()