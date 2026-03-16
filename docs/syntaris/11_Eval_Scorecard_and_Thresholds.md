# Eval Scorecard and Thresholds

- Dokumentum státusz: **living doc / minőségi scorecard**
- Dátum: **2026-03-16**
- Fő kapcsolatok: **03, 05, 06, 07, 12**

## Dokumentum célja

Ez a dokumentum a Syntaris minőségi mérőrendszerét és gate-küszöbeit rögzíti.
A célja, hogy a „jónak tűnik” helyett legyen mérhető, kapus döntési alap.

## 1. Scorecard-szabály

- A scorecard nem helyettesíti a józan mérnöki ítéletet, de kötelező ellenőrzési keret.
- Ha egy mérőszám még nincs teljesen automatizálva, ideiglenesen kézi adjudikációval kell mérni.
- A red-line metrikák átlépése merge-stop.

## 2. Red-line metrikák

### RL-1 — Source honesty violations
Küszöb: **0 megengedett**

### RL-2 — Explicit style-constraint violations
Küszöb: **0 megengedett** a gate-szintű validációs scenariókban

### RL-3 — Ack-collapse direct questionre
Küszöb: **0 megengedett** a gate-szintű validációs scenariókban

### RL-4 — Reply / trace / snapshot drift
Küszöb: **0 megengedett** a gate-szintű validációs scenariókban

### RL-5 — Current/historical source silent substitution
Küszöb: **0 megengedett**

## 3. Jelenlegi kapuállapot-adjudikáció

### Gate 1 — Artifact/source baseline
Állapot: **PASSED / MERGED**

A lezárás alapja:
- full `pytest -q` zöld ambient compat env mellett is,
- allowed-root text file read működik,
- outside-root refusal helyes,
- unsupported/binary refusal helyes,
- successful once-file import -> source-awareness + evidence follow-up működik,
- explicit historical log selection működik,
- failed new source handoff nem szennyezi silent módon a current source állapotot.

### Gate 2 — Interpretációs / kognitív kapu
Állapot: **ACTIVE / MÉG NEM ÁTMENT**

## 4. Gate 1 scorecard

| Metrika | Típus | Küszöb |
|---|---|---|
| Artifact registry creation success | core | >= 0.98 curated scenarios |
| Current source identification accuracy | core | >= 0.98 curated scenarios |
| Allowed-root local text read correctness | core | 1.00 on gate scenarios |
| Successful once-file evidence follow-up | core | 1.00 on gate scenarios |
| Explicit historical log selection correctness | core | 1.00 on gate scenarios |
| Outside-root refusal correctness | red-line adjacent | 1.00 |
| Unsupported/binary refusal correctness | red-line adjacent | 1.00 |
| Failed-read source contamination rate | red-line | 0 |
| Audit event completeness source műveleteknél | core | >= 0.95 |

## 5. Gate 2 scorecard

| Metrika | Típus | Küszöb |
|---|---|---|
| Chat-lock retention | core | >= 0.95 curated / >= 0.90 noisy live set |
| Explicit style-constraint obedience | red-line | 1.00 on gate scenarios |
| Ack-collapse incidence | red-line | 0 |
| Workframe classification accuracy | core | >= 0.95 curated / >= 0.85 real log adjudication |
| Multi-intent extraction quality | core | F1 >= 0.85 curated sets |
| Unknown handling honesty | core | >= 0.98 judged pass |
| Anti-hijack robustness | core | >= 0.90 targeted hijack scenarios |
| Noisy HU robustness | core | >= 0.85 judged pass |
| Casual live usefulness | core | >= 0.85 judged pass on golden set |

### Gate 2 residual mixed-turn surface (REBUILD-042)
- recap-only hijack arány: cél 0 regressziós mintákon
- style constraint sértés (brief/no_list): cél 0
- reflective + direct kérdés szétcsúszás: cél 0
- noisy HU mixed-turn félreroute: cél 0
- composition_* és surface_hijack_guarded trace koherencia: kötelező

### Gate 2 exit-prep adjudikáció (REBUILD-044)
- 24-turn HU live matrix: 21 PASS / 3 FAIL.
- FAIL minták: style-constrained direct ack-loop (1), direct-answer-first meta-terelés (1), honest-unknown túláltalános pontosításkérés (1).
- Recap-only hijack a vizsgált készletben: 0.
- Következtetés: Gate 2 **ACTIVE marad**; exit-candidate címke még korai.

## 6. Gate 3 scorecard

Gate 3 csak akkor értelmes, ha a Gate 2 fő red-line metrikái zöldek.
A mérés célja itt:
- az A-oldali pilot hozzáadott értékének mérése,
- nem a maghibák elrejtése.

Metrikák:
- interpretációs javulás noisy HU inputon,
- ambiguity handling javulás,
- multi-intent bontás javulás,
- latenciahatás,
- önellenőrzés integrálhatósága.

## 7. Minőségi jelzők, amelyeket mindig figyelni kell

- unsupported assertion rate,
- source-honesty failure count,
- live casual failure count,
- explicit workframe drift count,
- structured template hijack count,
- state/snapshot mismatch count.

## 8. Mérési gyakorlat

### Automatizált mérés
Ahol lehet, tesztben és scriptben.

### Kézi adjudikáció
Ahol a kérdés nyelvi és kvalitatív, ott canonical golden-scenario készlettel és logértékeléssel.

### Dokumentáció
Minden fontos scorecard kör eredménye kerüljön be:
- a validációs logba,
- szükség esetén a Current State Matrixba,
- és ha trendet változtat, az ADR logba.

## 9. Rövid végső összefoglalás

A scorecard célja, hogy a Syntaris ne érzet alapján lépjen kaput.
Ahol piros vonal van, ott nincs „majd később megoldjuk” kategória.


## Delta Journal

- 2026-03-15 | REBUILD-036 | Eval pontok kiegészítve: explicit style obey, direct-answer-first, chat-lock tartás, ack-collapse risk=0 cél | Miért: Gate 2 belépő küszöb objektivizálása.

- 2026-03-15 | REBUILD-036 finisher | Eval bizonyíték hozzáadva a 7 kötelező finisher scenarióra (violation=0 célok) | Miért: red-line zárás mérhető igazolása.

- 2026-03-15 | REBUILD-037 | Eval kiegészítés: recap-quality kritériumok (nem utolsó sor ismétlés, min. 2 releváns pont ahol van) | Miért: Gate 2 polish mérhetősége.

- REBUILD-037 review: interpret-pack hardening scope checked; document reviewed for Gate 2 alignment.

- 2026-03-16 | REBUILD-042 | Gate 2 scorecard kiegészítés: residual mixed-turn surface metrikák és kötelező trace-koherencia. | Miért: maradék regressziók objektív bizonyítása.

- 2026-03-16 | REBUILD-044 | Gate 2 exit-prep scorecard adjudikáció rögzítve (24-turn HU live matrix, 21/3, Gate 2 ACTIVE). | Miért: kapuzárás-előkészítés objektív residual képpel.
