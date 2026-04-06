# Evidence Router

Route each record into one or more analytical layers:

- `voice`: direct boss phrasing, tone, urgency, praise, criticism, cadence
- `operator`: decisions, approvals, prioritization, risk tradeoffs, reporting expectations, management actions
- `boundary`: authority limits, HR or legal topics, external commitments, compensation, signatures, public statements

Routing rules:

- Prefer `mixed` when more than one layer is materially present.
- Mark `voice` when the boss is speaking directly or the text clearly preserves the boss's wording.
- Mark `operator` when the text contains decisions, asks for outcomes, rejects options, sets priorities, or changes resourcing.
- Mark `boundary` whenever the material touches authorization, HR, legal, finance, external comms, or other high-risk commitments.
