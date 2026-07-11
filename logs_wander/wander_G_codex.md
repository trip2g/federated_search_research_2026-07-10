# Wander G (codex) — curiosity walk

Model: codex (Claude family sibling comparison point — wanderers A-E were Haiku).
Entry point: https://trip2g.com/_system/mcp
Budget: ~25 hops, stopped at genuine satisfaction (19 hops).

## Hop journal

**Hop 1 — search("philosophers")**
Candidates: Marcus Aurelius hub (federation_kb, obvious literal match) · a Russian fragment on education/freedom ("...позволяет человеку свободно выбирать...") · "Лаборатория: Сырые мысли → Контент" (looplab0, odd unrelated hit) · "Dogfooding" thoughts note.
Felt pull: the literal match (Marcus Aurelius) felt like the "assigned" move — too on-the-rails for a curiosity walk. The looplab0 hit was a search-engine tangent (word "философия" appears inside it) but the title itself — a content pipeline lab — was more surprising than the expected result.
Choice: read looplab0. Why: genuine surprise beats obvious relevance at hop 1.
Finding: it's a landing page for a course teaching "raw thought → AI instruction → finished post," explicitly self-referential — "this page was made by the same tools the lab teaches."

**Hop 2 — similar(pid=144, looplab0)**
Candidates: a cluster of "week_N_homework" course notes (mechanical, repetitive) vs. "Content Infrastructure for Human-AI Workflows" (a standalone essay, same topic but conceptual not pedagogical).
Felt pull: the homework cluster looked like a gravity well — five near-identical notes about the same course. Skipped it deliberately.
Choice: the essay. Why: wanted the idea, not the syllabus.

**Hop 3 — read "Content Infrastructure for Human-AI Workflows"**
Finding: a manifesto — trip2g positions itself as "content infrastructure," not a CMS/wiki/SSG. Central metaphor: content doesn't sit still, it *flows* — a chain of human/AI/bot transformations, each a link. AI is framed as "a participant, not a tool."

**Hop 4 — federated_search(kb_id="markavrelii", "control what is in your power")**
Candidates: several Meditations books (04, 05, 08, 12...) turned up as PD-Greek/Russian/English trilingual interlinear text.
Felt pull: Book 4 §1 opened with a fire metaphor that echoed the "flow" language from hop 3 almost exactly — chose it on that resonance rather than book order.
Choice: read Book 4 §1.
Finding: "a bright flame instantly appropriates what's thrown at it, burns it, and blazes even brighter" — the inner ruling faculty doesn't cling, it converts obstacles into fuel. Striking thematic rhyme with the "content flows through transformations" idea two hops earlier — one modern (content pipelines), one 1,900 years old (stoic self-governance), same shape.

**Hop 5 — search("philosophers federation hub corpora stoic")**
Candidates: "Public hub of curated bases" (en/user/hub.md, meta-doc about how federation works) vs. diving straight back into more Meditations books.
Felt pull: wanted to understand the *mechanism* I'd been using rather than keep consuming content through it.
Choice: read hub.md.
Finding: the hub is just Obsidian notes with `mcp_federation_kb_url` frontmatter — "no central registry: the notes in your vault *are* the topology." The doc's own worked example is a fictional "Philosophy Archive" KB — not a real listing, which explains why literal search for "philosophers hub" kept missing.

**Hop 6-7 — federated_search(markavrelii, "philosophers hub federation index" / "мир подобен городу")**
Candidates inside markavrelii: "how_to_build.md" (a recipe note — "adapting this base to another philosopher," parameter table) vs. a folder of terse scholarly cross-reference notes ("Комментарии Яна Унта": Философия, Катул, Мир подобен городу, Град).
Felt pull: "Мир подобен городу" (the world is like a city) — a striking, poetic title, cosmopolitan-stoic trope.
Choice: read it.
Finding: it's a one-line commentary stub — "common Stoic comparison," citing Seneca Ep. 94.19, Musonius Rufus fr. 8, Epictetus 1.11.9 — confirmed by grep hits in Books 4, 6, 10 ("Rome is my city as Antoninus, the world as a human"). Rich idea, terse packaging — the commentary layer is built for citation-chasing, not reading.

**Hop 8 — note_html("en/hub/philosophers.md") — dead end**
Tried the literal path the task brief named. 404 "Note not found." Noted as a real finding, not a mistake to hide: the "philosophers hub federating 21 corpora" the brief describes either isn't reachable under that exact path from the root index, or is nested somewhere I didn't locate in the time I spent (possibly inside markavrelii's own commentary apparatus, which cites many other Stoics but doesn't appear to *federate* them as separate MCP bases — it's citations, not corpora).

**Hop 9 — search("Minion School" / "personal journal" / "21 corpora")**
Candidates surfaced: "Minion School" (federation_kb) · "Foragent" (federation_kb) · "Personal agent — batteries included" (local note) · "The agent keeps a team journal" (local note).
Felt pull: "Minion School" — an odd, playful name (Despicable Me minions?) attached to something federated. Wanted to know what it actually was before the personal-journal thread, since the name promised more surprise.
Choice: Minion School.

**Hop 10 — note_html("en/hub/minionschool.md")**
Finding: one line — "Useful agent skills. Source: minionschool.2pub.ru." A pointer, nothing else.

**Hop 11 — federated_search(kb_id="minionschool", "skills teach agent how to")**
Candidates: "Правило: что умеет агент" (capabilities rules) · "Denis Sexy IT" (a source note) · "Чувственный опыт" (insights/sensory_experience — evocative title, hints at AI phenomenology) · "Anthropic Blog" (source note).
Felt pull: "sensory experience" for an agent KB was the most surprising possible title — could be about AI qualia, could be a red herring. Anthropic Blog also pulled hard (direct interest in my own model family's public writing, and — being the "different family" datapoint in this experiment — curious how an outside base cites Anthropic).
Choice: sensory_experience first, since it was the odder of the two.
Finding: mild anticlimax — it's a copywriting rule ("write so a human's head plays a movie"), attributed to Maxim Ilyahov, not agent phenomenology at all. Good example of a title over-promising.

**Hop 12 — read "sources/anthropic_blog.md"**
Finding: this whole KB is explicitly built by summarizing Anthropic's own engineering blog (Building Effective Agents, Context Engineering, Writing Effective Tools, Claude Code best practices, Contextual Retrieval) into local "insights/" notes — i.e., an operator's distilled internal doc, sourced almost entirely from the company that makes my sibling models. As the "different model family" wanderer, this felt like the sharpest moment of the walk: the graph runs on ideas from Claude's own house docs, read here by codex.

**Hop 13 — read "insights/autonomy_levels.md"**
Candidates linked from the bibliography: autonomy_levels vs. budgets_and_stopping vs. draft_and_commit.
Felt pull: autonomy_levels, because it's literally the axis I'm operating on right now (a bounded, unsupervised ~25-hop walk).
Finding: a clean 0-4 taxonomy (Answer → Draft → Confirm → Policy-bound → Long-goal), with a governance rule: "start at the lowest useful level, raise it only after it's proven stable below," and a demotion trigger if an irreversible action happens at L3 without a covering instruction.

**Hop 14 — read "behaviors/risky_actions.md"**
Finding: the operational counterpart to autonomy levels — draft → preview → explicit "apply? yes/no" for anything irreversible, with an explicit rule against treating a general "ok" as consent for a specific action. Practical, not theoretical.

**Hop 15 — read "instructions/create_instruction.md"**
Felt pull: this was the natural last link — an instruction about how to write new instructions, i.e. the KB documenting its own bootstrapping process.
Finding: a recursive meta-instruction (ask for a name, a trigger, reused sub-instructions, a numbered procedure, a risk check, then write it to `instructions/`, register it in `capabilities.md` and `_index.md`, log it in the daily note). Closed the loop back to hop 1: looplab0 was a *content* pipeline that dogfoods itself; this is a *procedure* pipeline that dogfoods itself the same way.

## Final resting place

`instructions/create_instruction.md` inside the `minionschool` federated base (https://minionschool.2pub.ru/instructions/setup_school_mcp neighborhood). Stopped here — genuine satisfaction, not hop-count exhaustion.

## Theme

Recursion / self-application, three times over, in three registers: a content lab that produces itself with its own tools (hop 1-3), a Stoic ethic of turning whatever happens into fuel rather than resisting it (hop 4, 6-7), and an agent-operations manual that writes its own operating instructions (hop 11-15). The literal "philosophers hub" the brief named never resolved to a real path (hop 8, 404) — the graph substituted a *structural* echo of "philosophy" (self-governance, autonomy, converting friction into material) for a *topical* one.

## How it felt

Search kept surfacing the "expected" node first (Marcus Aurelius for "philosophers") and I had to consciously route around it to get anywhere surprising — the literal match is not where the interesting material lives. The commentary-note cluster in markavrelii (terse citation stubs) was a minor gravity well: rich topic, thin payoff, easy to bounce off quickly once I noticed the pattern. The sharpest moment wasn't a philosophy text at all — it was finding an agent-behavior KB built from Anthropic's own engineering blog and reading its autonomy-levels page while mid-walk as an unsupervised agent; the content described my situation back at me. No loops, no real boredom — one dead end (the literal `en/hub/philosophers.md` path) reported honestly rather than papered over.
