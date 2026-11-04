# Work Shards

Work Shards is the included preparation helper for TensorShard. It provides named profiles, saved sets, sequential preparation and local receipts. DSH has a built-in saved-session adapter. A command adapter can invoke another application's explicitly configured preparation path. Automatic daily scheduling and additional native adapters are future extensions.

## Pay for the history, then reuse it

A Work Shard names an agent, project or workspace context you want ready. It is separate from a physical tensor shard or the head/worker KV split.

This is useful when you spend the day returning to two code repositories, a research profile and several assistants. Each has instructions, tools, documents and conversation that are expensive to prepare and mostly unchanged between turns. The applications continue their normal work; the helper gives you a small way to prepare their real contexts together.

For a history with an illustrative 40-second cold prefill, preparation pays that cost before you need an answer. Later turns can reuse the retained prefix and process the appended material. If the history leaves RAM, a retained compatible NVMe checkpoint provides another return path. Updated histories can be retained and committed again under the engine's storage policy. Initial computation has a cost; the benefit is choosing when to pay it and avoiding unnecessary repeats.

This is strongest for repeated long-context work. Short unrelated requests and workloads dominated by uninterrupted generation gain less. Cache compatibility, retention and available memory still matter. Compaction, early prompt changes or eviction from both tiers can require preparation again. Saved conversations remain in their application stores independently of cached computation.

## What the helper does

1. Select one or more named profiles, or a saved set.
2. Validate each selected workspace and adapter configuration.
3. For DSH, resume the saved session and verify its stored workspace matches the profile.
4. Request a short readiness turn through DSH's own model and tool loop, then wait for completion. The runtime decides whether to reuse RAM, restore disk or prefill.
5. Close the client and record the completion time and result. Move to the next profile.
6. Return to the same application session for normal work.

Profiles are prepared sequentially to avoid an unnecessary burst of competing prefills. Completed preparation releases generation slots; retained histories may remain cached while other requests use those slots. Leave room for growth and ad-hoc work instead of trying to fill the pool.

`check` uses the same DSH resume path but submits no model prompt. It checks session access and workspace continuity; it does not warm the cache. `--dry-run` validates selected local profiles without starting an application.

A **LAST PREPARED** receipt means the preparation operation completed at that time. The helper cannot determine current RAM residency or prove an NVMe checkpoint was committed. It records cache residency as unknown. It does not skip preparation merely because an old receipt exists. It does not expose a prefill-only API, guarantee zero output, pin contexts or preempt running work.

## Example daily set

| Profile | Application and intended context |
|---|---|
| Codex — `abliter8-fleet-cluster` | Codex app, selected local model, repository workspace and saved session |
| DeepSeek harness — `rpstudios` | DSH, project workspace and saved session |
| Professional productivity | Professional projects and relevant documents |
| Personal Hermes | Personal assistant and saved conversation |
| Work Hermes | Work assistant and saved conversation |
| OpenWebUI researcher | Research agent and working material |
| OpenWebUI image-prompt writer | Prompt-writing agent and project material |

These are example profiles, not seven bundled native integrations. The DSH SDK path was demonstrated on controlled coding sessions; the complete daily set above has not been measured as one product workflow. The command adapter runs a supported command you supply. It does not establish that every application can resume its GUI session through its CLI.

A quiet 05:00 preparation run is a possible use of the CLI through an existing scheduler. No timer is installed. Manual selections and saved sets work now; automatic work-plan selection is a possible later addition.

## Preserve the actual application context

Applications retain responsibility for agent loops, tools, retries, transcripts and task checks. DSH keeps the same saved session and original workspace. The helper refuses a workspace mismatch instead of silently moving or replacing the session.

Cache reuse depends on instructions, tool definitions and ordering, skills, chat formatting, document versions and conversation state. Concatenating repository files into an unrelated request does not automatically warm the next application turn. Prefix caching reuses compatible computation; it cannot make a changed prefix equivalent to the old one.

The preparation prompt asks for a short reply without tools or edits. That is an application instruction, not a new permission sandbox; existing application permissions and behavior still apply. Credentials stay in the application's usual configuration or inherited environment. The helper does not store model output or raw application diagnostics in receipts.

## Evidence and useful performance

Eight saved DSH sessions were prepared, resumed for checked revisions and measured at approximately 6,151 output tokens/min over the complete 93.501-second window. All 56 frozen checks passed. Those results demonstrate the application path reused by this helper; they predate this helper's packaging and are not a new benchmark of it. See [evidence](evidence.md) and [helper completion checks](CR-001-work-shards-helper.md).

Measure returning-turn responsiveness, checked edits and handoffs, time to a successful outcome including retries, and how many useful contexts remain available while switching projects. A corrected first attempt can still be a useful outcome; include the correction time. Single-stream decode speed does not capture the whole day of tool gaps and warm returns.

[Setup and commands](setup-and-usage.md)
