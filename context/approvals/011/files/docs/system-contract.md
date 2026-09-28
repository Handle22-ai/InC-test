# NGPL system contract and bounded classifier interface

Normative companions delegated by spec.md: requirements/behavior.yaml (supported behavioral rules), normalized-input.schema.json and normalized-output.schema.json (v1 boundary). The engineer edits the structured rules and schema; the behavioral table is generated and strictly checked. D1–D6 govern. BR-FIRM is adopted only as the bounded proposal rule in ADR 007; no materiality or publication authorization follows. The bounded normalized classifier executes the canonical data at runtime; storage/publication remain separate. A schema/hash is not proof that all prose is executable.

## Inputs and retained source

Supported ingestion evidence is saved NGPL HTML. Preserve exact bytes, SHA-256, pipeline, source URL when genuine, notice ID, capture/ingestion timestamp, and source field strings. Header fields are TSP/TSP Name; Critical; Notice Type Desc (1)/(2); Notice Eff Date/Time; Notice End Date/Time; Post Date/Time; Notice ID; Reqrd Rsp; Rsp Date; Notice Stat Desc; Prior Notice; Subject. Body follows Notice Text/Notice Detail; preserve source body/HTML even when presentation whitespace is normalized. Do not silently repair missing identity, timezone, prior links or conflicting same-ID bytes.

PDF, OCR, attachments, text-only exports and unknown formats are not extracted by the current application. A declared unsupported format returns UNRESOLVED/REVIEW_REQUIRED with reason and source reference, never an empty successful extraction. The normalized classifier consumes accepted structured source assertions, not HTML/PDF or a scraped site. Its support for normalized JSON does not imply an ingestion implementation.

The normalized input schema gives exact field names, scalar/array arity, required/null values, enums and evidence references. Source fields/bytes are immutable evidence; facts are extracted or normalized assertions with references. `content_kind`, service, availability and location describe the source. There is no `is_signal`, final classification, impact grade, human MATERIAL answer, or expected label in classifier input. An upstream model can be wrong: this boundary tests reasoning over supplied facts, not whether raw language was interpreted correctly.

History contains accepted versions with their explicit source hashes and prior links. Resolve the current chain to its root; missing ancestors, cycles, duplicate/disputed IDs or conflicting versions remain unresolved. No ID-order or text-similarity identity inference. Compare complete normalized operational facts (including effective interval and assertions), ignoring only ID/capture metadata; do not suppress changed dates as cosmetic. Reordered source assertions require an agreed normalization, otherwise treat equality as unproved. A terminated restriction changes operational status even when fields look alike.

## Quantities, locations and time

- SCHEDULED_TO_PCT_MDQ is allowed/scheduled-to percentage of contract MDQ, bounded 0–100. A 55% scheduled-to value is not 55% curtailed; do not derive absolute energy without source capacity and time basis.
- HOURLY_LIMIT_PCT is percentage of an entitlement/hourly rule, not MDQ. Do not apply the MDQ upper bound to it.
- ABSOLUTE_CURTAILMENT retains the stated MMBtu or Dth value, capacity/time basis and source span. No silent conversion or assumed mmbtu/h basis.
- UNAVAILABLE is categorical and may have no numeric quantity. Missing volume alone is neither malformed input nor a negative classification rule.
- Retain all stated segment/zone/system/LOC/compressor identifiers and roles; distinguish the cause of an outage from the scheduling constraint. Geography supports relevance but a zone name alone does not prove curtailed flow. Current binding annotations cover their identified cases only, not absolute volume or broad regional-price accuracy.

Reference time is an explicit timezone-aware UTC value. Source publication/effective/end strings and timezone meaning remain retained separately; unresolved source time meaning requires actionability/authorization review, never host-clock substitution; it does not alone prevent a source-grounded firm-service candidate under ADR 011. End at or before reference time prevents a new disruption recommendation. Unknown bounds and lifts need recorded actionability under D3. Historical labeled captures retain their original evaluation meaning; never rescore them against today. No arbitrary age, advance-notice or latency threshold is specified.

Record monotonic elapsed machine-processing time with its measured boundary (parsing, stub/provider, storage, checks/report). Report distribution and environment, not a desk SLA. Human approval time is unmeasured and may dominate operational latency; the current autonomy envelope prioritizes withholding unsafe recommendations over an unapproved speed guarantee.

## Classification and publication

The canonical ordered rules define candidate signal, non-signal and unresolved behavior and overlap precedence. Routine content with a current restriction is contradictory, not a shortcut to a negative. Initial operational notices and planned restrictions are considered from source facts; typical strong features are not an all-fields checklist. Partial changes and lifts without sufficient supported interpretation stay unresolved. No numeric materiality cutoff is inherited from scoring code.

The classifier output schema is a **proposal interface**, with identity/hash, tri-state classification, disposition, reasons, evidence references and `recommendation_allowed: false`. It does not fabricate a calibrated confidence score. The legacy parser's binary `is_signal`, numeric confidence, reasons, locations and restrictions remain a separate interface covered by existing OUTPUT-001/002/003 checks; mapping a new classifier into that interface is not assumed implemented.

Publication requires separate source/version/reference-time-bound D6 adjudication and authorization, complete identity/history, and actionability. D1 initial keys survive replay/restart. An unchanged revision creates no new initial/update. A material change needs D6 and may require a linked update; the existing bounded publisher does not implement updates, delivery or reconciliation. A report decision is not a transport attempt or acknowledgement. Failed delivery cannot be presented as success.

D4 requires immutable past-decision evidence including exact source/facts, history then available and missingness, reference/ingestion time, reasons, adjudications, spec/code/dependency/model/prompt identities and attempts/acks where relevant. Later evidence produces linked decisions, never silently backfills a prior explanation. Current snapshots and partial publisher records do not satisfy that whole obligation.

## Observable errors, adapters and dependencies

Invalid JSON/schema produces an explicit input-contract error; unsupported formats, missing history and contradictory facts produce review; unavailable necessary semantic evidence in the normalized classifier produces UNRESOLVED/ERROR restored by ADR 008. The publisher separately reports provider/execution errors. No successful negative/small-impact fallback. Valid extraction may remain scorable after a later helper failure. Structural/persistence observations remain evidence even when semantic accuracy is unscorable. Preserve last valid state; retain the failed/deferred input and reason.

The current parser adapter has arity limits: with LOC codes it retains only the first segment/CS/zone per location group; without LOC codes it forms a segment×CS×zone product and repeats restrictions. System-only groups can yield no location row. These are known implementation limitations, **not intended schema rules**. The normalized boundary retains each supported association explicitly and must not claim source extraction coverage beyond verified annotations.

Independent builder target: Python 3.14 standard library, `python classifier.py INPUT.json` → one JSON output matching normalized-output.schema.json on stdout. Exit 0 means a classified/review/error disposition was produced; unreadable/invalid JSON or input contract violation exits 2 with structured stderr. No provider/network/credential dependency, ingestion, publication, storage migration or classifier implementation is supplied. Named source references in normative text explain intent; they are not hidden instructions to read an existing implementation.

Repository runtime: `.venv/bin/python -B -m rebuilt.normalized_classifier INPUT.json` uses the existing pinned YAML dependency to load canonical rules on every call. Its stdout preserves v1: `reason_codes[0]` is the matched rule, and the Python Decision API and evaluation receipts additionally expose `matched_rule`. No runtime fixture/label dependency. The separate standard-library builder target above remains unlaunched.

## Executable normalization and temporal promotion

The retained-capture normalizer emits per-field normalization_trace records with original value, source/capture basis, normalized value, supplier (model, source_parser, human, normalizer, retained_history or unknown) and UNKNOWN handling. The trace is evidence, never an expected classification. Model-supplied information_only and restriction rows remain assertions to validate against the saved source, not self-proving labels. is_signal, confidence and oracle labels are excluded from normalization.

| Field | Source basis and supplier | Normalization and unknown handling |
|---|---|---|
| content_kind | Model information_only plus extracted restriction presence | INFORMATIONAL / RESTRICTION / UNKNOWN; any known operational row alongside information remains contradictory |
| availability/services | Each model restriction_type/service_type | Preserve every paired restriction; mixed scalar availability UNKNOWN does not erase known rows; unsupported vocabulary remains UNKNOWN |
| restriction status | Source parser Notice Stat Desc and Prior Notice | Preserve INITIATE/SUPERSEDE/TERMINATE and raw status; unsupported status has no inferred semantics |
| segment/geography | Model locations and each restriction location_index | Retain all identifiers and row association; no zone-to-price or cause/constraint inference; unknown roles remain unknown |
| quantity/unit | Model restriction kind/value/unit and source basis | MDQ and hourly entitlement remain distinct; absolute energy only with stated unit/basis; enforce compatible kind/unit pairs, finite nonnegative values and MDQ <=100 |
| timestamps/timezone | Source parser header strings plus model restriction interval strings | Retain exact strings. Only explicit offsets normalize to UTC; date-only/naive values remain UNRESOLVED. No NGPL timezone or gas-day conversion is invented |
| history/prior | Source parser prior link and retained versions | Explicit links only; missing, unsupported or disputed status requires review. Existing classification acceptance is not proof of source validity |

A SIGNAL_CANDIDATE with unresolved source timezone stays candidate-only, recommendation_allowed=false, actionability UNRESOLVED and publication REVIEW_REQUIRED even if a caller supplies authorization. Actually resolved historical intervals precede firm candidate classification. Unknown bounds and clock-dependent revision decisions still require explicit supported actionability under D3; no automatic approval is inferred.

A binding policy/requirement/assumption promotion requires exact artifact hashes and revision identities recorded in an ancestor approval commit, strictly before the first commit activating those artifacts. New working-tree or same-commit ADRs cannot authorize themselves. The owner request is approval evidence; this mechanism does not authenticate a human or prevent an attacker replacing the verifier and Git history.

A clean comparison baseline records observed PASS/UNKNOWN/FAIL separately from release acceptance. Identical semantic/evaluator identity permits behavior comparison: regressions FAIL, unchanged behavior PASS. Changed semantics/evaluator without mapping remains UNKNOWN/NONCOMPARABLE. Registering observed UNKNOWN never converts it to PASS or grants application acceptance. Current snapshot identity is a deterministic source-content hash excluding evidence/report/baseline outputs; a later evidence-only commit must verify the same source hash against HEAD, avoiding a self-referential commit hash.
