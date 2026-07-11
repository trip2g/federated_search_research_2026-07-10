# v6 — engine vs models: trip2g on qmd's models (EmbeddingGemma + Qwen3)

**TL;DR: the sweep that was unrunnable on CPU has now run on Apple-silicon
Metal — and the model swap buys nothing on accuracy.** Same engine (trip2g),
same clean 924-note vault, qmd's models (EmbeddingGemma-300m 768d +
Qwen3-Reranker-0.6B) instead of bge-m3 + bge-CE: correctness 9/24 vs v5's
8/24, hard misattribution 17 vs 12 under one mechanical bilingual filter
(same scale, same failure pattern), provenance still near-perfect (42/43,
0 fabricated). The confusion failure tracks the flat corpus, not the models —
now shown by direct measurement, not inference. On latency, Metal moves Qwen3
from "unservable" (~3.5 s/passage CPU, 408s at the app deadline) to **0.14
s/passage — a full reranked search at the product default top_n=50 in
median 7.6 s**, 5× faster than v5's bge-on-CPU (37 s). But naive torch/MPS
serving is NOT turnkey: it took four fixes (fp16, micro-batching, a process
lock, explicit cache release) to stop the sidecar from OOMing, crashing, and
degrading request-over-request. llama.cpp/GGUF (qmd's approach) gets all of
that for free.

Completed on a MacBook M3 Max (48 GB), 2026-07-11; the earlier CPU-VM attempt
and its findings are preserved below. Harness:
[`flat_hybrid_clean_bench.py`](./flat_hybrid_clean_bench.py) (v5's, env-swapped);
raw runs: [`logs_engine_swap/`](./logs_engine_swap/); rollup:
[`results/summary_engine_swap.json`](./results/summary_engine_swap.json).
Setup/fix log: `~/projects/research_fixes.md`. Sweep cost $0.107, no halt.

## What was tested

Hold the engine constant (trip2g, clean 924-note vault from
[v5](./RESULTS_flat_hybrid_clean.md)), swap the models to qmd's:

| | embedding | reranker | hardware |
|---|---|---|---|
| trip2g+bge (v5) | BAAI/bge-m3, 1024d | bge-reranker-v2-m3 (cross-encoder) | CPU (Linux VM) |
| trip2g+qmd-models (this) | EmbeddingGemma-300m, 768d | Qwen3-Reranker-0.6B (LLM yes/no logit) | **Metal (M3 Max)** |
| qmd engine ([RESULTS_qmd.md](./RESULTS_qmd.md)) | EmbeddingGemma-300M GGUF | Qwen3-Reranker-0.6B GGUF | CPU (Linux VM) |

The retriever sidecar (`retriever/` on trip2g branch
`feat/memcli-embedded-reranker`) runs **natively** on the Mac (Docker on macOS
gives containers no Metal access); the app container reaches it via
`host.docker.internal`. Both models selected by env, Qwen3 scored with the
official yes/no-logit template. Reranker `top_n=50` — the product default,
no CPU-era cut to 10.

## Finding 1 — the live model+dimension swap is hands-off (product finding)

Held from the CPU attempt and reconfirmed on the Mac from a fresh vault:
bge-m3 1024d → EmbeddingGemma 768d needs only new FEATURES values (`model`,
`dimensions: 768`, EmbeddingGemma's documented `query_prefix`/
`passage_prefix`). The embedding config is part of the note-content hash, so
`regenerate_note_embeddings` re-enqueues everything itself; stale-dimension
vectors are skipped at query time (search degrades to BM25, never breaks).
Indexing 925 notes took **~5 min on Metal** (~55 min on the VM's CPU).
`google/embeddinggemma-300m` is gated on HF; the ungated
`unsloth/embeddinggemma-300m` mirror was used.

One product bug surfaced by the Mac run: the snippet highlighter in the
current `ghcr.io/trip2g/trip2g:latest` cuts highlight windows at byte, not
rune, boundaries — Cyrillic snippets can carry invalid UTF-8 into the GraphQL
JSON (orphaned continuation byte at window start, half a rune at end). The
harness now decodes with `errors="replace"`; the server-side fix belongs in
the highlighter.

## Finding 2 — Qwen3 latency: unservable on CPU, servable on Metal, but not free

| | CPU (VM, v6 first attempt) | Metal (M3 Max, this run) |
|---|---|---|
| warm, per passage | ~3.5 s | **~0.14 s** (~25×) |
| rerank 50 passages (product top_n) | est. 5–6 min | 3.6–7.6 s |
| full hybrid search, reranked @ top_n=50 | 408s / abandoned | **median 7.6 s, p90 9.1 s** (24-run sweep, n=98 searches) |
| v5 baseline (bge-CE, CPU) for the same search | median 37.3 s, p90 55.8 s | — |

So the same stack that flirted with the server's 60 s deadline on CPU now
answers in single-digit seconds — 5× faster than the bge arm ever ran on its
CPU box — and the 24-run sweep completed with **zero timeouts**.

The caveat that belongs in any reproduction attempt: **naive torch/MPS serving
degraded to unservable within ~10 requests** until four fixes landed in the
sidecar (all in `retriever/server.py` on the branch):

1. **Micro-batched rerank scoring** (batch 8): a single padded batch of 50
   real passages OOMs MPS — the LM head materializes batch×seq×vocab logits
   (~19 GiB requested).
2. **One process-wide inference lock**: FastAPI's thread pool issued
   concurrent encode/predict calls; torch-on-MPS answered with heap
   corruption inside the MPSGraph/MLIR compiler (SIGABRT) — the process
   simply died mid-sweep.
3. **fp16 for the reranker** (fp32 softmax at the end): halves the activation
   footprint.
4. **`torch.mps.empty_cache()` after every request**: the MPS caching
   allocator grows monotonically across differently-shaped batches; left
   alone, query embeds degraded 0.15 s → 34 s and reranks 8 s → 25 s as the
   process slid into swap.

Even on a top-end M3 Max the interactive verdict is qualified: ~7 s per
search is *servable* (it clears every timeout with 8× headroom) but not
*snappy*, and the per-passage cost is only at parity with a small
cross-encoder on CPU. qmd sidesteps this entire class of problems by running
quantized GGUF models in-process via llama.cpp, which has a native Metal
backend and no torch allocator. For trip2g the strategic reading: a
llama.cpp-backed sidecar speaking the same TEI wire would beat torch/MPS on
both robustness and memory.

## Finding 3 — no accuracy case for the swap (now measured, not inferred)

Full 24-run sweep (nano+mini × EN+RU × 6 questions), identical harness,
judges, and cite-and-verify metric as v5. `misattr` = hard flags after **one
mechanical bilingual noise filter applied identically to both arms' stored
judge outputs** (drop entries whose `belongs_to` self-declares correctness
in EN or RU, or where `attributed_to` = `belongs_to`; counts therefore differ
slightly from v5's published hand-audited numbers — the *comparison* is
filter-consistent):

| cell | correct (v5 → swap) | misattr (v5 → swap) |
|---|---|---|
| nano EN | 0/6 → 1/6 | 1 → 3 |
| nano RU | 4/6 → 3/6 | 3 → 4 |
| mini EN | 3/6 → 3/6 | 5 → 6 |
| mini RU | 1/6 → 2/6 | 3 → 4 |
| **total** | **8/24 → 9/24** | **12 → 17** |

- **Correctness: unchanged** (±1 run is noise at n=6/cell). Facts covered
  42/64 vs v5's 43/64.
- **Confusion: not cured, if anything marginally worse.** Blending flagged in
  4/24 runs in both arms. The swap arm retrieves off-corpus at 9–15% per cell
  — same band as v5.
- **Provenance: the v5 finding replicates exactly.** 42/43 judgeable
  citations name the right thinker, **0 fabricated paths** (v5: 45/45, 2
  fabricated). Forcing the claim→source binding into the output format
  remains the one intervention that reliably works.

Three-way, on the matched slice (gpt-5.4-nano, Q1–Q5, EN):

| arm | models | engine | correct | hard misattr |
|---|---|---|---|---|
| trip2g+bge, clean (v5) | bge-m3 + bge-CE | trip2g | 0/5 | 1 |
| qmd (polluted vault, n=5) | Gemma + Qwen3 GGUF | qmd | 1/5 | 3 |
| trip2g+qmd-models, clean (this) | Gemma + Qwen3 | trip2g | 1/5 | 1 |

Two engines × two model stacks, every combination lands in the same narrow
band. **The confusion failure is a property of flat semantic retrieval over
this corpus** — v4/v5's conclusion, now closed with the direct same-models
measurement that was missing.

## Honest limits

- n=6 per cell, 1 run each — differences of 1–2 runs are noise; only the
  provenance counts are large enough to lean on.
- v5 ran on CPU/Linux, this on Metal/macOS and a *fresh re-index* of the same
  vault (925 vs 924 notes — one AGENTS.md seed difference; all 925 embedded
  here vs 883/924 in v5). Engine image differs too (ghcr latest vs the
  branch build). None of these plausibly reverse an accuracy null, but they
  are not controlled.
- The misattribution filter was re-implemented mechanically; v5's published
  counts (6 EN / 8 RU) came from a hand-audited pass and differ by ±1 per RU
  cell from this recount. Both arms here use the same code path
  (see `research_fixes.md`).
- The qmd row remains n=5, one model, polluted vault — directional only.
- Latency numbers compare different hardware by design: the claim is "Metal
  makes this stack servable", not "Metal beats CPU on like hardware".

## Reproduce

```bash
# native retriever (Metal), from trip2g branch feat/memcli-embedded-reranker:
cd trip2g/retriever && MODEL_NAME=unsloth/embeddinggemma-300m \
  RERANKER_MODEL=Qwen/Qwen3-Reranker-0.6B LOAD_RERANKER=1 \
  python3 -m uvicorn server:app --host 0.0.0.0 --port 8900
# app: ghcr.io/trip2g/trip2g:latest via patched memcli (FEATURES_JSON env
# override), FEATURES → host.docker.internal:8900, dimensions 768, Gemma
# prefixes, reranker top_n 50 timeout 120; CRONJOBS_RUN_ON_START=1 to index.
# See ~/projects/research_fixes.md for the full setup + gotchas.
LOG_DIR=logs_engine_swap SUMMARY_FILE=summary_engine_swap.json \
  CONDITION=flat-hybrid-qwen SEARCH_TIMEOUT=900 \
  VAULT=~/projects/trip2g_mac_vault OPENROUTER_KEY=... \
  python3 flat_hybrid_clean_bench.py   # ~$0.11, ~1.5h
```
