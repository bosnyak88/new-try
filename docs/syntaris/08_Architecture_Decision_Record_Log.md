# Architecture Decision Record Log

- Dokumentum státusz: **living doc / kanonikus döntésnapló**
- Dátum: **2026-03-15**
- Fő kapcsolatok: **01, 03, 06, 09, 10, 13, 14**

## Dokumentum célja

Ez a dokumentum a fő architekturális döntéseket rögzíti.
A célja, hogy a csapat később is pontosan vissza tudja fejteni:
- milyen nagy döntés született,
- miért,
- milyen alternatívák voltak,
- és milyen következményekkel jár.

## Használati szabály

Új ADR kell minden olyan döntéshez, amely:
- gate-sorrendet változtat,
- rendszerréteget vezet be vagy tol hátrébb,
- contractot vagy semantikai állapotot érint,
- memory governance-t módosít,
- modell szerepét újradefiniálja,
- vagy a UX-felszín alapelveit átírja.

## Státuszjelölések

- **ACCEPTED** — elfogadott, aktív döntés
- **SUPERSEDED** — felülírt döntés
- **PROVISIONAL** — ideiglenes, felülvizsgálandó döntés

---

## ADR-001 — Offline-first, single-user, HU-first kognitív társ-rendszer
- Státusz: **ACCEPTED**
- Döntés: A Syntaris nem általános chatbot-termék, hanem offline-first, single-user, HU-first személyes kognitív társ-rendszer.
- Miért: Ez tükrözi a projekt valódi célját és a fejlesztési prioritásokat.
- Következmény: a többfelhasználós, generikus terméklogika másodlagos.

## ADR-002 — Determinisztikus mag, modellek moduláris szerepben
- Státusz: **ACCEPTED**
- Döntés: A központi state, truth model, evidence governance, memory governance és execution control determinisztikus marad; a modellek moduláris segítők.
- Miért: a rendszernek auditálhatónak és ellenőrizhetőnek kell maradnia.
- Következmény: modell nem írhatja felül a központi igazságmodellt.

## ADR-003 — Truth-first és uncertainty-aware működés
- Státusz: **ACCEPTED**
- Döntés: A rendszernek explicit módon külön kell kezelnie a biztos, következtetett, hiányzó és nem értett részeket.
- Miért: a projekt alapértéke az őszinteség és a forráshűség.
- Következmény: source-honesty sérülés merge-stop kategória.

## ADR-004 — Natural interaction, nem parancsnyelv
- Státusz: **ACCEPTED**
- Döntés: A user természetes, hibás, zajos magyar inputot adhat; a rendszer feladata az értelmezés.
- Miért: ez maga a rendszer lényege.
- Következmény: a fejlesztés nem támaszkodhat parancsnyelvre mint végső userfelületre.

## ADR-005 — Hidden complexity, egyszerű felszín
- Státusz: **ACCEPTED**
- Döntés: a háttérkomplexitás nőhet, de a felszínen menüzés és belső technikai kiírás nem elfogadható.
- Megengedett kivétel: rövid, természetes „gondolkodás folyamatban” jelzés.
- Következmény: route-nevek, certainty dump és technikai introspekció a végső UX-ben tiltott.

## ADR-006 — Gate 1 után közvetlenül Gate 2 következik
- Státusz: **ACCEPTED**
- Döntés: a REBUILD-035 forrásgerinc után a következő kötelező főkapu az interpretációs / kognitív kapu.
- Miért: a valós szűk keresztmetszet a megértés és workframe-tartás.
- Következmény: shell és execution nem kerülhet előre.

## ADR-007 — A korai A-oldali pilot nem fedhet el determinisztikus maghibát
- Státusz: **ACCEPTED**
- Döntés: A-modell pilot csak a valódi interpretációs plafon vizsgálatára nyitható.
- Miért: külön kell választani a modellhiányt a maghibáktól.
- Következmény: chat-lock elvesztés, ack-collapse, explicit style-constraint sérülés nem tolható át „majd az LLM megoldja” kategóriába.

## ADR-008 — Source/artifact registry a shell előtt
- Státusz: **ACCEPTED**
- Döntés: a source/artifact gerincet a shell és panelek előtt kell felépíteni.
- Miért: a shell csak így lehet truth-first és hasznos.
- Következmény: Gate 1 megelőzi a shell mélyítését.

## ADR-009 — Hot / warm / cold munkatér-modell
- Státusz: **ACCEPTED**
- Döntés: a rendszer munkaterét hot/warm/cold rétegekben kell modellezni.
- Miért: a több rétegű kognitív működéshez RAM-, index- és tárolási fegyelem kell.
- Következmény: nem minden kerül hot state-be.

## ADR-010 — Living docs kötelező karbantartása
- Státusz: **ACCEPTED**
- Döntés: a Current State Matrix, Capability Catalog, ADR log, Scorecard és Runbook minden rendszerszintű merge után kötelezően frissítendő.
- Miért: a no-silent-drift csak így tartható fenn.
- Következmény: dokumentumfrissítés nélküli PR nem tekinthető teljesnek.

## ADR-011 — Valós inputos validáció kötelező stratégiai réteg
- Státusz: **ACCEPTED**
- Döntés: a steril family-tesztek mellett valós emberi inputos körök is kötelezőek, különösen Gate 2-ben.
- Miért: a fő probléma nem ott látszik, ahol a prompt szép és egyértelmű.
- Következmény: live casual hibák nem söpörhetők félre, ha a unit tesztek zöldek.

## ADR-012 — Memória nem homogén és nem írható bárhogy
- Státusz: **ACCEPTED**
- Döntés: a memória több rétegből áll, külön írási, TTL, megerősítési és érzékenységi szabályokkal.
- Miért: a személyes rendszer integritása ezt megköveteli.
- Következmény: lásd 13_Data_and_Memory_Governance.md.

## ADR-013 — Gate 1 artifact/source baseline merge-elt és kapuzáró
- Státusz: **ACCEPTED**
- Döntés: a REBUILD-035 / 035b / 035c együtt lezárta a Gate 1 alapréteget.
- Miért: lokálisan validált és merge-elt baseline lett az artifact/source registry, a read-only local file bridge, a current-source visibility, az audit journal, az once-file evidence linkage és az explicit historical log selection.
- Következmény: a Gate 1 capability-k mostantól baseline-ként kezelendők, és a következő kötelező főirány a Gate 2.

## ADR-014 — Primer env override-ok és compat aliasok precedence-e szűken rögzített
- Státusz: **ACCEPTED**
- Döntés: a primary env override-ok (`SYNTARIS_DB_PATH`, `SYNTARIS_ARTIFACT_ALLOWED_ROOTS`) kanonikusak; a compat aliasok (`SYNTARIS_DB`, `SYNTARIS_SANDBOX_ROOTS`) csak a default/example config útvonal mellett értelmezhetők, és nem írhatják felül az explicit temp config/test izolációt.
- Miért: a 035b során reprodukálható ambient env leakage szennyezte a test isolationt.
- Következmény: explicit temp config + temp DB + temp roots futásnak izoláltnak kell maradnia még ambient compat env jelenlétében is.

## ADR-015 — Meaningful current-source selection és explicit historical log selection
- Státusz: **ACCEPTED**
- Döntés: a source-awareness válaszoknak a meaningful current source-ra kell támaszkodniuk, nem a legutóbbi tetszőleges conversational raw_paste artifactra.
- Kiegészítés:
  - explicit történeti wording (`korábbi logból`, hasonló) választhat korábbi releváns artifactot;
  - failed read/failed once-file nem szennyezheti silent módon a current source állapotot;
  - conversational raw_paste artifact megmaradhat traceability célra, de nem uralhatja a source-awareness-t.
- Miért: a Gate 1 acceptance fő problémája ez volt.
- Következmény: current source / historical source kiválasztás önálló, truth-first döntési szabályt kapott.

## ADR-016 — Ticketzáráskor kötelező a Fájlfrissítési jelentés
- Státusz: **ACCEPTED**
- Döntés: minden rendszerszintű ticket summary végén kötelező egy külön „Fájlfrissítési jelentés” blokk.
- Kötelező tartalom:
  - módosított kódfájlok,
  - frissített kanonikus dokumentumok,
  - átnézett, de változatlan living docok,
  - releváns, de szándékosan nem frissített fájlok és indokuk.
- Miért: a dokumentumszinkron csak így auditálható ticketenként.
- Következmény: ilyen blokk nélkül a ticket nem tekinthető teljesnek.

## Új ADR bejegyzés sablon

### ADR-XXX — [rövid cím]
- Státusz:
- Döntés:
- Alternatívák:
- Miért:
- Következmény:
- Érintett dokumentumok:
- Kötelező frissítések:
