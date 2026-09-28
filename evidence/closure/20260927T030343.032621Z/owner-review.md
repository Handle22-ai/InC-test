# Exact owner review — approval pending

This review compares the **actual pre-remediation overlay**, not Git HEAD alone: f7de5a5094a33c3b53cff33cede071e7c79127bd + manifest `8719cddb2403f9ed1560378a8089dcb91f8991c7474d956be8952843784be9fb`. The unchanged original owner instruction is byte-equal to the attachment supplied in this conversation (SHA256 `6c2f3167d93b8593f7712e808e1e77572f46f8160f5b736aadd5b4449e8ae05b`). Earlier approval applies to D1–D6 and the stated bounded scope; it is not a new approval of these integrity references.

[Exact scope and full hashes](owner-review-scope.json), [semantic diff](semantic-diff.json), [exact changes against the overlay](exact-changes.diff), and [coordinated self-repin result](../../integrity/20260927T021057.685073Z/trust-boundary-probe.json) are the review material. No owner approval was written.

| Decision | Recommended exact approval wording | Consequence / status |
|---|---|---|
| R1 — integrity/reference mechanism | “I approve the integrity/reference changes identified by owner-review-scope.json at the SHA256 shown below, with unchanged D1–D6 business intent and bounds. I accept local byte/status consistency as the implemented boundary; future normative promotion still requires my explicit review outside the implementation worker's writable checkout. This is not authentication, production acceptance or retrospective certification.” | Pending. Code is implemented and tested; promotion/commit awaits your review. |
| R2 — complete temporal reference | “I approve the exact proposed/capture-registry.json bytes at the SHA256 shown below, adding only the two identified complete storage results as observed temporal references. Their FAIL/UNKNOWN outcomes remain; registration does not approve a release or the application.” | Pending and not applied. Enables the existing demo/acceptance CLI to select this complete prior; no new loader/authentication feature. Recommend approval. |

## Semantic changes

| Area | Before → current | Intent and acceptance effect |
|---|---|---|
| Requirement/check bindings | Per-section substring checks and a generic check-name allowlist → exact per-ID structured fields, fixed 28-ID inventory, declared per-ID gate/type/check, full-row digests and supported parameter schemas. Comment-only clauses cannot satisfy current text. | All original per-ID check assignments and governance remain unchanged. Unsupported coordinated edits require a separately reviewed reference update; the worker could still bypass both code and reference. |
| Executable parameters | OUTPUT-001/002 had empty parameter maps with bounds in prose/check code → confidence_min=0, confidence_max=1; minimum=0, maximum_mdq=100 explicitly represented and consumed by the checker. Source/Policy/Executable parameters appear per spec section. | Existing values unchanged, no new threshold. Synthetic test changing 100→90 demonstrates derivation mechanics only; no real approval or current threshold change. |
| Expected oracle | Captured annotations could supply expectations → fixed requirements/dataset.json plus source-supported oracle-support.json, verified by recorded hashes, supply expectations. | Fixed 14 labels and field support unchanged; observations cannot redefine expected answers. Unusable helper results still leave persisted facts evaluable under the recorded D5 instruction. |
| Capture identity | Current bytes could pass through unpinned → four explicitly registered captures/results, exact case inventories and referenced input/case/manifest hashes; report verdicts recomputed. Verification does not update the registry. | Adds evidence admissibility refusals, not a new grading threshold. Registration attests local bytes only. New runs are not automatically trusted. |
| Approval/status/supersession | Manifest labels and decision text lacked registered consistency checks → seven exact decision/owner-record hashes and their existing statuses; reject inconsistent bodies/statuses, active/excluded overlap, duplicate active entries and unregistered “approved” claims. | ADRs 001–006 and the owner message are byte-unchanged; existing statuses and excluded/superseded list are unchanged. New references/learning are “consistency-reference”/“observed”, never invented “approved”. No parser proves all prose is consistent, and owner identity is not authenticated. |
| Acceptance and comparisons | Paired inherited/rebuilt delta labeled regression → separate paired result and each system's own temporal comparison. New accept-storage requires PASS for all selected current-snapshot checks and rebuilt temporal comparison. | This changes executable acceptance handling: applicable FAIL/ERROR/UNKNOWN refuses with exit 2. Missing history is not silently excluded. Demo remains measurement. Frozen policy interpretation without a selected temporal prior remains UNKNOWN. |

D1–D6 text, requirement IDs/statements/severity/approval/enforcement, fixed labels, native inherited/rebuilt behavior and model configuration are unchanged. OUTPUT-004/005/006 and STATE-004 remain binding within their already-approved source-supported scope. Eight approved complete lifecycle/refusal obligations stay unimplemented/unevaluated; neither hash registration nor owner approval makes them pass.

## Exact reference files and hashes

All repository files below, referenced source/capture files, manifest and verifier code remain writable by the implementation worker. Filesystem mode is recorded in the scope JSON; no permission protection was added. “Trusted reference” here means the values the current code consults, not proof of an independent trust root.

| File / role | Pre-remediation SHA256 | Current SHA256 |
|---|---|---|
| `spec.md` | `d54d2347e6c65ac7cb9711dce24290f722a6650a65c555f0154e2983a471c621` | `8ceae06ebf0a5c4a8a8e72fae516cffcd2c3df1fc014c1ff7bc459ed07ba6f25` |
| `requirements/requirements.yaml` | `05aea3d386f07b2c1c1099daaff4ce84f04d6382936657ebb1e13300e91eacab` | `c7b630fa694bd2d448bde78732f58f16197b0d06c6e9854d7fc10a4fa964b311` |
| `requirements/dataset.json` | `a51147dffc80b69de840865ea01091eee66ad720e334adee9a983179841810ef` | `a51147dffc80b69de840865ea01091eee66ad720e334adee9a983179841810ef` |
| `requirements/oracle-support.json` | `237d35251aeed2614370812ec175b543e91a5184daca3e5316af544f07f0fe46` | `237d35251aeed2614370812ec175b543e91a5184daca3e5316af544f07f0fe46` |
| `context/authority-reference.json` | `absent` | `e6b8a63c9fae1cd44baab8441c8e1089ba84d7643302f779db2c29f369fb1f88` |
| `requirements/capture-registry.json` | `absent` | `972ad41564adc5a637e36f59c74f859412998cdb5e0c4e934fe77c87da342f39` |
| `context/manifest.yaml` | `294e89eea171e2278ce5e5434bfa656786b88f3db841df042a3a596451d1e6b4` | `92b4664d5373dc89204bf9cc6f807936648b4fa763f6b3d7c21f14999872d203` |

`authority-reference.json` supplies policy ID, required IDs, per-ID gate/type/check, full-row hashes and registered decision statuses/hashes. `capture-registry.json` supplies oracle/support hashes, registered results hashes, ordered case IDs and referenced bytes. `artifacts/inherited_manifest.json` remains the inherited-source reference. The exact owner message/ADRs establish the recorded scope but local copies do not authenticate it. Verifier modules, schema allowlists and acceptance code are also part of this review's pinned scope.

| Registered approval record | Status carried forward unchanged | SHA256 |
|---|---|---|
| `context/decisions/001-baseline-snapshot.md` | approved | `73a188dc5e44ea989697e53f57f37ea9229becb80b30cb1dcb93580e511f5ecf` |
| `context/decisions/002-controlled-token-experiment.md` | approved | `1123c667764cc454e167c62c11a7404d7ee0e327f60625befefc2930c74f8572` |
| `context/decisions/003-notice-snapshot-scope.md` | historical-approved-scope | `bde7e33cad119159bdfa97f1f850a2538e6f5da6aa4df7a330df80f899ca8947` |
| `context/decisions/004-capture-reference-extension.md` | approved-technical-extension | `92d30b1a776f2bd21f4b580ac256ac4a5d5f6f0d3f50b74bb570a78eb4048b9f` |
| `context/decisions/005-synthetic-capture-reference-alias.md` | approved-synthetic-technical-extension | `6bb139944015eca838b3b5766f5923500bd1731f21665fb4cd2ac2176e4f4ca2` |
| `context/decisions/006-assessment-lifecycle-policy.md` | owner-approved | `28cf6ae126e12952dca8bd2b2dd434455a500c51894a5f60fce8190421426367` |
| `evidence/policy/20260927T010449.918426Z/owner-approval.txt` | owner-instruction | `6c2f3167d93b8593f7712e808e1e77572f46f8160f5b736aadd5b4449e8ae05b` |

| Currently registered observations | Results SHA256 | Cases / referenced files |
|---|---|---|
| `evidence/candidates/impact-budget-512/full/20260926T191722.363460Z/results.json` | `3d57b5097d451e332bd3ff35b7b85705861f759e9a4b3e9bbde8b01a9f9ab615` | 23 / 41 |
| `evidence/legacy/20260926T185618.823020Z/results.json` | `98279d697dd3c5d05f9383a32886ad245dc335607d6784a684a1e8f664a09703` | 23 / 41 |
| `evidence/policy/20260927T010449.918426Z/storage-final/inherited/results.json` | `9cb0c7bab2e2685888b9fa6832335bc5979421ea0311882a6f013bf45da2d508` | 21 / 3 |
| `evidence/policy/20260927T010449.918426Z/storage-final/rebuilt/results.json` | `a4161ced8a17e0d71400b5c1b3821e7284527c05167e1c9867ba4f826fe67304` | 21 / 3 |

The optional proposed registry adds only `evidence/integrity/20260927T021057.685073Z/storage-release/{inherited,rebuilt}/results.json`, with that run's manifest/fixtures hashes and its ending-identity pin. The purpose text explicitly denies release acceptance. [Exact optional patch](proposed/capture-registry.diff). It remains unapplied; the current CLI rejects these unregistered paths. The closure's no-change comparison uses the existing comparator directly with pinned same-evaluator observations and claims no CLI registration.

## Manual trust boundary

The coordinated self-repin probe changed spec, rules and reference together and was accepted locally. It remains retained, with authenticated_owner_approval=false. Local checks cannot prevent a writer from replacing the reference or verifier.

Available now: the owner compares this exact scope/diff and hashes against the original conversation/attachment, outside the writable checkout, and replies approve/amend. The attachment is outside this session's declared writable roots; that is a useful comparison source, not cryptographic identity verification. The owner can independently keep the reviewed hash/reference in an operator-controlled location not writable by the worker. No such protected verification workflow is currently integrated. No authentication service will be built in this pass.

Approval of R1/R2 would authorize the corresponding reviewed promotion and subsequent local staging/commit preparation. Actual worker evidence and final clean-checkout verification remain separate dependencies; neither decision claims those have completed.

R1 scope-file SHA256: `4376ed60534d1752d5f8f7ba538715fface6639614ac25a8dc73ad6118fbd720`.

R2 proposed registry SHA256: `65f575bd5b496bed3757279c7752d02b87171dbf93511b61502d068ec797a9b3`.
