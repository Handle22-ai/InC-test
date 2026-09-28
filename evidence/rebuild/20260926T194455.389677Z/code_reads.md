# Code-read record for the rebuild

Human source inspections requested/reported: **none**. Agent boundary inspection is
listed below; it is not represented as evidence of a human maintaining the system from
source. The future fresh session must separately record any human explanation required.

CODE-READ-ID: AGENT-REBUILD-001
Observed failure: inherited replay accumulates current child observations.
Why evidence was insufficient: evidence established the fault, but implementing a fair
port required the existing invocation protocol and normalized payload schema.
Source inspected: `harness/adapter.py`, `harness/evaluator.py`, parser output interface,
`harness/gates.py`; inherited `database.py` schema/public API and FK initialization flow.
What was learned: parser returns complete notice/location/restriction collections;
the baseline enables FK enforcement after insertion, not before it. The first new port
used the wrong order, producing spurious missing-prior insert failures; that attempt
is preserved. Existing insert SQL was not copied into the independently built document store.
Missing harness/evidence capability: explicit port fidelity coverage and complete readback.
Harness improvement made: same protocol, paired frozen fixtures, exact persisted readback,
persisted joins and preservation of other snapshots; a regression test proves inherited
duplicates remain visible through the port.
Could the same code read be avoided next time? The selected package now identifies the
public boundary, port protocol, failure evidence and executable checks. Agent inspection
of a changed boundary may still be required; no human source read was needed here.
