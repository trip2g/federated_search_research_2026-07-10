# Reproduce the federated-search research. Needs Python 3 (stdlib only) + an
# OpenRouter key. Every run stops at BUDGET_USD before spending more.
#
#   export OPENROUTER_KEY=sk-or-...
#   make reproduce      # v2 headline table — live hub, KEY ONLY, no local setup (~$0.69)
#
# Other arms (need local data — see README):
#   make v3             # walls-vs-flat; flat arm reads ~/projects/korpuses/*.2pub.me (~$0.13)
#   make v4             # flat-hybrid; needs a local memcli instance (vector+reranker)
#   make qmd            # off-the-shelf qmd hybrid over the same flat pile

# The exact five models from the published v2 table.
MODELS ?= ["openai/gpt-5.4-nano","openai/gpt-5.4-mini","mistralai/ministral-14b-2512","google/gemini-2.5-flash-lite","anthropic/claude-haiku-4.5"]
BUDGET_USD ?= 1.0

.PHONY: reproduce v2 v3 v4 v5 qmd check
check:
	@test -n "$$OPENROUTER_KEY" || { echo "ERROR: set OPENROUTER_KEY (export OPENROUTER_KEY=sk-or-...)"; exit 1; }
	@echo "key set — runs halt at BUDGET_USD=$(BUDGET_USD). Recorded costs: v2 = \$$0.69, v3 = \$$0.13."

# v2: the one-command reproduction. Live hub philosophers.2pub.me, no local infra.
reproduce v2: check
	MODELS='$(MODELS)' BUDGET_USD=$(BUDGET_USD) python3 bench.py

# v3: walled (live hub) vs a naive local full-text pile over ~/projects/korpuses.
v3: check
	BUDGET_USD=$(BUDGET_USD) python3 v3_bench.py

# v4: flat-hybrid (BM25 + bge-m3 vector + bge-reranker) over one big local store.
# Bring the instance up first (see README "Reproduce the flat-hybrid arm"):
#   MODELS_DIR=/mnt/extssd/models node cli/memcli/dist/memcli.js up \
#     --embedded --reranker --folder ~/projects/trip2g_all_kbs --port 24091 --name allkbs
v4: check
	BUDGET_USD=$(BUDGET_USD) python3 flat_hybrid_bench.py

# qmd: an off-the-shelf local hybrid engine (github.com/tobi/qmd) over the same
# flat pile. Set it up first (see README "Reproduce the qmd arm"):
#   npm install -g @tobilu/qmd
#   qmd collection add ~/projects/trip2g_all_kbs --name allkbs
#   qmd context add qmd://allkbs "22 philosopher corpora, one flat store"
#   qmd embed
qmd: check
	BUDGET_USD=$(BUDGET_USD) python3 qmd_bench.py
# v5: clean corpus (924 unique notes) + cite-and-verify provenance, EN+RU.
# Same instance setup as v4 but on ~/projects/trip2g_all_kbs_clean
# (see RESULTS_flat_hybrid_clean.md "Reproduce it").
v5: check
	BUDGET_USD=$(BUDGET_USD) python3 flat_hybrid_clean_bench.py
