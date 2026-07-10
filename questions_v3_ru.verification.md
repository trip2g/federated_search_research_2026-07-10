# questions_v3_ru.json — evidence verification

TL;DR: all 25 RU evidence substrings in `questions_v3_ru.json` are grep-verified
verbatim in the corpus (`~/projects/korpuses/*.2pub.me/**/*.md`, same notes as the
flat vault `~/projects/trip2g_all_kbs`). Verified 2026-07-10 with `grep -rF`.
Q4 is the only question whose contrast-axis evidence lives mostly in the hub
corpus, not the individual thinkers' corpora — see limits below.

Schema mirrors `questions_v3.json` (id / kind / expect_kb / q / required_facts /
evidence) plus one extra parallel array `evidence_sources` with the note path each
substring was verified in. Evidence substrings are chosen to sit on a single
physical line in the source note, so plain line-based grep matches even in
hard-wrapped notes.

## Per-question verification (grep -rF hit counts across the corpus)

### Q1 — Nietzsche, will to power
All 4 in `nietzsche.2pub.me/concepts/volya-k-vlasti.md`:
- "сама жизнь есть воля к власти" — 3 files (also `principles/zhizn-est-volya-k-vlasti.md`, `schopenhauer.2pub.me/concepts/nietzsche-predtecha.md`)
- "самосохранение есть только одно из косвенных" — 2 files
- "не политическая жажда господства" — 1 file
- "духовная воля к власти" — 3 files

### Q2 — Nietzsche vs Schopenhauer
- "воля к жизни" — 7 files, key: `schopenhauer.2pub.me/concepts/volya-k-zhizni.md`
- "первичный и коренной элемент человеческой природы" — 1 file (same note)
- "не тщета воли и отказ от жизни, а её утверждение и самопреодоление" — 1 file (`nietzsche.2pub.me/peer-schopenhauer.md`)
- "сама жизнь есть воля к власти" — 3 files

### Q3 — Epictetus, dichotomy of control
All 4 in `epictetus.2pub.me/concepts/dihotomiya-kontrolya.md` (1 file each).
Note: the EN file's evidence strings "в нашей власти — мнение, побуждение к вещи,
желание, уклонение" and "не в нашей власти — тело, имущество, репутация" do NOT
exist verbatim in the corpus (hard line wrap splits them); replaced with verified
single-line substrings of the same quote.

### Q4 — hub orientation (opponents of Stoic detachment)
- "лоскутная душа vs стоическая цитадель" — 20 files (every corpus's `see-also.md` + `philosophers.2pub.me/ru/contradictions.md`)
- "покой через отказ от неподвластного vs пафос воли" — 1 file (hub `contradictions.md`)
- "душа непостоянна и лоскутна" — 1 file (hub `contradictions.md`)
- "апатия — отказ от жизни" — 1 file (hub `contradictions.md`)
- "Презрение к смерти как поза" — 2 files (`larochefoucauld.2pub.me/concepts/prezrenie-k-smerti.md`, hub)
Note: the EN file's "презрение к смерти — последняя поза гордости" does NOT exist
verbatim anywhere; replaced with the real note title.

### Q5 — Pascal vs Montaigne
- "Монтень — мишень «Мыслей»" — 1 file (`pascal.2pub.me/peer-montaigne.md`)
- "тревогу о ничтожестве человека без Бога" — 1 file (same)
- "ставку на Бога и бездну без Него" — 1 file (`montaigne.2pub.me/peer-pascal.md`)
- "скептической невозмутимости" — 1 file (same)

### Q6 — Confucius vs Laozi
- "Ось: ритуал vs недеяние" — 1 file (hub `contradictions.md`)
- "форма — насилие над течением" — 1 file (hub `contradictions.md`)
- "Недеяние — не бездействие" — 1 file (`laozi.2pub.me/concepts/wuwei.md`)
- "без внутреннего содержания ритуал пуст" — 1 file (`confucius.2pub.me/concepts/li.md`)
- "без неё достоинства вырождаются" — 1 file (`confucius.2pub.me/principles/ritual-i-forma.md`)

## Limits / weak-support flags

- **Q4 (main flag):** 4 of 5 evidence strings live only in the hub corpus
  (`philosophers.2pub.me/ru/contradictions.md`); only the axis label
  "лоскутная душа vs стоическая цитадель" is replicated into each thinker's
  `see-also.md`. If a run's federation misses the hub KB, verbatim RU grounding
  for the *grounds* of the disagreement gets thin — the individual corpora state
  the positions but not the contrast axes in these exact words. This mirrors the
  question's intent (hub orientation) but makes Q4 the most hub-dependent item.
- **Q6 (secondary flag):** the primary-source quotes in the confucius/laozi
  corpora are English (Legge) + Chinese; the verified RU substrings are the
  notes' own commentary prose, not translated scripture. RU verbatim grounding
  is real corpus text but commentary-level. Same applies to Epictetus (Q3),
  where the RU strings are the note's "перевод наш" translation lines — those
  ARE verbatim corpus text, so Q3 is fine.
- Q1, Q2, Q5: clean — all evidence verbatim in the target thinkers' own notes.
