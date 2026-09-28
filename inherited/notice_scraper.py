import re
import time
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NoticeScraperConfig:
    """Configuration for the notice scraper."""
    BASE_URL = "https://pipeline2.kindermorgan.com/Notices/Notices.aspx?type={notice_type}&code=NGPL"
    NOTICE_LINK_XPATH = "//td//a[contains(@id, 'lnkbtnDownload')]"
    NEXT_PAGE_BUTTON_XPATH = "//span[@class='igg_NautilusPageLink' and text()='>']"
    WAIT_TIMEOUT = 15
    IMPLICIT_WAIT = 5


class NoticeScraper:
    """Scrapes notices from Kinder Morgan's electronic bulletin board."""

    def __init__(self, output_dir: str = "notices", notice_type: str = "Critical"):
        self.config = NoticeScraperConfig()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.notice_type = notice_type
        self.metadata: List[Dict] = []
        self.driver: Optional[webdriver.Chrome] = None

    def _init_driver(self):
        """Initialize Chrome WebDriver."""
        if self.driver is None:
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                logger.warning(f"Failed to use webdriver-manager: {e}, trying direct path")
                self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(self.config.IMPLICIT_WAIT)

    def _quit_driver(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _wait_for_element(self, locator: tuple, timeout: int = None) -> None:
        """Wait for an element to be present."""
        if timeout is None:
            timeout = self.config.WAIT_TIMEOUT
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
        except TimeoutException:
            logger.warning(f"Element not found: {locator}")

    def _wait_for_element_clickable(self, locator: tuple, timeout: int = None):
        """Wait for an element to be clickable and return it."""
        if timeout is None:
            timeout = self.config.WAIT_TIMEOUT
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )

    def _navigate_to_landing_page(self):
        """Navigate to the notices page for the specified notice type."""
        type_param = {
            "Critical": "C",
            "Non-Critical": "N",
            "Planned Service Outage": "P"
        }.get(self.notice_type, "C")

        url = self.config.BASE_URL.format(notice_type=type_param)
        logger.info(f"Navigating to {self.notice_type} notices: {url}")
        self.driver.get(url)
        time.sleep(2)

    def _wait_for_notices_table(self):
        """Wait for the notices table to load."""
        try:
            self._wait_for_element((By.XPATH, self.config.NOTICE_LINK_XPATH), timeout=15)
            logger.info("Notices table loaded successfully")
        except TimeoutException as e:
            logger.error(f"Failed to load notices table: {e}")
            raise

    @staticmethod
    def _val_from_data_ig(attr: str) -> str:
        """Extract the value from a data-ig attribute like x:...:val:\"TEXT\" or x:...:val:12345."""
        m = re.search(r':val:(?:&quot;|"?)([^&"]+)', attr or "")
        return m.group(1).strip() if m else ""

    def _get_notice_subjects(self) -> List[Dict]:
        """Extract all notice subjects from the table, filtering out PIPELINE CONDITIONS."""
        notices = []
        try:
            notice_links = self.driver.find_elements(By.XPATH, self.config.NOTICE_LINK_XPATH)
            logger.info(f"Found {len(notice_links)} total notice links on page")

            for link in notice_links:
                try:
                    row = link.find_element(By.XPATH, "./ancestor::tr[1]")
                    cells = row.find_elements(By.XPATH, "./td")

                    if len(cells) < 9:
                        continue

                    notice_type = self._val_from_data_ig(cells[0].get_attribute("data-ig"))
                    if not notice_type or notice_type == "PIPELINE CONDITIONS":
                        continue

                    notice_id = self._val_from_data_ig(cells[5].get_attribute("data-ig"))
                    # Subject is in cell[8] for virtualized rows; fall back to link text for visible rows
                    subject = (
                        link.text.strip()
                        or self._val_from_data_ig(cells[8].get_attribute("data-ig"))
                    )
                    if not subject:
                        continue

                    href = link.get_attribute("href") or ""
                    match = re.search(r"__doPostBack\('([^']+)'", href)
                    if not match:
                        logger.debug(f"Could not extract doPostBack target from href: {href}")
                        continue

                    notices.append({
                        "index": len(notices),
                        "notice_id": notice_id,
                        "notice_type": notice_type,
                        "subject": subject,
                        "postback_target": match.group(1),
                    })

                except Exception as e:
                    logger.debug(f"Error processing link: {e}")

            logger.info(f"Extracted {len(notices)} notices (after filtering PIPELINE CONDITIONS)")

        except Exception as e:
            logger.error(f"Error extracting notices: {e}")

        return notices

    def _trigger_postback(self, event_target: str):
        """Click the link whose id corresponds to the postback event target."""
        # ASP.NET postback targets use '$' as separator; DOM ids use '_'
        element_id = event_target.replace("$", "_")
        link = self.driver.find_element(By.ID, element_id)
        self.driver.execute_script("arguments[0].click();", link)
        time.sleep(3)
        logger.info(f"Triggered postback via element click: {element_id}")

    def _save_notice_html(self, notice_id: str, notice_type: str) -> str:
        """Save the current page's HTML to a file named <notice_id>_<notice_type>.html."""
        try:
            html_content = self.driver.page_source
            safe_type = "".join(c for c in notice_type if c.isalnum() or c in (' ', '-', '_')).strip()
            filename = f"{notice_id}_{safe_type}.html"
            filepath = self.output_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"Saved notice HTML to {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save notice HTML: {e}")
            raise

    def _download_impact_report(self, notice_id: str) -> Optional[str]:
        """Find the Outage Impact Report PDF link in the current page and download it."""
        try:
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            pdf_url = None
            for a in soup.find_all("a", href=True):
                # Normalize whitespace so "Outage\nImpact Report" matches "Outage Impact Report"
                text = " ".join(a.get_text().split())
                if text.lower().startswith("outage impact report"):
                    pdf_url = a["href"]
                    break

            if not pdf_url:
                logger.info(f"No Outage Impact Report link found for notice {notice_id}")
                return None

            logger.info(f"Downloading impact report PDF: {pdf_url}")
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()

            pdf_path = self.output_dir / f"{notice_id}_OUTAGE_IMPACT_REPORT.pdf"
            with open(pdf_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Saved impact report to {pdf_path}")
            return str(pdf_path)

        except Exception as e:
            logger.error(f"Failed to download impact report for notice {notice_id}: {e}")
            return None

    def _save_metadata(self, notice: Dict, html_path: str, impact_report_path: Optional[str] = None):
        """Save metadata about the downloaded notice."""
        metadata_entry = {
            "notice_id": notice["notice_id"],
            "notice_type": notice["notice_type"],
            "subject": notice["subject"],
            "html_file": html_path,
            "download_date": datetime.now().isoformat(),
            "source_url": self.config.BASE_URL,
        }
        if impact_report_path:
            metadata_entry["impact_report_file"] = impact_report_path
        self.metadata.append(metadata_entry)
        logger.info(f"Metadata saved for notice {notice['notice_id']}")

    def _save_metadata_file(self):
        """Save all metadata to a JSON file."""
        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)
        logger.info(f"Metadata file saved to {metadata_path}")

    def _navigate_to_page(self, target_page: int):
        """Navigate from page 1 to the target page by clicking Next repeatedly."""
        self._navigate_to_landing_page()
        self._wait_for_notices_table()
        for _ in range(target_page - 1):
            next_button = self.driver.find_element(By.XPATH, self.config.NEXT_PAGE_BUTTON_XPATH)
            self.driver.execute_script("arguments[0].click();", next_button)
            time.sleep(2)
            self._wait_for_notices_table()

    def _collect_all_notice_targets(self, max_notices: Optional[int] = None) -> List[Dict]:
        """Collect postback targets for all notices across all pages without downloading."""
        all_notices = []
        page_num = 1

        while True:
            logger.info(f"Collecting notice links from page {page_num}")
            self._wait_for_notices_table()
            page_notices = self._get_notice_subjects()
            logger.info(f"Page {page_num}: found {len(page_notices)} notices")

            for notice in page_notices:
                if max_notices and len(all_notices) >= max_notices:
                    break
                notice["page_num"] = page_num
                all_notices.append(notice)

            if max_notices and len(all_notices) >= max_notices:
                break

            try:
                next_button = self.driver.find_element(By.XPATH, self.config.NEXT_PAGE_BUTTON_XPATH)
                style = next_button.get_attribute("style") or ""
                if "display: none" in style:
                    logger.info("Reached last page")
                    break
                self.driver.execute_script("arguments[0].click();", next_button)
                page_num += 1
                time.sleep(2)
            except Exception:
                logger.info("No next page button found, reached last page")
                break

        logger.info(f"Collected {len(all_notices)} notice targets total")
        return all_notices

    def _save_notice_list(self, notices: List[Dict]):
        """Save the collected notice list to JSON for inspection before downloading."""
        notice_list_path = self.output_dir / "notice_list.json"
        output = [
            {
                "index": n["index"],
                "page_num": n["page_num"],
                "notice_id": n["notice_id"],
                "notice_type": n["notice_type"],
                "subject": n["subject"],
                "element_id": n["postback_target"].replace("$", "_"),
            }
            for n in notices
        ]
        with open(notice_list_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        logger.info(f"Notice list saved to {notice_list_path} ({len(output)} notices)")
        for entry in output:
            logger.info(f"  [{entry['index']:3}] id={entry['notice_id']:6}  type={entry['notice_type']:22}  subject={entry['subject']!r}")

    def fetch_notices(self, max_notices: Optional[int] = None):
        """Fetch and download notices of the specified type, including multiple pages."""
        try:
            self._init_driver()
            self._navigate_to_landing_page()

            # Phase 1: collect all postback targets across pages and save list for inspection
            all_notices = self._collect_all_notice_targets(max_notices)
            self._save_notice_list(all_notices)

            # Phase 2: download each notice, navigating to the correct page first
            current_page = None
            for downloaded_count, notice in enumerate(all_notices):
                try:
                    logger.info(f"Downloading notice {downloaded_count + 1}/{len(all_notices)}: {notice['subject']} (page {notice['page_num']})")
                    if notice["page_num"] != current_page:
                        self._navigate_to_page(notice["page_num"])
                        current_page = notice["page_num"]
                    self._trigger_postback(notice["postback_target"])
                    html_path = self._save_notice_html(notice["notice_id"], notice["notice_type"])
                    impact_report_path = None
                    if "OUTAGE IMPACT REPORT" in notice["subject"].upper():
                        impact_report_path = self._download_impact_report(notice["notice_id"])
                    self._save_metadata(notice, html_path, impact_report_path)
                    # After postback the browser is on the detail page; navigate back to correct page for next notice
                    current_page = None
                except Exception as e:
                    logger.error(f"Failed to download notice '{notice['subject']}': {e}")
                    current_page = None
                    continue

            self._save_metadata_file()
            logger.info(f"Successfully downloaded {len(self.metadata)} notices")

        finally:
            self._quit_driver()

    def fetch_single_notice(self, subject_index: int) -> Optional[str]:
        """Fetch a single notice by its index in the filtered list."""
        try:
            self._init_driver()
            self._navigate_to_landing_page()
            self._wait_for_notices_table()

            notices = self._get_notice_subjects()

            if subject_index >= len(notices):
                logger.error(f"Notice index {subject_index} out of range (only {len(notices)} notices found)")
                return None

            notice = notices[subject_index]
            logger.info(f"Processing notice {subject_index}: {notice['subject']}")

            self._trigger_postback(notice["postback_target"])
            html_path = self._save_notice_html(notice["notice_id"], notice["notice_type"])
            self._save_metadata(notice, html_path)
            self._save_metadata_file()

            logger.info(f"Successfully downloaded notice {subject_index}")
            return html_path

        except Exception as e:
            logger.error(f"Failed to fetch notice: {e}")
            return None
        finally:
            self._quit_driver()


if __name__ == "__main__":
    scraper = NoticeScraper(output_dir="notices")
    scraper.fetch_notices(max_notices=3)
