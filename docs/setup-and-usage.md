# Setup and usage

The adopted serving configuration and the Work Shards helper are separate parts of TensorShard. The helper uses an existing application and model endpoint. It does not install or reload the inference engine.

## Work Shards quickstart

Requirements: Python 3.10 or newer. The built-in DSH adapter uses the SDK interface verified with installed **DSH 0.2.1-rc.5**. DSH must already have a working provider configuration and a saved session for the intended workspace.

```sh
python3 work_shards.py init
```

This creates `work-shards.local.json` from the included example without overwriting an existing file. That file and `.work-shards/` receipts are ignored by Git. Keep your real workspace, session IDs and application configuration there.

The example's environment placeholders are:

| Variable | Value supplied locally |
|---|---|
| `WORK_SHARD_WORKSPACE` | The original session's existing project directory |
| `WORK_SHARD_SESSION` | Its saved DSH session ID |
| `WORK_SHARD_PROVIDER` | The provider ID already configured in DSH |
| `WORK_SHARD_MODEL` | The model ID for that provider |
| `WORK_SHARD_PATCH` | The existing DSH provider patch file |

You can replace placeholders with local values in the ignored JSON file. Secrets belong in the application's normal credential configuration or environment, not in the public example. Use the same provider settings, tools and session store as the application you intend to return to.

```sh
python3 work_shards.py list
python3 work_shards.py check --set daily --dry-run
python3 work_shards.py check --set daily
python3 work_shards.py prepare --set daily
python3 work_shards.py status
```

`check` resumes and closes the DSH session without a model prompt. `prepare` resumes it, verifies its workspace, requests a short readiness turn and waits for completion. That turn appends to the saved conversation and can incur a cold prefill if no compatible cached prefix remains. The default prompt requests no tools or edits; the application's own permission policy still applies.

Choose individual profiles with `prepare profile-name`, or define additional arrays of profile names in `sets`. Selection is deduplicated and profiles run sequentially. Failures are recorded and remaining selected profiles can continue; a failed set returns a nonzero exit code. `--config` selects another local configuration file:

```sh
python3 work_shards.py --config work-shards.local.json prepare --set daily
```

A local receipt is evidence of an operation at a time, not a live cache-residency monitor. Status does not promise that the context is still warm. The helper does not replace conversations or source backups with KV snapshots.

## Profile fields

| Field | Purpose |
|---|---|
| `adapter` | `dsh` for built-in SDK resumption, or `command` for a supplied application command |
| `workspace` | Existing original workspace; DSH's stored directory must match |
| `session_id` | Existing DSH saved-session identity; a missing session fails rather than creating a replacement |
| `provider`, `model` | Existing DSH route selection |
| `command` | DSH executable/SDK arguments, or an explicit application command as an argv array |
| `patch` | Optional DSH patch file appended with `--patch` |
| `prompt` | Optional DSH preparation instruction |
| `max_tokens` | DSH output cap, default 256; existing route reasoning defaults apply |
| `timeout_s` | Bounded preparation timeout, default 120 seconds |
| `env` | Optional process environment values; normal environment is inherited |
| `check_command` | Separate command-adapter check; absence means check is unsupported |

The command adapter executes an argv array directly, without a shell. It runs the real application's command in its selected workspace. It does not invent resume flags or turn an unrelated API request into an application integration. A successful command means that command completed; the application must provide its own preparation and session semantics. Paths and environment substitutions are resolved locally.

## Serving configuration

The [adopted recipe](recorded-recipe.yaml) records C12, the 4,198,400-position shared pool, 513/1,537-block ownership, the 1,048,576-token request limit and separate 4 GiB NVMe stores. The project owner selected this configuration for continued use on 4 November 2026.

The [integration notes](implementation.md) explain the unequal-owner allocation, movement, kernels and persistent-spill work. Exact image and source hashes identify the measured builds. The public repository does not yet distribute the engine build/patch bundle, deployment launcher or model weights. That distribution boundary does not change the adopted configuration's status.

[Mia's pinned recipe](https://github.com/MiaAI-Lab/DeepSeek-v4.1-Flash-1017-2x-DGX-Sparks/tree/f424dfe3b14ac9f02fe12f5777c852dba967a79a) documents the upstream starting point. Applying only TensorShard's environment values to an unmodified upstream build does not reproduce the unequal-owner integration.

## Verification

Run the helper's focused offline checks without a model request:

```sh
python3 -m unittest -v test_work_shards.py
python3 work_shards.py --help
```

The tests use a temporary SDK fixture and verify selection, session/workspace continuity, timeouts, failures and receipts. The separate installed-DSH check is documented in the [completion report](CR-001-work-shards-helper.md). The prior [performance results](evidence.md) remain unchanged; packaging the helper is not a new throughput claim.
