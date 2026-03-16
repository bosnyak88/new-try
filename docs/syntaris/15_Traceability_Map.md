# Traceability Map

- Dokumentum státusz: **kanonikus követelmény-visszavezetési térkép**
- Dátum: **2026-03-16**
- Cél: **megmutatni, hogy a csomag fő követelményei, döntései és kapui mely dokumentumokból vezethetők vissza**

## Dokumentum célja

Ez a dokumentum a teljes csomag navigációs és visszakeresési térképe.
A célja, hogy egy fejlesztő, reviewer vagy jövőbeli csapattag gyorsan meg tudja találni:
- melyik kérdésre melyik dokumentum ad választ,
- hol van a normatív előírás,
- hol van az aktuális állapot,
- és hol van a mérés vagy operátori eljárás.

## 1. Fő témák és elsődleges dokumentumok

| Téma | Elsődleges dokumentum | Másodlagos dokumentumok |
|---|---|---|
| Mi a Syntaris és mi a végcél | 01 | 08, 14 |
| Mi a jelenlegi valós állapot | 06 | 07, 03 |
| Milyen sorrendben szabad fejleszteni | 03 | 01, 08 |
| Mi a következő kötelező főkapu | 03 | 06, 11 |
| Mit tud most a rendszer | 07 | 06 |
| Miért született egy architekturális döntés | 08 | 01, 03 |
| Milyen state-ek és contractok kötelezőek | 09 | 14, 10 |
| Melyik modul miért felel | 10 | 09 |
| Milyen minőségi küszöb kell | 11 | 05, 03 |
| Hogyan kell validálni és reprodukálni | 12 | 05 |
| Hogyan kell kezelni a memóriát és adatot | 13 | 09, 14 |
| Mit jelentenek a kulcsfogalmak | 14 | 09 |

## 2. Kritikus stratégiai állítások visszavezetése

### A rendszer nem chatbot, hanem személyes kognitív társ-rendszer
- Elsődleges: 01
- Kiegészítő: 08 (ADR-001)

### A központi mag determinisztikus, a modellek moduláris segítők
- Elsődleges: 01
- Kiegészítő: 08 (ADR-002), 02, 09

### A projekt truth-first és uncertainty-aware
- Elsődleges: 01
- Kiegészítő: 08 (ADR-003), 05, 11

### A user természetes magyar nyelven beszélhet, nem parancsnyelven
- Elsődleges: 01
- Kiegészítő: 02, 08 (ADR-004)

### A belső komplexitás elrejthető, a menüzés nem elfogadható
- Elsődleges: 01
- Kiegészítő: 02, 08 (ADR-005), 07

### A REBUILD-035 után Gate 2 a kötelező főirány
- Elsődleges: 03
- Kiegészítő: 01, 08 (ADR-006), 06

### Az A-oldali pilot nem fedheti el a determinisztikus maghibákat
- Elsődleges: 03
- Kiegészítő: 01, 02, 08 (ADR-007), 11

### A source/artifact gerincnek a shell előtt kell jönnie
- Elsődleges: 03
- Kiegészítő: 01, 08 (ADR-008), 07, 10

### A hot/warm/cold munkatér-modell kötelező szemlélet
- Elsődleges: 04
- Kiegészítő: 01, 02, 08 (ADR-009), 13

### A living docs minden rendszerszintű merge után frissítendők
- Elsődleges: 00
- Kiegészítő: 08 (ADR-010), 06, 07, 11, 12

## 3. Kritikus operátori kérdések visszavezetése

### „Milyen parancsokkal validáljak?”
- Elsődleges: 12
- Kiegészítő: 05

### „Mi számít kontaminált körnek?”
- Elsődleges: 12
- Kiegészítő: 05

### „Mi számít merge-stop hibának?”
- Elsődleges: 05
- Kiegészítő: 11

### „Mi kell ahhoz, hogy Gate 2 átmentnek számítson?”
- Elsődleges: 03
- Kiegészítő: 11, 05

### „Mit kell frissíteni egy rendszerszintű PR után?”
- Elsődleges: 00
- Kiegészítő: 06, 07, 08, 11, 12

### REBUILD-042 mixed-continuity kanonizálás és residual hardening
- Elsődleges: 06, 09, 11, 12
- Kiegészítő: 07, 08, 10, 15

### REBUILD-044 Gate 2 exit-prep live validation
- Elsődleges: 06, 11, 12, artifacts/rebuild044_live_matrix.md, artifacts/rebuild044_validation.log
- Kiegészítő: src/syntaris/orchestration/response_plan.py, src/syntaris/orchestration/thread_focus.py, src/syntaris/orchestration/turns.py, src/syntaris/trace/events.py, tests/test_rebuild041_surface_continuity.py, tests/test_rebuild042_gate2_residual_surface.py

## 4. Kritikus fejlesztői kérdések visszavezetése

### „Hol van leírva, hogy milyen mezőknek kell létezniük?”
- 09

### „Hol van leírva, hogy melyik modul mit hívhat?”
- 10

### „Hol van leírva a jelenlegi valós támogatottság?”
- 07

### „Hol van leírva a jelenlegi valós rendszerállapot?”
- 06

### „Hol van leírva, mikor írhat a rendszer stabil memóriát?”
- 13

### „Hol van leírva, mit jelent pontosan egy fogalom?”
- 14

## 5. Rövid végső összefoglalás

A csomag akkor használható jól, ha a fejlesztő nem találgat, hanem visszakeres.
Ez a térkép ezt gyorsítja fel.


## Delta Journal

- 2026-03-15 | REBUILD-036 | Traceability bővítés: Gate 2 követelmények leképezése response_plan.py, workframe_state.py, turns.py, trace/events.py, test_rebuild036_gate2.py és validation log felé. | Miért: követelmény-visszaszármaztatás fenntartása.

- 2026-03-15 | REBUILD-036 finisher | Traceability kiterjesztés: finisher acceptance 1-9 -> konkrét kód- és tesztpontok + finisher validation log | Miért: visszakereshető lezárás.

- 2026-03-15 | REBUILD-037 | Traceability update: brief recap quality acceptance -> thread_focus.py/response_plan.py/tests/test_rebuild037_recap_quality.py + validation log | Miért: követelmény-visszavezetés aktualizálása.

- REBUILD-037 review: interpret-pack hardening scope checked; document reviewed for Gate 2 alignment.

- 2026-03-16 | REBUILD-042 | Traceability update: mixed-turn residual acceptance -> response_plan.py, thread_focus.py, turns.py, trace/events.py, tests/test_rebuild042_gate2_residual_surface.py, artifacts/rebuild042_validation.log. | Miért: követelmény-visszavezetés és proof-lánc.

- 2026-03-16 | REBUILD-044 | Traceability update: Gate 2 exit-prep live HU matrix + residual adjudikáció -> response_plan.py, gate2 surface tesztek, rebuild044 artifact pack. | Miért: kapuállítás visszavezethetősége objektív evidence-re.
