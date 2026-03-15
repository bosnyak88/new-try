# System Map and Dependency Guide

- Dokumentum státusz: **kanonikus rendszertérkép és dependency guide**
- Dátum: **2026-03-15**
- Fő kapcsolatok: **01, 02, 09, 12, 14**

## Dokumentum célja

Ez a dokumentum megmutatja, hogyan áll össze a Syntaris rendszere logikai rétegekben, és milyen függőségi szabályok vannak.
A célja, hogy a fejlesztőcsapat ne építsen rejtett kerülőutakat vagy giant-brain-file típusú szivárványos központot.

## 1. Fő rendszertérkép

```text
User input
  -> Capture / Normalize
  -> Interpret / Candidate pack
  -> Thread + Workframe arbitration
  -> Memory / Evidence / Source retrieval
  -> Decision / Response plan
  -> Verbalization
  -> State update + Trace + Audit
  -> User-visible reply
```

Kapcsolódó rétegek:
- source/artifact bridge
- persistence / storage
- capability layer
- model-assisted cognition
- validation / observability

## 2. Fő logikai zónák

### Zóna A — Felszíni be- és kimenet
Feladata:
- input capture,
- output surface,
- rövid állapotjelzés,
- de nem itt dől el a fő igazság.

### Zóna B — Kognitív orchestration
Ez a rendszer közepe.
Itt történik:
- jelkinyerés,
- workframe/thread döntés,
- self-check,
- response plan.

### Zóna C — Állapot és memória
Itt élnek:
- stable explicit memory,
- temporary state,
- thread-state,
- conclusions,
- applicability,
- identity/relationship state,
- later long-horizon model.

### Zóna D — Source és artifact gerinc
Itt élnek:
- current source,
- historical source,
- artifact metadata,
- source audit,
- read-only source bridge.

Gate 1 után ez a zóna már merge-elt baseline:
- artifact/source registry,
- read-only local text bridge,
- current-source visibility,
- once-file import source-awareness,
- explicit historical log selection,
- refusal guards,
- audit trail.

### Zóna E — Model-assisted réteg
Csak segítő szerep.
Nem lehet saját igazságforrás.

### Zóna F — Observability és validation
Trace, audit, metrics, scorecard, runbook, regression.

## 3. Source-selection ladder

A source-awareness és evidence follow-up kötelező preferenciarendje:

1. **Explicit historical source request**
   - pl. `korábbi logból`, explicit történeti forrásjelzés

2. **Current meaningful source**
   - aktív `local_text_file` / `once_file_import` / más meaningful source

3. **Trace-only conversational artifact**
   - csak akkor, ha nincs jobb meaningful source, és a feladat ezt tényleg indokolja

Tiltás:
- failed read/import nem veheti át a current source szerepét
- tetszőleges user kérdésből létrejött `raw_paste` nem nyomhatja le a meaningful current source-t

## 4. Config és runtime precedence boundary

A CLI / operator boundary része a config/runtime precedence is.

Kötelező szabály:
- explicit temp config és per-test izoláció nem sérülhet ambient compat aliasok miatt
- a primary env override-ok kanonikusabbak, mint a compat aliasok
- a config loader / runtime boundary nem kerülheti meg a test isolationt

Ez Gate 1 utóvédelmi baseline része lett a 035b fix után.

## 5. Engedélyezett dependency irányok

### Megengedett
- CLI / operator boundary -> orchestration
- orchestration -> contracts
- orchestration -> persistence / state access
- orchestration -> model helpers (később)
- orchestration -> reply surface
- orchestration -> trace / audit
- source bridge -> orchestration / contracts / persistence

### Tiltott vagy erősen korlátozott
- CLI közvetlenül írjon központi state-et megkerülve az orchestrationt
- model layer közvetlenül írja felül a truth-state-et
- reply surface döntsön workframe-ről vagy source-ról önállóan
- adapterek saját mini-truth-modellt tartsanak fenn
- source bridge közvetlenül szöveget juttasson a reply rétegbe a kognitív lánc megkerülésével

## 6. Anti-bypass szabály

A következőket tilos megkerülni:
- response plan,
- source honesty ellenőrzés,
- source selection ladder,
- state update discipline,
- trace / audit írás,
- memory governance.

## 7. Modulfelelősségi elv

### Contracts réteg
A jelentések és semantikai elvárások helye.

### Orchestration réteg
A döntési és irányítási logika helye.

### Persistence réteg
A tárolás és visszaolvasás helye.

### Reply / verbalization réteg
A felszíni válasz helye, de nem a fő jelentés döntéshozója.

### Trace / audit réteg
A megfigyelhetőség és visszakövethetőség helye.

### CLI / operator boundary
Belépési pont, de nem logikai központ.

### Model-assisted réteg
Segítő, nem uralkodó.

## 8. Ticket-scope térkép

### Kis ticket
Egyértelműen lokális változás, contract- és capability-hatás nélkül.

### Közepes ticket
Több zónát érint, de nincs gate-váltási hatása.

### Rendszerszintű ticket
Érintheti:
- contracts,
- orchestration,
- persistence,
- reply,
- trace,
- CLI,
- docs,
- tests.

A Gate 2 ticketjei alapértelmezésben rendszerszintűek.

## 9. Living docs és rendszerkép kapcsolata

Minden fő rétegnek vissza kell köszönnie legalább itt:
- North Starban,
- State Matrixban,
- Capability Catalogban,
- ha döntés született: ADR logban,
- ha contract változott: Contract docban,
- ha mérési elv változott: Scorecardban,
- ha operátori menet változott: Runbookban.

## 10. Rövid végső összefoglalás

A Syntaris nem egyetlen „okos fájl”, hanem több rétegű rendszer.
A dependency guide célja, hogy ezt a rétegességet a kódban is megőrizze.


## Delta Journal

- 2026-03-15 | REBUILD-036 | Frissítve: interpret -> response_plan -> trace.events függési láncban új arbitration-meta átvezetés | Miért: rendszerszintű ticket scope dokumentálása.
