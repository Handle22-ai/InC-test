# Rules generated from spec.md

Spec SHA256: `a5bb4e2231092d6da4928c346d8d8f3722c8d44299a721de5c58d4be35249e76`

Source-grounded normalized facts -> candidate only, including when source timezone is UNKNOWN. Unknown timezone blocks automatic current/future actionability and recommendation authorization, requiring REVIEW_REQUIRED. No timezone is inferred.

| Rule | Format | Oracle answer | Conflict | History | Operational change | Information-only | Restriction | Service class | Restriction current | Action |
|---|---|---|---|---|---|---|---|---|---|---|
| BR-FORMAT | UNSUPPORTED | ANY | ANY | ANY | ANY | ANY | ANY | ANY | ANY | UNSUPPORTED_FORMAT |
| BR-SEMANTICS | ANY | UNUSABLE | ANY | ANY | ANY | ANY | ANY | ANY | ANY | UNUSABLE_SEMANTICS |
| BR-CONTRADICTION | ANY | ANY | YES | ANY | ANY | ANY | ANY | ANY | ANY | CONTRADICTORY_EVIDENCE |
| BR-HISTORY | ANY | ANY | ANY | GAP | ANY | ANY | ANY | ANY | ANY | MISSING_HISTORY |
| BR-UNCHANGED | ANY | ANY | ANY | ANY | UNCHANGED | ANY | ANY | ANY | ANY | UNCHANGED_REVISION |
| BR-ROUTINE | ANY | ANY | ANY | ANY | ANY | YES | NONE | ANY | ANY | NO_OPERATIONAL_RESTRICTION |
| BR-HISTORICAL | ANY | ANY | ANY | ANY | ANY | ANY | ANY | FIRM_DISRUPTION | ENDED | HISTORICAL_ONLY |
| BR-FIRM | ANY | ANY | ANY | ANY | ANY | ANY | ANY | FIRM_DISRUPTION | ANY | FIRM_CANDIDATE |
| BR-UNRESOLVED | ANY | ANY | ANY | ANY | ANY | ANY | ANY | ANY | ANY | UNRESOLVED |

Precedence: BR-FORMAT > BR-SEMANTICS > BR-CONTRADICTION > BR-HISTORY > BR-UNCHANGED > BR-ROUTINE > BR-HISTORICAL > BR-FIRM > BR-UNRESOLVED

No generated consequence is independent evaluation or approval.
