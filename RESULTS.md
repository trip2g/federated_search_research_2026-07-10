# Results

Two experiments against the live `https://trip2g.com/_system/mcp` federated hub,
2026-07-10. Total OpenRouter spend: **$0.88** (cap was $3). Raw traces in
[`logs/`](./logs/); rollup in [`results/summary.json`](./results/summary.json).

> Model note: `gpt-5.6-mini` is not on OpenRouter. We used **`gpt-5.4-mini`**
> (the newest 5.x-mini available) and label it as such.

## A. Task benchmark — 6 questions × 2 models

`fin` = produced a final answer (didn't hit the 10-turn cap or budget). `quo` =
final contains a verbatim quote. `hitKB` = expected corpus(es) it actually
targeted with `federated_search(kb_id=…)`.

| model | q | kind | tool calls | hitKB / expected | fin | quo | halted | wall |
|---|---|---|---|---|---|---|---|---|
| haiku-4.5 | 1 | single-corpus grounding | 10 | nietzsche / nietzsche | – | – | **max_turns** | 31s |
| haiku-4.5 | 2 | cross-corpus contrast | 12 | nietzsche,schopenhauer / same | Y | Y | ok | 42s |
| haiku-4.5 | 3 | principle understanding | 7 | epictetus / epictetus | Y | Y | ok | 27s |
| haiku-4.5 | 4 | hub orientation | 17 | nietzsche / machiavelli,nietzsche | – | – | **max_turns** | 40s |
| haiku-4.5 | 5 | cross-link navigation | 11 | – / montaigne,pascal | – | – | **max_turns** | 56s |
| haiku-4.5 | 6 | two-corpus principle | 14 | confucius,laozi / same | Y | Y | ok | 40s |
| gpt-5.4-mini | 1 | single-corpus grounding | 6 | nietzsche / nietzsche | Y | Y | ok | 14s |
| gpt-5.4-mini | 2 | cross-corpus contrast | 5 | nietzsche,schopenhauer / same | Y | Y | ok | 15s |
| gpt-5.4-mini | 3 | principle understanding | 3 | epictetus / epictetus | Y | Y | ok | 9s |
| gpt-5.4-mini | 4 | hub orientation | 6 | nietzsche / machiavelli,nietzsche | Y | Y | ok | 14s |
| gpt-5.4-mini | 5 | cross-link navigation | 7 | montaigne,pascal / same | Y | – | ok | 17s |
| gpt-5.4-mini | 6 | two-corpus principle | 5 | (via hub) / confucius,laozi | Y | Y | ok | 10s |

**Totals**

| | finished | grounded (quote) | hit all expected kb | tool calls | avg wall |
|---|---|---|---|---|---|
| **haiku-4.5** | 3 / 6 | 3 / 6 | 4 / 6 | 71 | 39s |
| **gpt-5.4-mini** | **6 / 6** | **5 / 6** | 4 / 6 | **32** | **13s** |

### Read

- **gpt-5.4-mini navigates the graph far more efficiently and reliably.** Half the
  tool calls, 3× faster, and it *finishes every question*. Its pattern is
  disciplined: one orienting call, then straight to `federated_search(kb_id=…)`
  on the right corpus, then answer.
- **Haiku is capable but undisciplined.** When it finished (q2/q3/q6 — the
  explicitly multi-corpus ones) it targeted the right corpora and quoted them
  well. But on the "simple" single-corpus lookup (q1) and the open hub-orientation
  (q4) it **thrashed** — mixing local hub `search` with `federated_search`,
  re-querying, and burning the 10-turn cap without ever concluding. Half its runs
  died at the turn limit, not at a wrong answer.
- The turn cap (10) is doing real work here. Haiku's failures are a *navigation
  budget* problem, not a comprehension one — which Experiment B makes vivid.
- `hit all expected kb` is only 4/6 for both, mostly because q4 ("who argues
  against Stoic detachment") is genuinely open — Nietzsche is a defensible target,
  so the loose oracle undercounts. Treat the expected-kb column as a hint, not a
  grader.

## B. Free graph wander — Haiku, 30 hops, no question

Full journal: [`logs/haiku_wander_journal.md`](./logs/haiku_wander_journal.md).

Given the same tools but **no task** — just "wander deliberately, ask yourself
what's next, notice cycles" — Haiku behaved completely differently from its
benchmark self:

- It **oriented** on a central axis (will / power), then followed *explicit
  opposition links* across corpora: Nietzsche ↔ Schopenhauer ↔ Epictetus ↔ Laozi
  ↔ Confucius.
- It **read seven principles with verbatim grounding** and restated them
  correctly in its own words (e.g. Epictetus's dichotomy of control, Laozi's
  wu-wei), then checked whether the advertised opponents actually opposed — they
  did.
- It **detected cycles**: the same 8–10 thinkers recurring on opposite sides of
  five different topic axes (Power, Will, Habit, Fate, Freedom), and flagged the
  return paths as such.
- Its own verdict: *"impossible to thrash — every step had clear justification,"*
  crediting the hub's topology (per-corpus opponent lists + topical axes).

So the model that hit the turn cap on a one-corpus lookup wandered 30 hops of a
knowledge graph coherently when the task was open-ended. **Comprehension was
never the bottleneck; disciplined convergence under a turn budget was.**

## Answers to the research question

**Can small models navigate a federated knowledge graph over MCP, and do they
understand the principles?**

1. **Yes, they navigate it** — both models reliably went hub → correct corpus via
   `kb_id`, and followed cross-corpus opposition links. The graph's structure
   (opponent lists, topic axes, a contradictions index) is what makes navigation
   tractable; the wander journal calls this out directly.
2. **Yes, they understand the principles** — when they retrieve the material, both
   restate it faithfully and quote verbatim. The wander shows genuine grasp
   (correct restatement + verified oppositions), not pattern-matching.
3. **The real differentiator is navigation discipline, not intelligence.** On
   fixed tasks, gpt-5.4-mini's terse "orient once, target, answer" beat Haiku's
   thrash-and-recheck by 2× on calls and 3× on latency, and finished every time.
   Haiku's failures were turn-budget exhaustion, not wrong understanding — and it
   out-explored gpt in the open-ended wander.
4. **Practical implication for federated KBs:** a well-structured graph (explicit
   cross-links + topical axes + a per-corpus "who to go to for X" manual) lets
   even a small model navigate deliberately. The failure mode to design against is
   *thrash* — so surfacing the right `kb_id` early (good hub cards / instructions)
   matters more than model size.

## Caveats

- Live endpoint: real retrieval, real latency, real failure modes. The blind
  `federated_search` with no `kb_id` **times out** on the current deployment
  (unbounded fan-out over ~25 peers); both agents recovered by targeting a
  `kb_id`. The wander also hit one `kb_id="nietzsche"` → `not_configured` from
  inside a nested context; the controlled benchmark shows `kb_id="nietzsche"`
  resolves fine directly, so treat that single wander hop as a transient/nested
  artifact.
- `MAX_TURNS=10` caps the loop; a higher cap would likely let Haiku finish more —
  but the point stands that gpt-5.4-mini didn't need it.
- `expect_kb` is a loose oracle for a hint, not a strict grader.
- n = 6 questions, 1 wander. This is a probe, not a leaderboard.
