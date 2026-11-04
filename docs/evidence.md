# Evidence summary

This document records bounded measurements of the TensorShard serving candidate on 4 November 2026. The serving integration was exercised; the general Work Shards helper remains planned. Exact configuration is in the [recorded recipe](recorded-recipe.yaml), and the application-preparation direction is in [Work Shards](work-shards.md).

## Measured source-project work

The writing, code, DSH and sequencing runs used thinking disabled. The first three generation rows used eight agents on the C12 engine. Writing/code used custom Python drivers and synthetic near-200k histories; they were not Codex-harness runs. DSH used its actual application loop, native tools and eight exact saved sessions, with 27,427–32,496-token contexts.

- Writing r2: 16 complete calls, 16,416 output tokens, 158.622 s, **6,209.49 tok/min**, 98.9367% prefix reuse. Eight fictional initial briefs and eight revisions passed the mechanical workflow checks. All documents were 650–1200 words; 7/16 were approximately 800–1000 words. They require editorial/domain review and are not deployment documents.
- Code r2: 48 complete calls, 19,433 output tokens, 185.448 s, **6,287.37 tok/min**, 98.6807% prefix reuse. Eight initial modules and eight revisions passed. Independent validation of the generated code passed 104 test-method executions: 48 initial and 56 revision. The eight variants share one ordered-iterable algorithm family; initial modules were 125–172 lines before the revision function was added. This is not a large-application or general software-quality evaluation.
- DSH warm-revision r2: 34 native model calls, 9,585 output tokens, 93.501 s, **6,150.74 tok/min**, 93.0457% prefix reuse, eight revisions passed with 56 real test checks. Separate warm controls produced eight READY sessions in 9.757 s at 95.237% reuse. This is actual DSH/native evidence, distinct from custom Python fixture checks. The cold setup result is preserved but excluded from this headline.
- Completion-driven sequencing: six bounded arms recorded 72 validated edits and 72 completed handoffs. Client admission eight pooled **4,373.47 tok/min**; admission twelve pooled **4,472.15 tok/min**, a 2.26% difference. Task throughput was effectively tied: 6.568 versus 6.549 checked tasks/min. Both limits used the same C12 engine; this is not a native C8-versus-C12 deployment comparison.

The writing and code arms used 0.25-second initial staggering and immediate independent follow-ups after model/tool completion. DSH used the same initial staggering for its resumed revisions. All 16 writing, 48 code and 34 measured DSH calls completed without request/runtime faults. DSH's full 93.501-second window includes client startup, model/tool work, final replies, independent validation and shutdown. Its narrower request window is not the headline rate. Initial coding work and readiness turns are preparation, excluded from the timed DSH result.

## Historical storage evidence

A separate historical NVMe owner-restore measurement on the earlier C8 candidate used a 196,106-token input: cold TTFT 88.3685 s, RAM TTFT 1.2778 s, and disk TTFT 5.1893 s under four active agents (17.03× cold-to-disk). Output hashes matched and the subsequent checked continuation passed. This is a specific first-token comparison, not a 17× end-to-end productivity claim or a universal restore-time guarantee.

## Boundaries

Initial setup and cold history preparation are excluded from warm-throughput rates. “Time to checked outcome” includes model retries and local validation when those occur; a successfully corrected task remains a completed task. Output counts include intermediate model output and tool arguments, not final source-code tokens alone. Writing checks cover supplied facts, required sections and revised values; they do not establish general factual accuracy, and sampled design assumptions need editorial review.

The custom-driver runs exercise real model generation and real local file/test operations, but do not establish Codex application behaviour. DSH is the measured application-level exception: the installed SDK resumed its own saved sessions and original workspaces. Its revision-only workload and smaller contexts prevent treating similar token rates as equal harness overhead. General Work Shards integrations and current warm multi-agent Codex performance remain unmeasured.

Long-context extraction, harder thinking-enabled planning, substantial external tool waits and sustained dormant-project rotation with foreground responsiveness remain expected/inferred rather than tested as proposed end-to-end workloads. Earlier bounded controls retain their stated scope. Historical copy-heavy 9.5–10k tok/min output is a separate workload; the older stock-C4 comparison is a modelled counterfactual rather than a measured A/B. None establishes an all-day rate.

Initial harness-invalid writing/code attempts and pre-inference DSH startup failures were preserved and excluded from the measured rows. Their exclusion and the distinct cold/prewarm/measured phases remain part of the source record.

The JSON companion contains curated numeric excerpts and SHA-256 provenance for the saved result records. It intentionally does not reproduce raw transcripts or private infrastructure details; the excerpts are not a complete public raw archive.

## Reproduction boundary

The recorded runs and full receipts remain preserved in the source project. This package includes curated numeric excerpts and content hashes instead of private transcripts, machine identities or operational paths. No new inference, benchmark campaign, model reload, scheduler or serving change was needed for this documentation pass.
