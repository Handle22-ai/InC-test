"""
Test llm_extract_notice() on a single notice with full LLM input/output logging.
Edit NOTICE below to target a different notice.

Usage:
  python tests/test_llm_parser.py
"""
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bs4 import BeautifulSoup
from notice_parser import _extract_header, _extract_body, _parse_dt
from llm_utils import llm_extract_notice

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stdout,
)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

NOTICE = {
    "notice_id":   "46818",
    "notice_type": "MAINTENANCE",
    "html_file":   "notices/46818_MAINTENANCE.html",
}


def main():
    root = Path(__file__).parent.parent
    html_file = root / NOTICE["html_file"]
    notice_id = int(NOTICE["notice_id"])

    print(f"\n{'='*60}")
    print(f"Testing LLM parser on notice {notice_id} [{NOTICE['notice_type']}]")
    print("=" * 60)

    assert html_file.exists(), f"HTML file not found: {html_file}"

    soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser")
    header = _extract_header(soup)
    body = _extract_body(soup)

    effective_dt = _parse_dt(header.get("effective", ""))
    end_dt = _parse_dt(header.get("end", ""))

    print("\n[HEADER]")
    for k, v in header.items():
        print(f"  {k:15s}: {repr(v)}")

    print(f"\n[BODY]  ({len(body.split())} words)")
    print("-" * 40)
    print(body[:2000])
    if len(body) > 2000:
        print(f"  ... [{len(body) - 2000} more chars]")

    print(f"\n{'='*60}")
    print("Calling LLM...")
    print("=" * 60)

    result = llm_extract_notice(header, body, notice_id, effective_dt, end_dt)

    print(f"\n{'='*60}")
    print("STRUCTURED OUTPUT")
    print("=" * 60)

    if result is None:
        print("LLM returned None — check logs above.")
        return

    locations, restrictions, information_only = result

    print(f"\ninformation_only: {information_only}")
    print(f"\nLocations ({len(locations)}):")
    for i, loc in enumerate(locations, 1):
        print(f"  [{i}] {json.dumps({k: v for k, v in loc.items() if k != 'notice_id'})}")

    print(f"\nRestrictions ({len(restrictions)}):")
    for i, r in enumerate(restrictions, 1):
        print(f"  [{i}] {json.dumps({k: v for k, v in r.items() if k not in ('notice_id', 'start_datetime', 'end_datetime')})}")

    out = {
        "notice_id": notice_id,
        "notice_type": NOTICE["notice_type"],
        "html_file": NOTICE["html_file"],
        "header": header,
        "body": body,
        "information_only": information_only,
        "locations": locations,
        "restrictions": restrictions,
    }
    out_path = OUTPUT_DIR / f"llm_parse_{notice_id}.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nSaved → {out_path}")


if __name__ == "__main__":
    main()
