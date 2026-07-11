# Philosophy of the Federation — Round 3 (fable, fixed graph)

**TL;DR.** Core belief: a claim is only knowledge when it has an anchor and an owner — and the note is the single primitive that carries both, plus the topology itself. Main tension: an open, "no central registry" network whose actual heart is a hand-curated, pragmatist canon with an unabashed business plan. Door sentence: **"Say only what you can anchor; where the corpus is silent, be silent."** The fixed graph flips the round-1 reading: the limits are still everywhere, but with the router visible they read as switchboard discipline, not fortress walls.

## Core beliefs

1. **The note is the universal primitive.** One markdown note with `mcp_federation_kb_url` in frontmatter *is* the network topology ("No central registry: the notes in your vault are the topology" — en/thoughts/public-hub). The same note is the base's public description, its routing card for agents ("Use when / Don't use when"), its permission bit (`free: true`), and a browsable human page. Knowledge, wiring, access control and marketing collapse into one artifact the owner can `git clone` away at any moment.

2. **Truth is anchored or it is nothing.** The philosophers layer is verbatim-gated end to end: principles carry blockquotes verified as normalized substrings of ingested units (Nietzsche: "144/144 evidence blockquotes ... verified as verbatim substrings"), QUOTE_AUTHENTICITY pages classify meme quotes (`verified_primary` / `popular_but_unverified` / `misattributed`), and the RAG-time rule is explicit: a popular-quote-shaped query with no corpus match answers `NO_RELEVANT_KB_EVIDENCE`, never confirms. The debate rule in `_instructions`: "no strong claim is made without an anchor. If the base is silent, say so in character; do not invent." Honesty extends to gaps: *Übermensch* — "0 occurrences in BGE — concept pages exist with `evidence: not_in_ingested_corpus`."

3. **Disagreement is a first-class artifact.** Truth here is positional, not consensual: an 80-pair contradiction index (axis of conflict + each side's thesis + grounding slugs + `debate_bridge` notes), 18 topic axes mapping topic × philosopher → one-phrase position, "Direct opponents" sections on every author card, "Антипринцип" blocks inside principles. The system doesn't average its sources into a view; it stages them against each other and cites both corners.

4. **Attention is the scarce resource; routing is a virtue.** The hub's own instructions are an economy of context: read one ~300-token section, never a whole note; "No fan-out first ... a last resort, not a first move"; topic matrix answers "often ... without a single federated query." The architecture is a funnel — root → philosophers hub (a base that proudly contains *no corpora*, only routing) → author base → one section of one note. Delegation all the way down, now mechanically real: nested `kb_id` with `/` works recursively (`philosophers/nietzsche`, `philosophers/tolstoy` both answered from the root endpoint).

5. **Agents are the primary readers; humans get the same pages.** Every layer self-describes in second person to an agent (`initialize` instructions, `_instructions` notes, author cards with "manner of speech for debates"), yet each artifact doubles as a public web page. The system believes a good knowledge base needs no separate API doc — the docs *are* the data.

6. **Ownership without a toll booth.** Discovery is public, content can be gated (the Telegram node "returns nothing to an anonymous caller"); the seller keeps "markdown files, domain, subscriber list and the full amount of every payment ... trip2g takes no commission because trip2g is not in the payment chain." The tradeoffs page is unusually honest: you run the server, there's no built-in checkout, acquisition is on you.

## Tensions / contradictions

- **Open network, curated soul.** The rhetoric is decentralist ("no central registry", any node speaking the protocol joins — the Qdrant Telegram node proves it), but everything that makes the federation *good* is heavy manual curation: hand-written author cards, a hand-sorted contradiction index, a chosen canon. The topology is open; the value is editorial.
- **The canon is a confession.** "21 philosophers" = Nietzsche, Pascal, Laozi, Montaigne ... next to Ford, Rockefeller, Hill, Wattles, Smiles. No Plato, no Aristotle, no Kant, no women, nothing academic or 20th-century-critical. This is not a philosophy department; it's a *practitioner's* canon optimized for decisions, debates and success-vs-measure axes. Nietzsche himself would approve of the honesty: every philosophy is the confession of its author.
- **One author = one book.** Nietzsche is BGE only; Tolstoy is the Confession. The system prefers a verifiably narrow author to a fuzzily complete one — coverage is sacrificed to the verbatim gate. Rigor produces flattening it explicitly warns against ("Do not turn into a meme").
- **Ascetic epistemics, expansionist telos.** Inside: "do not invent", NO_RELEVANT_KB_EVIDENCE, silence over confabulation. Outside: "Build a company on top of the network ... content and access as the product." The truth machinery is simultaneously the sales demo. Not hypocrisy — but the door of the monastery opens onto a marketplace.
- **Anti-fan-out doctrine vs fan-out marketing.** User docs advertise "fan out across all accessible bases" as the headline convenience; the agent instructions treat exactly that as a failure mode. What it sells as breadth, it internally governs as a last resort.

## What it optimizes for, at the expense of what

Provenance, addressability and cheap targeted reach — at the expense of coverage (single-book corpora), canonical breadth (a pragmatist's bookshelf), and serendipity (fan-out is disciplined away; you meet what the routing layers already indexed).

## The sentence over the door

**"Say only what you can anchor; where the corpus is silent, be silent."**

(Runner-up, for the network rather than the corpora: "One note is enough — to describe a base, to wire it in, and to own it back.")

## Evidence list

- Root `initialize` instructions: retrieval loop, ~300-token sections, "ignore demo/", "ground answers only in sections you actually read".
- `en/user/hub.md` (pid 1109): KB-note = frontmatter-registered base; "Use when / Don't use when"; `free: true` gating; hub entries are browsable pages.
- `en/hub/philosophers.md` (pid 1447, kind `federation_kb`): "routing hub over 21 philosopher knowledge corpora ... nested kb_id".
- philosophers `en/MOC.md` (pid 6): "not a corpus but a routing layer"; fan-out "a last resort, not a first move".
- philosophers `en/_instructions.md`: anchor rule, "If the base is silent, say so in character; do not invent"; corpus base layout (MOC / TERMINOLOGY / principles with Anti-principle / chains / QUOTE_AUTHENTICITY).
- Nested routing verified live from the root endpoint: `federated_search(kb_id="philosophers/nietzsche")` and `philosophers/tolstoy` both returned corpus notes (nietzsche.2pub.me, tolstoy.2pub.me).
- nietzsche `QUOTE_AUTHENTICITY.md` (pid 4): status taxonomy, NO_RELEVANT_KB_EVIDENCE rule, 144/144 verbatim verification, negative controls, `not_in_ingested_corpus`.
- nietzsche `principles/stradanie-vozvyshaet.md` (pid 47): thesis → BGE-anchored blockquotes → status → Антипринцип block.
- philosophers `en/contradictions.md`: 80 opponent pairs, axes, grounding slugs, `debate_bridge`.
- philosophers `en/topics/uspekh-i-usilie.md` (pid 46): topic × philosopher positions, ally clusters, "Against the cult of effort".
- philosophers `en/_index.md`: the 21-author canon (Adler ... Wattles).
- `en/thoughts/public-hub.md` (pid 1071): "the notes in your vault are the topology"; discovery public / content gated; "Build a company on top of the network".
- `en/hub/telegram.md` (pid 1064): non-trip2g Qdrant node speaking the protocol; anonymous callers get nothing.
- `ru/user/sell-obsidian-notes.md` § "Что остаётся у вас": owner keeps files/domain/subscribers, no trip2g commission, honest tradeoffs.
- `similar(pid=658)`: surfaces the federation MVP plan and a "Marketplace / Reseller Mode (FUTURE DESIGN)" dev doc — the commercial arc is in the graph itself.

## Where I ended, and did the journey change the reading

I started at the root's self-description and ended, ~30 moves later, in a Russian page about what a seller keeps when they leave — which is itself the reading: the same system that gates quotes with verbatim checks gates its business with an exit guarantee. The journey changed my reading once, at `_instructions`: I came in expecting "federation" to be the philosophy (plumbing as ideology) and left convinced the philosophy is *anchoring* — federation is just anchoring applied to topology.

**Fixed vs broken graph.** A round-1 reader on the broken graph, with the router hidden, would meet the limits without the delegation they serve — guardrails, gates, "ignore demo/", content that returns nothing — and reasonably conclude "limits are the center." With the router working, every one of those limits resolves into a handoff that lands somewhere real: root → hub → corpus → section → verbatim unit. The center is not limitation but *delegation with receipts*; the limits are the cost of making the handoffs cheap. A broken graph doesn't just hide content — it converts a switchboard into a wall, and the reader's verdict inverts with it.
