# v4 results — flat-hybrid: no walls, real retrieval

**TL;DR: upgrading the flat pile from naive keyword search to a real hybrid
stack (BM25 + bge-m3 vectors + bge-reranker cross-encoder) did not rescue the
no-walls condition — it made confusion worse.** On the same 6 questions, the
flat-hybrid arm produced the most who-said-what errors of the three arms
(9 hard misattributions vs 7 walled, 2 naive-flat), pulled ~16% of its
retrieved notes from the wrong thinker's corpus, and scored fewer fully-correct
answers (2/12 vs 5/12 naive-flat, 8/12 walled). The mechanism is visible in the
traces: semantic search surfaces *conceptually adjacent material from the wrong
author* (self-help corpora next to Nietzsche, a hub contrast-note's "axis"
mistaken for a thinker's own position), and small models blend it. Keyword
search never offered that temptation; the walls made the source explicit.
n=6 questions, 1 run per cell — read as a probe, not a verdict.

This is the controlled comparison [v3](./RESULTS_v3.md) said it lacked: v3's
flat arm was deliberately naive (substring TF), so "walls beat flat" could just
mean "any real retrieval beats no retrieval." Now the flat arm has a serious
stack and the question is clean: **do the walls themselves — explicit corpus
identity — matter once retrieval quality is equal?** On this probe: yes, and
mostly for *attribution*, not for reaching the material.

## The arm

One trip2g instance holding all 22 corpora — **1344 notes** — as a single flat
pile: no `kb_id`, no federation, no per-thinker walls. Retrieval is the
product's hybrid search lane (`internal/case/sitesearch`): BM25 full-text +
bge-m3 chunk vectors fused by RRF, then a bge-reranker-v2-m3 cross-encoder
blended on top ([`docs/dev/reranker.md`](https://github.com/trip2g/trip2g/blob/main/docs/dev/reranker.md)).
Embedding and reranking run in one local arm64-native sidecar
(`embedding-reranker-server/`, branch `feat/memcli-embedded-reranker`) — the
whole stack is local, no external APIs.

The model gets ONE tool, same shape as v3-flat: `search(query)` → top notes
with paths and highlight snippets. It calls the GraphQL `search` endpoint
(`/_system/graphql`), because that is where the cross-encoder executes today;
the MCP `search` tool is a separate resolver that fuses BM25+vector but does
**not** yet rerank (a product gap found during this run, being fixed
separately). Verified before spending: the sidecar logs the app's completed
`POST /rerank` (200, sub-second once warm), and the top result visibly reorders
vs the degraded RRF-only order.

Two operational findings that shaped the setup (both reproduced, both matter):

- **OOM two-phase.** Indexing 1344 notes with both models resident killed the
  instance at 648/1344 on a 19GB box. Fix: index with `--embedded` only
  (~1.7GB sidecar), then restart with `--reranker` for query time.
- **Cold-start + timeout.** The first cross-encoder call after boot exceeds the
  app's default 10s rerank timeout, and reranking the default 50 candidates on
  CPU takes 15–30s — either way the app *silently degrades to RRF order*, so a
  "hybrid" benchmark can quietly not be hybrid at all. Fix: warm the CE with a
  throwaway call and set `vector_search.reranker.timeout_seconds: 60`
  (a documented knob), then confirm `POST /rerank 200` in the sidecar log
  before any paid run.

## Results (2 models × 6 questions per arm)

Walled and naive-flat rows are v3's runs ([`logs_v3/`](./logs_v3/)); the
flat-hybrid row is this run ([`logs_flat_hybrid/`](./logs_flat_hybrid/)).
`misattr` = hard misattributions: same gpt-5.4-nano confusion judge run over
**all three arms' final answers** (v3 answers judged post-hoc from stored logs,
[`results/confusion_v3.json`](./results/confusion_v3.json)), after filtering
the judge's self-declared non-errors ("X ← X, no misattribution detected" —
it pads its list; raw counts are ~40% noise). `blend` = runs the judge flagged
for merging two thinkers' positions. `off-corpus` = retrieved notes whose
corpus folder is outside the question's expected corpora (hub notes neutral;
only measurable for this run — v3 logs truncate result paths).

| model | arm | correct | facts | misattr | blend | off-corpus | quotes v/f | calls | 1st rel | $/q |
|---|---|---|---|---|---|---|---|---|---|---|
| nano | walled | **4/6** | 13/16 | 3 | 3 | — | 13/33 | 57 | 2.5 | $0.0035 |
| nano | naive-flat | 2/6 | 11/16 | **2** | 2 | — | 17/24 | **16** | **1.0** | **$0.0020** |
| nano | flat-hybrid | 1/6 | 9/16 | 4 | 2 | 39/232 (17%) | 3/22 | 30 | 2.0 | $0.0022 |
| mini | walled | **4/6** | 14/16 | 4 | 1 | — | 12/32 | 44 | 4.3 | $0.0090 |
| mini | naive-flat | 3/6 | 13/16 | **0** | 0 | — | 13/20 | **18** | **2.0** | $0.0064 |
| mini | flat-hybrid | 1/6 | 9/16 | 5 | 2 | 33/224 (15%) | 10/20 | 30 | 2.2 | $0.0071 |

Flat-hybrid run: $0.062 for 12 runs + judges; re-judging v3 for confusion:
$0.007. No budget halt ($1.0 guard, ~$3.6 on the key).

## The confusion findings

**1. Semantic retrieval imports plausible wrong-author material; models use
it.** The pile mixes philosophers with success-literature corpora (Hill,
Wattles, Adler…). A vector query about drive/will/growth retrieves them as
near-neighbors of Nietzsche — semantically fair, attributionally poisonous.
Clearest case (nano Q4, 21/48 retrieved notes off-corpus, judge: blend=true):
asked who argues against Stoic detachment, the model answered **Wattles** as
the most direct opponent, promoting a hub contrast-note's *comparison axis*
into Wattles' own anti-Stoic doctrine. The naive-flat arm never did this — TF
keyword search simply never surfaced the wrong corpus for these questions
(its worst instinct was answering thinly, not wrongly).

**2. The classic pairs blend.** Q6 (Confucius vs Laozi) drew misattribution
flags in both flat-hybrid runs — mini swapped the axis outright (govern-by-
self-correction credited to the wrong side); nano hung both quotes on the
right names but replaced the key's li-vs-wu-wei axis with a retrieval-shaped
one. Q2 (Nietzsche vs Schopenhauer) and Q5 (Pascal vs Montaigne) each drew
blend flags — the comparison *notes* (hub contrast pages, "predecessor" notes
inside a corpus) are retrieved from both sides at once, and the model merges
the axis note's framing with the thinkers' own claims.

**3. Walls don't eliminate confusion — they change its texture.** The walled
arm's 7 hard flags cluster in the cross-corpus questions too (mini Q5: Pascal's
abyss credited to Montaigne). But walled runs misattribute *within the
material they deliberately opened*, while flat-hybrid runs misattribute
because *retrieval put the wrong author on the table unasked*. With explicit
`kb_id` routing the model always knows which thinker's base it is reading;
in the flat pile the only source signal is a path prefix in the tool output,
and small models demonstrably don't respect it under blending pressure.

**4. Correctness dropped — but read this with the confound below.** 18/32
facts vs naive-flat's 24/32. Part of this is real (answers built on blended
material fail the fact key), but part is format: the hybrid lane returns
~200-char highlight windows, v3-flat returned ~900-char raw excerpts, so the
model simply has less text to state facts from — and nano's verbatim-quote
validity collapsed (3/22) for the same reason: you can't lift a 6-word verbatim
quote from a window that clips mid-sentence.

## Confounds and limits

- **Snippet length** (above) confounds the correctness and quote columns
  against v3-flat. It does *not* obviously confound the confusion counts —
  shorter snippets contain less material to misattribute, if anything.
- **The confusion judge is noisy.** gpt-5.4-nano pads its misattribution list
  with entries it itself marks as non-errors; we filtered those (filter in
  the repo, `results/confusion_v3.json` keeps raw output). The surviving
  "hard" flags were spot-audited by hand; the Wattles and Confucius/Laozi
  cases are real, one or two borderline flags likely remain in every arm.
  Between-arm *differences* of 1–2 flags are within judge noise; naive-flat's
  2 vs flat-hybrid's 9 is not.
- n=6 questions, 1 run per cell, 2 small models. Same caveats as v3.
- The corpora themselves contain authored cross-thinker notes (hub contrast
  pages, "Nietzsche as predecessor" inside Schopenhauer's base). These are
  exactly what vector search likes to return and exactly what models blend.
  That is a property of real knowledge bases, not an artifact — but it means
  "confusion" here measures the *system* (notes + retrieval + model), not the
  model alone.

## Answer to the headline question

**Does one big flat vector+reranker store confuse small models more than the
walled hub?** On this probe: **yes, somewhat — and much more than a naive flat
pile.** Ranking by hard misattributions: naive-flat 2 < walled 7 < flat-hybrid 9.
The interesting inversion: v3 concluded naive-flat's weakness was *reaching*
material; giving the flat pile semantic reach fixed that (relevant material at
call ~2, VECTOR origins dominate 92% of retrieved results) and thereby created
the attribution problem — reach without provenance. The walls' surviving value
after equalizing retrieval is not navigation (flat-hybrid navigates fine) but
**source identity**: the `kb_id` tells the model whose words it is holding.
A flat store that wants to compete on faithfulness probably needs to shove
provenance into the model's face (per-result author fields, not path prefixes)
— untested here, and a natural v5.

## Reproduce it

Everything local except the model calls. Needs the trip2g repo on branch
`feat/memcli-embedded-reranker` (arm64 and amd64 both fine — the sidecar is
the bundled native server), Docker, and the corpus vault (22 public-domain
philosopher/writer corpora, 1344 notes, one folder).

```bash
# 1. Bring up the instance with local vector search (first phase: index only —
#    on a small box don't keep the reranker resident while embedding).
cd trip2g && git checkout feat/memcli-embedded-reranker
MODELS_DIR=/mnt/extssd/models node cli/memcli/dist/memcli.js up \
  --embedded --folder ~/projects/trip2g_all_kbs --port 24091 --name allkbs

# 2. Embed all notes: trigger the regenerate_note_embeddings cron (admin GraphQL
#    runCronJob; it is otherwise weekly), then wait until the count reaches 1344:
sqlite3 ~/projects/trip2g_all_kbs/.trip2g-memory/data/local.sqlite3 \
  "select count(*) from note_version_embeddings;"

# 3. Second phase: restart with the reranker, warm the cross-encoder, and raise
#    the rerank timeout for CPU (else it silently degrades to RRF):
node cli/memcli/dist/memcli.js down --name allkbs --folder ~/projects/trip2g_all_kbs
MODELS_DIR=/mnt/extssd/models node cli/memcli/dist/memcli.js up \
  --embedded --reranker --folder ~/projects/trip2g_all_kbs --port 24091 --name allkbs
curl -s -X POST http://localhost:24093/rerank -H 'content-type: application/json' \
  -d '{"query":"warm","texts":["up"]}'            # cold CE takes >10s once
# set vector_search.reranker.timeout_seconds: 60 in the container FEATURES env
# (recreate the app container with the patched FEATURES), then confirm the
# sidecar logs the app's "POST /rerank 200" on a test search.

# 4. Run the benchmark:
export OPENROUTER_KEY=sk-or-...
make v4          # → logs_flat_hybrid/ + results/summary_flat_hybrid.json (~$0.07)
```

The harness ([`flat_hybrid_bench.py`](./flat_hybrid_bench.py)) authenticates
via the HAT flow using the instance's own state-dir secret, gives the model the
single `search` tool, tracks per-result corpus origin and match origin
(TEXT/VECTOR/HYBRID), and runs the fact judge + confusion judge per answer.
Budget guard: `BUDGET_USD` (default 1.0), enforced before every model call.
