#!/usr/bin/env python3
"""
v5: the clean re-test — deduplicated vault + cite-and-verify provenance.

Two changes vs flat_hybrid_bench.py (v4):

1. CLEAN corpus. v4 ran over a vault polluted with ~400 docs-hub duplicate
   cards; this run uses ~/projects/trip2g_all_kbs_clean — 924 unique notes
   (concepts/principles/chains + the philosophers hub, duplicates stripped).

2. CITE-AND-VERIFY. The model must append a SOURCES section citing, per claim,
   the exact note path from the search results plus the thinker it belongs to.
   Provenance is then checked deterministically, no judge:
     - fabricated: the cited path never appeared in this run's search results;
     - author mismatch: the cited path's corpus folder is not the thinker the
       claim is attributed to (hub notes counted separately, not as mismatch).
   Paths are language-stable, so this metric works identically for the EN and
   RU question sets and dodges the EN/RU verbatim-quote confound.

Runs both questions_v3.json (EN) and questions_v3_ru.json (RU) over both
models. Everything else (tool, judges, budget guard) is inherited from
flat_hybrid_bench.py — this script monkeypatches only the system prompt.
"""
import json, os, re, sys, time

os.environ.setdefault("VAULT", "~/projects/trip2g_all_kbs_clean")
os.environ.setdefault("BASE_URL", "http://localhost:24091")

import flat_hybrid_bench as b  # noqa: E402  (env must be set before import)

HERE = os.path.dirname(os.path.abspath(__file__))

CITE_PROMPT = (
    " After your final answer, append a section titled SOURCES. In it, one "
    "line per claim, formatted exactly: `- <thinker>: <note path exactly as "
    "shown in the search results> — <short claim summary>`. The thinker name "
    "before the colon is REQUIRED — name whose position the claim is. Example: "
    "`- Nietzsche: nietzsche/concepts/volya_k_vlasti — will to power drives "
    "all life`. Cite ONLY paths that appeared in your search results in this "
    "conversation.")

# corpus folder → name aliases (EN + RU) for the author-match check
ALIASES = {
    "adler": ["adler", "адлер"],
    "confucius": ["confucius", "конфуций", "конфуци"],
    "epictetus": ["epictetus", "эпиктет"],
    "ford": ["ford", "форд"],
    "franklin": ["franklin", "франклин"],
    "goethe": ["goethe", "гёте", "гете"],
    "hill": ["hill", "хилл"],
    "ignatius": ["ignatius", "игнатий", "игнати"],
    "james-allen": ["james-allen", "james allen", "аллен"],
    "laozi": ["laozi", "лао-цзы", "лао цзы", "лаоцзы", "lao tzu", "lao-tzu"],
    "larochefoucauld": ["larochefoucauld", "la rochefoucauld", "ларошфуко"],
    "lebon": ["lebon", "le bon", "лебон"],
    "machiavelli": ["machiavelli", "макиавелли"],
    "montaigne": ["montaigne", "монтень"],
    "nietzsche": ["nietzsche", "ницше"],
    "pascal": ["pascal", "паскаль"],
    "rockefeller": ["rockefeller", "рокфеллер"],
    "schopenhauer": ["schopenhauer", "шопенгауэр"],
    "smiles": ["smiles", "смайлс"],
    "tolstoy": ["tolstoy", "толстой", "толсто"],
    "wattles": ["wattles", "уоттлс", "уотлс"],
}

PATH_RE = re.compile(r"[A-Za-z0-9_\-]+(?:/[A-Za-z0-9_\-.]+)+")


def _norm_path(p):
    return p.strip().strip("/").removesuffix(".md")


def verify_citations(final, retrieved_paths):
    """Parse the SOURCES section and verify each citation deterministically."""
    retrieved = {_norm_path(p) for p in retrieved_paths}
    m = re.search(r"^#*\s*(?:SOURCES|ИСТОЧНИКИ)\b.*$", final or "",
                  re.I | re.M)
    cites = []
    if m:
        block = (final or "")[m.end():]
        for line in block.splitlines():
            line = line.strip()
            if not line.startswith(("-", "*", "•")):
                continue
            pm = PATH_RE.search(line)
            if not pm:
                continue
            path = _norm_path(pm.group(0))
            corpus = path.split("/", 1)[0].lower()
            low = line.lower()
            named = [c for c, names in ALIASES.items()
                     if any(n in low[:pm.start()] for n in names)]
            if not named:
                # No `<thinker>:` prefix — fall back to the claim text, but
                # only when it names exactly one thinker (else ambiguous).
                in_claim = [c for c, names in ALIASES.items()
                            if any(n in low[pm.end():] for n in names)]
                if len(in_claim) == 1:
                    named = in_claim
            cites.append({
                "line": line[:200], "path": path, "corpus": corpus,
                "named": named,
                "retrieved": path in retrieved,
                "hub": corpus == "philosophers",
                # author match only judgeable when the line names a thinker
                # and the cite is a corpus note (hub notes carry many thinkers)
                "author_match": (corpus in named) if (named and corpus != "philosophers") else None,
            })
    total = len(cites)
    fabricated = sum(1 for c in cites if not c["retrieved"])
    judgeable = [c for c in cites if c["author_match"] is not None]
    mismatch = sum(1 for c in judgeable if not c["author_match"])
    return {
        "cites": cites, "total": total, "fabricated": fabricated,
        "hub_cites": sum(1 for c in cites if c["hub"]),
        "judgeable": len(judgeable), "author_mismatch": mismatch,
        "provenance_ok": (len(judgeable) - mismatch),
    }


def trace_paths(out):
    paths = []
    for step in out["trace"]:
        for tc in step.get("tool_calls", []):
            paths.extend(tc.get("paths", []))
    return paths


def main():
    models = json.loads(os.environ.get(
        "MODELS", '["openai/gpt-5.4-nano", "openai/gpt-5.4-mini"]'))
    langs = json.loads(os.environ.get("LANGS", '["en", "ru"]'))
    only_q = os.environ.get("ONLY_Q")
    qfiles = {"en": "questions_v3.json", "ru": "questions_v3_ru.json"}

    b.SYS_PROMPT = b.SYS_PROMPT + CITE_PROMPT

    # CPU-reranked searches and slow model turns both exceeded the inherited
    # 90s read timeout and one hung read killed a whole sweep. Raise the
    # default read timeout to 120s and retry a timed-out HTTP call once.
    _orig_post = b._post

    def _patched_post(url, payload, headers, timeout=120):
        try:
            return _orig_post(url, payload, headers, timeout)
        except (TimeoutError, OSError):
            time.sleep(5)
            return _orig_post(url, payload, headers, timeout)
    b._post = _patched_post

    resume = os.environ.get("RESUME", "1") not in ("", "0", "false")

    probe = b.hybrid_search("воля к власти")
    if not probe.get("ok"):
        sys.exit(f"hybrid search probe failed: {probe.get('error')}")
    print(f"probe ok: {len(probe['paths'])} results, origins={probe['origins']}; "
          f"budget ${b.BUDGET_USD}")
    os.makedirs(os.path.join(HERE, "logs_flat_hybrid_clean"), exist_ok=True)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    summary, halted = [], None
    try:
        for model in models:
            for lang in langs:
                questions = json.load(open(os.path.join(HERE, qfiles[lang])))
                if only_q:
                    questions = [q for q in questions if str(q["id"]) == only_q]
                for q in questions:
                    slug = model.split("/")[-1]
                    log_path = os.path.join(HERE, "logs_flat_hybrid_clean",
                                            f"clean__{lang}__{slug}__q{q['id']}.json")
                    if resume and os.path.exists(log_path):
                        prev = json.load(open(log_path))
                        if "summary_row" in prev:
                            summary.append(prev["summary_row"])
                            print(f"[clean|{lang}|{slug}] Q{q['id']} — resumed from log",
                                  flush=True)
                            continue
                    print(f"[clean|{lang}|{slug}] Q{q['id']} (spent ${b._spent:.4f})",
                          flush=True)
                    t0 = time.time()
                    try:
                        out = b.run_question(model, q)
                    except b.BudgetHit:
                        raise
                    except Exception as e:  # noqa: BLE001 — one bad run must not kill the sweep
                        print(f"   -> RUN FAILED: {e!r}", flush=True)
                        summary.append({"model": model, "lang": lang,
                                        "qid": q["id"], "verdict": "run-error",
                                        "error": repr(e)[:200]})
                        continue
                    verdict = b.judge(q, out["final"])
                    confusion = b.confusion_judge(q, out["final"])
                    prov = verify_citations(out["final"], trace_paths(out))
                    cost_q = sum(s.get("cost", 0) for s in out["trace"])
                    r = out["retrieval"]
                    row = {
                        "model": model, "lang": lang, "qid": q["id"],
                        "verdict": verdict["verdict"],
                        "facts_covered": len(verdict["facts_covered"]),
                        "facts_required": len(q["required_facts"]),
                        "misattributions": len(confusion["misattributions"]),
                        "blending": confusion["blending"],
                        "cites": prov["total"], "cites_fabricated": prov["fabricated"],
                        "cites_judgeable": prov["judgeable"],
                        "cites_author_mismatch": prov["author_mismatch"],
                        "cites_hub": prov["hub_cites"],
                        "retrieval_results": r["results"],
                        "retrieval_offtarget": r["offtarget"],
                        "origins": r["origins"],
                        "quotes": out["grounding"]["quotes"],
                        "quotes_valid": out["grounding"]["quotes_in_retrieval"],
                        "tool_calls": out["tool_calls"],
                        "first_relevant_call": out["first_relevant_call"],
                        "forced_final": out["forced_final"],
                        "cost_usd": round(cost_q, 5),
                        "wall_s": round(time.time() - t0, 1)}
                    rec = {"model": model, "condition": "flat-hybrid-clean",
                           "lang": lang, "qid": q["id"], "q": q["q"],
                           "kind": q["kind"], "wall_s": row["wall_s"],
                           "judge": verdict, "confusion": confusion,
                           "provenance": prov, "summary_row": row, **out}
                    with open(log_path, "w") as f:
                        json.dump(rec, f, ensure_ascii=False, indent=2)
                    summary.append(row)
                    print(f"   -> {verdict['verdict']} "
                          f"({len(verdict['facts_covered'])}/{len(q['required_facts'])}), "
                          f"misattr={len(confusion['misattributions'])} "
                          f"cites={prov['total']} fab={prov['fabricated']} "
                          f"mismatch={prov['author_mismatch']}/{prov['judgeable']} "
                          f"offtarget={r['offtarget']}/{r['results']}, ${cost_q:.4f}",
                          flush=True)
    except b.BudgetHit as e:
        halted = str(e)
        print(f"HALT: {e}", flush=True)
    with open(os.path.join(HERE, "results", "summary_flat_hybrid_clean.json"), "w") as f:
        json.dump({"spent_usd": round(b._spent, 4), "budget_usd": b.BUDGET_USD,
                   "halted": halted, "runs": summary}, f,
                  ensure_ascii=False, indent=2)
    print(f"\nDONE. total spent: ${b._spent:.4f}  runs: {len(summary)}")


if __name__ == "__main__":
    main()
