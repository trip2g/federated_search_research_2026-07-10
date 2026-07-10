# qmd results — an off-the-shelf hybrid over the same flat pile (PARTIAL)

> **Status: partial run.** gpt-5.4-nano, questions 1–5 only. The harness
> process died mid-Q6 (the box dropped to ~300MB available; an OOM kill is the
> likely but unconfirmed cause), and gpt-5.4-mini never started — the box was
> needed for the next experiment before a ~2h re-run was justifiable. Treat
> every number below as n=5, one model, one run.

**TL;DR: on the matched slice (nano, Q1–Q5), the off-the-shelf qmd stack lands
almost exactly where trip2g's own flat-hybrid landed — same correctness (1/5),
same audited hard-misattribution count (3), same confusion *pattern*
(success-literature corpora invade will/drive questions; comparison notes get
blended) — while being ~4.5× slower per query on CPU.** The headline is that
two completely different hybrid stacks (different embedder, different
reranker, different fusion code) over the same flat pile produce the same
failure mode. That strengthens the v4 reading: the confusion is a property of
*flat retrieval over this corpus*, not a quirk of one engine.

## The arm

Same ~1344-note vault as [v4](./RESULTS_flat_hybrid.md), third independent
retrieval stack: [qmd](https://github.com/tobi/qmd) v2.5.3, a self-contained
local hybrid engine — BM25 (SQLite FTS) + EmbeddingGemma-300M (GGUF) vectors +
Qwen3-Reranker-0.6B LLM rerank + a 1.7B query-expansion model, all local via
node-llama-cpp. The model gets ONE tool, same shape as the other flat arms:
`search(query)` → top-8 notes with paths and snippets.

Tool implementation: the harness ([`qmd_bench.py`](./qmd_bench.py)) shells
`qmd query <q> -n 8 --json` per call. That is qmd's **recommended** mode: a
single plain query triggers the implicit-expand hybrid path (BM25 probe → LLM
query expansion → vector → RRF → chunked LLM rerank). qmd's MCP `query` tool
was deliberately *not* used — it only executes pre-expanded typed sub-queries
and skips the LLM query-expansion step, so the CLI is the more faithful
"as designed" configuration. Expansion/rerank results are cached in qmd's
index, so only novel queries pay the full pipeline cost.

Judging is identical to v4: same preregistered keys
([`questions_v3.json`](./questions_v3.json)), same fact judge and
misattribution judge (gpt-5.4-nano), same 12-call cap and off-corpus metric,
same "hard misattribution" filter (drop the judge's self-declared non-errors).

## Two apples-to-apples caveats, up front

1. **Coverage differs by construction.** qmd deduplicates by content hash:
   the 1344 files collapse to **946 unique documents** (398 of the files are
   byte-identical stale hub-card copies). trip2g's flat-hybrid embedded all
   1344. So qmd faced *less* duplicate noise than v4 did — an advantage it
   gets for free, and a reason its off-corpus numbers are not exactly
   comparable.
2. **Engine AND models differ together.** qmd = EmbeddingGemma-300M +
   Qwen3-Reranker-0.6B; trip2g flat-hybrid = bge-m3 + bge-reranker-v2-m3.
   Nothing here isolates the engine from the embedding/rerank models — a
   same-models engine-isolation run is planned separately.

## Results — nano, Q1–Q5, vs the same slice of the other arms

flat-hybrid numbers below are recomputed from [`logs_flat_hybrid/`](./logs_flat_hybrid/)
for exactly this slice (nano, Q1–Q5) with the same hard-misattribution filter,
so the rows are directly comparable. `misattr` = hard flags after filter
(audited value in parentheses — see below). `off-corpus` = retrieved notes
outside the question's expected corpora (hub notes neutral).

| arm | correct | facts | misattr | blend | off-corpus | quotes v/f | calls | $ total | tool time |
|---|---|---|---|---|---|---|---|---|---|
| qmd (this run) | 1/5 | 9/13 | 5 (3) | 1 | 55/184 (30%) | 5/22 | 23 | $0.013 | **61 min** |
| trip2g flat-hybrid | 1/5 | 8/13 | 3 (3) | 2 | 38/200 (19%) | 2/20 | 25 | $0.010 | 14 min |

Per-question (qmd): Q1 partial (2/3), Q2 **correct** (3/3), Q3 partial (2/3),
Q4 partial (1/2, off-corpus 27/40), Q5 partial (1/2, blend). Raw traces in
[`logs_qmd/`](./logs_qmd/), rollup in
[`results/summary_qmd.json`](./results/summary_qmd.json).

**The audit note on `misattr`.** qmd's 5 mechanical hard flags shrink to 3 on
inspection: both Q2 flags are contradicted by the judge's own note ("no clear
case … the answer correctly assigns") — the answer attributes everything to
the right thinker, but quotes it from `schopenhauer/concepts/nietzsche-predtecha.md`,
and the judge apparently keyed on the source folder. The surviving 3 are real:
Q4 promotes **Tolstoy** to "most direct opponent of Stoic detachment" (the
key's corpus-attested opponents are Nietzsche/Montaigne/La Rochefoucauld —
same *shape* of error as v4's Wattles case, a different wrong author), and Q5
muddles who holds which side of the Pascal–Montaigne axis (blend). The
flat-hybrid slice's 3 hard flags survive the same audit (Wattles ×2, Pascal/
Montaigne ×1).

## What it says

1. **Same pile, different stack, same confusion.** qmd retrieves the
   success-literature corpora (Wattles, James Allen, Adler, Smiles…) as
   semantic neighbors of Nietzsche-and-will questions exactly as bge-m3 did
   (Q1: 6/24 off-corpus; Q2: 11/40), and its cross-corpus questions blend the
   authored comparison notes exactly as v4's did. The wrong-opponent
   promotion (Wattles in v4, Tolstoy here) reproduces across engines. This is
   the strongest single takeaway: **flat semantic retrieval over a
   multi-author pile imports plausible wrong-author material regardless of
   whose embeddings you use.**
2. **Task metrics are a wash.** 1/5 correct both arms; 9/13 vs 8/13 facts;
   3 vs 3 audited hard misattributions. qmd's higher off-corpus rate (30% vs
   19%) partly reflects Q4, where it pulled 12 Epictetus notes (the metric
   counts them off-target because the key expects the *opponents'* corpora,
   though the question names Epictetus — true for both arms, worth knowing
   when reading the column).
3. **The cost of qmd's approach on CPU is time, and it is large.** An
   uncached `qmd query` costs ~2–3 minutes on this box — LLM query expansion
   plus reranking 40 chunks through Qwen3-0.6B (~150s measured; a cached
   repeat is ~1s). Five questions took **62 minutes of wall time, 98% of it
   inside qmd**; trip2g's cross-encoder arm did the same slice in ~15 min,
   and the run ultimately died with the box near OOM. LLM-as-reranker is
   qmd's design choice — it buys quality on paper, but on modest CPU-only
   hardware it costs ~4.5× the latency of a cross-encoder stack and a
   multi-GB model-resident footprint.
4. **qmd quoted a bit more faithfully** (5/22 vs 2/20 verified verbatim
   quotes) — its snippets are raw markdown windows, slightly longer than the
   hybrid lane's highlight fragments. Same format-artifact caveat as v3/v4:
   this measures snippet copyability as much as model faithfulness.

## Limits

- n=5 questions, ONE model, one run, no mini — differences of one run are
  noise; this is a probe of a probe. The missing Q6/mini cells may be
  completed later.
- The crash itself is only circumstantially attributed to OOM (the box was
  down to ~300MB available around that time; no kernel log was captured).
- Coverage (946 vs 1344 docs) and engine+models are confounded with the arm
  (caveats above).
- The confusion judge is the same noisy nano judge as v4 — mechanical counts
  are reported next to audited ones, and the raw judge output is kept in the
  logs.

## Reproduce it

```bash
npm install -g @tobilu/qmd          # qmd 2.5.3, node >= 22
qmd collection add ~/projects/trip2g_all_kbs --name allkbs
qmd context add qmd://allkbs "22 philosopher corpora, one flat store"
qmd embed                           # ~2GB GGUF downloads; 1504 chunks / 946 docs, ~10 min CPU
qmd query "воля к власти" -n 5 --json   # sanity: Nietzsche notes on top
export OPENROUTER_KEY=sk-or-...
make qmd                            # halts at BUDGET_USD (default 1.0)
```

Mind the RAM: qmd keeps ~2–3GB of GGUF models resident while querying, and a
cold query pins all cores for minutes. Don't run it alongside another
embedding stack on a small box — that is how this run ended.
