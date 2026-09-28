# Generated input contract

Source: spec.md SHA256 a5bb4e2231092d6da4928c346d8d8f3722c8d44299a721de5c58d4be35249e76

| ID | Source field | Type | Missing | Malformed | Supplier |
|---|---|---|---|---|---|
| INPUT-SOURCE-001 | header.tsp | text | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-002 | header.critical | text | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-003 | header.type1 | text | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-004 | header.type2 | text | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-005 | header.notice_effective_date | timestamp | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-006 | header.notice_end_date | timestamp | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-007 | header.post_date | timestamp | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-008 | header.notice_id | identifier | ERROR | ERROR | source_parser |
| INPUT-SOURCE-009 | header.req_rsp | text | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-010 | header.rsp_date | timestamp | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-011 | header.status | text | ERROR | ERROR | source_parser |
| INPUT-SOURCE-012 | header.prior_notice_id | identifier | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-013 | header.subject | text | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-014 | metadata.notice_id | identifier | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-015 | metadata.notice_type | text | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-016 | metadata.subject | text | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-017 | metadata.download_date | timestamp | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-018 | metadata.source_url | text | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-019 | metadata.html_file | text | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-020 | body | text | ERROR | ERROR | source_parser |
| INPUT-SOURCE-021 | notice.notice_id | integer | ERROR | ERROR | source_parser |
| INPUT-SOURCE-022 | notice.prior_notice_id | integer | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-023 | notice.status | text | ERROR | ERROR | source_parser |
| INPUT-SOURCE-024 | notice.notice_type | text | ERROR | ERROR | source_parser |
| INPUT-SOURCE-025 | notice.information_only | flag | UNKNOWN | ERROR | model |
| INPUT-SOURCE-026 | notice.body_text | text | ERROR | ERROR | source_parser |
| INPUT-SOURCE-027 | notice.effective_datetime | timestamp | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-028 | notice.end_datetime | timestamp | UNKNOWN | ERROR | source_parser |
| INPUT-SOURCE-029 | locations | rows | UNKNOWN | ERROR | model |
| INPUT-SOURCE-030 | restrictions | rows | UNKNOWN | ERROR | model |
| INPUT-SOURCE-031 | locations[].loc_code | text_or_integer | UNKNOWN | ERROR | model |
| INPUT-SOURCE-032 | locations[].segment | text_or_integer | UNKNOWN | ERROR | model |
| INPUT-SOURCE-033 | locations[].compressor_station | text_or_integer | UNKNOWN | ERROR | model |
| INPUT-SOURCE-034 | locations[].zone | text_or_integer | UNKNOWN | ERROR | model |
| INPUT-SOURCE-035 | locations[].system | text_or_integer | UNKNOWN | ERROR | model |
| INPUT-SOURCE-036 | restrictions[].service_type | text | UNKNOWN | ERROR | model |
| INPUT-SOURCE-037 | restrictions[].restriction_type | text | UNKNOWN | ERROR | model |
| INPUT-SOURCE-038 | restrictions[].restriction_value | number | UNKNOWN | ERROR | model |
| INPUT-SOURCE-039 | restrictions[].restriction_unit | text | UNKNOWN | ERROR | model |
| INPUT-SOURCE-040 | restrictions[].status | text | UNKNOWN | ERROR | model |
| INPUT-SOURCE-041 | restrictions[].location_index | integer | UNKNOWN | ERROR | model |
| INPUT-SOURCE-042 | restrictions[].start_datetime | timestamp | UNKNOWN | ERROR | model |
| INPUT-SOURCE-043 | restrictions[].end_datetime | timestamp | UNKNOWN | ERROR | model |
| INPUT-SOURCE-044 | semantic.extraction_usable | boolean | ERROR | ERROR | retained_evidence |
| INPUT-SOURCE-045 | semantic.execution_error | text | UNKNOWN | ERROR | retained_evidence |
| INPUT-SOURCE-046 | semantic.helpers | helper_pairs | UNKNOWN | ERROR | retained_evidence |
| INPUT-SOURCE-047 | semantic.source_media_type | text | UNKNOWN | ERROR | retained_evidence |
