# v5 results — clean corpus + cite-and-verify provenance

**TL;DR: three findings, one of which corrects our own v4 metric.**
(1) When the model is *required to cite* — path + thinker per claim, checked
deterministically against what was actually retrieved — provenance is nearly
perfect: **0 wrong-author citations out of 45 judgeable** across 24 runs, and
only 2 fabricated paths (nano, RU, same near-miss slug twice). Small models
*can* bind claims to sources when the tool surface makes them.
(2) Deduplicating the corpus (1344 → 924 notes, the 420 hub-card copies
stripped) did **not** cure prose-level blending: 6–8 hard misattribution flags
per language — the same scale as the polluted v4 and the walled hub — and Q4
still crowns an adjacent corpus the chief anti-Stoic (Goethe now, Wattles
before; the failure survived the cleanup, only the neighbor changed).
(3) The LLM confusion judge does not travel across languages: its raw RU flag
counts were 3–10× inflated by self-declared non-errors in Russian phrasing our
EN-tuned noise filter missed — and at least one surviving RU flag is the judge
itself misattributing. The deterministic citation check, which is
language-stable by construction, is the metric to trust.
n=6 questions per cell, 1 run each — probe, not verdict.

Continues [v4](./RESULTS_flat_hybrid.md) (polluted flat-hybrid) against
[v3](./RESULTS_v3.md) (walled vs naive-flat). Harness:
[`flat_hybrid_clean_bench.py`](./flat_hybrid_clean_bench.py); raw runs:
[`logs_flat_hybrid_clean/`](./logs_flat_hybrid_clean/); rollup:
[`results/summary_flat_hybrid_clean.json`](./results/summary_flat_hybrid_clean.json).

## What changed vs v4

- **Clean corpus.** `~/projects/trip2g_all_kbs_clean`: 924 unique notes; the
  ~420 byte-identical `<corpus>/docs/{en,ru}/hub/*` card copies (each corpus
  carried cards for all thinkers — the qmd comparison caught this) are gone.
  883 of 924 notes embedded (the remainder are short/frontmatter-only; the
  count plateaued and was accepted). One operational trap worth recording:
  the vault shipped *with* its old `.trip2g-memory` state dir, and on first
  `up` the two-way sync **pulled all 420 stripped duplicates back onto disk**
  from the stale DB. A copied vault must never include its state dir. We
  re-stripped, wiped the state, and verified 924 before indexing.
- **Cite-and-verify.** The system prompt requires a SOURCES section
  (`- <thinker>: <note path> — <claim>`). Verification is deterministic:
  a cited path must have appeared in this run's search results (else
  *fabricated*), and its corpus folder must be the thinker the claim names
  (else *author mismatch*; hub notes counted separately). No judge involved,
  and note paths are the same in both question languages.
- **Both languages.** Same 6 questions in EN (`questions_v3.json`) and RU
  (`questions_v3_ru.json`).
- **Harness resilience.** A CPU-reranked search takes 25–35s and one slow
  OpenRouter read killed the first sweep at 10/24: read timeout is now 120s
  with one retry, each question is isolated (a failed run records and the
  sweep continues), and completed runs resume from their logs.

## Results (per model × question language, 6 questions each)

`prov` = judgeable citations with the right author / total judgeable;
`fab` = cited paths never retrieved; `misattr` = hard flags from the LLM
confusion judge after the *revised* bilingual noise filter (see below);
`off-corpus` = retrieved notes outside the question's expected corpora.

| model | lang | correct | facts | prov | fab | misattr (judge) | off-corpus | quotes v/f | calls | $/q |
|---|---|---|---|---|---|---|---|---|---|---|
| nano | en | 0/6 | 8/16 | **8/8** | 0 | 1 | 9% | 10/24 | 21 | $0.0018 |
| nano | ru | **4/6** | 12/16 | **12/12** | 2 | 4 | 18% | 8/23 | 26 | $0.0027 |
| mini | en | 3/6 | 13/16 | **12/12** | 0 | 5 | 10% | 10/13 | 23 | $0.0054 |
| mini | ru | 1/6 | 10/16 | **13/13** | 0 | 4 | 13% | 5/10 | 26 | $0.0068 |

Sweep cost $0.091 (incl. judges), no budget halt.

## Cross-arm comparison, one filter for everything

Applying the same revised noise filter to **all** stored judge outputs
(v3 walled, v3 naive-flat, v4 polluted hybrid, v5 clean hybrid) — which is
why v4's number here reads 8, not the 9 published in RESULTS_flat_hybrid.md:

| arm (12 runs each) | hard misattr | correct |
|---|---|---|
| v3 naive-flat (EN) | 2 | 5/12 |
| v3 walled (EN) | 7 | 8/12 |
| v4 hybrid, polluted corpus (EN) | 8 | 2/12 |
| v5 hybrid, clean corpus (EN) | 6 | 3/12 |
| v5 hybrid, clean corpus (RU) | 8 | 5/12 |

**Did the dedup change the confusion story? Marginally at best.** EN hybrid
went 8 → 6 flags and 2 → 3 correct — a one-to-two-run-sized improvement,
within noise. The instructive detail is *qualitative*: v4's emblematic failure
(Q4 promoting Wattles, a success-lit neighbor, to chief anti-Stoic) recurred
on the clean corpus with **Goethe** in the role. Removing duplicate cards
removed noise copies, but semantic retrieval still surfaces
conceptually-adjacent wrong thinkers, and models still promote them. The
blending failure is a property of *flat semantic retrieval + comparative
notes*, not of dirty data.

**The provenance finding cuts the other way.** The same models, same runs, at
the citation layer: 45/45 judgeable citations name the right corpus's thinker;
2 fabrications total (nano RU citing `confucius/principles/pravlenie`, a
plausible slug that was never in its results — twice). When asked *whose note
says this, exactly*, the models are almost never wrong; the who-said-what
damage lives in the free prose, where claims from a comparison note blend
across its two sides. That suggests the practical fix for flat stores is not
walls but **forcing the claim→source binding into the output format** — and
checking it mechanically, which costs nothing.

## EN vs RU

The raw judge numbers said RU answers were misattribution-riddled (nano: 12 RU
vs 1 EN). Hand-auditing killed that headline: the judge, answering in Russian,
pads its list with entries whose `belongs_to` *says the attribution is
correct* ("верно", "корректно", "Ключ...") — phrasings the EN-tuned filter
didn't catch — and one of its surviving RU flags is itself wrong (it assigns
the wu-wei ruler to Confucius). After the bilingual filter: EN 6, RU 8 — no
meaningful gap. The deterministic citation metric agrees: 0 mismatches in both
languages. Lesson for anyone reusing this harness: **an LLM confusion judge is
not language-portable; recalibrate its noise filter per language or use the
deterministic check.**

What RU *did* change is correctness, in opposite directions: nano went 0/6 EN
→ 4/6 RU (asking in the corpus language lets it lift and match RU evidence
directly), while mini went 3/6 EN → 1/6 RU (its RU answers drew more partials;
facts 13 → 10). With n=6 per cell we note the pattern and resist a story.

## Confounds and limits

- n=6 per cell, 1 run; differences of 1–2 runs are noise. The provenance
  result (45/45) is the only cell-independent count large enough to lean on.
- The confusion-judge filter was *revised during analysis* (bilingual noise
  markers). All arms were recounted with the same filter; raw judge output is
  preserved in every log for re-analysis.
- Only 883/924 notes embedded; BM25 covers all 924, so un-embedded notes are
  reachable but only by keyword.
- The SOURCES requirement itself may reduce prose blending (writing citations
  disciplines the answer) — v5's slightly lower EN flag count vs v4 could be
  this rather than the dedup; the design can't separate them.
- nano's EN 0/6 looks alarming but is mostly graded-strictness: its facts
  total (8/16) sits near v4's (9/16); it produced partials, not nonsense.

## Reproduce it

```bash
# instance (two-phase; MODELS_DIR = HF cache with bge-m3 + bge-reranker-v2-m3)
MODELS_DIR=/mnt/extssd/models node cli/memcli/dist/memcli.js up \
  --embedded --folder ~/projects/trip2g_all_kbs_clean --port 24091 --name allkbsclean
# trigger regenerate_note_embeddings (admin GraphQL runCronJob), wait for
#   sqlite3 ~/projects/trip2g_all_kbs_clean/.trip2g-memory/data/local.sqlite3 \
#     "select count(*) from note_version_embeddings;"   # → ~883
node cli/memcli/dist/memcli.js down --name allkbsclean --folder ~/projects/trip2g_all_kbs_clean
MODELS_DIR=/mnt/extssd/models node cli/memcli/dist/memcli.js up \
  --embedded --reranker --folder ~/projects/trip2g_all_kbs_clean --port 24091 --name allkbsclean
# warm the CE once (first call >10s) and set reranker.timeout_seconds: 60 in FEATURES

export OPENROUTER_KEY=sk-or-...
make v5          # → logs_flat_hybrid_clean/ + results/summary_flat_hybrid_clean.json (~$0.09)
```
