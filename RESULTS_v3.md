# v3 results — walls vs no walls

**TL;DR: the wall helped correctness, but less than the thesis hopes, and it cost
more.** On the same 6 questions over the same notes, the federated hub (walled)
produced 8/12 fully-correct runs vs 5/12 for a naive flat pile — but the flat
condition reached relevant material in 1–2 tool calls (walled: 2.5–4.3), used 3×
fewer calls, cost ~35% less, and its verbatim quotes verified at 68% vs 38%.
n=6 questions per cell; read this as a probe, not a verdict.

This run addresses the methodology review ([`REVIEW.md`](./REVIEW.md)) of
[v1/v2](./RESULTS.md): preregistered answer keys, LLM-judge task-correctness,
no assistant-turn cap (12 individual tool calls, then a forced final),
cross-lingual quote validity, navigation efficiency, model vs tool latency.
Harness: [`v3_bench.py`](./v3_bench.py); keys: [`questions_v3.json`](./questions_v3.json);
raw traces incl. judge verdicts: [`logs_v3/`](./logs_v3/);
aggregate: [`results/summary_v3.json`](./results/summary_v3.json).

## The two conditions

Same knowledge, two access modes:

- **WALLED** — the live hub `philosophers.2pub.me/_system/mcp`: 21 corpora behind
  `kb_id` walls, hub-level author cards / topic axes / contradictions index,
  cross-corpus links. Tools: `search`, `federated_search(kb_id)`, `note_html`,
  `federated_note_html`.
- **FLAT** — one local `search(query)` over all 1494 notes of the same corpora as
  a single undifferentiated pile (case-insensitive term-frequency scoring, top 6
  snippets ≈900 chars with file paths). No kb_id, no structure, no note reading.

**The flat baseline here is deliberately naive** — substring/TF scoring, no
embeddings, no reranker. A serious flat store (vector + reranker) is a separate,
ongoing build; treat these numbers as the *floor* of what "no walls" can do.

> **Confound, stated plainly.** The WALLED arm is **not** full-text: the live
> philosopher hubs run **vector search** (verified — an English paraphrase with no
> shared words returns the right Russian notes, with `pN:cM` chunk match ids). So
> this comparison varies *two* things at once — walls **and** the retrieval engine
> (vector vs. substring). Much of the walled arm's correctness edge could be the
> embeddings, not the walls. This table therefore reads as *"authored structure +
> vector beats a crude keyword pile,"* **not** *"walls beat a flat store."* The
> only clean test holds retrieval fixed — vector + reranker on **both** arms — and
> that is exactly the flat-hybrid **v4** run (same corpora, one flat store, vector
> + reranker). Read v3 as the floor; v4 is the controlled comparison.

## Results (2 models × 2 conditions × 6 questions, 1 run each)

`correct` = judge says all preregistered facts stated; `facts` = required facts
covered (sum over 6 questions); `quotes v/f` = verbatim quotes verified in
retrieved text / total quotes emitted; `1st rel` = mean tool call index at which
a preregistered evidence substring first appeared in a result.

| model | condition | correct | facts | quotes v/f | tool calls | 1st rel | model s | tool s | $/q |
|---|---|---|---|---|---|---|---|---|---|
| gpt-5.4-nano | **walled** | **4/6** | 13/16 | 13/33 (39%) | 57 | 2.5 | 85 | 46 | $0.0035 |
| gpt-5.4-nano | flat | 2/6 | 11/16 | 17/24 (71%) | **16** | **1.0** | 49 | ~0 | **$0.0020** |
| gpt-5.4-mini | **walled** | **4/6** | 14/16 | 12/32 (38%) | 44 | 4.3 | 64 | 41 | $0.0090 |
| gpt-5.4-mini | flat | 3/6 | 13/16 | 13/20 (65%) | **18** | **2.0** | 37 | ~0 | $0.0064 |

Total v3 spend: **$0.13** (incl. 24 judge calls at ~$0.0002 each). No run was
dropped for budget; the $1 guard was never approached.

Per-question spread (verdicts, walled/flat): Q1–Q3 and Q6 (single- and
two-corpus retrieval) were mostly correct in both conditions. **Q4** ("who
argues against Stoic detachment, on corpus grounds") was the hardest cell in
the whole grid — never fully correct anywhere, incorrect twice for nano.
**Q5** (Pascal vs Montaigne cross-link) split: walled-nano and flat-mini got
it fully, their counterparts didn't.

## What it says

1. **Walls helped correctness — modestly.** 8/12 vs 5/12 correct, 27/32 vs 24/32
   required facts. The gain concentrates where the hub's authored structure
   carries the answer: the contradictions index literally states the opposition
   axes that Q4/Q5 ask about, and walled runs that consulted it did better. The
   flat condition failed most when the needed fact lives in a note whose
   keywords don't overlap the question (Q4: "стоическая цитадель" doesn't
   contain "стоическое безразличие"-style query words the models tried).
2. **Walls cost real navigation.** 101 walled tool calls vs 34 flat; first
   relevant snippet at call 2.5–4.3 vs 1–2; ~87s of cumulative tool latency vs
   ~0 (local pile); ~1.4–1.75× the per-question cost. Three walled runs hit the
   12-call ceiling and had to be forced to answer. The wall is a maze as well
   as a map.
3. **The flat condition quoted more faithfully.** 68% vs 38% verified quotes.
   Likely a format artifact, not a virtue of flatness: flat snippets are raw
   markdown the model can copy verbatim, while walled `note_html` returns
   HTML whose tags break exact substring matching after our whitespace-only
   normalization. Treat the *between-condition* quote comparison as confounded;
   within-condition it still shows models can lift verbatim RU quotes when the
   text is in front of them.
4. **A structural confound cuts in the walls' favor — and against a strong
   reading.** The flat pile *contains* the hub's own notes (peer-links,
   contradictions index) as plain files, so flat models could in principle find
   the same authored structure by keyword luck — sometimes they did (flat-mini
   Q4 found the contradictions note at call 2). So this experiment separates
   walls-as-*navigation* from nothing; it does **not** separate
   walls-as-navigation from walls-as-*authored-content*. The honest reading:
   what helped was mostly that someone **wrote the comparison notes**; the
   kb_id routing delivered them a bit more reliably and much less cheaply.

## Confounds and limits

- n=6 questions, 1 run each, 2 models; differences of 1–2 runs are noise-sized.
- The flat search is crude (TF over substrings); a vector+reranker flat store
  would likely close some of the correctness gap — that comparison is the
  natural v4 and is being built separately.
- RU-primary corpus, EN-phrased questions: flat search only works when models
  guess RU keywords (both models did switch to Russian queries unprompted).
- The judge (gpt-5.4-nano, one call per run) is itself a small model; verdicts
  were derived deterministically from its fact-coverage list, and spot-checks
  matched, but it was not audited run-by-run.
- Live-endpoint quirk fixed mid-harness-build (before the sweep): the hub
  returns an empty note whenever a `pid` argument is passed, so v3 removed
  `pid` from the tool schema and surfaces empty reads as errors. v2 silently
  fed models `text:""` — one more reason v2's navigation numbers were kind.
- `1st rel` is conservative: it only counts exact preregistered substrings, so
  a run can answer correctly with `1st rel = None` (evidence arrived phrased
  differently, e.g. inside HTML markup).

## Answer to the headline question

**Does structure (walls / kb_id / cross-links) make models more correct, more
grounded, cheaper?** On this probe: more correct — yes, modestly (driven by
authored cross-corpus notes more than by routing); more grounded — not
measurably (the quote metric favored flat for format reasons); cheaper — no,
walls cost ~1.5× per question and 3× the tool calls against even a naive flat
baseline. The trip2g thesis survives as "curated structure carries answers
plain retrieval misses," but not (yet) as "federated navigation beats a flat
store" — that needs the vector-flat v4 and more questions.
