# Recovered reconstructed-baseline maintenance demonstration

The actual later worker completed the synthetic alias task. This package was exported only after both launch records contained terminal `turn.completed` events and `worker-exit.json` recorded exit 0. No worker files were changed and its task/tests were not rerun in the recovering session.

| Launch | CLI exit | Observed task outcome |
|---|---:|---|
| 20260926T234438.211512Z | 0 | BLOCKED: execution host disabled; transcript reports no reads, edits or checks |
| 20260926T234823.493230Z | 0 | Technical replay completed: baseline 49 tests; extension before change 4 failures/14 subtest errors; final 55 tests pass |

An even earlier launcher failed before a worker started because of a strict configuration key; those logs are preserved too. A CLI exit alone is not task completion.

Read the unchanged [worker report](worker-fresh_session.md), [actual request](starting_request.txt), [decoder diff](worker-change.diff), and our [independent recomputation](verification.json). The [archive](worker-evidence.zip) and [byte inventory](inventory.json) contain both launch transcripts, operator launch controls, the reconstructed baseline, selected context, changed source/tests, comparisons, retained learning and subsequent selection. Archive paths preserve baseline/ and completed/ separately. The historical contract is not the current policy or evaluator.

Recomputed: all 672 reconstruction entries match except the two declared changes (decoder and manifest); 32 before and 34 after selected hashes/content match; all six full-result comparisons match (21 cases and 157 findings per implementation against three baselines). Observed logs support 49-before/55-after tests. These are inspected historical executions, not newly reproduced test runs.

Qualification: the missing *technical maintenance replay* is now supported. Strict no-original-conversation isolation is partially demonstrated: an independent ephemeral launch, disabled memory/import tools, restricted paths/network and observed denied temp writes support separation; the worker's statements about no supplied prior conversation and no additional human explanation are assertions, not authentication of hidden platform state. The preparer had previously seen the solution. No earlier session is retrospectively certified and no current-harness recertification follows. The replay's source was not transplanted into the polished candidate.

The owner's later firsthand account says no human source reads and is recorded separately in the current code-read index. It is not an independent account of every participant. The original worker's UNKNOWN human-read wording remains untouched.
