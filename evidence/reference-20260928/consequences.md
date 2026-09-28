## Generated consequences of this spec

Captured cases: **46** (two 23-case captures; 14 labels per capture). No abstention is a correct negative.

| Rule | Matches / cases | Wins / cases | First failed conditions (counts) |
|---|---:|---:|---|
| BR-FORMAT | 0/46 | 0/46 | Format: 46 |
| BR-SEMANTICS | 1/46 | 1/46 | Oracle answer: 45 |
| BR-CONTRADICTION | 3/46 | 3/46 | Conflict: 43 |
| BR-HISTORY | 6/46 | 5/46 | History: 40 |
| BR-UNCHANGED | 4/46 | 4/46 | Operational change: 42 |
| BR-ROUTINE | 6/46 | 6/46 | Information-only: 37; Restriction: 3 |
| BR-HISTORICAL | 0/46 | 0/46 | Restriction current: 24; Service class: 22 |
| BR-FIRM | 24/46 | 20/46 | Service class: 22 |
| BR-UNRESOLVED | 46/46 | 7/46 |  |

Previous commit: `0164af56c69e227c574b72b624da2f16bdc77bd2`. Spec-to-spec consequences with current fixed compiler; not a runtime regression mapping

| Notice/capture | From | To |
|---|---|---|
| — | No changed outcome observed | — |

### Every nonmatch: first failed domain condition

| Notice/capture | Rule | First failed condition | Required | Observed |
|---|---|---|---|---|
| capture-0/46507 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/46507 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/46507 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/46507 | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/46507 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/46507 | BR-ROUTINE | Information-only | YES | NO |
| capture-0/46507 | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-0/46528 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/46528 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/46528 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/46528 | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/46528 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/46528 | BR-ROUTINE | Information-only | YES | NO |
| capture-0/46528 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46528 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46604 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/46604 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/46604 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/46604 | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/46604 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/46604 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46604 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46615 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/46615 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/46615 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/46615 | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/46615 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/46615 | BR-ROUTINE | Information-only | YES | NO |
| capture-0/46615 | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-0/46624 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/46624 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/46624 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/46624 | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/46624 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/46624 | BR-ROUTINE | Information-only | YES | NO |
| capture-0/46624 | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-0/46725 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/46725 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/46725 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/46725 | BR-ROUTINE | Restriction | NONE | KNOWN |
| capture-0/46725 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46725 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46728 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/46728 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/46728 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/46728 | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/46728 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/46728 | BR-ROUTINE | Information-only | YES | NO |
| capture-0/46728 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46728 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46732 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/46732 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/46732 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/46732 | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/46732 | BR-UNCHANGED | Operational change | UNCHANGED | CHANGED |
| capture-0/46732 | BR-ROUTINE | Information-only | YES | NO |
| capture-0/46732 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46732 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46775 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/46775 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/46775 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/46775 | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/46775 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/46775 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46775 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46795 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/46795 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/46795 | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/46795 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/46795 | BR-ROUTINE | Restriction | NONE | KNOWN |
| capture-0/46795 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46795 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46805 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/46805 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/46805 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/46805 | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/46805 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/46805 | BR-ROUTINE | Information-only | YES | NO |
| capture-0/46805 | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-0/46818 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/46818 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/46818 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/46818 | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/46818 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/46818 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46818 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46864 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/46864 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/46864 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/46864 | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/46864 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/46864 | BR-ROUTINE | Information-only | YES | NO |
| capture-0/46864 | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-0/46881 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/46881 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/46881 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/46881 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/46881 | BR-ROUTINE | Information-only | YES | NO |
| capture-0/46881 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/46881 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/duplicate-seed | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/duplicate-seed | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/duplicate-seed | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/duplicate-seed | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/duplicate-seed | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/duplicate-seed | BR-ROUTINE | Information-only | YES | NO |
| capture-0/duplicate-seed | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-0/duplicate-input | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/duplicate-input | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/duplicate-input | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/duplicate-input | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/duplicate-input | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/duplicate-input | BR-ROUTINE | Information-only | YES | NO |
| capture-0/duplicate-input | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-0/restart-replay | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/restart-replay | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/restart-replay | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/restart-replay | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/restart-replay | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/restart-replay | BR-ROUTINE | Information-only | YES | NO |
| capture-0/restart-replay | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-0/unchanged-revision | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/unchanged-revision | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/unchanged-revision | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/unchanged-revision | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/unchanged-revision | BR-ROUTINE | Information-only | YES | NO |
| capture-0/unchanged-revision | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-0/repeated-revision | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/repeated-revision | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/repeated-revision | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/repeated-revision | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/repeated-revision | BR-ROUTINE | Information-only | YES | NO |
| capture-0/repeated-revision | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-0/missing-prior | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/missing-prior | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/missing-prior | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/missing-prior | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/missing-prior | BR-ROUTINE | Information-only | YES | NO |
| capture-0/missing-prior | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/missing-prior | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/late-prior-arrival | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/late-prior-arrival | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/late-prior-arrival | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/late-prior-arrival | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/late-prior-arrival | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/late-prior-arrival | BR-ROUTINE | Information-only | YES | NO |
| capture-0/late-prior-arrival | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-0/reconcile-termination | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/reconcile-termination | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/reconcile-termination | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/reconcile-termination | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/reconcile-termination | BR-UNCHANGED | Operational change | UNCHANGED | CHANGED |
| capture-0/reconcile-termination | BR-ROUTINE | Information-only | YES | NO |
| capture-0/reconcile-termination | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/reconcile-termination | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-0/field-mutation | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-0/field-mutation | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-0/field-mutation | BR-CONTRADICTION | Conflict | YES | NO |
| capture-0/field-mutation | BR-HISTORY | History | GAP | COMPLETE |
| capture-0/field-mutation | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-0/field-mutation | BR-ROUTINE | Information-only | YES | NO |
| capture-0/field-mutation | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-1/46507 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/46507 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/46507 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/46507 | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/46507 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/46507 | BR-ROUTINE | Information-only | YES | NO |
| capture-1/46507 | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-1/46528 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/46528 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/46528 | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/46528 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/46528 | BR-ROUTINE | Information-only | YES | NO |
| capture-1/46528 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46528 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46604 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/46604 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/46604 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/46604 | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/46604 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/46604 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46604 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46615 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/46615 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/46615 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/46615 | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/46615 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/46615 | BR-ROUTINE | Information-only | YES | NO |
| capture-1/46615 | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-1/46624 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/46624 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/46624 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/46624 | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/46624 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/46624 | BR-ROUTINE | Information-only | YES | NO |
| capture-1/46624 | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-1/46725 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/46725 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/46725 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/46725 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/46725 | BR-ROUTINE | Information-only | YES | NO |
| capture-1/46725 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46725 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46728 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/46728 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/46728 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/46728 | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/46728 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/46728 | BR-ROUTINE | Information-only | YES | NO |
| capture-1/46728 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46728 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46732 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/46732 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/46732 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/46732 | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/46732 | BR-UNCHANGED | Operational change | UNCHANGED | CHANGED |
| capture-1/46732 | BR-ROUTINE | Information-only | YES | NO |
| capture-1/46732 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46732 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46775 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/46775 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/46775 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/46775 | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/46775 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/46775 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46775 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46795 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/46795 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/46795 | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/46795 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/46795 | BR-ROUTINE | Restriction | NONE | KNOWN |
| capture-1/46795 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46795 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46805 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/46805 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/46805 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/46805 | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/46805 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/46805 | BR-ROUTINE | Information-only | YES | NO |
| capture-1/46805 | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-1/46818 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/46818 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/46818 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/46818 | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/46818 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/46818 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46818 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46864 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/46864 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/46864 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/46864 | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/46864 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/46864 | BR-ROUTINE | Information-only | YES | NO |
| capture-1/46864 | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-1/46881 | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/46881 | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/46881 | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/46881 | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/46881 | BR-ROUTINE | Information-only | YES | NO |
| capture-1/46881 | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/46881 | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/duplicate-seed | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/duplicate-seed | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/duplicate-seed | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/duplicate-seed | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/duplicate-seed | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/duplicate-seed | BR-ROUTINE | Information-only | YES | NO |
| capture-1/duplicate-seed | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-1/duplicate-input | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/duplicate-input | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/duplicate-input | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/duplicate-input | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/duplicate-input | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/duplicate-input | BR-ROUTINE | Information-only | YES | NO |
| capture-1/duplicate-input | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-1/restart-replay | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/restart-replay | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/restart-replay | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/restart-replay | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/restart-replay | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/restart-replay | BR-ROUTINE | Information-only | YES | NO |
| capture-1/restart-replay | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-1/unchanged-revision | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/unchanged-revision | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/unchanged-revision | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/unchanged-revision | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/unchanged-revision | BR-ROUTINE | Information-only | YES | NO |
| capture-1/unchanged-revision | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-1/repeated-revision | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/repeated-revision | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/repeated-revision | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/repeated-revision | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/repeated-revision | BR-ROUTINE | Information-only | YES | NO |
| capture-1/repeated-revision | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-1/missing-prior | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/missing-prior | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/missing-prior | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/missing-prior | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/missing-prior | BR-ROUTINE | Information-only | YES | NO |
| capture-1/missing-prior | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/missing-prior | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/late-prior-arrival | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/late-prior-arrival | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/late-prior-arrival | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/late-prior-arrival | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/late-prior-arrival | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/late-prior-arrival | BR-ROUTINE | Information-only | YES | NO |
| capture-1/late-prior-arrival | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
| capture-1/reconcile-termination | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/reconcile-termination | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/reconcile-termination | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/reconcile-termination | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/reconcile-termination | BR-UNCHANGED | Operational change | UNCHANGED | CHANGED |
| capture-1/reconcile-termination | BR-ROUTINE | Information-only | YES | NO |
| capture-1/reconcile-termination | BR-HISTORICAL | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/reconcile-termination | BR-FIRM | Service class | FIRM_DISRUPTION | OTHER |
| capture-1/field-mutation | BR-FORMAT | Format | UNSUPPORTED | SUPPORTED |
| capture-1/field-mutation | BR-SEMANTICS | Oracle answer | UNUSABLE | USABLE |
| capture-1/field-mutation | BR-CONTRADICTION | Conflict | YES | NO |
| capture-1/field-mutation | BR-HISTORY | History | GAP | COMPLETE |
| capture-1/field-mutation | BR-UNCHANGED | Operational change | UNCHANGED | UNKNOWN |
| capture-1/field-mutation | BR-ROUTINE | Information-only | YES | NO |
| capture-1/field-mutation | BR-HISTORICAL | Restriction current | ENDED | UNKNOWN |
