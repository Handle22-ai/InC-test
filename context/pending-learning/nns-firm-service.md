# NNS firm service (pending learning, not a requirement)

Status: UNAPPROVED learning from the 2026-09-28 fresh maintenance session. NNS-FIRM-001 itself is approved in spec.md.

- Service mappings, `FIRM_SERVICES` and the interface service enums are spec-owned. Changing what counts as firm is a spec-only change; no component or harness read is needed.
- No captured or labeled NNS outage exists, so `make consequences` shows 0 of 46 changes. The effect is unmeasured until the owner adds an NNS-unavailable witness (an oracle change).
- The desk should confirm that a partial NNS limit stays non-firm, as it does for primary and secondary firm service.
