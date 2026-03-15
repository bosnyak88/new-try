# Syntaris Current State Matrix

- Dokumentum státusz: **living doc / kötelezően frissítendő**
- Dátum: **2026-03-15**
- Cél: **kanonikus pillanatkép a rendszer jelenlegi állapotáról**
- Fő kapcsolatok: **01, 03, 07, 08, 11, 12**

## Dokumentum célja

Ez a dokumentum nem víziót rögzít, hanem a jelenlegi állapotot.
Ez az a fájl, amelyből egyértelműen ki kell derülnie, hol tart a rendszer most.

## Living-doc szabály

Minden rendszerszintű merge után kötelező frissíteni.
Ha ez a fájl eltér a valós kódbázistól, az dokumentációs hiba.

## Állapotbélyeg

- Snapshot dátum: **2026-03-15**
- Értelmezés: ez az állapot a már merge-elt és validált **REBUILD-035 / 035b / 035c** eredményét is tartalmazza.
- Fontos: ha a repó ennél frissebb, ezt a fájlt elsőként kell szinkronba hozni.

## Státuszlegendák

- **MERGED** — kódban bent, validálva, irányadó baseline része
- **PARTIAL** — részben elkészült, de nem tekinthető általánosan stabilnak
- **ACTIVE** — jelenlegi aktív fejlesztési kapu vagy ticket
- **PLANNED** — elfogadott, de még nem aktív
- **DEFERRED** — tudatosan későbbre tett réteg
- **BLOCKER** — aktív, stratégiai jelentőségű hiány vagy hiba

## Magas szintű állapotkép

| Terület | Státusz | Rövid megjegyzés |
|---|---|---|
| Determinisztikus alapmag | MERGED | használható, lokálisan validált baseline |
| Thread / recall / compare alapok | MERGED | baseline része |
| Workframe / blocker / next-step alapok | MERGED | baseline része |
| Evidence ingest / source honesty alapok | MERGED | failed-ingest honesty guard bent van |
| Identity / relationship explicit baseline | MERGED | explicit owner/system distinction működik |
| Presence első merged alapelemei | PARTIAL | van javulás, de nem általánosan stabil casual live |
| Casual live beszélgetési stabilitás | BLOCKER | Gate 2 fő stratégiai probléma |
| Noisy HU interpretáció | BLOCKER | Gate 2 fő stratégiai probléma |
| Artifact / source registry baseline | MERGED | Gate 1 lezárt, merge-elt baseline |
| Read-only local file bridge | MERGED | allowed-root olvasás, outside-root refusal, binary refusal validált |
| Current source visibility | MERGED | meaningful current-source kiválasztás és source-awareness baseline működik |
| Once-file evidence linkage | MERGED | sikeres once-file import forráshű follow-upot ad |
| Explicit historical source reuse | MERGED | explicit „korábbi logból” jellegű visszanyúlás baseline működik |
| Audit / journal source műveletekhez | MERGED | source műveletek auditálhatók |
| Compat env precedence hardening | MERGED | ambient compat env nem írhatja felül a temp test/config izolációt |
| Gate 2 — Interpretációs / kognitív kapu | ACTIVE | kötelező következő főirány |
| A-oldali interpretációs pilot | PLANNED | csak Gate 2 után / végén |
| Shell / panelek mélyítése | DEFERRED | Gate 4 előtti tiltás |
| Permissioned execution foundation | DEFERRED | Gate 5 |
| Long-horizon személyes modell | DEFERRED | Gate 6 |
| Érett multi-model orchestration | DEFERRED | Gate 7 |
| Voice irány | DEFERRED | későbbi réteg, nem aktuális kapu |

## Részletes rendszerállapot

### 1. Már merged és validált baseline

#### Determinisztikus kognitív alap
- thread / previous-thread / recall / compare alapok: **MERGED**
- snapshot / focus / trace alapok: **MERGED**
- explicit memory + temporary scoped state: **MERGED**
- blocker / objective / next-step alapok: **MERGED**
- missing-info / open-question / decision-state alapok: **MERGED**
- thread-weave / conclusion / carry-forward alapok: **MERGED**

#### Evidence és maintenance baseline
- evidence ingest / source-grounding baseline: **MERGED**
- maintenance baseline: **MERGED**
- failed raw ingest honesty guard: **MERGED**

#### Identity / relationship baseline
- owner/system explicit distinction: **MERGED**
- explicit relationship framing baseline: **MERGED**
- live relationship alignment baseline: **MERGED**

#### Presence első merged alapelemei
- re-entry / folytassuk innen / hol tartottunk család első baseline: **PARTIAL**
- natural casual beszélgetés általános stabilitása: **NEM ÁTMENT**

#### Gate 1-ben lezárt és baseline-ba emelt source/artifact réteg
- artifact/source registry baseline: **MERGED**
- read-only local file bridge: **MERGED**
- current-source visibility: **MERGED**
- meaningful current-source kiválasztás: **MERGED**
- once-file import source-awareness és evidence linkage: **MERGED**
- explicit historical log/artifact reuse: **MERGED**
- source operation audit journal: **MERGED**
- outside-root refusal guard: **MERGED**
- binary / unsupported refusal guard: **MERGED**
- compat env isolation / precedence hardening: **MERGED**

### 2. Jelenlegi aktív kapu

#### Gate 2 — Interpretációs / kognitív kapu
Állapot: **ACTIVE, KÖTELEZŐ KÖVETKEZŐ FŐIRÁNY**

Fő problémák, amelyek ezt indokolják:
- noisy HU input gyengeség,
- workframe-tartási hibák,
- casual chat stabilitási problémák,
- explicit style-constraint megsértés,
- certainty/time hijack mintázatok,
- ack-collapse direkt kérdésekre,
- a természetes, nem parancsnyelvű input alultervezettsége,
- a több szándékot és hirtelen váltást tartalmazó valós input elégtelen kezelése.

### 3. Következő későbbi kapuk

#### Gate 3 — Korai A-oldali interpretációs pilot
Állapot: **PLANNED**

Feltétel:
- csak akkor nyitható, ha Gate 2 fő red-line problémái már nem determinisztikus maghibák.

#### Gate 4+ — Shell, execution, long-horizon, multi-model
Állapot: **DEFERRED**
- Gate 4: shell / panelek
- Gate 5: permissioned execution / risk matrix
- Gate 6: long-horizon személyes modell
- Gate 7: érett multi-model orchestration

## Ismert piros zászlók

1. **Casual live instabilitás**
   - explicit „csak beszélgessünk” után is workframe drift vagy structured sablonhijack történhet.

2. **Ack-collapse**
   - egyes direkt kérdésekre tartalmatlan nyugtázás eshet.

3. **Style-constraint sérülés**
   - explicit „ne listázz / ne bontsd biztos-bizonytalanra” tiltás ellenére is sablon aktiválódhat.

4. **Noisy HU input gyengeség**
   - zajos, félig kimondott, hirtelen váltó magyar inputnál a rendszer könnyen félreroute-olhat.

5. **Natural multi-intent hiány**
   - egy turnön belüli kevert szándékok kezelése még nem elég stabil.

## Merge / update szabályok

Ez a dokumentum kötelezően frissítendő:
- minden rendszerszintű merge után,
- minden kapuváltáskor,
- minden olyan ticket után, amely capability státuszt vagy ismert red flaget változtat.

## Rövid döntési szabály

Ha kérdés merül fel arról, hogy „hol tart most a rendszer?”, erre a dokumentumra kell nézni.
Ha a válasz nem fér bele ide, akkor a dokumentum hiányos és bővítendő.


## Delta Journal

- 2026-03-15 | REBUILD-036 | Gate 2 starter státusz rögzítve: chat-lock/style-obedience/direct-answer-first/anti-hijack fókusz aktív | Miért: red-line interpretációs hibák determinisztikus kezelése.
