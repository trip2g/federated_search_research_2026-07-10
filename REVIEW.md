# Codex methodology review (external, read-only)

> Independent skeptic-methodologist review of the v1 study, requested to stress-test the conclusions and propose a better test. Model note printed on its first line.

gpt-5.6-sol is unavailable in this session; I proceeded with the available model.

## 1) Verdicts

1. **UNSOUND — model-comparison fairness.** The data show GPT stopped sooner, not that it navigated better: any no-tool response counts as “finished,” and all six GPT finals fail to fully answer the task—often explicitly declining—while Haiku q5 retrieved relevant Pascal–Montaigne material on turn 10 but was denied the next turn to answer. The cap counts model completions, although each completion may contain multiple calls. [bench.py](/home/alexes/projects2/trip2g_federated_search_research/bench.py:129), [GPT q2](/home/alexes/projects2/trip2g_federated_search_research/logs/gpt-5.4-mini__q2.json:12), [Haiku q5](/home/alexes/projects2/trip2g_federated_search_research/logs/claude-haiku-4.5__q5.json:214)

2. **UNSOUND — grounding.** No quote metric exists in the harness; logs retain only 500-character result previews, so general source matching is impossible. Worse, Haiku q3 and GPT q3 explicitly say they could not retrieve the requested quote but are marked `quo=Y`; GPT q4 quotes a bibliographic blurb while admitting it does not support its anti-Stoicism claim. [bench.py](/home/alexes/projects2/trip2g_federated_search_research/bench.py:154), [Haiku q3](/home/alexes/projects2/trip2g_federated_search_research/logs/claude-haiku-4.5__q3.json:11), [GPT q4](/home/alexes/projects2/trip2g_federated_search_research/logs/gpt-5.4-mini__q4.json:12)

3. **UNSOUND — expected-KB oracle use.** Although RESULTS calls it a hint, the headline “both reliably went to the correct corpus” relies on it; `summary.json` records any supplied `kb_id` without checking whether retrieval succeeded, and many supposedly successful hits returned “Federation is not configured.” [bench.py](/home/alexes/projects2/trip2g_federated_search_research/bench.py:193), [summary.json](/home/alexes/projects2/trip2g_federated_search_research/results/summary.json:211), [Haiku q2](/home/alexes/projects2/trip2g_federated_search_research/logs/claude-haiku-4.5__q2.json:21)

4. **OVERSTATED — statistical weight.** Safe probe observations are only that these particular runs recorded 71 versus 32 calls, Haiku reached the cap three times, and its journal is a coherent retrospective. Claims that comprehension “was never the bottleneck,” GPT is generally more disciplined, or Haiku “out-explored GPT” are unsupported by six unreplicated tasks and one Haiku-only wander whose raw trace is absent. [RESULTS.md](/home/alexes/projects2/trip2g_federated_search_research/RESULTS.md:78), [wander journal](/home/alexes/projects2/trip2g_federated_search_research/logs/haiku_wander_journal.md:202)

5. **UNSOUND — live-endpoint interpretation.** The stored benchmark contradicts the claimed single nested anomaly: direct `nietzsche`, `schopenhauer`, `epictetus`, and other IDs repeatedly returned `not_configured` for both models and nano. The recorded blind fan-outs returned successfully in 2.6s and 15.0s rather than timing out. Thus endpoint state contaminates success and wall time, and the “fan-out always times out/targeted IDs work” claim is not supported. [GPT q2](/home/alexes/projects2/trip2g_federated_search_research/logs/gpt-5.4-mini__q2.json:33), [Haiku q5](/home/alexes/projects2/trip2g_federated_search_research/logs/claude-haiku-4.5__q5.json:21), [RESULTS.md](/home/alexes/projects2/trip2g_federated_search_research/RESULTS.md:107)

6. **OVERSTATED — reproducibility and harness bias.** The system prompt prescribes “orient with search, then target a specific corpus,” and tool descriptions provide the intended sequence and example IDs, so the experiment tests compliance with a supplied policy more than spontaneous navigation. Parallel calls consume one turn but are executed serially; the live endpoint instructions are fetched but not logged, preventing exact prompt reproduction. [bench.py](/home/alexes/projects2/trip2g_federated_search_research/bench.py:58), [bench.py](/home/alexes/projects2/trip2g_federated_search_research/bench.py:90), [bench.py](/home/alexes/projects2/trip2g_federated_search_research/bench.py:119)

## 2) Biggest flaw

The study has no valid task-success outcome: “finished” means merely that the model stopped calling tools, while “grounded” is an unimplemented and evidently misapplied quote heuristic.

That flips the main comparison. Under the questions’ stated requirements, GPT is **0/6 fully successful**, not 6/6: q1–q3 decline the requested grounded answer, q4 offers an explicitly unsupported candidate, q5 does not locate or explain the disagreement, and q6 does not provide the requested contrast. [GPT q1](/home/alexes/projects2/trip2g_federated_search_research/logs/gpt-5.4-mini__q1.json:11), [GPT q5](/home/alexes/projects2/trip2g_federated_search_research/logs/gpt-5.4-mini__q5.json:12), [GPT q6](/home/alexes/projects2/trip2g_federated_search_research/logs/gpt-5.4-mini__q6.json:12)

Therefore:

- “GPT uses fewer calls and stops sooner in this run” is supported.
- “GPT navigates more successfully” is not.
- “Both models understand the principles” is not established.
- The data do not establish Haiku as better either.

The wander cannot rescue those claims: it is a self-authored journal, not an auditable trace, and it admits that it largely remained inside the `philosophers` hub rather than navigating into individual federated corpora. [wander journal](/home/alexes/projects2/trip2g_federated_search_research/logs/haiku_wander_journal.md:205)

## 3) Better-test specification

**Design**

- Use 8 preregistered tasks: two direct-corpus retrievals, three two-hop opponent-link tasks, two principle-application/contrast tasks, and one deliberately unanswerable or broken-link task.
- Prefer obscure evidence and exact graph-specific slugs so pretrained philosophical knowledge cannot substitute for retrieval.
- For every task, preregister acceptable source paths, evidence spans, required propositions, and all valid alternative routes. Do not grade by a guessed `kb_id`.
- Add paired controls:
  - evidence excerpt supplied directly: isolates comprehension;
  - correct corpus supplied directly: isolates retrieval;
  - full hub only: measures the incremental navigation burden.

**Execution**

- Run the five named models with exact provider/version metadata and identical context/output limits.
- Use a neutral main prompt that requires evidence but does not prescribe a tool sequence; run the current guided prompt on a small crossover subset.
- Remove the assistant-turn cap. Allow, for example, 12 individual MCP calls plus one forced final response. Count every parallel call separately.
- Interleave model order by task. Preflight required sources before each block; endpoint failures invalidate and rerun the trial rather than count against a model.
- Log the complete initialize instructions, full untruncated tool results, endpoint/version metadata, response hashes, model latency, MCP latency, and application-level errors separately.

**Scoring**

- **Task success:** all preregistered answer propositions correct and required sources used.
- **Quote validity:** after HTML and whitespace normalization, every quoted span of at least eight tokens must be an exact substring of a previously retrieved source; record call ID and offsets. Exclude user/system text and hub catalog prose when primary-corpus evidence is required.
- **Claim faithfulness:** split the answer into atomic claims and label each `entailed`, `unsupported`, or `contradicted` against retrieved text; report supported-claim precision and required-claim recall.
- **Understanding:** require a paraphrase or novel application whose rubric is fixed from the source before model runs; quoting alone earns no understanding credit.
- **Navigation efficiency:** report success-at-call-\(k\), calls-to-first-valid-evidence, actual calls divided by shortest accepted route, redundant-call rate, invalid-target rate, tokens, and cost. Score efficiency only conditional on correct completion; treat exhausted runs as censored failures.
- **Latency:** report model and MCP components separately; do not describe aggregate live wall time as model speed.

Eight tasks × five models, with cheap no-tool controls and a 12-call ceiling, should remain compatible with a few-dollar pilot. Report exact paired counts and uncertainty descriptively; do not make leaderboard or architecture-wide claims from that sample.
