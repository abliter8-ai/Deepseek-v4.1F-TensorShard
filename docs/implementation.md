# TensorShard recorded implementation

Status: draft. Recorded 2026-11-04. This checkout is a public-safe descriptive archive, not a launcher or installation package.

## Scope and provenance

The candidate combines the tuned IP-447 worker-heavy layout with the selective combined spill/shard semantics from MiaAI-Lab's pinned 0019 patch. The upstream project and exact revision are recorded in `recorded-recipe.yaml`:

https://github.com/MiaAI-Lab/DeepSeek-v4.1-Flash-1017-2x-DGX-Sparks/tree/f424dfe3b14ac9f02fe12f5777c852dba967a79a

The upstream contribution supplies equal-owner combined spill packing, store/reopen flow and two-rank coordination. The candidate contribution adapts that design to unequal owners `[513,1537]`, preserves the tuned 48-row kernels and C12 controls, binds identity to the complete owner vector, and fixes owned-spill teardown after queued users drain. These are recorded contributions, not claims that the upstream patch natively provides unequal geometry.

## Memory model

The 4,198,400-position pool is compressed KV capacity in RAM. Ownership is unequal: the head owns 513 blocks and the worker owns 1,537 blocks. The owner vector is part of placement, wire identity, cache compatibility and movement decisions. The two ranks coordinate ordered range placement and restore; the owner of a range supplies its bytes, while shared index/metadata remains compatible with the paired layout.

Prompt state is separate from the Engram control. `PROMPT_CACHE_GIB=1` is the prompt-cache budget. `TF_DS_ENGRAM_CACHE_MB=1024` is the Engram cache setting. Neither enlarges the main KV pool, adds decode slots, or converts NVMe into active decode memory.

NVMe is a dormant tier. Each rank has a rank-local 4 GiB spill quota and 128 MiB staging area, with a 50 GiB free-space floor and a 4,096-token minimum stored prefix. A committed snapshot records the complete layout identity, owner/range information, valid extent and bytes. Restore must place each range on its owning rank and preserve ordered coordination across both ranks. The bounded policy allows two restores and four readers with a 30-second deadline; capacity refusal waits and retries while decode continues.

## Runtime controls

The tuned runtime keeps `TF_DS_ROUND_ROWS=48` and `TF_DS_COPY_ROWS=48`, with copy multi/self caps of 15. `TF_DS_PAIR=0` keeps prefill pairing disabled. C12 uses 12 streams and a 1,048,576-token request window. Prefill nesting is 16,384 tokens and interleave is 250 ms. KV sharding and spill carry/twins/ring/overlap remain enabled. The full exact values are in `recorded-recipe.yaml`.

The model and overlay pins are independent from cache identity. The model is the pinned Mia EXL3 EAQ 2.9-bpw checkpoint with the Keys attention overlay and FP4 KV cache. The engine identity and recipe-patch identity must remain unchanged for stored bytes to be interpreted safely; changing model/overlay pins is not a compatible cache reuse operation.

## Addressing, movement and teardown

The planner addresses ranges from the explicit owner vector, not from an equal split. Admission and movement carry the range base/end, owner and layout identity. Fetch/carry decisions use the owner map, and follower state is restored before a request can consume moved KV. Wire handshakes exchange and validate the complete vector, model/runtime identity, layout version and block format; mismatched totals or splits are rejected.

Store commits are transactional. Incomplete or cancelled writes are not publishable. Reopen validates checksums and extent bounds before placement. The final worker block and a moved extent boundary are first-class compatibility cases. Teardown drains queued work and detaches KV/spill references before destroying the tier, then releases the owned spill object through its destructor. This ordering prevents the head-owned spill lifetime omission found in the earlier path.

## Compatibility and qualification boundary

The candidate preserves the tuned CUDA/kernel path and 48-row scheduler behavior. The archive records source, image, model, quantization, overlay and environment pins separately so a future launcher can reproduce the identity without copying private deployment details. Readiness requires exact greedy references, both rank identities, owner capacities, commit/restore counters, physical read receipts, memory guards and bounded restore success. The recipe remains `draft`; this document does not claim public adoption, installation, serving, or production qualification.
