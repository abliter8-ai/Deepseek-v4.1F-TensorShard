# Work Shards

Status: product direction, recorded 4 November 2026. The general selector, scheduler and cross-application adapters are planned. The existing DSH resumption result is a demonstrated building block, not a complete implementation of this design.

## Prepare useful work before it is needed

A Work Shard names an agent, project or workspace context that the user wants ready. It describes application-level preparation. Physical tensor shards and the head/worker KV ownership split remain runtime concepts.

The intended working day begins with familiar coding agents, professional and personal assistants, a researcher and a prompt writer available to resume. Users can switch projects, wait for a tool and return to another agent without repeatedly paying for unchanged context.

The initial computation still costs time. Prewarming chooses a quieter time for predictable preparation; retaining RAM state and restoring compatible NVMe checkpoints reduce repeat work. This aims to extract more practical value from two finite, already-owned machines while preserving room for ad-hoc requests.

People sometimes arrange work around provider usage windows or keep working while a context is warm. Those experiences motivate the design; provider policies differ. Expiry of cached computation is distinct from loss of a saved conversation.

## Example daily set

| Profile | Application and intended context |
|---|---|
| Codex — `abliter8-fleet-cluster` | Codex app, selected local model, repository workspace and saved session where applicable |
| DeepSeek harness — `rpstudios` | DSH, project workspace and saved session |
| Professional productivity | The application supporting professional projects and their relevant documents |
| Personal Hermes | The main personal Hermes agent and its saved conversation |
| Work Hermes | The work Hermes agent and its saved conversation |
| OpenWebUI researcher | The research agent and current working material |
| OpenWebUI image-prompt writer | The prompt-writing agent, instructions and relevant project material |

This is a concrete seven-profile example. Three repositories, five bots or one or two workspace agents are other possible selections, not capacity requirements. The underlying DSH SDK path has been demonstrated on controlled coding fixtures; the named `rpstudios` profile and the complete set above have not been qualified as an integrated daily-preparation product.

## Proposed user flow

1. Choose profiles manually and save a set.
2. Request preparation now, or select a quiet preparation time. **05:00 is an example**, not an automation installed by this project.
3. For each profile, identify the actual application, project/workspace, model route, saved session where applicable and relevant context sources.
4. Reuse compatible resident state, resume the saved session, or restore an available committed checkpoint through the supported path. Refresh changed material as needed instead of rebuilding the whole set blindly.
5. Report what is ready, what needed preparation and what could not be resumed. Finish preparation and release generation slots for active requests.
6. Open or resume those same applications and workspaces during the day.

Retained dormant contexts occupy cache capacity but do not continuously occupy generation slots. Selection needs headroom for growing conversations, allocation overhead, other work and ad-hoc requests. Filling the pool is not the objective, and adding irrelevant documents to inflate context is not useful preparation.

A later extension could read a work plan and suggest likely projects or documents. Manual choices and saved sets come first.

## Keep the helper thin

Codex, DSH, Hermes and OpenWebUI retain their own agent loops, tools, retries, transcripts and task checks. The proposed helper coordinates preparation and resumption; it does not substitute a generic API loop for those applications.

Cache compatibility depends on what the application actually sends: instructions, tool definitions and ordering, skills, chat formatting, document versions and conversation history. An unrelated request assembled from repository files is not proof that the application's next turn is warm.

Continue a real conversation using its saved session and original workspace. A change early in the prompt, a tool-schema change or compaction can reduce reuse to the remaining compatible prefix. Restoring a checkpoint also depends on the recorded model/layout identity, committed bytes and available capacity.

The documented implementation does not expose a general prefill-only endpoint, guarantee zero-output requests, pin arbitrary contexts indefinitely or instantly preempt running work. The demonstrated DSH readiness step requested a short explicit reply. A preparation helper must use supported application behaviour and report actual reuse, rather than assume it.

## Demonstrated building block

The recorded DSH exercise used this sequence:

**Prepare actual application state → resume the same saved session and workspace → perform useful tool-driven work → check the result.**

Eight initial coding sessions were kept as preparation. Eight short resumed readiness turns confirmed warm reuse. The subsequent measured revisions used the installed DSH SDK, application loop and native tools; all 56 frozen checks passed. The full measured window was 93.501 seconds at approximately 6,151 output tokens/min. [Evidence and context limits](evidence.md).

The general Work Shards selector and daily scheduler are not needed to explain this result, and this documentation does not make further testing a prerequisite for presenting it.

## What useful performance means

Measure returning-turn responsiveness, checked edits and handoffs, time to a successful outcome including corrections, the number of useful contexts available across project switches, and the intervention required to keep work moving.

A failed first tool call or generation followed by a successful correction can be a good outcome when the complete workflow is faster and more useful. Preserve that correction time in the measurement. Single-stream decode speed and aggregate simultaneous tok/s remain diagnostics; they do not describe a whole day of tool gaps, dormant agents and warm returns.
