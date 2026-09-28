"""
Validator test harness.

Loads pre-computed LLM extraction results from tests/output/llm_parse_*.json,
runs validate_notice() on each, and writes results to tests/output/validation_results.json.

Usage:
  # First generate LLM parse files:
  python tests/test_llm_parser.py

  # Then run validation:
  python tests/test_validator.py
"""
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from notice_validator import validate_notice

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent / "output"


def run_tests():
    input_files = sorted(OUTPUT_DIR.glob("llm_parse_*.json"))
    if not input_files:
        logger.error(f"No llm_parse_*.json files found in {OUTPUT_DIR}")
        logger.error("Run tests/test_llm_parser.py first.")
        return

    results = []

    for path in input_files:
        data = json.loads(path.read_text())
        notice_id = data["notice_id"]
        notice_type = data["notice_type"]
        header = data["header"]
        body = data["body"]
        locations = data["locations"]
        restrictions = data["restrictions"]
        information_only = data.get("information_only", False)
        status = header.get("status", "INITIATE")

        is_signal, confidence, flags = validate_notice(
            notice_type, status, header, body, locations, restrictions,
            prior_notice_row=None, information_only=information_only,
        )

        result = {
            "notice_id": notice_id,
            "notice_type": notice_type,
            "status": status,
            "information_only": information_only,
            "locations_count": len(locations),
            "restrictions_count": len(restrictions),
            "is_signal": is_signal,
            "confidence_score": confidence,
            "validity_flags": flags,
        }
        results.append(result)

        logger.info(
            f"Notice {notice_id:6}  [{notice_type:25}]  "
            f"is_signal={str(is_signal):5}  confidence={confidence:.2f}  "
            f"flags={[f.split(':')[0] for f in flags]}"
        )

    summary = {
        "total": len(results),
        "signals": sum(1 for r in results if r["is_signal"]),
        "non_signals": sum(1 for r in results if not r["is_signal"]),
    }

    out_path = OUTPUT_DIR / "validation_results.json"
    out_path.write_text(json.dumps({"summary": summary, "notices": results}, indent=2))
    logger.info(f"\nResults → {out_path}")
    logger.info(f"Summary: {summary['total']} notices | {summary['signals']} signals | {summary['non_signals']} non-signals")


if __name__ == "__main__":
    run_tests()
