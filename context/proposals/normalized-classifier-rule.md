# Bounded classifier proposal — approved disposition

Status: **APPROVED prospectively under [ADR 007](../decisions/007-br-firm-proposal-classification.md)**. The wording below is preserved from the original proposal. The subsequent owner message is a new decision, not an earlier approval; local hashes do not authenticate it.

Original proposed exact wording:

> For an accepted normalized NGPL notice with a current or future operational restriction, explicit unavailability of primary or secondary firm service, or explicit primary-firm-only allocation, supports SIGNAL_CANDIDATE even when curtailed volume is absent. Routine/administrative content with no operational restriction is NON_SIGNAL. Partial restrictions without enough evidence to establish meaningful flow or price impact remain UNRESOLVED; no numeric materiality cutoff is inferred. Unusable/contradictory evidence and unresolved required history take precedence. This classification never authorizes a recommendation by itself; D1–D6 authorization remains required.

Basis: challenge p. 5, D5–D6, supplied capacity-constraint calibration examples. Consequence: a precise but deliberately narrow positive classifier proposal rule; no new scoring cutoff or runtime authorization. At the original review, active derivation skipped BR-FIRM and the prospective positive fixtures were blocked. Those frozen records remain unchanged. The new owner decision activates BR-FIRM prospectively without weakening the positive expectations; a separate builder has not run. ADR 008 corrects the unauthorized interpretation of “remains REVIEW_REQUIRED”: BR-SEMANTICS retains its prior ERROR disposition.
