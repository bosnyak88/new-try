# Syntaris kapus roadmap és kilépési feltételek v1

- Dokumentum státusz: **kanonikus kapurend**
- Verzió: **v1**
- Dátum: **2026-03-15**
- Fő kapcsolatok: **01, 05, 06, 07, 11, 12**

## Dokumentum célja

Ez a dokumentum rögzíti a Syntaris kötelező fejlesztési sorrendjét.
A kapuk célja az, hogy a projekt ne csússzon el látványos, de korai vagy instabil feature-ök felé, miközben az alap kognitív rétegek hiányosak.

## 1. Miért kell kapus roadmap

A Syntaris nem lineáris feature-lista.
Ez egy olyan rendszer, ahol bizonyos rétegek csak akkor értelmesek, ha alattuk már stabilabb, igazabb és auditálhatóbb alap működik.

A kapurend ezt védi.

## 2. Kapuáttekintés

- **Gate 0** — Stabil determinisztikus alap
- **Gate 1** — Forrásgerinc / artifact-source registry / read-only source bridge
- **Gate 2** — Interpretációs / kognitív kapu
- **Gate 3** — Korai interpretációs modellpilot
- **Gate 4** — Presence mélyítés és korai shell-hasznosság
- **Gate 5** — Permissioned execution foundation
- **Gate 6** — Long-horizon személyes modell és always-on irány
- **Gate 7** — Érett multi-model orchestration

## 3. Gate 0 — Stabil determinisztikus alap

### Cél
Legyen egy használható, auditálható, lokálisan validált determinisztikus rendszer-mag.

### Tartalma
- thread / previous-thread / compare / recall alapok,
- trace / snapshot / focus alapok,
- explicit memory + temporary state,
- workframe / objective / blocker / next-step alapok,
- evidence-governance baseline,
- maintenance baseline,
- identity / relationship explicit baseline,
- failed-ingest honesty guard,
- presence első merged alapelemei.

### Státusz
**Nagyrészt teljesített.**
Nem lezárt végállapot, de elég erős ahhoz, hogy a következő kapu nyíljon.

### Mi nem számít még itt átmentnek
- általánosan stabil casual live beszélgetés,
- zajos magyar multi-intent interpretáció,
- shell vagy execution readiness.

## 4. Gate 1 — REBUILD-035 és a forrásgerinc lezárása

### Miért még most
A shell, a source panelek és a későbbi környezeti híd csak akkor lehet igaz, ha a rendszernek már van első osztályú artifact/source gerince.

### Kötelező tartalom
- artifact / source registry baseline,
- read-only local file bridge,
- current-source visibility,
- audit / journal baseline a source műveletekhez,
- source-honesty kiterjesztése artifact szintre,
- outside-root és unsupported read refusal.

### Exit criteria
Gate 1 akkor tekinthető átmentnek, ha:
- létezik persisted artifact/source modell,
- a current-source kérdésekre a rendszer truth-first módon tud válaszolni,
- read-only local file műveletek auditáltak,
- failed source read nem szennyezi a current-source kontextust,
- explicit historical source reuse működik,
- és a Gate 0 képességek nem estek szét.

### Továbbhaladási szabály
Gate 1 után **nem** shell jön automatikusan, hanem a Gate 2 interpretációs kapu.

## 5. Gate 2 — Interpretációs / kognitív kapu

### Miért ez a következő főkapu
A rendszer jelenlegi legnagyobb valódi szűk keresztmetszete a zajos, természetes, kevert magyar input értelmezése.
Ez stratégiai kapu, nem kényelmi finomítás.

### Kötelező al-képességek
- noisy HU input kezelése,
- elütés- és hibás toldalék-tűrés,
- multi-intent bontás,
- workframe helyesebb tartása,
- thread-váltás és thread-visszatérés robusztusabb kezelése,
- explicit style-constraint obedience,
- chat-lock persistence,
- anti-hijack guard,
- ack-collapse guard,
- őszinte unknown handling,
- valós inputos live stabilitás javítása.

### Gate 2 tiltások
Gate 2 alatt tilos:
- a hibákat shelllel elfedni,
- execution felé menekülni,
- modellpilotot maghibák elfedésére használni,
- menüzéssel helyettesíteni az értelmezést.

### Gate 2 exit criteria
Gate 2 akkor tekinthető átmentnek, ha:
- a scorecard szerinti fő mutatók elérik a küszöböt,
- a merge-stop piros zászlók nincsenek jelen,
- valós emberi inputos körökben a rendszer nem omlik ack-loopba,
- explicit formakérést stabilan megtart,
- és a valós live próbák már nem mutatnak sorozatos workframe / sablonhijack hibákat.

## 6. Gate 3 — korai interpretációs modellpilot

### Mikor szabad megnyitni
Csak Gate 2 után vagy Gate 2 végén, ha a determinisztikus plafon tisztán látszik.

### Mi a célja
Nem a rendszer „okosnak láttatása”, hanem annak mérése, hogy az A-oldali interpretációs segítség mennyit javít:
- ambiguity handlingen,
- candidate generationön,
- zajos magyar inputon,
- multi-intent bontáson.

### Mi marad determinisztikus
- state,
- truth model,
- evidence governance,
- source honesty,
- memory governance,
- execution control,
- merge-stop hibák kezelése.

### Kemény tiltás a Gate 3 alatt is
Az A-oldali pilot nem fedhet el determinisztikus maghibákat.

## 7. Gate 4 — presence mélyítés és korai shell-hasznosság

### Előfeltétel
Gate 2 stabilabb interpretáció, és ha volt Gate 3, annak kiértékelt eredménye.

### Tartalom
- presence mélyítés,
- jobb live folytonosság,
- shell / panelek első valóban hasznos formái,
- source / thread / state vizualizáció.

### Miért nem korábban
Mert a látványosabb shell rossz alapra csak elfedi a kognitív hiányosságot.

## 8. Gate 5 — permissioned execution foundation

### Előfeltétel
Gate 4 után.

### Tartalom
- permission / risk matrix,
- session/action execution foundation,
- review / approval flow,
- auditált végrehajtási csatorna.

### Miért később
Mert a végrehajtás csak akkor biztonságos, ha a megértés, forráshonesty és state-fegyelem már erősebb.

## 9. Gate 6 — long-horizon személyes modell és always-on irány

### Tartalom
- hosszú távú személyes modell,
- event/watcher irány,
- always-on működési irány,
- napokon/heteken átívelő folytonosság.

### Előfeltétel
Stabilabb execution foundation és erős memory governance.

## 10. Gate 7 — érett multi-model orchestration

### Tartalom
- érett A/B modellrendszer,
- critic/verifier réteg,
- finomabb modellváltási policy,
- költség / latencia / megbízhatóság egyensúlya.

### Fontos pontosítás
Ez nem kezdőkapu.
Csak akkor értelmes, ha az alatta levő rendszer már jó alapot ad.

## 11. Általános továbblépési szabályok

- Kaput ugrani nem szabad.
- Egy gate csak akkor tekinthető átmentnek, ha a hozzá tartozó exit criteria teljesül és a Current State Matrix ezt tükrözi.
- Egy új, látványos réteg nem írhatja felül a korábbi gate unresolved hibáit.
- A PR summary és a dokumentációs csomag frissítése a kapuváltás része.

## 12. Rövid végső összefoglalás

A jelenlegi aktív fejlesztési sorrend:
1. Gate 1 lezárása,
2. Gate 2 mint kötelező főkapu,
3. csak ezután, szükség esetén, korai A-oldali interpretációs pilot,
4. és csak ezt követően presence / shell / execution mélyítés.
