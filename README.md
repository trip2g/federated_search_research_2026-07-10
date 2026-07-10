# Federated-search research: can small LLMs navigate a knowledge graph over MCP?

**Question.** Give a small model an MCP endpoint onto a *federated* knowledge
graph — many independent knowledge bases, cross-linked by "who argues with whom"
— and see how well it navigates: does it target the right corpus, follow links,
reach a principle, and ground its answer in verbatim material rather than
inventing it?

**Target (live).** `https://trip2g.com/_system/mcp` — a [trip2g](https://trip2g.com)
hub that federates ~25 knowledge bases, most of them philosopher corpora
(`nietzsche`, `schopenhauer`, `epictetus`, `tolstoy`, `confucius`, `laozi`,
`pascal`, `montaigne`, `machiavelli`, …). Each corpus carries concepts, principles,
and **verbatim-anchored quotes**, plus federation links to the neighbours it
disputes (e.g. Nietzsche → Schopenhauer, Pascal → Montaigne). One protocol (MCP);
each base can implement retrieval however it likes (vector search, a wiki-LLM,
or a mix) and ship its own usage manual — the agent only sees the tools.

## Two experiments

### A. Task benchmark — `bench.py`
Six philosophy questions of increasing navigation difficulty (single-corpus
grounding → cross-corpus contrast → hub orientation → cross-link following), each
run through a real MCP tool-use loop against the live hub. Models:
`anthropic/claude-haiku-4.5` and `openai/gpt-5.4-mini` (via OpenRouter).

We log **every tool call** (name, args, the real result, latency) and the final
answer. No scoring is baked into the harness — the raw traces in `logs/` are the
primary artifact; the read is in [`RESULTS.md`](./RESULTS.md).

### B. Free graph wander — `logs/haiku_wander_journal.md`
A separate run: Haiku is given the same MCP tools and **no question** — just told
to wander the graph for 30 hops, at each hop asking itself "what is my next point
of interest and why", following cross-links, and noticing cycles. The point is to
see whether the model can move through a knowledge graph *deliberately* rather than
thrash.

## Reproduce it — one command

Python 3 (stdlib only) and an OpenRouter key. Nothing else for the headline run.

```bash
export OPENROUTER_KEY=sk-or-...   # your key; never committed
make reproduce                    # v2 table, live hub, ~$0.69, halts at BUDGET_USD
```

`make reproduce` runs `bench.py` against the **live** hub
`philosophers.2pub.me/_system/mcp` with the exact five models from the published
v2 table — **no local setup**. Every run tracks spend from OpenRouter's own usage
accounting and stops before `BUDGET_USD` (default `1.0`; override with
`make reproduce BUDGET_USD=2`).

| command | what it reproduces | needs | recorded cost |
|---|---|---|---|
| `make reproduce` (`v2`) | headline navigation/grounding/cost table | key only | **$0.69** |
| `make v3` | walls-vs-flat (naive flat) | key + `~/projects/korpuses/*.2pub.me` | $0.13 |
| `make v4` | flat-hybrid (vector + reranker) | key + a local memcli instance | ~$0.15 |

The flat arms need local corpora because a "flat pile" and a "hybrid local store"
only exist on your machine — the walled arm is the live hub. Steps for `v3`/`v4`
data are in the arm sections below. Totals are small: a full re-run of every arm
is well under **$1**.

## Notes & honesty

- `gpt-5.6-mini` is **not** on OpenRouter; `gpt-5.4-mini` (the newest 5.x-mini
  available) was substituted and is labelled as such everywhere.
- Everything hits the **live** hub, so results reflect real retrieval + real
  latency/timeouts (the blind, no-`kb_id` fan-out times out on the current
  deployment — itself a finding; targeted `kb_id` calls are fast).
- No API key, secret, or private data is in this repo. The corpora queried are
  public-domain philosophy.

## Integrity note

The first run (**v1**) was **invalid**: it targeted an endpoint that didn't
resolve the corpus `kb_id`s, so models answered from memory while the metrics
scored it as success. An external skeptic review ([`REVIEW.md`](./REVIEW.md))
caught it; it was verified and corrected in **v2** (working endpoint + a
quote-validity check). The flawed v1 traces are kept as evidence. See
[`RESULTS.md`](./RESULTS.md) for the full story — including what this pilot still
can't measure.

## Layout

```
bench.py                     harness: MCP client + tool loop + cost guard + quote-validity + logging
questions.json               the 6 benchmark questions (kind + expected corpus)
logs/                        v2 per-run full traces (working endpoint)
logs_v1_broken_endpoint/     the invalidated v1 traces + Haiku wander journal (kept as evidence)
results/summary.json         v2 rollup;  results/summary_v1.json  the v1 rollup
RESULTS.md                   interpretation (v1 mistake → v2 correction → honest read)
REVIEW.md                    external skeptic-methodologist critique + a better-test spec
```
