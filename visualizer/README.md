# MCP Graph Walk — live visualizer

Watch a model walk the trip2g MCP knowledge graph as an animated force-directed graph.
Single-file `index.html` (no build, no dependencies), plus a small stdlib proxy that
serves the app, bridges CORS to the hub, and can hold the OpenRouter key server-side.

**TL;DR:** `OPENROUTER_KEY=sk-or-... python3 proxy.py` → open <http://localhost:8787>
→ **Start walk**. Or press **Demo** — no key needed.

## What you see

- **The spine**: every tool call becomes a large numbered STEP node, chained
  step 1 → step 2 → … with long, strong links so consecutive steps sit visibly apart.
  The current step pulses blue.
- **Satellites**: the notes each step returned orbit it on short links (color =
  knowledge base; purple = federated-base pointer). Results are **deduped by note
  identity per kb** — a note returned by two different steps is ONE shared node with
  edges to both steps, and node size grows with how many steps touched it, so
  convergence hubs stand out. Notes the model actually opened with `note_html` glow
  with a white outline.
- **Each hop animates at the real tool-call latency** (measured per call, capped at
  2.5 s) — slow federated hops visibly take longer than local reads.
- **Click anything**: a step opens an inspector with the tool name, query/args, kb,
  latency, and the model's reasoning before that call; a result node shows its title,
  path, URL, snippet, how many steps returned it, and the content excerpt if it was
  read. Journal entries (right sidebar) are clickable too and highlight their step.
- **Header**: running cost, summed from OpenRouter's `usage.cost`.
- **End state**: the final answer (TASK mode) or the final resting place + emergent
  theme (WANDER mode) in an overlay.

## Usage

One command:

```
cd visualizer
OPENROUTER_KEY=sk-or-... python3 proxy.py
# open http://localhost:8787
```

With the env key set, the page (via `GET /config`) hides the key input entirely and
routes model calls through the proxy's `POST /openrouter`, which adds the
`Authorization` header server-side — the key never reaches the browser, localStorage,
or exported traces.

Fallback (no env key): run `python3 proxy.py` plain and either open
<http://localhost:8787> or `index.html` via `file://`. Paste your OpenRouter key in the
UI (stored in `localStorage` only; sent only to `openrouter.ai`, which is CORS-open).

1. Pick a model (default `openai/gpt-5.4-nano`; any OpenRouter model id works).
2. Choose **TASK** (type a question) or **WANDER** (no task — a curiosity prompt makes
   the model explore and then describe where it ended up and what theme emerged).
3. Set max turns (default 12) and press **Start walk**.

**Replay** re-animates the last recorded walk from its trace (same hops, same
latencies). **Export** downloads the trace as JSON. **Demo** replays a bundled
pre-recorded trace of real MCP calls against `trip2g.com` (search → section read →
similar → federated hop into the `philosophers` base) with real latencies — works
offline and without any key.

## Why the proxy

`https://trip2g.com/_system/mcp` answers OPTIONS with 204 but sends **no
`Access-Control-Allow-Origin` header**, so browsers block direct fetches. `proxy.py`
(stdlib only) serves the app on `http://localhost:8787` and exposes:

| Route | What it does |
|---|---|
| `GET /` | serves `index.html` |
| `GET /config` | `{"hasKey": bool, "mcpTarget": "..."}` — the UI probes this on load |
| `POST /openrouter` | forwards to OpenRouter, adding `Authorization` from `OPENROUTER_KEY` (403 if unset) |
| `POST /` (anything else) | forwards JSON-RPC to the MCP hub, adding a custom `User-Agent` (the hub 403s default library UAs) |

Point it at another instance with `MCP_TARGET=https://other.host/_system/mcp`.

## How it works

The page speaks JSON-RPC 2.0 to the MCP endpoint: `initialize` + `tools/list` on start,
then maps `search`, `note_html`, `expand`, `similar` and their `federated_*` twins into
OpenAI-style function tools (appending a hint that nested bases chain with `/` in
`kb_id`, e.g. `philosophers/machiavelli`). A plain tool-use loop against OpenRouter
`/chat/completions` executes each tool call via `tools/call`, measures its latency,
feeds the text content back to the model, and interprets `structuredContent` into graph
deltas (query node → result notes; note → note; hub → federated base). JSON-RPC `error`
responses are surfaced as errors in the journal and fed back to the model as `ERROR:`,
never rendered as empty results.

The trace format (also what Export produces):

```json
{ "mode": "task", "task": "…", "model": "…", "cost": 0.0042,
  "events": [
    { "t": "assistant", "text": "reasoning…" },
    { "t": "tool", "name": "search", "args": {…}, "ms": 1470,
      "result": { "text": "snippet…", "structured": { "results": […] } } },
    { "t": "final", "text": "answer…" } ] }
```

Replay re-feeds these events through the same graph interpreter, sleeping `min(ms, 2500)`
per hop, so a replayed walk moves exactly like the live one did.
