"""
Batch evaluation script.
Runs llm_extract_notice + validate_notice on all HTML notices in evaluation/notices/.
Processes notices in notice_id order so prior notices are in the DB when
TERMINATE/SUPERSEDE notices are evaluated.

Saves:
  evaluation/results/parse/<notice_id>_parse.json        — raw extraction output
  evaluation/results/validation/<notice_id>_validation.json — validation result
  evaluation/results/summary.json                        — all notices in one table
  evaluation/results/eval.db                             — SQLite DB with all notices
"""
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))

from notice_parser import _extract_header, _extract_body, _parse_dt
from llm_utils import llm_extract_notice
from notice_validator import validate_notice
from database import init_db, insert_notice

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stdout,
)

NOTICES_DIR = Path(__file__).parent / "notices"
RESULTS_DIR = Path(__file__).parent / "results"
PARSE_DIR   = RESULTS_DIR / "parse"
VAL_DIR     = RESULTS_DIR / "validation"
DB_PATH     = str(RESULTS_DIR / "eval.db")

# Hand-labeled ground truth (see calibration.md)
LABELS = {
    46507: True,  46528: False, 46604: False, 46615: True,  46624: True,
    46725: False, 46728: False, 46732: True,  46775: False, 46795: False,
    46805: True,  46818: False, 46864: True,  46881: True,
}

for d in (PARSE_DIR, VAL_DIR):
    d.mkdir(parents=True, exist_ok=True)


def _fetch_prior(conn, prior_id):
    if prior_id is None or conn is None:
        return None
    row = conn.execute(
        "SELECT notice_id, is_signal, confidence_score, notice_type, subject, body_text "
        "FROM notices WHERE notice_id = ?",
        (prior_id,),
    ).fetchone()
    if row is None:
        return None
    return dict(zip(
        ["notice_id", "is_signal", "confidence_score", "notice_type", "subject", "body_text"],
        row,
    ))


def run_one(html_path: Path, conn) -> dict:
    name = html_path.stem
    notice_id_str = name.split("_")[0]
    try:
        notice_id = int(notice_id_str)
    except ValueError:
        notice_id = 0

    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    header = _extract_header(soup)
    body   = _extract_body(soup)

    effective_dt = _parse_dt(header.get("notice_effective_date", ""))
    end_dt       = _parse_dt(header.get("notice_end_date", ""))
    post_dt      = _parse_dt(header.get("post_date", "")) or datetime.utcnow().isoformat()
    status_raw   = header.get("status", "INITIATE").strip().upper() or "INITIATE"
    notice_type  = (header.get("type1") or name.split("_", 1)[-1].rsplit(".", 1)[0]).upper()
    notice_subtype = header.get("type2", "").strip().upper() or None

    prior_raw = header.get("prior_notice_id", "").strip()
    try:
        prior_id = int(re.sub(r"\D", "", prior_raw)) if prior_raw else None
    except ValueError:
        prior_id = None

    # Agent 1: extraction
    llm_result = llm_extract_notice(header, body, notice_id, effective_dt, end_dt)
    if llm_result is not None:
        locations, restrictions, information_only = llm_result
        provenance = "llm_extraction"
    else:
        locations, restrictions, information_only = [], [], False
        provenance = "llm_failed"

    # Save parse output
    parse_out = {
        "notice_id":        notice_id,
        "notice_type":      notice_type,
        "html_file":        str(html_path),
        "header":           header,
        "body":             body,
        "information_only": information_only,
        "locations":        locations,
        "restrictions":     restrictions,
        "provenance":       provenance,
    }
    (PARSE_DIR / f"{notice_id}_parse.json").write_text(
        json.dumps(parse_out, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Agent 2: validation (with prior notice from DB if available)
    prior_notice_row = _fetch_prior(conn, prior_id)
    is_signal, confidence, flags = validate_notice(
        notice_type, status_raw, header, body, locations, restrictions,
        prior_notice_row=prior_notice_row,
        information_only=information_only,
    )
    flags.append(provenance)

    val_out = {
        "notice_id":        notice_id,
        "notice_type":      notice_type,
        "status":           status_raw,
        "prior_notice_id":  prior_id,
        "information_only": information_only,
        "is_signal":        is_signal,
        "confidence_score": confidence,
        "validity_flags":   flags,
    }
    (VAL_DIR / f"{notice_id}_validation.json").write_text(
        json.dumps(val_out, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Write to DB so subsequent notices can look up this one as prior
    notice_row = {
        "notice_id":          notice_id,
        "tsp_name":           header.get("tsp", "NATURAL GAS PIPELINE CO.").strip(),
        "pipeline_code":      "NGPL",
        "is_critical":        1 if header.get("critical", "").upper() == "Y" else 0,
        "notice_type":        notice_type,
        "notice_subtype":     notice_subtype,
        "effective_datetime": effective_dt or post_dt,
        "end_datetime":       end_dt,
        "post_datetime":      post_dt,
        "response_required":  1 if header.get("req_rsp", "").strip() not in ("", "0") else 0,
        "response_due_date":  _parse_dt(header.get("rsp_date", "").strip()),
        "status":             status_raw,
        "prior_notice_id":    prior_id,
        "subject":            header.get("subject", "").strip(),
        "body_text":          body,
        "outage_report_ref":  None,
        "tariff_section":     None,
        "information_only":   1 if information_only else 0,
        "is_signal":          1 if is_signal else 0,
        "confidence_score":   confidence,
        "validity_flags":     json.dumps(flags),
        "source_url":         None,
        "scraped_at":         datetime.utcnow().isoformat(),
        "html_file":          str(html_path),
    }
    insert_notice(conn, notice_row, locations, restrictions)

    return val_out


def main():
    # Delete old DB so schema is always fresh
    db_file = Path(DB_PATH)
    if db_file.exists():
        db_file.unlink()
    conn = init_db(DB_PATH)

    # Sort by notice_id so prior notices are always inserted first
    html_files = sorted(
        NOTICES_DIR.glob("*.html"),
        key=lambda p: int(p.stem.split("_")[0]) if p.stem.split("_")[0].isdigit() else 0
    )
    print(f"Found {len(html_files)} HTML notices\n")

    summary = []
    for path in html_files:
        print(f"Processing {path.name} ...", end=" ", flush=True)
        try:
            result = run_one(path, conn)
            signal_str = "SIGNAL" if result["is_signal"] else "no-signal"
            print(f"{signal_str}  conf={result['confidence_score']:.2f}")
            summary.append(result)
        except Exception as e:
            print(f"ERROR: {e}")
            summary.append({"notice_id": path.stem, "error": str(e)})

    conn.close()

    (RESULTS_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\n{'='*60}")
    print(f"{'Notice ID':<12} {'Type':<30} {'Signal':<10} {'Conf'}")
    print("-" * 60)
    for r in summary:
        if "error" in r:
            print(f"{str(r['notice_id']):<12} ERROR: {r['error']}")
        else:
            print(
                f"{r['notice_id']:<12} {r['notice_type']:<30} "
                f"{'YES' if r['is_signal'] else 'no':<10} {r['confidence_score']:.2f}"
            )

    signals = [r for r in summary if r.get("is_signal")]
    print(f"\nSignals: {len(signals)} / {len(summary)}")

    scored = [r for r in summary if "error" not in r and r["notice_id"] in LABELS]
    correct = sum(1 for r in scored if bool(r["is_signal"]) == LABELS[r["notice_id"]])
    if scored:
        print(f"Classification accuracy: {correct}/{len(scored)} ({100.0 * correct / len(scored):.1f}%)")
    print(f"\nResults saved to {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
