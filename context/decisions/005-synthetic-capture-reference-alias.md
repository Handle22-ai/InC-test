# Decision 005 — synthetic serialized capture-reference alias

Status: explicitly authorized technical format exercise. Exact request:
`evidence/format-compatibility/20260926T204022.284775Z/starting_request.txt`.
This is not evidence that NGPL changed its source format or approval of new domain policy.

The rebuilt native serialized-snapshot reader accepts `captureReference` as an alternate
spelling of `capture_reference`. Only the decoder changes; callers and the normalized
notice/location/restriction projection retain their existing interface.

| Serialized metadata | Native result |
|---|---|
| Neither spelling | `capture_reference=None` |
| Canonical only | Existing optional string/null validation |
| Alternate only | Same validation, exposed as `capture_reference` |
| Both equal valid strings or nulls | Accept the common value |
| Both with different values | Explicit `StorageError` naming the conflicting spellings |
| Invalid types, including equal invalid values | Reject through existing validation |

Canonical serialization remains unchanged: actual writes use `capture_reference` when
non-null, and omit it for None. An exact replay remains a no-op and does not migrate
stored alias bytes. A later ordinary refresh writes the canonical format. Reads do not
modify storage or dereference values. Notice/source identity, child rows, prior links,
receipt behavior and changed-source conflict policy remain unchanged.

Validation: nine rebuilt-only synthetic compatibility tests in
`tests/test_capture_reference_alias.py`, separate from unchanged shared gates. The
inherited store is not required or claimed to support this extension.
