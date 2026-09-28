# Inherited-system runs

Each directory is one run of the inherited system. Two are registered as captures in `requirements/capture-registry.json`; the gate scores them, and `evidence/CURRENT.md` is the current report on them.

**`20260928T180936.681804Z/summary.md` is superseded.** It was written by the code of the time, which counted the inherited system's own unusable verdicts (46528, restart-replay) as an invalid measurement. So it says "Measurement valid: False; Gate 1 FAIL; Gate 2 ERROR". The directory is hash-registered as capture-2, so the file cannot be edited or stamped without changing the oracle. Read the capture-2 columns of CURRENT.md instead: the run's calls were all answered, and 46528 and restart-replay are findings about the inherited system, not a measurement failure (code-read entry AGENT-LIVE-PATH-20260928).
