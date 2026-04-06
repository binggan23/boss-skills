# Init Wizard

Run `/boss:init` in five steps:

1. Capture `slug`, `display_name`, and `boss_type`.
2. Choose one ingestion mode for this step: describe, paste chat, import file, import image.
3. Normalize the import into records with the schema in `references/evidence-schema.md`.
4. Recompute coverage and identify missing evidence.
5. Stop in `collecting` unless the ready gate is fully satisfied.

Report:

- current status
- coverage score
- distinct source types
- whether direct-expression evidence exists
- whether decision evidence exists
- concrete missing evidence categories
