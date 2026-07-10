#!/usr/bin/env python3
"""
flat-hybrid: no walls, but a real retrieval stack.

RESULTS_v3.md compared the walled federated hub against a deliberately naive
flat pile (substring TF scoring). This run upgrades the flat side to a serious
local store: the same ~1338 notes in ONE trip2g instance with hybrid search —
BM25 + bge-m3 vector search fused by RRF + bge-reranker-v2-m3 cross-encoder
blending (the GraphQL `search` path, internal/case/sitesearch). Still one
`search(query)` tool, still no kb_id, no walls, no note reading.

Focus: CONFUSION. Does a big flat pile make small models conflate thinkers —
attribute claims to the wrong philosopher, blend Nietzsche/Schopenhauer,
retrieve cross-contaminating snippets? Two measurements per run:
  - retrieval contamination: share of returned notes whose corpus folder is
    outside the question's expected corpora (questions_v3.json expect_kb);
    hub-level notes (philosophers/) count as neutral;
  - answer misattribution: a second LLM-judge call flags claims attributed to
    the wrong thinker or blended between thinkers.

Everything else mirrors v3_bench.py: same 6 questions + preregistered keys,
same fact judge (gpt-5.4-nano), same 12-tool-call cap, cross-lingual verbatim
quote check, $1.0 hard budget guard.

Requires a running instance:
  MODELS_DIR=/mnt/extssd/models node cli/memcli/dist/memcli.js up \
    --embedded --reranker --folder ~/projects/trip2g_all_kbs \
    --port 24091 --name allkbs
Auth: reads JWT_SECRET from <vault>/.trip2g-memory env file and logs in via
the HAT flow, exactly like memcli itself does.
"""
import base64, hashlib, hmac, json, os, re, sys, time
import urllib.error, urllib.parse, urllib.request

BASE_URL = os.environ.get("BASE_URL", "http://localhost:24091")
VAULT = os.path.expanduser(os.environ.get("VAULT", "~/projects/trip2g_all_kbs"))
EMAIL = os.environ.get("EMAIL", "memory@local")
OR_URL = "https://openrouter.ai/api/v1/chat/completions"
OR_KEY = os.environ["OPENROUTER_KEY"]
BUDGET_USD = float(os.environ.get("BUDGET_USD", "1.0"))
MAX_TOOL_CALLS = 12
HTTP_TIMEOUT = 90
JUDGE_MODEL = "openai/gpt-5.4-nano"
HERE = os.path.dirname(os.path.abspath(__file__))

# hub-level notes legitimately mention several thinkers — neutral, not contamination
NEUTRAL_FOLDERS = {"philosophers"}

_spent = 0.0


class BudgetHit(Exception):
    pass


def _post(url, payload, headers, timeout=HTTP_TIMEOUT):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"content-type": "application/json",
                 "user-agent": "trip2g-federated-search-research/flat-hybrid", **headers},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _norm(s):
    return re.sub(r"\s+", " ", (s or "")).strip().lower().replace("ё", "е")


# ---------- auth: HAT flow (mirrors memcli signHatJwt/hatAuth) ----------

def _b64url(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def hat_token():
    env_file = os.path.join(VAULT, ".trip2g-memory", "env")
    secret = dict(l.split("=", 1) for l in open(env_file).read().splitlines()
                  if "=" in l)["JWT_SECRET"].strip()
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps(
        {"e": EMAIL, "ae": True, "exp": int(time.time()) + 300}).encode())
    signing = f"{header}.{payload}"
    sig = _b64url(hmac.new(secret.encode(), signing.encode(), hashlib.sha256).digest())
    jwt = f"{signing}.{sig}"
    req = urllib.request.Request(
        f"{BASE_URL}/_system/hat", data=f"token={urllib.parse.quote(jwt)}".encode(),
        headers={"content-type": "application/x-www-form-urlencoded"}, method="POST")

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    opener = urllib.request.build_opener(NoRedirect)
    try:
        r = opener.open(req, timeout=30)
        cookie = r.headers.get("set-cookie", "")
    except urllib.error.HTTPError as e:  # 302 lands here with NoRedirect
        cookie = e.headers.get("set-cookie", "")
    m = re.search(r"trip2g_token=([^;]+)", cookie)
    if not m:
        raise RuntimeError(f"HAT login failed, set-cookie={cookie!r}")
    return m.group(1)


_TOKEN = None


def token():
    global _TOKEN
    if _TOKEN is None:
        _TOKEN = hat_token()
    return _TOKEN


# ---------- the one tool: hybrid GraphQL search ----------

SEARCH_GQL = """query($q:String!){ search(input:{query:$q}) {
  totalCount nodes { url score matchOrigin highlightedTitle highlightedContent } } }"""

TOOLS = [
    {"type": "function", "function": {
        "name": "search", "description":
        "Hybrid search (full-text + semantic vector + cross-encoder reranker) over the "
        "entire knowledge store — all notes in one pile. Returns top matching notes with "
        "their paths and snippets. Notes are mostly in Russian; Russian terms match best, "
        "but semantic search also works across languages.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}},
            "required": ["query"]}}},
]

TAG_RE = re.compile(r"<[^>]+>")


def hybrid_search(query):
    t0 = time.time()
    try:
        d = _post(f"{BASE_URL}/_system/graphql",
                  {"query": SEARCH_GQL, "variables": {"q": query}},
                  {"authorization": f"Bearer {token()}"}, timeout=120)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": repr(e), "ms": int((time.time() - t0) * 1000),
                "paths": [], "origins": []}
    ms = int((time.time() - t0) * 1000)
    if "errors" in d and d["errors"]:
        return {"ok": False, "error": json.dumps(d["errors"])[:300], "ms": ms,
                "paths": [], "origins": []}
    nodes = d.get("data", {}).get("search", {}).get("nodes", []) or []
    out, paths, origins = [], [], []
    for n in nodes[:8]:
        path = urllib.parse.unquote(n.get("url", "").lstrip("/"))
        paths.append(path)
        origins.append(n.get("matchOrigin"))
        snippets = [TAG_RE.sub("", s) for s in (n.get("highlightedContent") or [])[:3]]
        title = TAG_RE.sub("", n.get("highlightedTitle") or "")
        out.append(f"### {path}\n[{n.get('matchOrigin')} score={n.get('score'):.3f}] "
                   f"{title}\n" + "\n".join(f"…{s}…" for s in snippets))
    text = "\n\n".join(out) if out else "no matches"
    return {"ok": True, "text": text[:6000], "ms": ms,
            "paths": paths, "origins": origins}


# ---------- shared machinery (mirrors v3_bench.py) ----------

def grounding_check(final, retrieved):
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
               "X-Title": "federated-search-research-flat-hybrid"})
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


def corpus_of(path):
    return (path.split("/", 1)[0] if "/" in path else path).lower()


def run_question(model, q):
    messages = [{"role": "system", "content": SYS_PROMPT},
                {"role": "user", "content": q["q"]}]
    trace, retrieved = [], []
    calls_used, first_relevant, model_ms, tool_ms = 0, None, 0, 0
    evid = [_norm(e) for e in q.get("evidence", [])]
    expect = set(k.lower() for k in q.get("expect_kb", []))
    ret_total, ret_offtarget, off_corpora = 0, 0, {}
    origin_counts = {}

    while True:
        forced = calls_used >= MAX_TOOL_CALLS
        msg, cost, usage, ms = or_chat(
            model, messages, TOOLS, tool_choice="none" if forced else "auto")
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
                    "retrieved_chars": len("".join(retrieved)),
                    "retrieval": {"results": ret_total,
                                  "offtarget": ret_offtarget,
                                  "offtarget_corpora": off_corpora,
                                  "origins": origin_counts}}
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
            elif fn == "search":
                result = hybrid_search(args.get("query", ""))
            else:
                result = {"ok": False, "error": f"unknown tool {fn}", "ms": 0}
            tool_ms += result.get("ms") or 0
            for p, o in zip(result.get("paths", []), result.get("origins", [])):
                c = corpus_of(p)
                ret_total += 1
                origin_counts[o] = origin_counts.get(o, 0) + 1
                if expect and c not in expect and c not in NEUTRAL_FOLDERS:
                    ret_offtarget += 1
                    off_corpora[c] = off_corpora.get(c, 0) + 1
            txt = result.get("text") or ""
            if txt:
                retrieved.append(txt)
                if first_relevant is None and any(e in _norm(txt) for e in evid):
                    first_relevant = calls_used
            step["tool_calls"].append({
                "n": calls_used, "name": fn, "args": args,
                "result_ok": result.get("ok"),
                "paths": result.get("paths", []),
                "origins": result.get("origins", []),
                "result_preview": (txt or result.get("error", ""))[:800],
                "ms": result.get("ms")})
            messages.append({"role": "tool", "tool_call_id": tc["id"],
                             "content": json.dumps(
                                 {k: result[k] for k in ("ok", "text", "error", "ms")
                                  if k in result}, ensure_ascii=False)[:6000]})
        trace.append(step)


def judge(q, final):
    """Fact-coverage judge — byte-identical prompt to v3_bench.py for comparability."""
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


def confusion_judge(q, final):
    """Misattribution judge: does the answer put claims in the wrong mouth?"""
    facts = "\n".join(f"- {f}" for f in q["required_facts"])
    messages = [
        {"role": "system", "content":
         "You are checking a philosophy answer for MISATTRIBUTION. Given the "
         "question, a preregistered answer key (who actually holds which position), "
         "and a candidate answer, list every place the answer attributes a claim, "
         "quote, or position to the WRONG thinker, or blends two thinkers' positions "
         "into one without distinguishing them. Judge only against the key and "
         "widely-basic attribution (e.g. 'will to power' is Nietzsche, 'will to "
         "live' is Schopenhauer). Ignore correctness/completeness — only who-said-"
         "what errors. Reply with ONLY a JSON object: {\"misattributions\": "
         "[{\"claim\": \"<short paraphrase>\", \"attributed_to\": \"X\", "
         "\"belongs_to\": \"Y\"}], \"blending\": true|false, \"note\": \"<one line>\"}."},
        {"role": "user", "content":
         f"QUESTION:\n{q['q']}\n\nANSWER KEY:\n{facts}\n\nANSWER:\n{final or '(no answer)'}"}]
    msg, cost, _usage, _ms = or_chat(JUDGE_MODEL, messages, tools=None)
    raw = msg.get("content", "") or ""
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        v = json.loads(m.group(0)) if m else {}
    except Exception:  # noqa: BLE001
        v = {}
    mis = v.get("misattributions") or []
    mis = [x for x in mis if isinstance(x, dict)]
    return {"misattributions": mis, "blending": bool(v.get("blending")),
            "note": v.get("note", ""), "raw": raw[:500], "judge_cost": round(cost, 6)}


def main():
    models = json.loads(os.environ.get(
        "MODELS", '["openai/gpt-5.4-nano", "openai/gpt-5.4-mini"]'))
    only_q = os.environ.get("ONLY_Q")
    questions = json.load(open(os.path.join(HERE, "questions_v3.json")))
    if only_q:
        questions = [q for q in questions if str(q["id"]) == only_q]
    probe = hybrid_search("воля к власти")
    if not probe.get("ok"):
        sys.exit(f"hybrid search probe failed: {probe.get('error')}")
    print(f"probe ok: {len(probe['paths'])} results, origins={probe['origins']}; "
          f"budget ${BUDGET_USD}")
    os.makedirs(os.path.join(HERE, "logs_flat_hybrid"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    summary = []
    halted = None
    try:
        for model in models:
            for q in questions:
                slug = model.split("/")[-1]
                print(f"[hybrid|{slug}] Q{q['id']} (spent ${_spent:.4f})", flush=True)
                t0 = time.time()
                out = run_question(model, q)
                verdict = judge(q, out["final"])
                confusion = confusion_judge(q, out["final"])
                rec = {"model": model, "condition": "flat-hybrid", "qid": q["id"],
                       "q": q["q"], "kind": q["kind"],
                       "wall_s": round(time.time() - t0, 1),
                       "judge": verdict, "confusion": confusion, **out}
                with open(os.path.join(HERE, "logs_flat_hybrid",
                          f"hybrid__{slug}__q{q['id']}.json"), "w") as f:
                    json.dump(rec, f, ensure_ascii=False, indent=2)
                cost_q = sum(s.get("cost", 0) for s in out["trace"])
                r = out["retrieval"]
                summary.append({
                    "model": model, "condition": "flat-hybrid", "qid": q["id"],
                    "verdict": verdict["verdict"],
                    "facts_covered": len(verdict["facts_covered"]),
                    "facts_required": len(q["required_facts"]),
                    "misattributions": len(confusion["misattributions"]),
                    "blending": confusion["blending"],
                    "retrieval_results": r["results"],
                    "retrieval_offtarget": r["offtarget"],
                    "origins": r["origins"],
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
                      f"misattr={len(confusion['misattributions'])} "
                      f"blend={confusion['blending']} "
                      f"offtarget={r['offtarget']}/{r['results']}, "
                      f"{out['tool_calls']} calls, ${cost_q:.4f}", flush=True)
    except BudgetHit as e:
        halted = str(e)
        print(f"HALT: {e}", flush=True)
    with open(os.path.join(HERE, "results", "summary_flat_hybrid.json"), "w") as f:
        json.dump({"spent_usd": round(_spent, 4), "budget_usd": BUDGET_USD,
                   "halted": halted, "runs": summary}, f,
                  ensure_ascii=False, indent=2)
    print(f"\nDONE. total spent: ${_spent:.4f}  runs: {len(summary)}")


if __name__ == "__main__":
    main()
