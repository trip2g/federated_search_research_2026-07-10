# v6 — engine vs models: trip2g on qmd's models (EmbeddingGemma + Qwen3)

**TL;DR: the model swap itself worked flawlessly — the benchmark of it could
not be run, and the reason IS the finding.** trip2g re-indexed the clean vault
onto EmbeddingGemma-300m (768d, a live dimension change) hands-off, and
Qwen3-Reranker-0.6B served through the product's rerank stage — but at
~3.5 s per passage on CPU (~25× slower than bge-reranker-v2-m3), a reranked
search takes 40–70 s even with the candidate set cut from 50 to 10, and the
app's own HTTP deadline sometimes expires first (408). A stack whose single
search flirts with the server timeout is not benchmarkable and not shippable:
the 24-run sweep was abandoned after its probe query 408'd, per plan.
**Verdict: the alternative reranker is not worth it on CPU** — no accuracy
evidence in its favor (the qmd arm, which uses the same Qwen3 reranker family,
showed the *same* confusion failure as trip2g+bge), and a latency penalty that
crosses from "slow" into "unservable."

## What was tested

Hold the engine constant (trip2g, clean 924-note vault from
[v5](./RESULTS_flat_hybrid_clean.md)), swap the models to qmd's:

| | embedding | reranker |
|---|---|---|
| trip2g+bge (v5) | BAAI/bge-m3, 1024d | BAAI/bge-reranker-v2-m3 (cross-encoder) |
| trip2g+qmd-models (this) | EmbeddingGemma-300m, 768d | Qwen/Qwen3-Reranker-0.6B (LLM yes/no logit) |
| qmd engine ([RESULTS_qmd.md](./RESULTS_qmd.md)) | EmbeddingGemma-300M GGUF | Qwen3-Reranker-0.6B GGUF |

The retriever sidecar (`retriever/` on trip2g branch
`feat/memcli-embedded-reranker`) selects both models by env
(`MODEL_NAME`, `RERANKER_MODEL`); Qwen3 gets the official yes/no-logit scoring
backend rather than the CrossEncoder path.

## Finding 1 — the live model+dimension swap is hands-off (product finding)

Swapping a running instance from bge-m3 (1024d) to EmbeddingGemma (768d)
required only new env/FEATURES values (`model`, `dimensions: 768`, and
EmbeddingGemma's documented prompts as `query_prefix`/`passage_prefix`) —
no manual index wipe, no migration:

- the embedding config is part of the note-content hash, so the
  `regenerate_note_embeddings` cron re-enqueued **all 924 notes by itself**;
- stored 1024d vectors are skipped (dimension mismatch) at query time until
  replaced, so search degrades to BM25 instead of breaking;
- re-index took ~55 min on CPU (~16 notes/min — comparable to bge-m3 despite
  the smaller model).

Two deployment notes: `google/embeddinggemma-300m` is **gated** on HF (401
without an accepted license + token); the ungated `unsloth/embeddinggemma-300m`
mirror (same weights, full sentence-transformers stack) was used instead. And
retrieval quality passed the smoke probe: the RU will-to-power paraphrase
returned `nietzsche/concepts/volya_k_vlasti` first — subjectively a cleaner
top-5 than bge-m3 gave the same query in v4/v5.

## Finding 2 — Qwen3-Reranker on CPU: from slow to unservable

Measured on this arm64 box (same conditions as the v5 bge numbers):

| | bge-reranker-v2-m3 | Qwen3-Reranker-0.6B |
|---|---|---|
| cold first call | ~28 s | ~30 s |
| warm, per passage | ~0.14 s | **~3.5 s** (~25×) |
| 30 medium passages | ~7 s | ~105 s |
| full search @ top_n=50 (v5 default) | 25–35 s | est. **5–6 min** |
| full search @ top_n=10 | — | 40–70 s |

At the product default (rerank top 50 candidates) a single search costs 5–6
minutes — an 8–10 h sweep, abandoned before starting. Even after cutting
`top_n` to 10 (a documented deviation), the 40–70 s search runs into the app's
own HTTP request deadline: the sweep's very first probe query got **HTTP 408**
from the GraphQL endpoint and the harness exited; a manual retry of the same
search returned 200 in 41.6 s. That flakiness is the practical ceiling: when
p50 latency sits at the server's timeout, half your searches fail regardless
of quality. (The graceful-degradation path from v4 — rerank timeout → RRF
order — does not help here, because it is the *outer request*, not the rerank
call, that dies.)

LLM-logit rerankers of this class need a GPU to be interactive; on commodity
CPU they are not a drop-in alternative to a small cross-encoder.

## Finding 3 — no accuracy case for the swap (3-way, with caveats)

No sweep ran on trip2g+qmd-models, so there is no direct accuracy row for it.
The best available evidence is the qmd arm, which used the **same**
EmbeddingGemma + Qwen3 models inside a different engine, on the matched slice
(gpt-5.4-nano, Q1–Q5, polluted 1344-note vault):

| arm | models | correct | hard misattr | per-query tool time |
|---|---|---|---|---|
| trip2g+bge, clean (v5, nano EN, Q1–6) | bge-m3 + bge-CE | 0/6 | 1 | ~25–35 s |
| trip2g+bge, polluted (v4, nano, Q1–6) | bge-m3 + bge-CE | 1/6 | 3 | ~25–35 s |
| qmd engine (nano, Q1–5, polluted) | EmbeddingGemma + Qwen3 | 1/5 | 3 | ~2.4 min (~4.5×) |
| trip2g+qmd-models (this) | EmbeddingGemma + Qwen3 | — abandoned — | — | 40–70 s @ top_n=10, 408-flaky |

Same correctness, same misattribution count, same failure *pattern*
(success-literature corpora invading will/drive questions; comparison notes
blended) on both model stacks. Nothing in that table suggests Qwen3/Gemma
would have improved trip2g's accuracy or confusion — and it costs 25× the
rerank compute. The confusion failure tracks the *flat corpus*, not the
engine or the models: that is now shown across three stacks
(v4/v5 trip2g+bge, qmd, and — by failure mode — the walled hub itself).

## Honest limits

- The abandoned sweep means "no accuracy difference" is an inference from the
  qmd arm, not a measurement of this exact stack. If a GPU box appears, the
  sweep is one command away (below).
- The probe crash was partly a harness bug: HTTP 408 raises `HTTPError`,
  which the retry wrapper (built for `TimeoutError`/`OSError`) did not catch,
  so the probe made a single attempt. With a retry it might have limped
  through — into 8-per-question searches each flirting with the same 408.
  The conclusion stands; the mechanism is worth recording.
- qmd's row is n=5, one model, on the polluted vault (its run predates the
  dedup) — directional only.
- `top_n=10` vs v5's 50 means the latency rows compare different work per
  query; the per-passage number (3.5 s vs 0.14 s) is the clean comparison.

## Reproduce

```bash
# retriever with qmd's models (image built from trip2g:feat/memcli-embedded-reranker retriever/)
docker run -d --name <name>-embedding --network <name>-net -p 127.0.0.1:24093:8000 \
  -v /mnt/extssd/models:/data \
  -e MODEL_NAME=unsloth/embeddinggemma-300m \
  -e LOAD_RERANKER=1 -e RERANKER_MODEL=Qwen/Qwen3-Reranker-0.6B \
  trip2g-embedding-server
# app FEATURES (custom model = explicit overrides):
#   vector_search: { model: "unsloth/embeddinggemma-300m", dimensions: 768,
#     max_input_tokens: 2048,
#     query_prefix: "task: search result | query: ",
#     passage_prefix: "title: none | text: ",
#     reranker: { enabled: true, model: "Qwen/Qwen3-Reranker-0.6B",
#       top_n: 10, timeout_seconds: 600, base_url: "http://<name>-embedding:8000/rerank" } }
# then trigger regenerate_note_embeddings and wait for the re-index; sweep:
LOG_DIR=logs_engine_swap SUMMARY_FILE=summary_engine_swap.json \
  CONDITION=flat-hybrid-qwen SEARCH_TIMEOUT=900 \
  VAULT=~/projects/trip2g_all_kbs_clean python3 flat_hybrid_clean_bench.py
```
