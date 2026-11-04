<div align="center">

![TensorShard](https://abliter8-ai.b-cdn.net/a8-github/54D4B58F-C3FC-4793-A336-2A87053A679D.jpeg)

# TensorShard

**Your local agents, prepared for the working day.**

<p>
<img src="https://img.shields.io/badge/hardware-2%C3%97_DGX_Spark-FF093A?style=for-the-badge&labelColor=0D0D0D" alt="Hardware: two DGX Sparks">
<img src="https://img.shields.io/badge/serving_recipe-recorded_candidate-FF093A?style=for-the-badge&labelColor=0D0D0D" alt="Serving recipe: recorded candidate">
<img src="https://img.shields.io/badge/Work_Shards-planned-FF093A?style=for-the-badge&labelColor=0D0D0D" alt="Work Shards: planned">
</p>

[Project](https://github.com/abliter8-ai/Deepseek-v4.1F-TensorShard) · [Working day](#overview) · [Memory tiers](#how-it-works) · [Work Shards](#work-shards) · [Getting started](#how-to-start) · [Evidence](#evidence)

</div>

---

**TensorShard helps a pair of DGX Sparks retain more agent context and resume work with less repeated prefill.** It combines a tuned TensorFold serving recipe, unequal KV ownership and NVMe-backed restoration to keep a larger working set of local agent histories available.

The serving integration and recorded DSH session resumption are demonstrated. **Work Shards**, the proposed layer for selecting and preparing daily agent contexts, remains planned. This repository packages the recorded configuration, integration notes and curated evidence; it does not yet ship a portable installer or the general preparation helper.

<a name="overview"></a>
## <img src="https://get.abliter8.ai/doc-assets/overview-intro.png" alt="Overview" height="58">

A working agent carries more than the latest question: repository instructions, `AGENTS.md`, tools, skills, documentation and conversation history. Its day alternates between generating, using tools, waiting and returning. Switching projects can mean returning to several substantial contexts.

Repeatedly computing the same prefix adds waiting and consumes capacity that could serve useful work. TensorShard combines more retained KV capacity with a second return path on NVMe. The intended experience is a local team ready to resume: coding agents, assistants, a researcher and a prompt writer, with room for ad-hoc requests.

Prewarming moves predictable preparation into quiet periods. Retention and restoration reduce how often it must be repeated. The first computation still costs time; the benefit comes from when it happens and how often it can be reused. Saved conversations remain distinct from the cached computation used to serve them.

<a name="what-it-does"></a>
## <img src="https://get.abliter8.ai/doc-assets/features-whatitdoes.png" alt="What it does" height="58">

The recorded candidate uses two 128 GB GB10-class DGX Sparks, TensorFold, and DeepSeek-V4.1-Flash-1017 with the pinned Mia EXL3 EAQ 2.9-bpw checkpoint and Keys attention overlay. Configuration status remains **draft**; the recorded measurements are dated **4 November 2026**.

| Recorded capability | Configuration | Working-day benefit |
|---|---|---|
| Shared KV arena | **4,198,400 logical positions** | A larger working set of retained histories |
| Unequal ownership | **513 head / 1,537 worker blocks**, 2,048 positions per block | Places more KV on the worker, which has more spare memory |
| Active generation | **Up to 12 concurrent sequences** | Slots for competing active turns |
| Per-request context | **1,048,576 tokens** | A separate limit for one request |
| Persistent spill | **4 GiB NVMe store per rank** | A return path for compatible committed checkpoints beyond RAM |
| Restore handling | Bounded admission and corrected first-request context binding | Capacity contention can wait and retry instead of immediately triggering cold prefill |

Exact model, image, patch and environment pins are in the [recorded recipe](docs/recorded-recipe.yaml). The [implementation notes](docs/implementation.md) explain the integration and its inherited mechanisms.

<a name="how-it-works"></a>
## <img src="https://get.abliter8.ai/doc-assets/howitworks-function.png" alt="How it works" height="58">

The head has more model/runtime responsibilities. Unequal KV placement uses the worker's greater remaining memory: **1,050,624 positions on the head** and **3,147,776 on the worker**. It improves usable retained capacity without adding physical bandwidth or removing compute, communication and thermal limits.

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#FF093A','primaryTextColor':'#ffffff','primaryBorderColor':'#7a0620','lineColor':'#FF093A','secondaryColor':'#1b1b1b','secondaryTextColor':'#ffffff','tertiaryColor':'#1b1b1b','tertiaryTextColor':'#ffffff','clusterBkg':'#0d0d0d','clusterBorder':'#FF093A','fontFamily':'monospace'}}}%%
flowchart LR
    A[Returning application turn] --> B{Compatible prefix available?}
    B -->|RAM| C[Reuse resident KV]
    B -->|Committed NVMe checkpoint| D[Admit and restore on owning ranks]
    B -->|Cache miss| E[Compute missing prefix]
    C --> F[Process new suffix]
    D --> F
    E --> F
    F --> G[Generate and use application tools]
```

The **4.20M pool**, **1M request limit** and **12 active sequences** answer different questions. Twelve generation slots are not a twelve-history retention limit. Dormant retained contexts use cache capacity while slots serve other work. Growth, allocation overhead and the active working set still need headroom.

The **1 GiB prompt-state cache** has a different role from the KV arena; their sizes are not interchangeable token capacity. NVMe holds compatible checkpoints subject to commit, retention, quota and configuration limits. It is not conversation backup or an unlimited archive. Prefix changes, tool changes and compaction can reduce reuse. More retained capacity does not imply a proportional rise in single-stream decode speed.

<a name="work-shards"></a>
## Work Shards — planned

A **Work Shard** is a named agent, project or workspace context you want prepared. It is a logical preparation profile, separate from a physical tensor shard or a rank's KV ownership.

Select a saved set, prepare it now or during a quiet period, and return to those applications when work starts. A proposed 05:00 schedule is an example of the experience, not an installed automation. The helper should reuse compatible resident state, resume saved sessions or restore checkpoints where supported, and refresh only what needs preparation.

| Example Work Shard | Intended context |
|---|---|
| Codex — `abliter8-fleet-cluster` | Repository work using local models exposed in the Codex app |
| DeepSeek harness — `rpstudios` | The project's DSH session and workspace |
| Professional productivity | Professional projects and their working material |
| Personal Hermes | The main personal assistant |
| Work Hermes | The work assistant |
| OpenWebUI researcher | The frequently used research agent |
| OpenWebUI image-prompt writer | The frequently used image-prompt-writing agent |

These seven profiles are an example selection, not a fixed population or a claim that these integrations ship today. Leave capacity for conversation growth and unplanned work. Existing applications keep their loops, tools, retries, transcripts and checks; the helper coordinates preparation and resumption.

The demonstrated building block is **eight real DSH sessions resumed in their original workspaces to perform checked code revisions**. A general selector, scheduler and integrations across the example applications remain planned. Preparing an unrelated request from concatenated repository files does not automatically warm an application's next turn. [Work Shards design and status](docs/work-shards.md).

<a name="how-to-start"></a>
## <img src="https://get.abliter8.ai/doc-assets/quickstart.png" alt="How to start" height="58">

Start with the [setup and usage notes](docs/setup-and-usage.md), then the [recorded recipe](docs/recorded-recipe.yaml). They distinguish the demonstrated configuration, the real DSH resume path and what this public package contains.

The image digests are evidence identities, not published image download locations. The [upstream recipe](https://github.com/MiaAI-Lab/DeepSeek-v4.1-Flash-1017-2x-DGX-Sparks/tree/f424dfe3b14ac9f02fe12f5777c852dba967a79a) describes its own setup; reproducing TensorShard also requires the recorded unequal-owner and spill integration.

<a name="evidence"></a>
## <img src="https://get.abliter8.ai/doc-assets/whyitworks.png" alt="Why it works" height="58">

### Measured results

**Measure time to a checked outcome, including retries and tools.** A corrected attempt is still a successful task. Output rate is useful alongside returning-turn latency, completed work and the human intervention needed to keep it moving.

| Recorded workload | Result | What was checked |
|---|---|---|
| Eight warm writing agents, custom driver | **6,209 output tok/min**, 98.94% prefix reuse | 8 original briefs + 8 revisions; stated fact and structure checks |
| Eight warm coding agents, custom driver | **6,287 output tok/min**, 98.68% reuse | 8 new modules + 8 revisions; 48 initial + 56 revision test-method executions passed |
| Eight resumed **DSH** sessions | **6,151 output tok/min**, 93.05% reuse, **93.501 s** | 8 revisions; all 56 frozen checks passed through real application tools |
| Historical C8, approximately 196k-token return | TTFT: **88.37 s cold**, **1.28 s RAM**, **5.19 s disk** under four active agents | A concrete cold-to-disk first-token improvement of about **17×** |
| Client admission of eight versus twelve on the same C12 engine | **4,373 vs 4,472 output tok/min**, pooled | 72 checked edits and 72 handoffs across six arms; task throughput effectively tied |

The first three rows used eight agents with thinking disabled. The custom writing/code histories were synthetic and near 200k tokens; they were **not Codex-harness runs**. DSH used its actual application loop with approximately 27–32k contexts, and its measured task was revision only. Similar rates do not establish equal harness overhead. Current warm multi-agent Codex performance remains unmeasured.

Initial preparation is excluded. DSH's full timed window includes client startup, tools, final replies, validation and shutdown. Output counts include intermediate model output and tool arguments, rather than only final source-code tokens. Code cases share one algorithm family; writing used fictional briefs, with all outputs inside 650–1,200 words and seven of sixteen inside the approximate 800–1,000-word target. These checks establish the stated outcomes, not universal model quality.

Historical copy-heavy 9.5–10k tok/min results describe a different workload. A modelled gain over an older C4 scenario is a counterfactual, not a measured stock-versus-TensorShard A/B. The admission row also compares client limits on one C12 engine, not native C8 versus C12 deployments. These bounded results do not promise an all-day rate or qualify every application, compaction, reasoning or long-tool workflow. [Methods, limits and curated receipts](docs/evidence.md).

<a name="acknowledgements"></a>
## <img src="https://get.abliter8.ai/doc-assets/acknowledgements.png" alt="Acknowledgements" height="58">

TensorShard builds on [DeepSeek](https://huggingface.co/deepseek-ai), [Mia's EXL3 quantization](https://huggingface.co/Mia-AiLab/DeepSeek-V4.1-Flash-1017-EXL3-EAQ-v1-2.9-bpw) and [two-Spark recipe](https://github.com/MiaAI-Lab/DeepSeek-v4.1-Flash-1017-2x-DGX-Sparks), the [Keys overlay by drowzeys](https://huggingface.co/drowzeys/keys-DeepSeek-V4.1-Flash-1017-Abliterated), [TensorFold](https://github.com/ashhart/TensorFold), and [sehoon's tuned recipe](https://github.com/sehoon123/DeepSeek-v4.1-Flash-1017-2x-DGX-Sparks-Tuned/tree/0700221). Prefix caching, speculative decoding, KV sharding and NVMe caching predate this project.

The specific contribution is making unequal worker-heavy ownership work across allocation, addressing, movement, kernels and compatibility, then integrating owner-aware spill packing, ordered rank coordination and restore/teardown corrections. The workflow direction is to put that retained capacity behind a user's daily selection of agents and projects. [Implementation and upstream attribution](docs/implementation.md).
