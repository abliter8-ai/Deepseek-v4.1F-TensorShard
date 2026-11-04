# CR-001 — Work Shards helper

Status: complete. Date: 4 November 2026. Implements [IP-001](IP-001-work-shards-helper.md).

## Delivered

The C12 worker-heavy/NVMe configuration is recorded as **production**, following the project owner's decision to retain it. Public documentation now explains who benefits, the change from the original C4/1M deployment, and the prepare → append → retain or save → resume working-day cycle. The 40-second prefill example is illustrative; historical measurements retain their original labels.

The small Work Shards helper ships in this repository. It supports named profiles, saved sets, sequential preparation, validation without launch, a DSH session check, a built-in DSH preparation adapter and an explicit command adapter. Local receipts retain the last result for each profile. The helper preserves application session/workspace identity and does not replace application loops or credential stores.

DSH preparation sends `initialize`, `session/resume`, `session/working-directory/get`, `session/prompt`, `session/wait` and `shutdown`. A workspace mismatch fails before the prompt. Check mode omits `session/prompt` and `session/wait`. Dry runs start no application and write no preparation receipt. Timeouts and application failures produce a failed result; other selected profiles can continue.

## Verification

| Check | Result |
|---|---|
| `python3 -m unittest -v test_work_shards.py` | 13 tests passed using temporary subprocess fixtures |
| Protocol and identity | Method order, original workspace and unchanged session ID checked |
| Failure handling | RPC errors, premature exit, nonzero shutdown and partial-line timeout checked |
| Selection and receipts | Deduplication, unknown profiles, continuation, dry-run and prior-result retention checked |
| Command execution | Literal argv passed without shell expansion |
| Installed DSH 0.2.1-rc.5 | One existing saved session resumed, original workspace verified and SDK closed in 1.919 seconds |
| Installed-session generation | No prompt submitted; this was a session-access check, not a prewarm or throughput test |
| CLI usage | Help, example initialization and listing checked |

The prepare sequence is covered by offline protocol tests. Earlier application-level DSH preparation and revision results are recorded separately in [evidence](evidence.md); they predate this helper's packaging. This report does not claim a new model benchmark.

## Operating boundary

A completed preparation is recorded at a time; current cache residency remains unknown. RAM reuse, disk commit, restore and eviction belong to the serving engine. Existing application permissions still apply. Native adapters for other applications and an automatic daily scheduler are separate extensions. No timer, model reload or serving change was installed by this work.
