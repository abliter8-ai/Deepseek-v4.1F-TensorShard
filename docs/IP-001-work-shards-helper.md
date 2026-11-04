# IP-001 — Small Work Shards helper

Status: approved for implementation by the project owner's 4 November 2026 direction to retain the configuration and include a small Work Shard helper.

## Scope

1. Mark the existing C12, worker-heavy, NVMe configuration as adopted. Preserve its measured evidence and exact pins.
2. Ship a Python standard-library helper with named profiles, saved sets, sequential preparation and local receipts.
3. Resume DSH through its existing SDK in the original workspace and session. Use a short readiness turn for preparation. Provide a separate session check that sends no generation request.
4. Allow explicit user-supplied application commands without inventing other applications' resume interfaces. Keep application loops, credentials and transcripts in their existing applications.
5. Keep local profiles, receipts, private names and paths out of version control. Do not claim that a completed preparation proves current RAM residency.

## Acceptance

- Offline protocol tests verify session/workspace continuity, method ordering, selection, failures, timeouts and receipts.
- A bounded check against an installed DSH saved session verifies the real SDK path without a model request.
- README commands match the shipped helper, and the configuration is clearly marked as adopted for continued use.
- No inference benchmark, model reload, cache experiment, live serving change or scheduled automation is required.

A full cross-application scheduler and automatic work-plan selection remain outside this small helper.
