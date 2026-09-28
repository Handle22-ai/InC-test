"""
SQLite database layer for the trading signal extractor.
Schema: notices (1) --< notice_locations (many)
        notices (1) --< notice_restrictions (many)
        notices.prior_notice_id --> notices.notice_id (supersede chain)
"""
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DDL = """
CREATE TABLE IF NOT EXISTS notices (
    notice_id           INTEGER PRIMARY KEY,
    tsp_name            TEXT    NOT NULL,
    pipeline_code       TEXT    NOT NULL,
    is_critical         BOOLEAN NOT NULL DEFAULT 0,
    notice_type         TEXT    NOT NULL,
    notice_subtype      TEXT,
    effective_datetime  DATETIME NOT NULL,
    end_datetime        DATETIME,
    post_datetime       DATETIME NOT NULL,
    response_required   BOOLEAN,
    response_due_date   DATE,
    status              TEXT    NOT NULL DEFAULT 'INITIATE',
    prior_notice_id     INTEGER REFERENCES notices(notice_id),
    subject             TEXT    NOT NULL,
    body_text           TEXT    NOT NULL,
    outage_report_ref   TEXT,
    tariff_section      TEXT,
    information_only    BOOLEAN NOT NULL DEFAULT 0,
    is_signal           BOOLEAN,
    confidence_score    REAL,
    validity_flags      TEXT,
    source_url          TEXT,
    scraped_at          DATETIME NOT NULL,
    html_file           TEXT
);

CREATE TABLE IF NOT EXISTS notice_locations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    location_index      INTEGER NOT NULL,
    notice_id           INTEGER NOT NULL REFERENCES notices(notice_id),
    loc_code            TEXT,
    loc_name            TEXT,
    segment             TEXT,
    compressor_station  TEXT,
    zone                TEXT,
    system              TEXT
);

CREATE TABLE IF NOT EXISTS notice_restrictions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    location_index      INTEGER NOT NULL,
    notice_id           INTEGER NOT NULL REFERENCES notices(notice_id),
    service_type        TEXT    NOT NULL,
    restriction_type    TEXT    NOT NULL,
    restriction_value   REAL,
    restriction_unit    TEXT,
    flow_direction      TEXT,
    start_datetime      DATETIME,
    end_datetime        DATETIME
);

CREATE INDEX IF NOT EXISTS idx_notices_type       ON notices(notice_type);
CREATE INDEX IF NOT EXISTS idx_notices_effective  ON notices(effective_datetime);
CREATE INDEX IF NOT EXISTS idx_notices_signal     ON notices(is_signal);
CREATE INDEX IF NOT EXISTS idx_notices_status     ON notices(status);
CREATE INDEX IF NOT EXISTS idx_locs_notice        ON notice_locations(notice_id);
CREATE INDEX IF NOT EXISTS idx_locs_loc_code      ON notice_locations(loc_code);
CREATE INDEX IF NOT EXISTS idx_locs_zone          ON notice_locations(zone);
CREATE INDEX IF NOT EXISTS idx_restr_notice       ON notice_restrictions(notice_id);
CREATE INDEX IF NOT EXISTS idx_restr_loc_index    ON notice_restrictions(notice_id, location_index);
"""


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    # FK enforcement is toggled off during bulk inserts (notices may reference
    # prior_notice_id for rows not yet inserted) and re-enabled afterward.
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.executescript(DDL)
    conn.commit()
    logger.info(f"Database initialized at {db_path}")
    return conn


def enable_fk(conn: sqlite3.Connection) -> None:
    """Call after all bulk inserts to enforce foreign-key integrity."""
    conn.execute("PRAGMA foreign_keys = ON")


def insert_notice(
    conn: sqlite3.Connection,
    notice: Dict,
    locations: List[Dict],
    restrictions: List[Dict],
) -> bool:
    """
    Upsert a notice and its child rows. Returns True on success.
    Existing notice_id rows are replaced; child rows for that notice_id
    are deleted and re-inserted so re-parsing is idempotent.
    """
    try:
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO notices (
                    notice_id, tsp_name, pipeline_code, is_critical,
                    notice_type, notice_subtype,
                    effective_datetime, end_datetime, post_datetime,
                    response_required, response_due_date,
                    status, prior_notice_id, subject, body_text,
                    outage_report_ref, tariff_section,
                    information_only, is_signal, confidence_score, validity_flags,
                    source_url, scraped_at, html_file
                ) VALUES (
                    :notice_id, :tsp_name, :pipeline_code, :is_critical,
                    :notice_type, :notice_subtype,
                    :effective_datetime, :end_datetime, :post_datetime,
                    :response_required, :response_due_date,
                    :status, :prior_notice_id, :subject, :body_text,
                    :outage_report_ref, :tariff_section,
                    :information_only, :is_signal, :confidence_score, :validity_flags,
                    :source_url, :scraped_at, :html_file
                )
                """,
                notice,
            )

            if locations:
                conn.executemany(
                    """
                    INSERT INTO notice_locations (
                        location_index, notice_id, loc_code, loc_name, segment,
                        compressor_station, zone, system
                    ) VALUES (
                        :location_index, :notice_id, :loc_code, :loc_name, :segment,
                        :compressor_station, :zone, :system
                    )
                    """,
                    locations,
                )

            if restrictions:
                conn.executemany(
                    """
                    INSERT INTO notice_restrictions (
                        location_index, notice_id, service_type, restriction_type,
                        restriction_value, restriction_unit,
                        flow_direction, start_datetime, end_datetime
                    ) VALUES (
                        :location_index, :notice_id, :service_type, :restriction_type,
                        :restriction_value, :restriction_unit,
                        :flow_direction, :start_datetime, :end_datetime
                    )
                    """,
                    restrictions,
                )
        return True
    except sqlite3.Error as e:
        logger.error(f"DB insert failed for notice {notice.get('notice_id')}: {e}")
        return False


def get_notice_chain(conn: sqlite3.Connection, notice_id: int) -> List[Dict]:
    """Traverse prior_notice_id links and return the full supersede chain, oldest first."""
    rows = conn.execute(
        """
        WITH RECURSIVE chain(notice_id, subject, status, prior_notice_id, depth) AS (
            SELECT notice_id, subject, status, prior_notice_id, 1
            FROM notices WHERE notice_id = ?
            UNION ALL
            SELECT n.notice_id, n.subject, n.status, n.prior_notice_id, c.depth + 1
            FROM notices n JOIN chain c ON n.notice_id = c.prior_notice_id
        )
        SELECT notice_id, subject, status, prior_notice_id, depth
        FROM chain ORDER BY depth DESC
        """,
        (notice_id,),
    ).fetchall()
    cols = ["notice_id", "subject", "status", "prior_notice_id", "depth"]
    return [dict(zip(cols, row)) for row in rows]


def get_active_signals(conn: sqlite3.Connection) -> List[Dict]:
    """Return non-superseded signals that haven't ended yet."""
    rows = conn.execute(
        """
        SELECT notice_id, notice_type, notice_subtype, subject,
               effective_datetime, end_datetime, confidence_score, validity_flags
        FROM notices
        WHERE is_signal = 1
          AND status != 'SUPERSEDE'
          AND (end_datetime IS NULL OR end_datetime > datetime('now'))
        ORDER BY effective_datetime DESC
        """
    ).fetchall()
    cols = [
        "notice_id", "notice_type", "notice_subtype", "subject",
        "effective_datetime", "end_datetime", "confidence_score", "validity_flags",
    ]
    return [dict(zip(cols, row)) for row in rows]
