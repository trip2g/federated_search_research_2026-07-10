# MCP Graph Walk — live visualizer

Watch a model walk the trip2g MCP knowledge graph as an animated force-directed graph.
Single-file `index.html` (no build, no dependencies), plus a 60-line CORS proxy.

**TL;DR:** `python3 proxy.py` in one terminal, open `index.html` in a browser, paste an
OpenRouter key, press **Start walk**. Or press **Demo** — no key needed.

## What you see

- **Center**: a force-directed graph growing live. Circles are notes (color = knowledge
  base), diamonds are search queries, hexagon-ish purple nodes are federated-base
  pointers. The node the model is currently on pulses blue.
- **Each hop animates at the real tool-call latency** (measured per call, capped at
  2.5 s) — slow federated hops visibly take longer than local reads.
- **Right sidebar**: journal streaming the model's reasoning text and every tool call
  (name, args, latency, result snippet). Click an entry to highlight its node in the
  graph; clicking a node on the canvas also selects it.
- **Header**: running cost, summed from OpenRouter's `usage.cost`.
- **End state**: the final answer (TASK mode) or the final resting place + emergent
  theme (WANDER mode) in an overlay.

## Usage

```
cd visualizer
python3 proxy.py                 # terminal 1: CORS proxy on :8787
python3 -m http.server 8000      # terminal 2 (or just open index.html via file://)
# open http://localhost:8000
```

1. Paste your OpenRouter API key (password field; stored in `localStorage` only — it is
   never embedded in the file and never sent anywhere except `openrouter.ai`).
2. Pick a model (default `openai/gpt-5.4-nano`; any OpenRouter model id works).
3. Choose **TASK** (type a question) or **WANDER** (no task — a curiosity prompt makes
   the model explore and then describe where it ended up and what theme emerged).
4. Set max turns (default 12) and press **Start walk**.

**Replay** re-animates the last recorded walk from its trace (same hops, same
latencies). **Export** downloads the trace as JSON. **Demo** replays a bundled
pre-recorded trace of real MCP calls against `trip2g.com` (search → section read →
similar → federated hop into the `philosophers` base) with real latencies — works
offline and without any key.

## Why the proxy

`https://trip2g.com/_system/mcp` answers OPTIONS with 204 but sends **no
`Access-Control-Allow-Origin` header**, so browsers block direct fetches. `proxy.py`
(stdlib only) forwards POSTs from `http://localhost:8787` to the hub, adds a custom
`User-Agent` (the hub 403s default library UAs), and adds CORS headers. Point it at
another instance with `MCP_TARGET=https://other.host/_system/mcp python3 proxy.py`.
OpenRouter itself is CORS-open and is called directly from the browser.

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
