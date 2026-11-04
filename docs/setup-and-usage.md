# Setup and usage boundaries

Recorded 4 November 2026. This package presents the demonstrated serving integration and its evidence. It does not install a service, start a model, create an automation or supply a general Work Shards scheduler.

## What is available here

| Item | Location | Use |
|---|---|---|
| Recorded configuration and pins | [recorded-recipe.yaml](recorded-recipe.yaml) | Inspect the candidate geometry, model/build identities and environment values |
| Integration notes | [implementation.md](implementation.md) | Understand the unequal-owner and persistent-spill work |
| Curated results | [evidence.md](evidence.md), [evidence-summary.json](evidence-summary.json) | Read measured outcomes, context sizes, acceptance and limits |
| Work Shards direction | [work-shards.md](work-shards.md) | Understand manual selection, saved sets and planned preparation |

The source implementation uses a pinned TensorFold build and modified two-rank recipe. The image digests identify the builds that produced the evidence; they are not registry download URLs. The portable patch/build bundle, deployment launcher and model weights are not distributed by this documentation package. Internal operating scripts and machine-specific paths have deliberately not been copied here.

## Recorded deployment prerequisites

The demonstrated configuration used two 128 GB GB10-class DGX Sparks, tensor parallelism across two ranks, CUDA, an RDMA interconnect and local NVMe storage on both ranks. It used the pinned DeepSeek-V4.1-Flash-1017 EXL3 checkpoint and overlay in the recipe. Exact model/build identity and compatible checkpoint interpretation matter to reuse.

The upstream starting point is [Mia's pinned two-Spark recipe](https://github.com/MiaAI-Lab/DeepSeek-v4.1-Flash-1017-2x-DGX-Sparks/tree/f424dfe3b14ac9f02fe12f5777c852dba967a79a). Its instructions describe that upstream version. Applying the TensorShard environment values to an unmodified upstream engine is not evidence that unequal ownership or the combined spill path is supported; the recorded source integration is part of the configuration.

There is consequently no invented install or launch command in this README. The archived recipe is a configuration record rather than an executable manifest. Its readiness entries describe the historical qualification, not a request to repeat those experiments.

## Demonstrated DSH usage

The application-level result used installed **DSH 0.2.1-rc.5** with native tools. The initial headless tasks created actual saved sessions in isolated workspaces. The one-shot headless runner did not expose the required resume path, so a small controller used the installed SDK JSON-RPC interface for subsequent turns:

```text
initialize
session/resume   — existing session ID, original workspace
session/prompt   — new readiness or work request
session/wait     — wait for the application turn to finish
shutdown
```

The controller selected the existing native model route. Request capture explicitly set thinking off, greedy sampling and a 4,096-token output cap for the comparison. The real DSH application retained its model loop, tools and persisted history. An independent checker confirmed the generated source against frozen tests.

The warm comparison excluded the initial coding tasks and the eight short readiness replies. Only the subsequent eight revisions were timed. Resumption therefore meant continuity of real application sessions, not sending a fabricated transcript through a separate model loop. See [the recorded method and results](evidence.md).

This sequence documents a supported building block. It is not a public CLI quickstart for every DSH installation, a new prefill-only API, or a claim that the other proposed application adapters are implemented.

## Day-to-day intent

Use saved application sessions and meaningful project context. Retain source files and conversations in their normal stores independently of KV caching. Treat a compatible resident prefix as the cheapest return path, a committed NVMe checkpoint as a second path, and recomputation as necessary when compatible cached state is unavailable.

The proposed Work Shards helper would coordinate that preparation across selected profiles while preserving room for growth and ad-hoc work. A 05:00 preparation time remains an example product experience. This package does not create that schedule or change a live serving configuration.
