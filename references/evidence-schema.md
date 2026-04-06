# Evidence Schema

Every normalized record is stored as JSON with these fields:

- `record_id`: stable content hash for the normalized record
- `source_type`: explicit source class such as `description`, `chat`, `meeting-note`, `email`, `speech`, `document`, `screenshot`, `correction`
- `source_name`: human-readable source label, usually the original filename or input label
- `timestamp`: ISO 8601 string when known, otherwise the ingestion timestamp
- `speaker`: original speaker when known
- `audience`: intended audience when known
- `content`: normalized text payload
- `attachment_refs`: list of attachment paths or related file hints
- `confidence`: float between `0.0` and `1.0`
- `privacy`: one of `internal`, `restricted`, `sensitive`
- `layer_hint`: one of `voice`, `operator`, `boundary`, `mixed`

Interpretation rules:

- `layer_hint` is a routing output, not a truth claim.
- `correction` records never count toward the ready gate.
- `speaker` may be `unknown` when the import does not expose it.
- `attachment_refs` may be empty.
