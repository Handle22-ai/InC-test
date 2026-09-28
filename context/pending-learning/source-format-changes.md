# Source format changes (pending learning, not a requirement)

Status: UNAPPROVED learning from a second audit's fresh session (2026-09-28). The change requested: accept header timestamps with a CT/CST/CDT suffix.

- A parser change in `rebuilt/source_input.py` plus a `date_formats` edit passed all three gates with 0/46 changed. Nothing in the captures or the fixed date list exercised the new format. `make consequences` now flags such edits as UNMEASURED; supply examples with `--inputs` or add a retained sample in the new format.
- REMEDIATION-002's "ended in every timezone" observation parses only naive ISO ends. A suffixed or labeled end time is not recognised, so a long-ended restriction can stay a candidate. Any timezone-label support must update that observation in both evaluators.
- The gate's date checks use a fixed list of sample strings in `harness/input_contract_checks.py`. A new declared format needs a new sample there, which is an evaluator change.
- To learn how `date_formats` reaches the parser checks, the session read 7 harness modules. The context package should say so directly.
