# Syntaris Capability Catalog v1

- Dokumentum státusz: **living doc / képességkatalógus**
- Verzió: **v1 (Gate 1 syncelt, normalizált státuszrendszerű kiadás)**
- Dátum: **2026-03-16**
- Fő kapcsolatok: **01, 03, 06, 09, 11, 14**

## Dokumentum célja

Ez a dokumentum azt rögzíti, hogy a rendszer jelenleg mit támogat, mi áll aktív fejlesztés alatt, mi van betervezve későbbre, és mi számít tudatosan tiltott capability-nek.

Ez tehát nem csak egy "mit tud most" lista, hanem a capability-k **kanonikus státuszkatalógusa**. A dokumentum célja, hogy egyetlen, félreérthetetlen helyen látszódjon:
- mi használható most stabilan,
- mi részlegesen működik,
- mi van aktív fejlesztés alatt,
- mi csak tervezett,
- mi későbbre halasztott,
- és mi tiltott a jelenlegi projektfázisban.

## Living-doc szabály

Minden rendszerszintű merge után kötelező frissíteni, ha bármely capability státusza vagy megjegyzése változott.

## Státuszlegendák

- **SUPPORTED** — használható, kanonikusan támogatott capability
- **PARTIAL** — részben működik, de ismert korláttal, red flaggel vagy merge-stop minőségű hiánnyal
- **ACTIVE** — jelenleg aktív fejlesztés alatt álló capability; még nem tekinthető támogatottnak
- **PLANNED** — elfogadott, de még nem aktív capability
- **DEFERRED** — tudatosan későbbre tett capability vagy réteg
- **FORBIDDEN** — a jelenlegi projektfázisban tiltott capability vagy viselkedés

## Állapotbélyeg

A katalógus a **2026-03-15-ös ismert rendszerállapotot** tükrözi, beleértve a merge-elt **REBUILD-035 / 035b / 035c** baseline-t.
A pontos jelenlegi helyzetet mindig a `06_Current_State_Matrix.md` és az utolsó validált merge alapján kell értelmezni.

## 1. Beszélgetési és kognitív capability-k

| Capability | Státusz | Megjegyzés |
|---|---|---|
| HU-first alap interakció | SUPPORTED | a rendszer elsődleges nyelve magyar |
| Természetes, nem parancsnyelvű input fogadása | PARTIAL | stratégiai cél és részben működő baseline, de Gate 2 előtt nem általánosan stabil |
| Kötetlen casual live beszélgetés | PARTIAL | explicit family-kben működhet, de nem általánosan stabil |
| Explicit workframe-váltás kezelése | PARTIAL | létezik, de néha nem tartja meg kellően |
| Chat-lock / „csak beszélgessünk” tartása | PARTIAL | ismert stratégiai hiány |
| Multi-intent bontás valós inputon | PARTIAL | koncepcionálisan cél, de Gate 2 előtt nem elég erős |
| Mixed continuity felszíni kompozíció (recap + next-step + reflective) | PARTIAL | REBUILD-041-ben bevezetve, REBUILD-042 residual hardeninggel erősítve; Gate 2 továbbra is aktív |
| Zajos magyar input tűrése | PARTIAL | még stratégiai fejlesztési cél |
| Direct question robustness | PARTIAL | ismert ack-collapse hiba miatt nem tekinthető teljesnek |
| Őszinte unknown handling | PARTIAL | alapelv megvan, de nem mindig elég jól érvényesül |
| Belső menük / route-nevek elrejtése | PARTIAL | elvileg kötelező; a végső UX-ben menüzés nem jelenhet meg |
| Rövid „gondolkodás folyamatban” jelzés | SUPPORTED | elfogadható állapotjelző, ha tényleges feldolgozás zajlik |
| Structured evidence bontás casual helyzetben | FORBIDDEN | csak explicit igény esetén elfogadható |

## 2. Memória, thread és állapot capability-k

| Capability | Státusz | Megjegyzés |
|---|---|---|
| Current thread kezelés | SUPPORTED | baseline része |
| Previous-thread / recall alapok | SUPPORTED | baseline része |
| Compare alapok | SUPPORTED | baseline része |
| Temporary scoped state | SUPPORTED | baseline része |
| Stable explicit memory alapok | SUPPORTED | baseline része |
| Blocker / objective / next-step | SUPPORTED | baseline része |
| Decision-state / missing-info alapok | SUPPORTED | baseline része |
| Long-horizon személyes modell | DEFERRED | Gate 6 |
| Rich multi-day continuity | PARTIAL | nem tekinthető még késznek |

## 3. Evidence és source capability-k

| Capability | Státusz | Megjegyzés |
|---|---|---|
| Raw evidence ingest | SUPPORTED | baseline része |
| Source-grounded válasz | SUPPORTED | baseline része |
| Failed-ingest honesty | SUPPORTED | merged guard |
| Current vs historical source explicit megkülönböztetés | SUPPORTED | Gate 1-ben megerősített baseline |
| Artifact/source registry | SUPPORTED | Gate 1 merge-elt baseline |
| Read-only local file bridge | SUPPORTED | allowed-root text olvasás, artifact-find, artifact-read |
| Meaningful current-source selection | SUPPORTED | a source-awareness nem az utolsó tetszőleges raw_paste-re esik vissza |
| Current source visibility | SUPPORTED | `miből dolgozol most?` / hasonló kérdések truthfully működnek |
| Once-file import source-awareness | SUPPORTED | `once_file_import` aktív forrásként viselkedik |
| Once-file evidence follow-up | SUPPORTED | `mi biztosan látszik ebből?` / `mi csak következtetés?` az importált forrásból dolgozik |
| Explicit historical log/artifact reuse | SUPPORTED | explicit „korábbi logból” jellegű visszanyúlás baseline működik |
| Auditált source-read műveletek | SUPPORTED | `artifact_find` / `artifact_read` / import / refusal auditálható |
| Binary/unsupported refusal guard | SUPPORTED | allowed rooton belül helyes refusal ok |
| Outside-root refusal guard | SUPPORTED | helyes refusal ok |
| Write-capable source módosítás | FORBIDDEN | jelenlegi fázisban tiltott |

## 4. Runtime, inspect és operator capability-k

| Capability | Státusz | Megjegyzés |
|---|---|---|
| `talk --once` | SUPPORTED | alap operátori capability |
| `talk --live` | SUPPORTED | használható, de casual quality nem általánosan stabil |
| `trace-last` | SUPPORTED | baseline része |
| `thread-snapshot --current` | SUPPORTED | baseline része |
| Fresh temp DB + init-db validáció | SUPPORTED | kanonikus eljárás |
| Ambient compat env melletti izolált explicit temp-config futás | SUPPORTED | 035b-ben hardenelt precedence baseline |
| Bizonytalan clean-run helperre épülő reset | FORBIDDEN | nem hivatalos resetút |
| `artifact-find` / `artifact-read` / `artifact-list` / `artifact-show` / `audit-last` | SUPPORTED | Gate 1 merge-elt operátori baseline |

## 5. Safety és execution capability-k

| Capability | Státusz | Megjegyzés |
|---|---|---|
| Artifact/source truthfulness a Gate 1 family-kben | SUPPORTED | source-honesty red-line itt merge-elt baseline |
| Általános truth-first / uncertainty-aware működés | PARTIAL | stratégiai alap, de bizonyos live helyzetekben még gyenge |
| Permissioned execution | DEFERRED | Gate 5 |
| Write/delete/move file operations | FORBIDDEN | a jelenlegi Gate-ekben tiltott |
| Risk matrix | DEFERRED | Gate 5 |
| Külső app-automáció | FORBIDDEN | jelenlegi fázisban tiltott; későbbi gate-ekben újraértékelhető |

## 6. Model-assisted cognition capability-k

| Capability | Státusz | Megjegyzés |
|---|---|---|
| A/B orchestration | DEFERRED | stratégiailag későbbi, teljes forma csak későbbi gate-ekben |
| A-oldali interpretációs pilot | PLANNED | Gate 3 feltételes; csak Gate 2 után |
| B-oldali verbalization pilot | DEFERRED | csak később |
| Modell általi maghiba-elfedés | FORBIDDEN | stratégiai tiltás |

## Kötelező karbantartási szabály

A capability státusz nem lehet marketingesebb, mint a valóság.
Ha egy capability csak family-tesztekben működik, de valós live inputon nem stabil, akkor **nem** jelölhető `SUPPORTED`-nek.

Az `ACTIVE` státuszú capability-k sem tekinthetők támogatottnak addig, amíg:
- a review,
- a lokális validáció,
- és a tényleges merge
nem zárult le sikeresen.

## Rövid döntési szabály

Ha a kérdés az, hogy a rendszer „mit tud most”, erre a dokumentumra kell nézni.
Ha a fejlesztőcsapat ennél többet állít, bizonyítania kell, vagy frissítenie kell a katalógust.


## Delta Journal

- 2026-03-15 | REBUILD-036 | Képességfrissítés: response-plan arbitration meta (style/chat-lock/direct-answer/ack-risk) trace-elt | Miért: menümentes, de auditálható döntéskövetés.

- 2026-03-15 | REBUILD-036 finisher | Képesség pontosítva: mixed-mode style+direct question együtt kezelve; recap kérdések direct-answer-first útvonalra kerülnek | Miért: természetes HU-first turnek stabilizálása.

- 2026-03-15 | REBUILD-037 | Képesség bővítés: brief recap legalább 2 releváns pontot tud visszahozni, nem domináns meta-turn alapon | Miért: user-facing recap minőség.

- REBUILD-037 review: interpret-pack hardening scope checked; document reviewed for Gate 2 alignment.

- 2026-03-16 | REBUILD-042 | Capability pontosítás: mixed continuity surface kompozíció és surface-hijack guard explicit jelölve, de Gate 2 státusz változatlan (ACTIVE). | Miért: REBUILD-041 viselkedés kanonizálása.
