"""
Integration tests for the notice scraper and parser.

Usage:
  python tests/test_scraper.py scraper [max_notices] [notice_type]
  python tests/test_scraper.py parser
  python tests/test_scraper.py all [max_notices] [notice_type]

Examples:
  python tests/test_scraper.py scraper 2 Critical
  python tests/test_scraper.py scraper 5 "Non-Critical"
  python tests/test_scraper.py parser
  python tests/test_scraper.py all 3 Critical
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from notice_scraper import NoticeScraper
from notice_parser import NoticeProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TEST_OUTPUT_DIR = Path(__file__).parent / "output"
TEST_NOTICES_DIR = TEST_OUTPUT_DIR / "notices"


def test_scraper(max_notices: int = 1, notice_type: str = "Critical") -> bool:
    try:
        logger.info(f"Testing scraper ({notice_type}, max={max_notices})...")
        TEST_NOTICES_DIR.mkdir(parents=True, exist_ok=True)
        scraper = NoticeScraper(output_dir=str(TEST_NOTICES_DIR), notice_type=notice_type)
        scraper.fetch_notices(max_notices=max_notices)
        logger.info(f"Scraper test passed. Downloaded {len(scraper.metadata)} notices.")
        return True
    except Exception as e:
        logger.error(f"Scraper test failed: {e}")
        return False


def test_parser() -> bool:
    try:
        logger.info("Testing parser...")
        if not TEST_NOTICES_DIR.exists():
            logger.error(f"Test notices dir not found. Run scraper test first.")
            return False

        processor = NoticeProcessor(notices_dir=str(TEST_NOTICES_DIR))
        results = processor.process_all_notices()
        signal_count = sum(1 for r in results if r["notice"]["is_signal"])
        logger.info(f"Processed {len(results)} notices, {signal_count} signals.")

        processor.save_signals_report(results, "test_signals.json")
        logger.info("Parser test passed.")
        return True
    except Exception as e:
        logger.error(f"Parser test failed: {e}")
        return False


def show_usage():
    print(__doc__)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_usage()
        sys.exit(0)

    mode = sys.argv[1]
    success = False

    if mode == "scraper":
        max_notices = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        notice_type = sys.argv[3] if len(sys.argv) > 3 else "Critical"
        success = test_scraper(max_notices=max_notices, notice_type=notice_type)
    elif mode == "parser":
        success = test_parser()
    elif mode == "all":
        max_notices = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        notice_type = sys.argv[3] if len(sys.argv) > 3 else "Critical"
        success = test_scraper(max_notices, notice_type) and test_parser()
    else:
        logger.error(f"Unknown command: {mode}")
        show_usage()
        sys.exit(1)

    sys.exit(0 if success else 1)
