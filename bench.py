#!/usr/bin/env python3
"""
Benchmark: how well do small LLMs navigate a federated MCP knowledge graph and
ground their answers in it?

Target: https://philosophers.2pub.me/_system/mcp — a trip2g hub that federates
21 philosopher corpora, each carrying verbatim-anchored quotes plus cross-corpus
"who argues with whom" links.

We give a model the hub's MCP tools (search / federated_search / note_html /
federated_note_html), ask a philosophy question, run a real tool-use loop against
the LIVE endpoint, and log every tool call + the final answer. No scoring is
baked in here — the raw logs are the deliverable; interpretation lives in RESULTS.md.

Cost is tracked from OpenRouter's own usage accounting and the run halts before a
hard budget ceiling.
"""
import json, os, sys, time, urllib.request, urllib.error

MCP_URL = "https://trip2g.com/_system/mcp"
OR_URL = "https://openrouter.ai/api/v1/chat/completions"
OR_KEY = os.environ["OPENROUTER_KEY"]
BUDGET_USD = float(os.environ.get("BUDGET_USD", "2.7"))  # stop before the real $3
MAX_TURNS = 10
HTTP_TIMEOUT = 60

_spent = 0.0
_mcp_id = 0


def _post(url, payload, headers, timeout=HTTP_TIMEOUT):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"content-type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def mcp_call(name, arguments):
    """One MCP tools/call against the live hub. Returns text + raw for logging."""
    global _mcp_id
    _mcp_id += 1
    body = {"jsonrpc": "2.0", "id": _mcp_id, "method": "tools/call",
            "params": {"name": name, "arguments": arguments}}
    t0 = time.time()
    try:
        d = _post(MCP_URL, body, {})
        res = d.get("result", {})
        parts = res.get("content", [])
        text = "\n".join(p.get("text", "") for p in parts if p.get("type") == "text")
        struct = res.get("structuredContent")
        return {"ok": True, "text": text[:6000], "structured": struct,
                "ms": int((time.time() - t0) * 1000)}
    except Exception as e:  # noqa: BLE001 — record any failure verbatim
        return {"ok": False, "error": repr(e), "ms": int((time.time() - t0) * 1000)}


# Tool schemas handed to the model (OpenAI/OpenRouter function-calling format).
TOOLS = [
    {"type": "function", "function": {
        "name": "search", "description":
        "Search the hub's own notes (author cards, topic matrix, contradictions index). "
        "Use first to orient — it tells you which corpus (kb_id) holds a thinker.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "federated_search", "description":
        "Search a connected corpus. Pass kb_id (e.g. 'nietzsche', 'epictetus') to target "
        "one base reliably. Omitting kb_id fans out to all peers and may time out.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}, "kb_id": {"type": "string"}},
            "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "note_html", "description":
        "Read a hub note in full by its path or pid (from a search result).",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "pid": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "federated_note_html", "description":
        "Read a note inside a connected corpus. Requires kb_id plus a path or pid.",
        "parameters": {"type": "object", "properties": {
            "kb_id": {"type": "string"}, "path": {"type": "string"},
            "pid": {"type": "string"}}, "required": ["kb_id"]}}},
]

TOOL_NAMES = {t["function"]["name"] for t in TOOLS}


def get_instructions():
    global _mcp_id
    _mcp_id += 1
    d = _post(MCP_URL, {"jsonrpc": "2.0", "id": _mcp_id, "method": "initialize",
              "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                         "clientInfo": {"name": "bench", "version": "1"}}}, {})
    return d.get("result", {}).get("instructions", "")


def or_chat(model, messages):
    """One OpenRouter completion. Returns (message, cost_usd)."""
    global _spent
    payload = {"model": model, "messages": messages, "tools": TOOLS,
               "tool_choice": "auto", "temperature": 0.0,
               "usage": {"include": True}}
    d = _post(OR_URL, payload,
              {"Authorization": f"Bearer {OR_KEY}",
               "HTTP-Referer": "https://trip2g.com",
               "X-Title": "federated-search-research"})
    if "choices" not in d:
        raise RuntimeError(f"OpenRouter error: {json.dumps(d)[:300]}")
    usage = d.get("usage", {}) or {}
    cost = float(usage.get("cost", 0.0) or 0.0)
    _spent += cost
    return d["choices"][0]["message"], cost, usage


def run_question(model, q):
    instr = INSTRUCTIONS
    sys_prompt = (
        "You are answering a philosophy question using ONLY a federated knowledge "
        "base reached through the given tools. Ground every claim in what the tools "
        "return; quote verbatim where the corpus provides quotes. If a claim isn't in "
        "the retrieved material, say so. Navigate deliberately: orient with `search`, "
        "then target a specific corpus with `federated_search(kb_id=...)`.\n\n"
        "Endpoint self-description:\n" + instr)
    messages = [{"role": "system", "content": sys_prompt},
                {"role": "user", "content": q}]
    trace = []
    for turn in range(MAX_TURNS):
        if _spent >= BUDGET_USD:
            trace.append({"halted": "budget", "spent": round(_spent, 4)})
            return {"trace": trace, "final": None, "halted": "budget"}
        msg, cost, usage = or_chat(model, messages)
        messages.append(msg)
        step = {"turn": turn, "cost": round(cost, 5),
                "tokens": {"in": usage.get("prompt_tokens"),
                           "out": usage.get("completion_tokens")}}
        tcalls = msg.get("tool_calls") or []
        if not tcalls:
            step["final_text"] = msg.get("content", "")
            trace.append(step)
            return {"trace": trace, "final": msg.get("content", ""), "halted": None}
        step["tool_calls"] = []
        for tc in tcalls:
            fn = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except Exception:  # noqa: BLE001
                args = {}
            if fn not in TOOL_NAMES:
                result = {"ok": False, "error": f"unknown tool {fn}"}
            else:
                result = mcp_call(fn, args)
            step["tool_calls"].append({"name": fn, "args": args,
                                       "result_ok": result.get("ok"),
                                       "result_preview": (result.get("text") or
                                                          result.get("error", ""))[:500],
                                       "ms": result.get("ms")})
            messages.append({"role": "tool", "tool_call_id": tc["id"],
                             "content": json.dumps(result)[:6000]})
        trace.append(step)
    trace.append({"halted": "max_turns"})
    return {"trace": trace, "final": None, "halted": "max_turns"}


INSTRUCTIONS = ""


def main():
    global INSTRUCTIONS
    models = json.loads(os.environ.get("MODELS", '["anthropic/claude-haiku-4.5"]'))
    questions = json.load(open(os.path.join(os.path.dirname(__file__), "questions.json")))
    INSTRUCTIONS = get_instructions()
    os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)
    summary = []
    for model in models:
        for q in questions:
            if _spent >= BUDGET_USD:
                print(f"BUDGET HIT (${_spent:.3f}); stopping"); break
            print(f"[{model}] Q{q['id']}: {q['q'][:60]}...  (spent ${_spent:.3f})")
            t0 = time.time()
            out = run_question(model, q["q"])
            rec = {"model": model, "qid": q["id"], "q": q["q"], "kind": q["kind"],
                   "expect_kb": q.get("expect_kb"),
                   "wall_s": round(time.time() - t0, 1),
                   "halted": out["halted"], "final": out["final"], "trace": out["trace"]}
            slug = model.split("/")[-1]
            with open(os.path.join(os.path.dirname(__file__), "logs",
                      f"{slug}__q{q['id']}.json"), "w") as f:
                json.dump(rec, f, ensure_ascii=False, indent=2)
            # compact summary row
            tools_used = [c["name"] for s in out["trace"] for c in s.get("tool_calls", [])]
            kbs = [c["args"].get("kb_id") for s in out["trace"]
                   for c in s.get("tool_calls", []) if c["args"].get("kb_id")]
            summary.append({"model": model, "qid": q["id"], "kind": q["kind"],
                            "n_tool_calls": len(tools_used), "tools": tools_used,
                            "kb_ids": kbs, "expect_kb": q.get("expect_kb"),
                            "halted": out["halted"], "wall_s": rec["wall_s"]})
    with open(os.path.join(os.path.dirname(__file__), "results", "summary.json"), "w") as f:
        json.dump({"spent_usd": round(_spent, 4), "runs": summary}, f,
                  ensure_ascii=False, indent=2)
    print(f"\nDONE. total spent: ${_spent:.4f}")
    print(json.dumps(summary, ensure_ascii=False, indent=1)[:2000])


if __name__ == "__main__":
    main()
