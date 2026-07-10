#!/usr/bin/env python3
"""
v3: walls vs no walls.

Same 6 questions, same underlying notes, two access modes:

  WALLED — the live federated hub https://philosophers.2pub.me/_system/mcp:
           the model navigates by kb_id, hub structure and cross-links
           (search / federated_search / note_html / federated_note_html).
  FLAT   — one local `search(query)` tool over ALL corpus notes as a single
           undifferentiated pile (~1500 *.md under ~/projects/korpuses/*.2pub.me,
           excluding .obsidian). No kb_id, no structure.

v3 changes vs bench.py, addressing REVIEW.md:
  - preregistered answer keys (questions_v3.json): required facts + corpus-language
    evidence substrings;
  - task-correctness scored by a cheap LLM judge (gpt-5.4-nano) against the key;
  - no assistant-turn cap: up to 12 individual tool calls, then a forced final;
  - quote validity is cross-lingual by construction: a quote counts if it is a
    substring of retrieved text in either language (EN paraphrase simply fails);
  - navigation efficiency: calls, calls-to-first-relevant-snippet, tokens, cost;
  - model latency and tool latency reported separately;
  - hard budget guard at $1.0 total (the key has ~$1.4 left).
"""
import glob, json, os, re, sys, time, urllib.request

MCP_URL = "https://philosophers.2pub.me/_system/mcp"
OR_URL = "https://openrouter.ai/api/v1/chat/completions"
OR_KEY = os.environ["OPENROUTER_KEY"]
BUDGET_USD = float(os.environ.get("BUDGET_USD", "1.0"))
MAX_TOOL_CALLS = 12
HTTP_TIMEOUT = 90
CORPUS_GLOB = os.path.expanduser("~/projects/korpuses/*.2pub.me")
JUDGE_MODEL = "openai/gpt-5.4-nano"
HERE = os.path.dirname(os.path.abspath(__file__))

_spent = 0.0
_mcp_id = 0


class BudgetHit(Exception):
    pass


def _post(url, payload, headers, timeout=HTTP_TIMEOUT):
    # The hub's front rejects the default python-urllib UA with 403.
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"content-type": "application/json",
                 "user-agent": "trip2g-federated-search-research/3.0", **headers},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip().lower().replace("ё", "е")


# ---------- WALLED condition: live MCP hub ----------

def mcp_call(name, arguments):
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
        ms = int((time.time() - t0) * 1000)
        if not text.strip():
            # The live hub returns an empty note when pid+path are combined or the
            # pid is stale; v2 silently fed the model text:"" — give a signal instead.
            return {"ok": False, "ms": ms,
                    "error": "empty result — use the exact 'path' shown in a "
                             "search result of the same corpus (no pid, no URL)"}
        return {"ok": True, "text": text[:6000], "ms": ms}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": repr(e), "ms": int((time.time() - t0) * 1000)}


WALLED_TOOLS = [
    {"type": "function", "function": {
        "name": "search", "description":
        "Search the hub's own notes (author cards, topic matrix, contradictions index). "
        "Tells you which corpus (kb_id) holds a thinker.",
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
    # v2 offered a `pid` parameter here; on the live endpoint any pid (alone or
    # with path) returns an empty note, and models kept re-sending it. v3 exposes
    # `path` only and strips stray pids (see run_question).
    {"type": "function", "function": {
        "name": "note_html", "description":
        "Read a hub note in full by its exact path from a search result.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "federated_note_html", "description":
        "Read a note inside a connected corpus by kb_id plus its exact path "
        "from a search result.",
        "parameters": {"type": "object", "properties": {
            "kb_id": {"type": "string"}, "path": {"type": "string"}},
            "required": ["kb_id", "path"]}}},
]

# ---------- FLAT condition: one big pile, local full-text search ----------

FLAT_TOOLS = [
    {"type": "function", "function": {
        "name": "search", "description":
        "Full-text search over the entire knowledge store (all notes in one pile). "
        "Returns the top matching snippets with their file paths. Notes are mostly "
        "in Russian; search terms in Russian match best.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}},
            "required": ["query"]}}},
]

_FLAT_DOCS = None  # [(relpath, text, norm_text)]


def flat_load():
    global _FLAT_DOCS
    if _FLAT_DOCS is not None:
        return _FLAT_DOCS
    docs = []
    for base in sorted(glob.glob(CORPUS_GLOB)):
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d != ".obsidian"]
            for fn in files:
                if not fn.endswith(".md"):
                    continue
                p = os.path.join(root, fn)
                try:
                    text = open(p, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                rel = os.path.relpath(p, os.path.dirname(base))
                docs.append((rel, text, _norm(text)))
    _FLAT_DOCS = docs
    return docs


def flat_search(query, limit=6):
    """Fair, crude full-text search: case-insensitive term-frequency scoring over
    every note, no structure, no kb awareness. Returns top snippets + paths."""
    t0 = time.time()
    docs = flat_load()
    terms = [t for t in re.findall(r"\w+", _norm(query)) if len(t) >= 3]
    if not terms:
        return {"ok": True, "text": "no usable search terms", "ms": 0}
    scored = []
    for rel, text, ntext in docs:
        distinct, tf_score, first_pos = 0, 0, None
        for t in terms:
            c = ntext.count(t)
            if c:
                distinct += 1
                tf_score += min(c, 10) * len(t)
                pos = ntext.find(t)
                if first_pos is None or pos < first_pos:
                    first_pos = pos
        if distinct:
            scored.append((distinct * 1000 + tf_score, first_pos or 0, rel, text, ntext))
    scored.sort(key=lambda x: -x[0])
    out = []
    for _score, _pos, rel, text, ntext in scored[:limit]:
        # snippet around the earliest match of the longest present term
        anchor = 0
        for t in sorted(terms, key=len, reverse=True):
            p = ntext.find(t)
            if p >= 0:
                # map normalized offset back approximately via lower() search
                p2 = text.lower().replace("ё", "е").find(t)
                anchor = max(p2, 0)
                break
        lo = max(0, anchor - 300)
        snippet = text[lo:anchor + 600].strip()
        out.append(f"### {rel}\n…{snippet}…")
    text_out = "\n\n".join(out) if out else "no matches"
    return {"ok": True, "text": text_out[:6000], "ms": int((time.time() - t0) * 1000)}


# ---------- shared machinery ----------

def grounding_check(final, retrieved):
    """A quote in the final answer counts iff it is a (normalized) substring of the
    retrieved text. Retrieved notes carry both RU originals and EN translations, so
    a real quote in either language matches; an EN paraphrase of a RU-only passage
    simply does not count."""
    hay = _norm(retrieved)
    quotes = re.findall(r'"([^"]{12,})"|“([^”]{12,})”|«([^»]{12,})»|„([^“]{12,})“',
                        final or "")
    spans = [next(g for g in q if g) for q in quotes]
    spans = [s for s in spans if len(s.split()) >= 6]
    verified = sum(1 for s in spans if _norm(s) in hay)
    return {"quotes": len(spans), "quotes_in_retrieval": verified}


def or_chat(model, messages, tools, tool_choice="auto"):
    global _spent
    if _spent >= BUDGET_USD:
        raise BudgetHit(f"budget ${BUDGET_USD} hit at ${_spent:.4f}")
    payload = {"model": model, "messages": messages, "temperature": 0.0,
               "usage": {"include": True}}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = tool_choice
    t0 = time.time()
    d = _post(OR_URL, payload,
              {"Authorization": f"Bearer {OR_KEY}",
               "HTTP-Referer": "https://trip2g.com",
               "X-Title": "federated-search-research-v3"})
    ms = int((time.time() - t0) * 1000)
    if "choices" not in d:
        raise RuntimeError(f"OpenRouter error: {json.dumps(d)[:300]}")
    usage = d.get("usage", {}) or {}
    cost = float(usage.get("cost", 0.0) or 0.0)
    _spent += cost
    return d["choices"][0]["message"], cost, usage, ms


SYS_PROMPT = (
    "You answer a philosophy question using ONLY the knowledge base reachable "
    "through the given tools. Ground every claim in what the tools return. When "
    "you quote, quote VERBATIM in the source language of the note (most notes are "
    "Russian) — do not translate inside quotation marks; you may add a translation "
    "outside the quotes. If a claim is not in the retrieved material, say so. "
    "You have at most 12 tool calls; then you must answer.")


def run_question(model, q, condition, instructions):
    tools = WALLED_TOOLS if condition == "walled" else FLAT_TOOLS
    sys_prompt = SYS_PROMPT
    if condition == "walled" and instructions:
        sys_prompt += "\n\nEndpoint self-description:\n" + instructions
    messages = [{"role": "system", "content": sys_prompt},
                {"role": "user", "content": q["q"]}]
    trace, retrieved = [], []
    calls_used, first_relevant, model_ms, tool_ms = 0, None, 0, 0
    evid = [_norm(e) for e in q.get("evidence", [])]

    while True:
        forced = calls_used >= MAX_TOOL_CALLS
        msg, cost, usage, ms = or_chat(
            model, messages, tools, tool_choice="none" if forced else "auto")
        model_ms += ms
        messages.append(msg)
        step = {"cost": round(cost, 5), "model_ms": ms,
                "tokens": {"in": usage.get("prompt_tokens"),
                           "out": usage.get("completion_tokens")}}
        tcalls = msg.get("tool_calls") or []
        if not tcalls:
            final = msg.get("content", "")
            step["final_text"] = final
            trace.append(step)
            return {"trace": trace, "final": final, "forced_final": forced,
                    "tool_calls": calls_used, "first_relevant_call": first_relevant,
                    "model_ms": model_ms, "tool_ms": tool_ms,
                    "grounding": grounding_check(final, "\n".join(retrieved)),
                    "retrieved_chars": len("".join(retrieved))}
        step["tool_calls"] = []
        for tc in tcalls:
            fn = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except Exception:  # noqa: BLE001
                args = {}
            calls_used += 1
            if calls_used > MAX_TOOL_CALLS:
                result = {"ok": False,
                          "error": "tool budget exhausted; give your final answer now",
                          "ms": 0}
            elif condition == "walled":
                args.pop("pid", None)  # pid is broken on the live endpoint
                result = mcp_call(fn, args) if fn in {t["function"]["name"] for t in WALLED_TOOLS} \
                    else {"ok": False, "error": f"unknown tool {fn}", "ms": 0}
            else:
                result = flat_search(**args) if fn == "search" \
                    else {"ok": False, "error": f"unknown tool {fn}", "ms": 0}
            tool_ms += result.get("ms") or 0
            txt = result.get("text") or ""
            if txt:
                retrieved.append(txt)
                if first_relevant is None and any(e in _norm(txt) for e in evid):
                    first_relevant = calls_used
            step["tool_calls"].append({
                "n": calls_used, "name": fn, "args": args,
                "result_ok": result.get("ok"),
                "result_preview": (txt or result.get("error", ""))[:800],
                "ms": result.get("ms")})
            messages.append({"role": "tool", "tool_call_id": tc["id"],
                             "content": json.dumps(result, ensure_ascii=False)[:6000]})
        trace.append(step)


def judge(q, final):
    """One cheap LLM-judge call against the preregistered answer key."""
    facts = "\n".join(f"{i+1}. {f}" for i, f in enumerate(q["required_facts"]))
    messages = [
        {"role": "system", "content":
         "You are a strict grader. Given a question, a preregistered list of "
         "required facts, and a candidate answer, decide which required facts the "
         "answer actually states (paraphrase in any language is fine). Include a "
         "fact number in facts_covered ONLY if that fact is fully and substantively "
         "stated — a partially stated fact does not count. Reply with ONLY a JSON "
         "object: {\"facts_covered\": [<fact numbers>], \"note\": \"<one line>\"}."},
        {"role": "user", "content":
         f"QUESTION:\n{q['q']}\n\nREQUIRED FACTS:\n{facts}\n\nANSWER:\n{final or '(no answer)'}"}]
    msg, cost, _usage, _ms = or_chat(JUDGE_MODEL, messages, tools=None)
    raw = msg.get("content", "") or ""
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        v = json.loads(m.group(0)) if m else {}
    except Exception:  # noqa: BLE001
        v = {}
    covered = [n for n in (v.get("facts_covered") or [])
               if isinstance(n, int) and 1 <= n <= len(q["required_facts"])]
    n_req = len(q["required_facts"])
    verdict = ("unparsed" if not m else
               "correct" if len(set(covered)) == n_req else
               "partial" if covered else "incorrect")
    return {"verdict": verdict, "facts_covered": sorted(set(covered)),
            "note": v.get("note", ""), "raw": raw[:500], "judge_cost": round(cost, 6)}


def get_instructions():
    global _mcp_id
    _mcp_id += 1
    d = _post(MCP_URL, {"jsonrpc": "2.0", "id": _mcp_id, "method": "initialize",
              "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                         "clientInfo": {"name": "bench-v3", "version": "3"}}}, {})
    return d.get("result", {}).get("instructions", "")


def main():
    models = json.loads(os.environ.get(
        "MODELS", '["openai/gpt-5.4-nano", "openai/gpt-5.4-mini"]'))
    conditions = json.loads(os.environ.get("CONDITIONS", '["walled", "flat"]'))
    only_q = os.environ.get("ONLY_Q")  # e.g. "1" for a smoke test
    questions = json.load(open(os.path.join(HERE, "questions_v3.json")))
    if only_q:
        questions = [q for q in questions if str(q["id"]) == only_q]
    instructions = get_instructions()
    n_docs = len(flat_load())
    print(f"flat pile: {n_docs} notes; budget ${BUDGET_USD}")
    os.makedirs(os.path.join(HERE, "logs_v3"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    summary = []
    halted = None
    try:
        for model in models:
            for cond in conditions:
                for q in questions:
                    slug = model.split("/")[-1]
                    print(f"[{cond}|{slug}] Q{q['id']} (spent ${_spent:.4f})",
                          flush=True)
                    t0 = time.time()
                    out = run_question(model, q, cond, instructions)
                    verdict = judge(q, out["final"])
                    rec = {"model": model, "condition": cond, "qid": q["id"],
                           "q": q["q"], "kind": q["kind"],
                           "wall_s": round(time.time() - t0, 1),
                           "judge": verdict, **out}
                    with open(os.path.join(HERE, "logs_v3",
                              f"{cond}__{slug}__q{q['id']}.json"), "w") as f:
                        json.dump(rec, f, ensure_ascii=False, indent=2)
                    cost_q = sum(s.get("cost", 0) for s in out["trace"])
                    summary.append({
                        "model": model, "condition": cond, "qid": q["id"],
                        "verdict": verdict["verdict"],
                        "facts_covered": len(verdict["facts_covered"]),
                        "facts_required": len(q["required_facts"]),
                        "quotes": out["grounding"]["quotes"],
                        "quotes_valid": out["grounding"]["quotes_in_retrieval"],
                        "tool_calls": out["tool_calls"],
                        "first_relevant_call": out["first_relevant_call"],
                        "forced_final": out["forced_final"],
                        "model_ms": out["model_ms"], "tool_ms": out["tool_ms"],
                        "cost_usd": round(cost_q, 5),
                        "wall_s": rec["wall_s"]})
                    print(f"   -> {verdict['verdict']} "
                          f"({len(verdict['facts_covered'])}/{len(q['required_facts'])} facts), "
                          f"{out['tool_calls']} calls, first_rel={out['first_relevant_call']}, "
                          f"${cost_q:.4f}", flush=True)
    except BudgetHit as e:
        halted = str(e)
        print(f"HALT: {e}", flush=True)
    with open(os.path.join(HERE, "results", "summary_v3.json"), "w") as f:
        json.dump({"spent_usd": round(_spent, 4), "budget_usd": BUDGET_USD,
                   "halted": halted, "runs": summary}, f,
                  ensure_ascii=False, indent=2)
    print(f"\nDONE. total spent: ${_spent:.4f}  runs: {len(summary)}")


if __name__ == "__main__":
    main()
