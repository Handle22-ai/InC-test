# Audit truth and quantity-evidence follow-up

Status: unapproved-proposal. This note carries observations, not new authority.

The audit of 427c7d7 exposed false successful gate exits, gate-side policy writes, MODEL_FAILUREs credited as TP/TN, and unobserved/deferred checks shown PASS. See evidence/audit-truth/20260928/report.md for retained controls and dispositions. Classify execution status before scoring behavior; generated drift checking must be read-only; report missing checks as UNKNOWN. D prose is unchecked separately from named code-owned boundary checks.

A completed comparison must bind to OBS-003 coverage before aggregation. The first correction still reported this requirement as unobserved while Gate 3 had a real comparison; the follow-up regression test checks both the observation count and the matching gate/coverage status.

The fresh quantity-maintenance session reproduced numeric source restrictions omitted from normalized quantities. Original rows survive in raw trace, but the omission lacks a row-specific retained explanation. Its proposed repair preserves raw value/unit and explains the omission; it does not infer absolute-volume meaning or convert MMcf/d to Dth. Automatic approval review blocked the component edit by citing the earlier instruction to preserve generated behavior while recording a review. Do not apply a proposed patch without resolving that approval block. The fresh-session evidence records its final disposition.

Open domain questions remain force-majeure extraction failure, WITHDRAWN semantics, Louisiana/Henry Hub/LNG relevance, absolute-volume basis/conversion, and abstention cost. TZ-NGPL-002 remains unchanged. Unknowns are not authorization, and this note cannot promote itself to policy or human review.
