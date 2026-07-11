# Philosopher-Investigator, Round 3 (Sonnet) — the fixed graph

## Core belief(s)

The system believes **knowledge is topology, not content** — "the notes in your
vault *are* the topology" (its own words, `en/thoughts/public-hub.md`). Ownership
stays radically local: a base is a note with `mcp_federation_kb_url` in its
frontmatter, and nothing more central exists. There is no registry to apply to,
no schema to conform to — you write one note and you're reachable.

But ownership is not flat. It's **two-level federation-of-federation**: root →
hub → corpus. I tried `kb_id="philosophers/nietzsche/willtopower"` (three levels)
and got `"Federation is not configured for kb_id \"willtopower\""` — the nesting
terminates at exactly one hop of indirection. The root doesn't know Nietzsche
exists; it only knows "philosophers" exists, and "philosophers" is the only party
that knows Nietzsche exists. Sovereignty is delegated, never inherited. Compare a
flat call from root, `kb_id="nietzsche"` with no prefix — rejected outright
("Federation is not configured"). The fixed graph enforces a strict chain of
trust: you cannot skip a level, you cannot address a grandchild directly.

Truth, in the Nietzsche corpus specifically, is treated as **citation-policed**:
one search hit contains the corpus correcting a misattribution inline — "'What
does not kill me...' is Twilight of the Idols, not this corpus; 'God is dead' is
The Gay Science" — i.e. the system defends against the exact kind of sloppy
misquotation LLMs are prone to reproduce. Truth is verbatim-anchored quotes plus
explicit source-boundary policing, not vibes-based paraphrase.

## Tensions / contradictions

1. **"Public discovery, gated content" is asserted, not universally enforced.**
   A fan-out `federated_search` with no `kb_id` returned four sibling bases at
   root level: `minionschool`, `nicksenin_journal`, `markavrelii`, `philosophers`.
   `minionschool` turned out to be someone's personal AI-agent training vault —
   fanfiction-game setup instructions, a rule note titled "don't write like an
   AI," persona A/B test transcripts naming a specific user ("Алексей,
   разработчик, ценит краткость"). None of that reads as content anyone curated
   for public philosophical consumption; it reads like a dev's private scratch
   vault that happens to speak the same MCP protocol and got swept into the
   federation graph anyway. The doc's stated two-layer privacy model (discovery
   public, content gated e.g. via the Telegram adapter's shared-key gate) is
   real for *some* peers and absent for others. Federation's minimal admission
   bar (one frontmatter key) is also its main privacy leak.

2. **"Philosophers" is a syncretic canon wearing an academic costume.** The
   MOC lists 21 "author cards," but alongside Nietzsche, Tolstoy, Montaigne,
   Pascal, Goethe, Confucius, Epictetus, Schopenhauer, Le Bon sit Henry Ford,
   Rockefeller, and Wallace Wattles's *The Science of Getting Rich*. There is no
   Plato (I probed `kb_id="philosophers/plato"` — not configured), no Kant, no
   Aristotle. This isn't the Western canon; it's a personal-development reading
   list that borrowed philosophy's authority. The hub's own self-description
   ("21 philosopher knowledge corpora") oversells the homogeneity of what's
   actually a syncretic mix of ethics, self-help, and business memoir.

3. **`kb_ids` (plural) doesn't compose the way its name implies.** I called
   `federated_search(kb_ids=["philosophers/nietzsche","philosophers/tolstoy"])`
   expecting a query scoped to exactly those two authors. Instead the response
   collapsed to a single `[philosophers]` bucket and searched the *whole* hub.
   The system can drill down one designated path at a time, but it can't yet
   compose an arbitrary multi-leaf index — you get the nearest common ancestor,
   not the intersection you asked for. Federation grants access by lineage, not
   by set-selection.

## What it optimizes for, at the expense of what

It optimizes for **frictionless network growth** ("add a base by writing one
note, every agent that points at the hub can reach it") and for **cheap,
scoped reads** (the whole `search → toc_path → note_html` loop exists purely to
avoid dumping 3,000-token notes into an agent's context). It explicitly is *not*
optimizing for curatorial completeness or canon fidelity — the philosopher
roster is opportunistic, not authoritative. And it is not optimizing for
privacy-by-default: reachability is the default state of any vault that speaks
the protocol, and the "gated content" model is opt-in per-peer rather than
structural.

## Door sentence

*"Anyone may be found here who agreed to be findable — but agreeing was as
cheap as writing one line, so look at who's here, not who chose to be."*

## Evidence list

- `initialize` → server self-description: retrieval-loop-first, section-cost
  framing ("~300 tokens... instead of a whole note (3,000+)"), and an explicit
  guardrail to ignore `demo/` (Marcus Aurelius) unless asked about the demo —
  the hub tells agents to look past its own showcase content.
- `search(query="federation")` on root → surfaced `en/user/federation.md`,
  `demo/federation_kb.md`, and two federation-planning docs — federation is
  documented as a first-class, load-bearing feature, not an afterthought.
- `federated_search(kb_id="philosophers", query="knowledge")` — direct one-hop
  federation into the hub works cleanly.
- `federated_search(kb_id="philosophers/nietzsche", query="will to power
  eternal recurrence")` — nested `/` routing confirmed live and correct
  (returned Nietzsche-specific Russian-language results from
  `nietzsche.2pub.me`), fixing the round-1 finding that this path was dead.
- `federated_search(kb_id="nietzsche")` (flat, no prefix, from root) →
  `"Federation is not configured for kb_id \"nietzsche\""` — proves nesting is
  *mandatory*, not optional shorthand.
- `federated_search(kb_id="philosophers/nietzsche/willtopower")` (3 levels) →
  same "not configured" error — nesting depth is capped at exactly one hop.
- `federated_search()` with no `kb_id`/`kb_ids` (full fan-out) → returned four
  sibling bases: `minionschool`, `nicksenin_journal`, `markavrelii`,
  `philosophers` — this is the evidence for the privacy tension above.
- `federated_search(kb_ids=["philosophers/nietzsche","philosophers/tolstoy"])`
  → collapsed to a single `[philosophers]`-wide search, not an intersection of
  the two named authors.
- `federated_search(kb_id="philosophers/plato")` → not configured — confirms
  the roster's real membership (no Plato, no Kant).
- `note_html(pid=1447)` (Philosophers Hub) → self-description: "A routing hub
  over 21 philosopher knowledge corpora... reached through this one peer."
- `federated_search(kb_id="philosophers", query="contradiction ... freedom")`
  → surfaced `en/contradictions.md` and `en/topics/svoboda.md`, confirming the
  cross-corpus contradiction index and topic-position matrix are real,
  queryable artifacts, not just described in the MOC.
- `federated_search(kb_id="philosophers", query="is God dead")` → Nietzsche
  card corrects its own misattribution inline, evidence of citation policing.
- `note_html(path="en/thoughts/public-hub.md")` — the founder's own essay:
  "no central registry: the notes in your vault are the topology," and the
  explicit "public discovery, gated content" design claim, tested and found
  only partially true in practice.
- `federated_search(kb_id="philosophers", query="author card list topic
  matrix")` → MOC note listing the 21-corpus structure (`hub/`, `topics/`,
  `en/contradictions.md`) and revealing the Ford/Rockefeller/Wattles mix.

## Where I ended, and whether the journey changed my reading

I stopped after confirming the `kb_ids`-plural non-composition behavior and the
21-author roster — that felt like the point of diminishing returns for a
one-page brief; deeper probing (e.g. testing the Telegram-adapter's gating
directly, or walking every one of the 21 corpora) would have been QA work, not
philosophy. The fixed graph *did* change my reading, substantially. A round-1
reader stuck on the broken root would reasonably conclude "the system believes
in strict, walled limits" — because that's all that was visible. With the
router working, the more accurate reading is that the system believes in
**delegated, capped trust**: reachability is real and the network is genuinely
alive (four independent live peers, 21 nested corpora, working citation
policing), but the delegation is shallow by design (one hop, no arbitrary
composition) and the admission bar is low enough that a stray personal vault
(`minionschool`) sits in the same fan-out as a curated philosophy corpus. The
limits aren't the center of this system's philosophy — but they aren't absent
either; they show up as the *shape* of trust (one hop deep, ancestor-scoped)
rather than as a wall around it.
