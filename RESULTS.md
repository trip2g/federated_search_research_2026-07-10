# Results

> **v3 exists:** [`RESULTS_v3.md`](./RESULTS_v3.md) runs the review's design
> (answer keys, LLM judge, no turn cap) and adds the walls-vs-flat comparison.

Two runs. **v1 was invalid** — a skeptic review ([`REVIEW.md`](./REVIEW.md))
caught it and it was confirmed. **v2** is the corrected run. Read this whole page
as a probe (n=6 questions, 1 run each), not a leaderboard.

> **Honest headline, after three passes.** We measured, corrected, and measured
> again — and each pass surfaced *another broken-retrieval-hidden-as-success*. v1:
> targeted `kb_id` calls returned `not_configured` (models answered from memory).
> v2 fixed that — but then **128 of 130 read-by-`pid` calls reached the model as
> empty** (see [below](#the-second-hidden-failure-read-by-pid-came-back-empty-128130)):
> the server actually *rejected* the model's string-shaped `pid` with a hard
> error, and our harness swallowed that error into an empty result. So even the
> "corrected" run fed models mostly *search snippets*, not the full notes they
> tried to open. The robust findings are therefore narrow: models **navigate** a
> federated graph reliably and cheaply, and **over-navigation cost (thrash)** is
> real and large. Whether they **faithfully ground / understand** the principles
> is *still unproven here* — retrieval the metrics assumed was intact was degraded
> twice. The recurring lesson is the finding: a failed retrieval that looks like a
> successful-but-empty one is invisible to every downstream metric — on the
> endpoint side *and* the harness side.

## The v1 mistake (kept, on purpose)

v1 pointed the harness at `https://trip2g.com/_system/mcp`. That hub does **not**
resolve the philosopher corpus `kb_id`s: **37 of 44** targeted
`federated_search(kb_id=…)` calls came back `"Federation is not configured for
kb_id …"`. So the models mostly retrieved *nothing* and answered from parametric
memory — while the v1 metrics ("finished" = stopped calling tools; "grounded" =
a quote is present) happily scored that as success. The external review's verdict
was blunt and correct: *the study had no valid task-success outcome.* The raw v1
traces are preserved in [`logs_v1_broken_endpoint/`](./logs_v1_broken_endpoint/)
and [`results/summary_v1.json`](./results/summary_v1.json) as the evidence.

## What changed for v2

- **Endpoint:** `https://philosophers.2pub.me/_system/mcp` — the hub that actually
  federates the 21 corpora by `kb_id` (verified: 0/67 targeted calls returned
  `not_configured` in v2).
- **Grounding is now measured, not assumed:** every quote in the final answer
  (≥6 words) is checked to be a real substring of the concatenated tool output.
  A quote the model didn't retrieve doesn't count.
- Bug fixes surfaced on the way: the harness never imported `re`; and the hub's
  front returns **403** to the default `python-urllib` user-agent (curl slips
  through) — a real UA header was required.

## v2 results — 6 questions × 5 models

`fin` = produced a final answer. **`grounded runs`** = runs with ≥1 quote actually
found in the retrieved text. `valid/found` = verified quotes / total quotes the
model emitted. `hitKB` = reached the expected corpus by `kb_id` (real content).
Total v2 spend: **$0.69**.

| model | fin | grounded runs | quotes valid/found | hitKB | tool calls | **$/question** |
|---|---|---|---|---|---|---|
| gpt-5.4-nano | 6/6 | 2/6 | 3 / 7 | 5/6 | 35 | **$0.0028** |
| gpt-5.4-mini | 6/6 | **4/6** | **8 / 20** | 5/6 | 36 | $0.0112 |
| ministral-14b (open) | 6/6 | 1/6 | 2 / **43** | 5/6 | 31 | $0.0039 |
| gemini-2.5-flash-lite | 6/6 | 3/6 | 7 / 15 | 4/6 | 16 | $0.0009 |
| claude-haiku-4.5 | 4/6 | 1/6 | 2 / 16 | 5/6 | **48** | **$0.0967** |

### What v2 actually shows

1. **Navigation is solid — and easy.** With a hub that resolves `kb_id`, every
   model reached the expected corpus 5/6 (gemini 4/6), and **0** targeted calls
   failed. Picking the right base by `kb_id` is not where models struggle.
2. **Verbatim grounding is weak across the board — but the metric is confounded.**
   Most quotes the models emit are *not* exact substrings of what the tools
   returned (ministral quoted 43 times; 2 verified). Two things drive this, and
   only one is a model failure:
   - **Language mismatch (metric artifact):** the corpora are Russian-primary
     (`concepts/volya-k-vlasti.md`, "Воля к власти"); the models answer in
     English and quote English translations, which can never be a substring of
     Russian source text. A strict substring check under-counts cross-lingual
     grounding badly.
   - **Real paraphrase/fabrication:** even allowing for that, the models clearly
     reformat and invent quote-shaped strings rather than lifting verbatim.
   So this pilot **cannot cleanly answer "do they understand the principles."**
   v1's confident "yes" was unearned. The honest read: models navigate *to* the
   material reliably; whether they faithfully ground on it needs a cross-lingual
   claim-faithfulness check this pilot doesn't have (see `REVIEW.md` §3).
3. **Cost-of-thrash is the one robust cross-run finding.** `claude-haiku-4.5`
   again over-navigates (48 tool calls, 4/6 finished) at **$0.097/question** —
   **~35× `gpt-5.4-nano`** ($0.0028) — because every wasted loop turn re-sends the
   growing transcript. This held in both v1 and v2 and is about tokens, not answer
   quality, so it survives the metric overhaul. If you build agents on federated
   knowledge, *convergence behaviour* is the cost driver, more than model choice.
4. `gemini-2.5-flash-lite` flipped from "lazy" (v1: 8 calls, 2/6 finished) to
   engaged (v2: 16 calls, 6/6) — a reminder that at n=6, per-model quality counts
   are noisy. Trust the behaviour classes and the cost ratios; don't trust the
   third decimal.

## B. Free graph wander — Haiku, 30 hops

Full journal: [`logs_v1_broken_endpoint/haiku_wander_journal.md`](./logs_v1_broken_endpoint/haiku_wander_journal.md).
(Ran against trip2g.com, so its deep-corpus reads hit the same `not_configured`
wall — it stayed mostly inside the hub's own topic/opponent notes. Treat it as a
demo of *deliberate hub-level traversal + cycle detection*, not verified
cross-corpus retrieval.) Given no task, Haiku oriented on the will/power axis,
followed opponent links, mapped the same ~10 thinkers recurring across five topic
axes, and flagged the cycles — coherent wandering, no thrash. Its own honest note
that individual corpora were `not_configured` is, in hindsight, the first sighting
of the v1 endpoint bug.

## Answers, honestly

- **Can small models navigate a federated MCP knowledge graph?** Yes, and it's not
  hard when the graph is structured (opponent lists, topic axes) and `kb_id`
  resolves — nano and an open 14B both did it reliably and cheaply.
- **Do they understand / faithfully ground the principles?** **Not established
  here.** They reach the right *corpus* but their full-note reads silently returned
  empty 128/130 times (the `pid` bug above), so they grounded on search snippets,
  not full notes — and even then rarely quote verbatim; the strict metric is also
  confounded by EN-answer/RU-corpus mismatch. A proper faithfulness check, on a
  read path that actually returns content, is future work.
- **What's the real cost lever?** Convergence, not intelligence: over-navigation
  (Haiku) is a ~35× cost multiplier; the win is a model + prompt that target and
  stop.

## The second hidden failure: read-by-`pid` came back empty (128/130)

Re-auditing the v2 traces surfaced a second broken-read-hidden-as-success — but,
importantly, **not the way it first looked.** In **128 of 130** `note_html` /
`federated_note_html` calls carrying a `pid`, the model received empty text. The
models were doing the sensible thing: a `federated_search` result hands back a
match id like `p36:c2` (a *passage:chunk* id) or a numeric note id, and the model
replayed that as `pid` to open the full note.

The cause was split across the server and our own harness, and we only pinned it
down by replaying the exact failing calls against the live hub:

- **Server side (ergonomics):** the `pid` field was typed `int64`. A string-shaped
  `pid` — `"70"` or `"p36:c2"` — made the whole call fail with a hard JSON-RPC
  error (`-32602 cannot unmarshal string … into int64`), **even when a valid
  `path` was also supplied**. So the server was *loud*, not silent — but it threw
  away a resolvable request over a type mismatch.
- **Harness side (the actual "empty"):** our `bench.py` read only the JSON-RPC
  `result` field and ignored `error`, so it turned every one of those errors into
  `{"ok": true, "text": ""}` and fed the model an empty-but-successful read. *That*
  is where the 128 empties came from — the metric never saw the server's error.

Consequence for this study is unchanged in effect: even in the "corrected" v2 run,
the *read the full note* step delivered nothing to the model 128/130 times, so its
evidence base was `federated_search` snippets (which did carry text — that's why
corpus-hit rate stayed ~5/6), not the full notes it tried to open. "They reach the
material" should be read as **"they reach search snippets."** v3 sidesteps this
(it doesn't hand models a `pid`), which is why its harness is the trustworthy one.
Both bugs are now fixed: the endpoint accepts string/`match_id`-shaped pids and
falls back to `path` (branch `fix/mcp-pid-empty-note`), and the harness must
surface JSON-RPC errors instead of coercing them to empty. The lesson holds, just
on two surfaces: *a failed retrieval that renders as successful-but-empty is
invisible to every downstream metric — check the server's `error`, don't just read
its `result`.*

## What this pilot still doesn't do (from `REVIEW.md`)

Preregistered answer propositions; cross-lingual claim faithfulness
(entailed/unsupported/contradicted) instead of substring matching; navigation
efficiency decoupled from a turn cap; paired controls (evidence-supplied vs
corpus-supplied vs hub-only). That's the v3 design.
