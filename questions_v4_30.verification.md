# questions_v4_30 — evidence verification

TL;DR: all **130 evidence substrings** shared by `questions_v4_30.json` (EN) and
`questions_v4_30_ru.json` (RU) are grep-verified verbatim in the corpus
(`~/projects/korpuses/*.2pub.me/**/*.md`, 22 corpora incl. the `philosophers`
hub). Verified 2026-07-11 with `grep -rF`; 0 failures, 0 declared-source
mismatches. 30 questions, 6 per difficulty kind, split 20 train / 10 test
(4/2 per kind). Both language files carry **identical** evidence /
evidence_sources / key arrays — evidence is source-language (mostly RU, some EN
where the primary text in the note is English), so quote-verification numbers
are comparable across question languages.

## What changed vs v3 (6 questions)

- **Questions 1–6 are the v3 originals**, same ids and text. Their `kind` tags
  are normalized into the v4 five-kind taxonomy: v3 "principle understanding"
  (Q3) → single-corpus grounding; "hub orientation" (Q4) → hub-orientation;
  "cross-link navigation" (Q5) → cross-link-following; "two-corpus principle"
  (Q6) → cross-corpus contrast.
- The v3 **EN** file carried 3 evidence strings that do not exist verbatim in
  the corpus (hard-wrap artifacts, documented in
  `questions_v3_ru.verification.md`). v4 uses the *verified* RU-file evidence
  arrays in **both** language files, so the EN arm no longer has dead keys.
- **New deterministic misattribution key**: every question lists
  `correct_thinkers` (who the answer may attribute claims to) and
  `tempting_thinkers` (semantically adjacent thinkers a flat search plausibly
  pulls in but who are NOT defensible sources for this question — naming one as
  a claim-holder is a checkable misattribution, no LLM judge needed). Where a
  thinker is neither clearly correct nor clearly wrong (e.g. has an indexed
  pair with the topic on a different axis), it is listed in `also_defensible`
  and must NOT be counted as a misattribution.
- `expect_kb` for hub-orientation questions now includes `philosophers`,
  because the preregistered evidence lives in the hub's topic/contradiction
  notes (v3's Q4 did not include it; keep this in mind when comparing
  off-corpus rates against v3 numbers).
- **Split**: `split: train` (20) / `split: test` (10), stratified 4/2 per kind,
  for DSPy/GEPA-style prompt optimization without overfitting.

## Distribution

| kind | ids | train | test |
|---|---|---|---|
| single-corpus grounding | 1, 3, 7, 8, 9, 10 | 1, 7, 8, 10 | 3, 9 |
| cross-corpus contrast | 2, 6, 11, 12, 13, 14 | 2, 11, 12, 14 | 6, 13 |
| hub-orientation | 4, 15, 16, 17, 18, 19 | 15, 16, 18, 19 | 4, 17 |
| cross-link-following | 5, 20, 21, 22, 23, 24 | 5, 20, 21, 23 | 22, 24 |
| contradiction-synthesis | 25, 26, 27, 28, 29, 30 | 25, 26, 28, 30 | 27, 29 |

Corpus coverage: all 21 thinker corpora appear in at least one question's
`correct_thinkers` (v3 covered 8).

## Per-question verification (grep -rF file-hit counts)

Counts are files containing the substring; the declared `evidence_sources`
entry is always among the hits (checked mechanically).

### Q1 (train) — Nietzsche, will to power — v3 original
correct: nietzsche · tempting: schopenhauer, adler, machiavelli
- "сама жизнь есть воля к власти" — 3 (`nietzsche/concepts/volya-k-vlasti.md`, `nietzsche/principles/zhizn-est-volya-k-vlasti.md`, `schopenhauer/concepts/nietzsche-predtecha.md`)
- "самосохранение есть только одно из косвенных" — 2
- "не политическая жажда господства" — 1
- "духовная воля к власти" — 3

### Q2 (train) — Nietzsche vs Schopenhauer — v3 original
correct: nietzsche, schopenhauer · tempting: goethe, wattles
- "воля к жизни" — 8 (key: `schopenhauer/concepts/volya-k-zhizni.md`)
- "первичный и коренной элемент человеческой природы" — 1
- "не тщета воли и отказ от жизни, а её утверждение и самопреодоление" — 1 (`nietzsche/peer-schopenhauer.md`)
- "сама жизнь есть воля к власти" — 3

### Q3 (test) — Epictetus, dichotomy of control — v3 original
correct: epictetus · tempting: james-allen, wattles, montaigne
All 4 in `epictetus/concepts/dihotomiya-kontrolya.md` (1 file each).

### Q4 (test) — hub: opponents of Stoic detachment — v3 original
correct: nietzsche, montaigne, larochefoucauld · tempting: wattles, goethe, james-allen
(tempting = the two thinkers the v4/v5 flat-hybrid runs actually promoted, plus james-allen)
- "лоскутная душа vs стоическая цитадель" — 20 (hub `contradictions.md` + every corpus's `see-also.md`)
- "покой через отказ от неподвластного vs пафос воли" — 1 (hub)
- "душа непостоянна и лоскутна" — 1 (hub)
- "апатия — отказ от жизни" — 1 (hub)
- "Презрение к смерти как поза" — 2 (`larochefoucauld/concepts/prezrenie-k-smerti.md`, hub card)

### Q5 (train) — Pascal vs Montaigne peer notes — v3 original
correct: pascal, montaigne · tempting: larochefoucauld, epictetus
All 4 at 1 file each (`pascal/peer-montaigne.md` ×2, `montaigne/peer-pascal.md` ×2).

### Q6 (test) — Confucius vs Laozi — v3 original
correct: confucius, laozi · tempting: machiavelli, franklin, smiles
All 5 at 1 file each (hub `contradictions.md` ×2, `laozi/concepts/wuwei.md`, `confucius/concepts/li.md`, `confucius/principles/ritual-i-forma.md`).

### Q7 (train) — Machiavelli, effectual truth
correct: machiavelli · tempting: lebon, larochefoucauld, nietzsche
- "many have pictured republics and principalities which in fact have never been known or seen" — 4 (key: `machiavelli/concepts/effektivnaya-istina.md`)
- "how one lives is so far distant from how one ought to live" — 3
- "уметь «поступать не по-доброму» и пользоваться этим по необходимости" — 1
- "«действительной правде вещей»" — 1

### Q8 (train) — Le Bon, personality in the crowd
correct: lebon · tempting: machiavelli, nietzsche, montaigne
- "become an automaton who has ceased to be guided by his will" — 2 (`lebon/concepts/disappearance-of-personality.md`, `lebon/principles/v-tolpe-lichnost-ischezaet.md`)
- "человек спускается на несколько ступеней по лестнице цивилизации" — 1
- "Индивид в толпе — песчинка среди других песчинок" — 1
- "в толпе он варвар — то есть существо, действующее инстинктом" — 1

### Q9 (test) — Hill, definite chief aim + desire
correct: hill · tempting: wattles, james-allen, smiles
- "девяносто пять процентов людей бесцельно блуждают по жизни" — 1 (`hill/concepts/definite-chief-aim.md`)
- "Сильное, глубоко укоренившееся желание — отправная точка любого достижения" — 1 (`hill/concepts/desire.md`)
- "сила — это организованное усилие" — 3
- "подкреплена жгучим желанием её достижения" — 1

### Q10 (train) — Ignatius, spiritual exercises + discernment
correct: ignatius · tempting: franklin, pascal, epictetus
(franklin is the sharpest trap: the index pairs franklin↔ignatius as "same
self-examination technique, opposite ends" — but this question asks only about
Ignatius's own doctrine)
- "разумеется всякий способ испытывать совесть, размышлять, созерцать, молиться устно и мысленно" — 2 (concept + `ignatius/translation/01-annotatsii.md`)
- "Ибо как прогулка, ходьба и бег суть упражнения телесные" — 2
- "отрешиться от всех беспорядочных привязанностей" — 3
- "ЧУВСТВОВАТЬ И РАСПОЗНАВАТЬ РАЗЛИЧНЫЕ ДВИЖЕНИЯ, ВЫЗЫВАЕМЫЕ В ДУШЕ" — 2 (`ignatius/concepts/razlichenie-dukhov.md` + translation)

### Q11 (train) — Hill vs Schopenhauer on desire
correct: hill, schopenhauer · tempting: wattles, james-allen, nietzsche
(wattles/james-allen have their own indexed pairs with schopenhauer on nearly
the same axis — attributing their claims to Hill, or answering with them
instead, is the blending failure this question is built to catch)
- "ЖЕЛАНИЕ — это семя всякого достижения" — 1 (`hill/concepts/desire.md`)
- "удовольствие есть состояние, которое никогда не может длиться долго" — 1 (`schopenhauer/concepts/futilnost-stremleniya.md`)
- "желать доли лучшей, чем есть, — слепая глупость" — 1
- "Ось: желание — двигатель успеха vs источник вечного страдания." — 1 (hub `contradictions.md`)

### Q12 (train) — Tolstoy vs Wattles on wealth
correct: tolstoy, wattles · tempting: hill, smiles, rockefeller
- "Я жил паразитом и, спросив себя, зачем я живу, получил ответ: ни зачем." — 2 (`tolstoy/concepts/parazity-zhizni.md` + source unit)
- "ему надо добывать ее не для себя, а для всех" — 3
- "Есть Наука о богатстве, и это точная наука, как алгебра или арифметика." — 3 (key: `wattles/principles/bogatstvo-est-tochnaya-nauka.md`)
- "Богатство как путь к полноте жизни → богатство как паразитизм." — 1 (`wattles/concepts/tolstoy-kontrast.md`, a `debate_bridge` note)

### Q13 (test) — Ford vs Tolstoy on machines and labor
correct: ford, tolstoy · tempting: smiles, rockefeller, hill
- "Power and machinery, money and goods, are useful only as they set us free to live." — 2 (`ford/principles/mashina-osvobozhdaet-dlya-zhizni.md`, `ford/concepts/machinery-as-liberator.md`)
- "не машина отнимает жизнь, а её отсутствие" — 1
- "Действия же трудящегося народа, творящего жизнь, представились мне единым настоящим делом." — 2 (`tolstoy/concepts/trud-dobyvanie-zhizni.md` + source unit)
- "Толстой видит в машинной цивилизации и разделении труда порабощение" — 1 (ford's own debate-contrast block — see flags)

### Q14 (train) — Franklin vs La Rochefoucauld on virtue
correct: franklin, larochefoucauld · tempting: smiles, machiavelli, hill
- "но запрещены, потому что вредны" — 1 (`franklin/principles/prosveshchenny-egoizm.md`)
- "vicious actions are not hurtful because they are forbidden, but forbidden because they are hurtful" — 2 (+ `franklin/concepts/art-of-virtue.md`)
- "Our virtues are most frequently but vices disguised." — 2 (`larochefoucauld/principles/dobrodeteli-pereodetye-poroki.md`, `larochefoucauld/concepts/dobrodeteli-kak-poroki.md`)
- "Vices enter into the composition of virtues as poison into that of medicines." — 2
- "Ось: добродетель-навык, которая окупается vs переодетое себялюбие." — 1 (hub)

### Q15 (train) — hub: wealth camps (topic matrix)
correct: ford, rockefeller, smiles, franklin, wattles, hill / schopenhauer, tolstoy, laozi · tempting: goethe, confucius, machiavelli
(tempting are absent from `topics/bogatstvo-i-trud.md`)
- "прибыль — награда за службу, а не основа дела" — 1 (hub `topics/bogatstvo-i-trud.md`)
- "обогащение — точная наука" — 2 (+ `wattles/chains/magistralny-metod.md`)
- "жизнь его круга — паразитизм на труде народа" — 1 (hub topic)
- "то, что человек есть, важнее того, что он имеет" — 2 (hub topic + `_souls/schopenhauer/SOUL.md`)

### Q16 (train) — hub: positions on death (topic matrix)
correct: montaigne, epictetus, tolstoy, pascal, schopenhauer, larochefoucauld, confucius · tempting: nietzsche, ignatius, goethe
- "философствовать — учиться умирать: продумавший смерть свободен" — 1 (hub `topics/smert.md`)
- "смерть уничтожает всякий конечный смысл" — 1
- "«презрение к смерти» мудрецов — поза" — 1
- "держи смерть перед глазами ежедневно" — 1
- "The necessity of dying created all the constancy of philosophers." — 1 (`larochefoucauld/concepts/prezrenie-k-smerti.md` — the one non-hub anchor)

### Q17 (test) — hub: crowd dissolves vs community as criterion
correct: lebon, nietzsche, larochefoucauld, montaigne, adler, confucius, tolstoy · also_defensible: franklin, smiles, machiavelli (present in the topic note under other headings) · tempting: epictetus, pascal, schopenhauer
- "в толпе личность исчезает: толпа — новое существо" — 1 (hub `topics/tolpa-i-obshchestvo.md`)
- "чувство общности — единственный критерий ценности человека" — 1
- "стадная мораль называет злым всё, что возвышает отдельного" — 1
- "сохрани заднюю лавку" — 2 (+ hub `topics/svoboda.md`)

### Q18 (train) — hub: who opposes wu wei
correct: laozi, smiles, franklin, hill, james-allen, ford · also_defensible: confucius, machiavelli, nietzsche (indexed laozi pairs on other axes) · tempting: epictetus, schopenhauer, wattles (no laozi pair in the index)
- "Ось: самопомощь vs недеяние." — 1 (hub `contradictions.md`)
- "«resolute determination» разрушает то, что растёт само" — 3 (+ `laozi/see-also.md`, hub card)
- "Ось: метод и учёт vs недеяние." — 1
- "Ось: желание и определённая цель vs безжелание и мягкая сила." — 1
- "Ось: деятельное улучшение vs недеяние." — 1

### Q19 (train) — hub: Machiavelli's allies vs opponents
correct: machiavelli, larochefoucauld, lebon, confucius, tolstoy · also_defensible: ford, epictetus, hill, laozi, smiles, rockefeller (all have indexed machiavelli pairs) · tempting: nietzsche, franklin (NO machiavelli pair in the index — power-adjacency traps)
- "союзники по трезвости" — 2 (hub `contradictions.md` + `_souls/machiavelli/SOUL.md`)
- "союзники-диагносты" — 1
- "Ось: правление через добродетель и пример vs через страх и видимость." — 1
- "Ось: сила и необходимость vs совесть и непротивление." — 1
- "казаться важнее, чем быть" — 3 (hub + `machiavelli/_instructions.md` + chain)

### Q20 (train) — cross-link: Wattles ↔ Epictetus bridge
correct: wattles, epictetus · tempting: james-allen, hill, tolstoy
- "«внешнее ты можешь вызвать мыслью»" — 1 (`wattles/concepts/epictetus-kontrast.md`)
- "Самый острый спор базы" — 1
- "Из существующего одно в нашей власти, другое не в нашей власти" — 1 (`epictetus/concepts/dihotomiya-kontrolya.md`)
- "Никакая возможная комбинация обстоятельств не может победить" — 2 (`wattles/principles/bogatstvo-est-tochnaya-nauka.md`, `wattles/concepts/opredelyonny-sposob.md`)

### Q21 (train) — cross-link: Schopenhauer's nietzsche-predtecha bridge
correct: schopenhauer, nietzsche · tempting: goethe, tolstoy
- "сделал шопенгауэровский пессимизм и этику сострадания главной мишенью переоценки" — 1 (`schopenhauer/concepts/nietzsche-predtecha.md`)
- "Воля к жизни → воля к власти" — 1
- "Сострадание-основа → сострадание-опасность" — 1
- "Итак, сострадание против сострадания!" — 1 (`nietzsche/concepts/sostradanie-zhalost.md`)
- "Наше сострадание более высокое и более дальновидное" — 2

### Q22 (test) — cross-link: Tolstoy's peer-epictetus
correct: tolstoy, epictetus · tempting: schopenhauer, montaigne, pascal
- "Толстой опирался на стоиков: власть над собой и безразличие к внешнему." — 1 (`tolstoy/peer-epictetus.md`)
- "И то, что в нашей власти, по природе свободно" — 1 (`epictetus/concepts/dihotomiya-kontrolya.md`)
- "а то, что не в нашей власти, немощно, рабственно" — 1

### Q23 (train) — cross-link: Goethe's debate map
correct: goethe, schopenhauer, nietzsche · also_defensible: tolstoy, ignatius, pascal, confucius, machiavelli, laozi (all named in the map/asymmetries) · tempting: montaigne, franklin (absent from the map)
- "Мне жаль людей, которые много носятся с бренностью всех вещей" — 2 (`goethe/concepts/goethe-v-debatakh.md`, `goethe/principles/delat-prekhodyashchee-neprekhodyashchim.md`)
- "деятельный, благоговейный, антиметафизический реализм" — 1
- "«последним немцем, которого я почитаю»" — 1
- "у Гёте ~19 концептов с блоками «Контраст для дебатов»" — 1 (hub `contradictions.md`, Асимметрии section)

### Q24 (test) — cross-link: Wattles ↔ La Rochefoucauld bridge
correct: wattles, larochefoucauld · tempting: franklin, hill, smiles
- "«всякая добродетель — переодетый интерес»" — 1 (`wattles/concepts/la-rochefoucauld-kontrast.md`)
- "спор психолога подозрения с проповедником изобилия" — 1
- "What we term virtue is often but a mass of various actions and divers interests" — 2 (`larochefoucauld/principles/dobrodeteli-pereodetye-poroki.md` + concept)
- "Давай каждому больше в потребительской ценности, чем берёшь у него в денежной стоимости" — 5 (key: `wattles/principles/otdavat-bolshe-polzy-chem-berosh.md`)

### Q25 (train) — synthesis: Epictetus vs James Allen
correct: epictetus, james-allen · tempting: wattles, hill (wattles has the *same-axis* indexed pair with epictetus — the strongest blending trap in the set)
- "а то, что не в нашей власти, немощно, рабственно, подвержено запрету" — 1 (`epictetus/concepts/dihotomiya-kontrolya.md`)
- "Circumstance does not make the man; it reveals him to himself" — 5 (key: `james-allen/concepts/thought-and-circumstance.md`)
- "Люди притягивают не то, что *хотят*, а то, чем они *являются*" — 1
- "Ось: граница контроля — только суждение vs мысль-причина до тела и обстоятельств." — 1 (hub)

### Q26 (train) — synthesis: Nietzsche vs Tolstoy
correct: nietzsche, tolstoy · tempting: schopenhauer, larochefoucauld, ignatius
- "Мораль рабов по существу своему есть мораль полезности." — 1 (`nietzsche/concepts/moral-rabov-i-gospod.md`)
- "Вера есть сила жизни." — 4 (key: `tolstoy/concepts/vera-sila-zhizni.md`)
- "Ось: мораль рабов vs мораль господ." — 1 (hub)
- "смирение и труд — сила жизни, а не слабость" — 1 (hub)

### Q27 (test) — synthesis: Adler vs Nietzsche
correct: adler, nietzsche · tempting: hill, lebon, schopenhauer (franklin excluded from tempting — the index pairs adler↔franklin as allies)
- "Ось: стремление вверх из дефицита vs из избытка." — 1 (hub)
- "is the driving force, the starting point" — 3 (key: `adler/concepts/chuvstvo-nepolnotsennosti.md`)
- "is the sole criterion of human values" — 3 (key: `adler/principles/chuvstvo-obshchnosti-edinstvennyy-kriteriy.md`)
- "стремление — из избытка силы" — 1 (hub)
- "Мораль в Европе есть нынче мораль стадных животных" — 3 (key: `nietzsche/concepts/stadnaya-moral.md`)

### Q28 (train) — synthesis: Laozi vs Smiles
correct: laozi, smiles · tempting: franklin, hill, james-allen, ford (all four have their OWN indexed anti-laozi pairs on the same effort-axis — same-axis blending traps)
- "небо помогает тем, кто помогает себе; упорство строит характер" — 1 (hub)
- "Help from without is often enfeebling in its effects, but help from within invariably invigorates." — 3 (key: `smiles/concepts/self-help.md`)
- "The soft overcomes the hard; and the weak the strong." — 2 (`laozi/concepts/rouruo.md`, `laozi/principles/myagkost-i-sila.md`)
- "He who acts (with an ulterior purpose) does harm" — 1 (`laozi/concepts/wuwei.md`)
- "Помощь извне часто расслабляет, а помощь изнутри неизменно укрепляет" — 1

### Q29 (test) — synthesis: Rockefeller vs Tolstoy
correct: rockefeller, tolstoy · also_defensible: larochefoucauld (rockefeller's own debate-contrast block names LR as a *different* opponent of scientific giving) · tempting: ford, franklin, hill
- "«эффективная филантропия» — самооправдание богатого" — 1 (hub)
- "The best philanthropy, the help that does the most good and the least harm" — 3 (key: `rockefeller/principles/davat-nado-nauchno.md`)
- "не воскресный импульс сердца, а дисциплина" — 1
- "Я отрекся от жизни нашего круга" — 2 (`tolstoy/concepts/parazity-zhizni.md` + source unit)
- "Толстой требует не «эффективного» распределения богатства, а отказа от собственности" — 1 (rockefeller's debate-contrast block — see flags)

### Q30 (train) — synthesis: Montaigne vs Nietzsche
correct: montaigne, nietzsche · tempting: epictetus, pascal, goethe
- "Ось: общая мера человека vs сверхчеловек." — 1 (hub)
- "на ходулях всё равно идёшь своими ногами" — 2 (`montaigne/concepts/obshchaya-mera-cheloveka.md`, `montaigne/principles/zhivi-po-obshchey-mere.md`)
- "instead of transforming themselves into angels, they transform themselves into beasts" — 2
- "самый великий тот, кто может быть самым одиноким" — 2 (`nietzsche/principles/velichie-v-otdelnosti.md`, `nietzsche/concepts/po-tu-storonu-dobra-i-zla.md`)
- "Всякое возвышение типа «человек» было до сих пор — и будет всегда — делом аристократического общества" — 3 (key: `nietzsche/concepts/znatnost-ranga.md`)

## Limits / weak-support flags

- **Hub-dependence (Q4, Q15, Q16, Q17, Q18, Q19).** For all six hub-orientation
  questions the core preregistered evidence lives in the `philosophers` hub
  (`ru/contradictions.md` and `ru/topics/*.md`); the individual corpora state
  the *positions* but not these exact axis phrasings. This is by design — the
  kind tests hub orientation — but a run that never reaches the hub KB cannot
  match these substrings verbatim even with a correct answer. Only Q16 (one
  larochefoucauld anchor) and Q18 ("resolute determination" also in
  `laozi/see-also.md`) have non-hub fallbacks.
- **One-sided debate blocks (Q13, Q29).** One evidence string each is the
  *opponent's* position as summarized inside ford's / rockefeller's own
  debate-contrast block ("Толстой видит…", "Толстой требует…"). Tolstoy's own
  corpus supports the position in other words (matched by the tolstoy-corpus
  strings in the same questions), but the exact phrasing exists only in the
  counterparty's corpus. A model quoting Tolstoy from tolstoy-notes will state
  the fact correctly yet miss that substring.
- **Q23 asymmetry is real and one-sided.** The goethe debate map (and the hub's
  Асимметрии section) says the opposed corpora barely answer back; there is no
  schopenhauer- or nietzsche-side note about Goethe. The question is answerable
  only from goethe + hub.
- **Q22 peer note is thin.** `tolstoy/peer-epictetus.md` is a 3-line pointer
  note; it carries exactly one substantive line (verified). Most grounding must
  come from the epictetus corpus. Tolstoy also has `peer-markavrelii.md`
  (Marcus Aurelius) — an answer naming Marcus Aurelius as "the Stoic peer" is
  half-right; the key treats only Epictetus as correct because the question
  asks for the doctrine in the peer's own KB and there is no Aurelius corpus.
- **Q27 OCR-wrapped partial lines.** The two adler EN strings are verbatim
  single physical lines of the OCR'd source ("is the driving force, the
  starting point"; "is the sole criterion of human values") — the full
  sentences are hard-wrapped, so only these mid-sentence spans match. Verbatim
  corpus text, but shorter and less distinctive than other keys.
- **Q30 deliberately avoids "Übermensch".** The nietzsche KB marks
  `sverkhchelovek` as `not_in_ingested_corpus` (the term never occurs in BGE
  and any BGE-attributed Übermensch quote is a fake per the KB itself). The
  required facts and evidence use BGE's own greatness/elevation formulations;
  an answer quoting Zarathustra "from the KB" would itself be a fabrication
  signal.
- **Commentary-translation evidence (Q8, Q9, Q11 hill-side, Q25 james-allen
  RU string).** As in v3's Q3/Q6, several RU strings are the notes' own
  "перевод наш" translation lines or commentary prose, not primary-source
  scripture; they ARE verbatim corpus text. EN primary quotes are included
  alongside where they exist (Q8, Q13, Q14, Q16, Q24, Q25, Q27, Q28, Q29, Q30).
- **`сила — это организованное усилие` (Q9) hits 3 hill files** including
  `hill/MOC.md` — broad within-corpus support, no cross-corpus ambiguity.
- **Tempting-thinker keys are question-relative.** A tempting thinker may be a
  perfectly fine answer to a *different* question (e.g. wattles is correct in
  Q12/Q20/Q24 and tempting in Q4/Q18/Q25). The misattribution check must be
  applied per-question: flag only claims sourced to a thinker in
  `tempting_thinkers`, never flag `correct_thinkers` or `also_defensible`.

## How verification was run

```bash
# for each of the 130 evidence strings (identical across EN/RU files):
grep -rFl "<substring>" ~/projects/korpuses --include="*.md"
# assert: >=1 hit AND the declared evidence_sources file is among the hits
```

All substrings sit on a single physical line in their source notes, so plain
line-based grep matches despite hard-wrapped note text. Script also asserts:
30 ids, 5 kinds × 6, 20/10 split stratified 4/2 per kind, EN/RU parity of
evidence, sources, and thinker keys.
