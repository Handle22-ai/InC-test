"""
Main entry point for the trading signal extraction pipeline.
"""
import argparse
import logging
from pathlib import Path
from notice_scraper import NoticeScraper
from notice_parser import NoticeProcessor
from database import init_db, enable_fk

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Extract trading signals from gas pipeline notices"
    )
    parser.add_argument(
        "action",
        choices=["fetch", "parse", "fetch-and-parse"],
        help="Action to perform"
    )
    parser.add_argument(
        "--output-dir",
        default="notices",
        help="Directory to store downloaded notices (default: notices)"
    )
    parser.add_argument(
        "--notice-type",
        choices=["Critical", "Non-Critical", "Planned Service Outage"],
        default="Critical",
        help="Type of notices to fetch (default: Critical)"
    )
    parser.add_argument(
        "--max-notices",
        type=int,
        default=None,
        help="Maximum number of notices to fetch (default: all)"
    )
    parser.add_argument(
        "--signal-output",
        default="trading_signals.json",
        help="Output file for trading signals report (default: trading_signals.json)"
    )
    parser.add_argument(
        "--db",
        default="notices.db",
        help="SQLite database file (default: notices.db in --output-dir)"
    )

    args = parser.parse_args()

    try:
        if args.action == "fetch":
            logger.info(f"Starting notice fetch ({args.notice_type})...")
            scraper = NoticeScraper(output_dir=args.output_dir, notice_type=args.notice_type)
            scraper.fetch_notices(max_notices=args.max_notices)
            logger.info(f"Fetched {len(scraper.metadata)} notices")

        elif args.action == "parse":
            logger.info("Starting notice parsing...")
            if not Path(args.output_dir).exists():
                logger.error(f"Output directory {args.output_dir} does not exist")
                return 1

            db_path = str(Path(args.output_dir) / args.db)
            conn = init_db(db_path)

            processor = NoticeProcessor(notices_dir=args.output_dir)
            results = processor.process_all_notices(db_conn=conn)
            enable_fk(conn)
            processor.save_signals_report(results, args.signal_output)
            conn.close()
            logger.info(f"Processed {len(results)} notices → {db_path}")

        elif args.action == "fetch-and-parse":
            logger.info(f"Starting full pipeline ({args.notice_type})...")
            scraper = NoticeScraper(output_dir=args.output_dir, notice_type=args.notice_type)
            scraper.fetch_notices(max_notices=args.max_notices)
            logger.info(f"Fetched {len(scraper.metadata)} notices")

            db_path = str(Path(args.output_dir) / args.db)
            conn = init_db(db_path)

            processor = NoticeProcessor(notices_dir=args.output_dir)
            results = processor.process_all_notices(db_conn=conn)
            enable_fk(conn)
            processor.save_signals_report(results, args.signal_output)
            conn.close()
            logger.info(f"Processed {len(results)} notices → {db_path}")
            logger.info("Pipeline completed successfully")

        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
