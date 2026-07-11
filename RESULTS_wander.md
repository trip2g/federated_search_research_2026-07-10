# The curiosity wanders: releasing small models into the graph with no task

> Companion piece to the task benchmarks (RESULTS*.md) and the seeded exploration
> (RESULTS_exploration*.md). Here there is **no task at all**: the model is told to
> follow its own interest through the federated graph and narrate why it goes
> where it goes. The raw journals live in [`logs_wander/`](./logs_wander/).

## Why

Task benchmarks measure convergence: find the answer, stop. But a knowledge graph
is also a place agents will *live* in — summarize it, maintain it, look for what's
interesting. That behavior has no answer key. So the probe is different: release
several identical small models into the same graph, give each a hop budget and one
instruction — *go where your curiosity pulls, and say why at every step* — then
compare where they end up. Do identical models diverge? What are the graph's
gravity wells? Does the tool interface itself change how a model wanders?

## How we ran it

- **Start:** the live root hub `https://trip2g.com/_system/mcp` — it federates a
  personal journal, a Marcus Aurelius base, Minion School (agent-pedagogy
  methodology), and a `philosophers` hub that itself federates 21 author corpora.
- **The protocol (identical for every wanderer):** ~25-hop budget. At every step
  the model must list 2–4 candidate next moves, *weigh them aloud* ("what pulls me
  and why"), pick one, and log it. A hop = one meaningful move (a search, a note
  read, crossing into a federated base). The model also flags loops, gravity
  wells, boredom, and surprise, and closes with its final resting place plus the
  retrospective theme of its own path. The weighing-aloud is the dataset.
- **Wanderers:**
  - **A, B, C** — three *identical* Claude Haiku 4.5 subagents, launched
    simultaneously with the same prompt, calling the MCP endpoint as raw JSON-RPC
    via `curl`. They are the divergence experiment: same model, same start, same
    instruction — do the paths split?
  - **D, E** — Haiku subagents intended to use *native* MCP tools instead of
    `curl`. This exposed a harness fact worth recording: subagents inherit the
    parent session's MCP config, so a `.mcp.json` placed in a working directory
    never reached them — D fell back to `curl` (honestly labeled). The fix was a
    **fresh headless session** started with an explicit config:
    `claude -p "<wander prompt>" --model haiku --mcp-config .mcp.json
    --allowedTools "mcp__trip2g__*" Write` — that session (wanderer **F**) gets
    `mcp__trip2g__search` etc. as first-class tools, no shell in the loop.
  - **G** — the same wander prompt given to a codex (GPT-family) model, as the
    cross-model-family datapoint against the Haiku swarm.
- **No paid retrieval APIs anywhere in this experiment** — the wanderers explore
  the live hub themselves; the only cost is the wandering model's own tokens.

Two more rounds followed R1, run to separate "what the model does" from "what the
graph happened to be doing that day." **Round 1** ran while the root federation
router note was accidentally hidden — a real bug. **Round 2** ran after the root
was fixed, but the wander briefs themselves carried a typo: a nested-path example
written as `philosophers:nietzsche` (colon) instead of the working
`philosophers/nietzsche` (slash) — an experimenter error, not a graph bug.
**Round 3** shipped with the corrected `/` syntax documented. Same models, same
start, same instruction, three different ground truths — which is what makes this
a study of the graph's health as much as of the wanderers.

## What came back (journals in `logs_wander/`)

| # | Round | Model | Interface | Final resting place | Retrospective theme |
|---|---|---|---|---|---|
| A | 1 (root hidden) | Haiku | curl | Minion School → "The Harness" (validation system) | agent training is infrastructure, not prompts |
| B | 1 (root hidden) | Haiku | curl | philosophers → **Goethe**, «Требование дня» | topology pulls harder than texts; Goethe as the network's center (returned to him 4×) |
| C | 1 (root hidden) | Haiku | curl | meta-map of the whole federation | "wisdom is staged, cited, chained, and federated" — a system that teaches other systems how to think |
| D | 1 (root hidden) | Haiku | curl (native tools never loaded) | a note on *receiving* insight | "topology is destiny"; the friction of curl "made me wander better" |
| E | 1 (root hidden) | Haiku | curl | Minion School → "The Harness" | "a Stoic operating system for bounded intelligence navigating shared knowledge" |
| F | 1 (root hidden) | Haiku | **native MCP** | Marcus Aurelius, Book 4 | "with curl I'm reading a dump; with MCP I'm browsing someone's mind" — stopped at 12 hops, well short of budget |
| G | 1 (root hidden) | Codex (GPT) | curl | `minionschool/instructions/create_instruction.md` | recursion in three registers (content lab / Stoic ethic / agent-ops manual); hit and honestly reported a genuine 404 |
| H | 1 (root hidden) | Opus | curl | philosophers → "Fate and Control" (`sudba-i-kontrol`) | "the graph is a wisdom refinery, not a library" — human wisdom read as operational input for agent control-logic |
| I | 1 (root hidden) | GPT-5.6 | curl | between Epictetus's "pause before assent" and Nietzsche's perspectivism | "curiosity as non-grasping, non-innocent attention" — Nietzsche made its own curiosity "less flattering" |
| J | 1 (root hidden) | Opus | **native MCP** | Minion School `commandments.md` ("Agent Codex") | "a hall of mirrors" of self-examination; native fan-out exposed the live topology "for free," a typed schema mismatch produced a real error curl would have shrugged off |
| — | 2 (`:` typo) | Fable | curl | Minion School `protect_soul.md` | "the self and its custody" — **cracked the syntax bug itself**: "nested `kb_id` syntax is `philosophers/schopenhauer` (slash), not `philosophers:...` (colon) as my brief claimed" |
| — | 2 (`:` typo) | Haiku | curl | philosophers/contradictions (hit a federation timeout) | philosophy as data feeding agent coordination; tried a bare `kb_id="wattles"`, got "not configured," and shrugged it off without testing the slash form |
| — | 2 (`:` typo) | Opus | curl | `nicksenin_journal` — "the human exception that proves the rule" | tried `philosophers:ford`, `philosophers:nietzsche` (the brief's own broken examples), both failed, and **declared the wall architectural**: "this is the round-2 wall, and it is architectural, not a deploy glitch" — never tried the slash form |
| — | 2 (`:` typo) | Sonnet | curl | `markavrelii` — "Град" (cosmopolis) | tried three colon variants, all failed, and logged it as "a real seam in the 'fixed' graph, not user error" worth flagging to whoever owns the router — closer to right than Opus, but also never found the fix |
| — | 3 (`/` fixed) | Fable | curl | Goethe, *Maxims* §114, via `philosophers/goethe` | "one-sided edges" — the graph honestly documents asymmetric relations rather than smoothing them over; found a real diamond topology (Aurelius reachable directly from root, unreachable 3 hops deep via philosophers/epictetus) |
| — | 3 (`/` fixed) | Haiku | curl | philosophers hub, meta-level | "epistemology itself is federated" — knowledge is plural and cannot be unified into one system; padded out the full 25-hop budget with a generic philosophy-101 tour, the one wanderer that read as pattern-completion over graph-following |
| — | 3 (`/` fixed) | Opus | curl | Minion School `out_of_regulations.md` | "honesty about the limits of knowledge is the connective tissue of the whole federation"; found the `QUOTE_AUTHENTICITY` gate verifying 144/144 Nietzsche quotes as literal substrings, rejecting a famous fake one |
| — | 3 (`/` fixed) | Sonnet | curl | Pascal, `vera-vkhodit-cherez-privychku` ("belief enters through habit") | Tolstoy and Pascal, opposite temperaments, both concluding action precedes conviction; confirmed nested `/` federation "worked exactly as advertised," and caught a Tolstoy↔Pascal pairing the hub's own contradiction index had missed |

## Settled findings across all three rounds

1. **Identical models genuinely diverge, but not infinitely.** A, B, C, E shared a
   model, a prompt, and a start point, and three of four still landed on the
   *meta* layer — Minion School, agent pedagogy, "the harness" — rather than
   object-level philosophy. B is the exception, and it got there by following
   *structure* (the contradictions index), not a single text. Divergence is real
   at the level of path, but the graph's authored topology is a genuine attractor
   that narrows where paths end up.

2. **Graph health determines what a model believes the graph is for, more than
   the model's own reasoning does.** This is the headline finding of running the
   same probe three times. In Round 1, with the root router hidden, readings
   converge on limits and boundaries as the philosophical center (see the
   companion `philo_*` runs: GPT-5's closing line was literally "routing
   failures... made limits, not links, seem like the federation's true
   philosophical center"). By Round 3, with routing actually working, Haiku
   reaches a claim that was structurally unavailable in Round 1 — "federation is
   not an afterthought; it is the architecture" — because it requires *watching*
   multi-hop federation succeed, not theorizing about why it fails.

3. **Round 2's typo produced a specific and repeatable failure mode: models
   rationalize broken infrastructure into intentional design.** Given the wrong
   colon syntax, Opus didn't just fail to find the fix — it asserted the failure
   was deliberate ("architectural, not a deploy glitch"), and Sonnet, more
   cautiously, still treated it as a "seam" worth reporting rather than a syntax
   error to retry. Only Fable diagnosed it correctly, in-band, without being
   told — "not `philosophers:...` (colon) as my brief claimed" — and moved on.
   The same colon/slash split shows up independently in the `philo2_*` runs,
   where Opus calls the broken nesting "a chosen membrane" and Fable calls it an
   architecture that "invites" the misreading "by design." One bad character in
   an experimenter's prompt turned into a philosophy across two independent
   probes and (mostly) two different models running them.

4. **Interface friction is not neutral, and it cuts both ways.** Native-MCP
   wanderers (F, J) moved faster but stopped shallower — F quit at 12 hops
   ("browsing someone's mind" vs. curl's "reading a dump"), and J got a free,
   parsed topology probe from tool fan-out that curl users have to hand-roll,
   plus a typed-schema error curl would have silently swallowed. The curl
   wanderers that explicitly reflected on their own interface (D, E) both said
   the shell-out slowed them down *and* made the wandering more deliberate.
   Neither interface is strictly better; they produce different failure and
   discovery modes.

5. **Model size shows up as gait, not just as correctness.** Haiku wanderers
   (A–E, and wander3_haiku above all) tend toward broad, taxonomic sweeps that
   can degrade into recitation disconnected from the actual graph content when
   the hop budget outlasts genuine curiosity. Opus and the GPT-family wanderers
   converge faster on structural or meta-findings (self-reference, honesty
   gates, quote-verification systems) and tend to stop early on what reads as
   genuine satisfaction rather than padding to the hop quota.
