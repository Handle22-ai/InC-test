"""
Test _extract_header() and _extract_body() on one notice of each type.
Results are saved to tests/output/ for manual review.

Usage:
  python tests/test_extraction.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bs4 import BeautifulSoup
from notice_parser import _extract_header, _extract_body

TEST_NOTICES = [
    {"notice_id": "46839", "notice_type": "FORCE MAJEURE",
     "html_file": "notices/46839_FORCE MAJEURE.html"},
    {"notice_id": "46614", "notice_type": "MAINTENANCE",
     "html_file": "notices/46614_MAINTENANCE.html"},
    {"notice_id": "46448", "notice_type": "CAPACITY CONSTRAINT",
     "html_file": "notices/46448_CAPACITY CONSTRAINT.html"},
    {"notice_id": "46527", "notice_type": "OPERATIONAL ALERT",
     "html_file": "notices/46527_OPERATIONAL ALERT.html"},
    {"notice_id": "46725", "notice_type": "OPERATIONAL FLOW ORDER",
     "html_file": "notices/46725_OPERATIONAL FLOW ORDER.html"},
]

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def run_test(entry: dict) -> dict:
    notice_id = entry["notice_id"]
    notice_type = entry["notice_type"]
    html_file = Path(__file__).parent.parent / entry["html_file"]

    print(f"\n{'='*60}")
    print(f"Notice {notice_id} — {notice_type}")
    print('='*60)

    assert html_file.exists(), f"HTML file not found: {html_file}"

    soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser")

    header = _extract_header(soup)
    print("\n[HEADER]")
    for k, v in header.items():
        print(f"  {k:15s}: {repr(v)}")

    body = _extract_body(soup)
    word_count = len(body.split())
    print(f"\n[BODY]  ({word_count} words)")
    print("-" * 40)
    print(body[:1500])
    if len(body) > 1500:
        print(f"  ... [{len(body) - 1500} more chars]")

    result = {
        "notice_id": notice_id,
        "notice_type": notice_type,
        "html_file": entry["html_file"],
        "header": header,
        "body_word_count": word_count,
        "body": body,
    }
    out_path = OUTPUT_DIR / f"extraction_{notice_id}.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\n  Saved → {out_path}")
    return result


def main():
    results = []
    errors = []

    for entry in TEST_NOTICES:
        try:
            results.append(run_test(entry))
        except Exception as e:
            errors.append({"notice_id": entry["notice_id"], "error": str(e)})
            print(f"  ERROR: {e}")

    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    for r in results:
        missing = [k for k, v in r["header"].items() if not v and k != "prior_notice_id"]
        print(
            f"  {r['notice_id']:6s}  {r['notice_type']:30s}  "
            f"words={r['body_word_count']:4d}  "
            f"missing={missing if missing else 'none'}"
        )
    for e in errors:
        print(f"  {e['notice_id']:6s}  ERROR: {e['error']}")

    summary_path = OUTPUT_DIR / "extraction_summary.json"
    summary_path.write_text(
        json.dumps({"results": results, "errors": errors}, indent=2, ensure_ascii=False)
    )
    print(f"\nFull summary → {summary_path}")


if __name__ == "__main__":
    main()
