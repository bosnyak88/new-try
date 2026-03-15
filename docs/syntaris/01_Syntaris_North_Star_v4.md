# Syntaris North Star v4

* Dokumentum státusz: **kanonikus, legmagasabb szintű irányadó dokumentum**
* Verzió: **v4**
* Dátum: **2026-03-15**
* Elsődleges cél: **meghatározni, mi a Syntaris, milyen minőségi mércének kell megfelelnie, és milyen sorrendben szabad felépíteni**
* Kapcsolódó dokumentumok: **02, 03, 05, 06, 07, 08, 09, 13, 14**

## Dokumentum célja

Ez a dokumentum a Syntaris legmagasabb szintű fejlesztési alkotmánya.
Nem implementációs ticket, nem sprintleírás, nem tesztjegyzet, hanem a projekt identitásának, minőségi elvárásainak és fejlődési logikájának végső kerete.

Minden későbbi döntés, ticket, rendszerbővítés és validáció ebből kell hogy levezethető legyen.

## 1\. Mi a Syntaris

A Syntaris:

* offline-first,
* single-user by design,
* HU-first,
* truth-first,
* mind-first,
* determinisztikus kognitív központtal rendelkező,
* személyes, hosszú távra épülő,
* réteges memóriával, evidence-governance-szal, thread-rendszerrel és auditálhatósággal működő
  **személyes kognitív társ-rendszer**.

A Syntaris célja nem egyszerűen az, hogy kérdésekre válaszoljon.
A cél az, hogy:

1. értelmezze a valós, zajos emberi inputot,
2. felismerje a szándékot és a munkakeretet,
3. vissza tudjon nyúlni a releváns threadhez, memóriához és forráshoz,
4. külön tudja választani a biztosan alátámasztott és a következtetett részt,
5. meg tudja mondani, mi hiányzik,
6. meg tudja tartani a kontextust és a személyes viszonyt,
7. és csak ezután adjon választ vagy lépjen tovább.

## 2\. Mi nem a Syntaris

A Syntaris nem:

* általános webes chatbot,
* promptokra optimalizált termék-demo,
* tool-first agent,
* menüvezérelt kérdezz-felelek shell,
* csupán LLM-wrapper,
* automatikusan döntő rendszer az owner helyett,
* teatralizált „személyiségjáték”,
* parancsnyelvet elváró CLI-bot,
* olyan rendszer, amely láthatatlanul hazudik a forrásairól, állapotáról vagy bizonytalanságáról.

## 3\. A végcél rövid definíciója

A végcél egy olyan rendszer, amely:

* napi több ezer, zajos, természetes, hibás, félbehagyott vagy hirtelen váltó magyar mondatot is elbír,
* felismeri, hogy mikor csevegés, munka, emlékezés, ötletelés, problémafeltárás, döntés vagy forráselemzés zajlik,
* a háttérben több lépcsőben és több rétegben dolgoz fel,
* a felszínen viszont egyszerűnek, természetesnek és követhetőnek tűnik,
* nem igényel parancsnyelvet,
* képes őszintén bizonytalannak lenni,
* és idővel alkalmas lesz személyes, hosszú távú, permissioned executionnel összekapcsolt működésre.

## 4\. A legfontosabb alapelvek

### 4.1 Mind-first, nem tool-first

A Syntaris központi identitása kognitív rendszer.
Az eszközök, adapterek, modellek és bridge-ek ennek alárendelt szereplők.
Minden olyan fejlesztés, amely látványosabb felszínt vagy több végrehajtást ad, de nem erősíti a megértést, másodlagos.

### 4.2 Truth-first / uncertainty-aware

A rendszernek mindig különbséget kell tennie aközött, hogy:

* mit tud biztosan,
* mit következtet,
* mi nyitott,
* mi hiányzik,
* és mit nem ért eléggé.

Tiltott:

* forrás nélküli túlállítás,
* régi forrás csendes újrahasznosítása aktuálisnak álcázva,
* belső bizonytalanság elrejtése magabiztos felszín mögé.

### 4.3 Offline-first

A rendszer alapműködése helyi és önálló kell legyen.
Külső szolgáltatások, online rendszerek vagy felhőfüggőség nem lehetnek a működés központi előfeltételei.

### 4.4 Single-user by design

A rendszer egy ownerre épül.
Nem többfelhasználós általános terméklogikát kell ráerőltetni, hanem személyes, hosszú távú, egyéni kognitív partnerként kell felépíteni.

### 4.5 HU-first

Az elsődleges nyelv a magyar.
Nem elfogadható, hogy a rendszer csak akkor működik jól, ha a user leegyszerűsíti, „promptosítja” vagy idegen nyelvre váltja a gondolatait.

### 4.6 Determinisztikus mag + moduláris modellek

A központi state, policy, route, evidence-governance, memory-governance és execution-control determinisztikus kell legyen.
A modellek moduláris segítők:

* interpretáció,
* ambiguity handling,
* candidate generation,
* verbalization,
* később critic/verifier.

A modellek nem vehetik át a központi igazság- és állapotmodell szerepét.

### 4.7 Permissioned execution

A válaszadás és a végrehajtás nem ugyanaz.
A Syntaris csak jól meghatározott, ellenőrizhető, engedélyezett és auditálható feltételek mellett léphet át a végrehajtásba.

### 4.8 No silent drift

Nincs elfogadható néma eltérés:

* kód és dokumentáció között,
* trace és reply között,
* capability claim és valós működés között,
* contract és implementáció között,
* jelenlegi állapot és hivatalos State Matrix között.

### 4.9 Natural interaction, nem parancsnyelv

A user természetesen beszélhet: hibásan, töredezetten, elütésekkel, hirtelen váltásokkal, kevert szándékokkal, félig megfogalmazva.
A rendszer feladata az értelmezés, nem a user feladata a gép nyelvére fordítás.

### 4.10 Hidden complexity, egyszerű felszín

A háttérben lehet többlépcsős, összetett, többmodulos feldolgozás.
A felszínen viszont a rendszernek egyszerűnek kell látszania.

Ami a felszínen elfogadható:

* rövid állapotjelzés, például: „Gondolkodás folyamatban…”, „Átnézem…”, „Egy pillanat…”,
* természetes, emberi ritmusú válasz,
* rövid, célhoz illesztett kérdés, ha valóban kell.

Ami nem elfogadható a végső UX-ben:

* menüzés,
* route-nevek,
* belső pipeline lépések kiírása,
* „így értelmeztem a kérésedet” típusú technikai narráció,
* certainty/evidence bontás olyan helyen, ahol a user egyszerű beszélgetést kért.

### 4.11 Functional equivalence, nem agymásolás

A cél nem az emberi agy 1:1 modellezése, hanem annak funkcionális megfelelője:

* zajtűrő értelmezés,
* munkamemória,
* több szándék egyidejű kezelése,
* threadek közti mozgás,
* önellenőrzés,
* bizonytalanságkezelés,
* személyes folytonosság.

### 4.12 Surface honesty

Ha a rendszer nem ért valamit elég jól, azt őszintén kell jeleznie.
Nem omlhat ack-loopba, nem csúszhat semmitmondó sablonba, és nem válthat át strukturált elemzésre csak azért, mert kiesett az ismert family-ből.

## 5\. Jelenlegi ismert baseline

A jelenlegi, 2026-03-15-ös ismert baseline röviden:

### Már létező, merged és lokálisan validált alapok

* session / thread / previous-thread kezelés,
* recall / compare alapok,
* snapshot / focus / trace alapok,
* explicit memória és temporary scoped state,
* workframe / objective / blocker / next-step alapok,
* missing-info / open-question / decision-state alapok,
* thread-weave / conclusion / carry-forward alapok,
* evidence-ingest / source-grounding baseline,
* maintenance baseline,
* live relationship alignment és failed-ingest honesty baseline,
* presence első merged alapelemei.

### Amit a baseline még nem jelent

Ez a baseline **nem** jelenti azt, hogy a rendszer jelenleg általánosan stabil, szabad, élő, kötetlen beszélgetésben jól működik.

Jelenleg:

* a letesztelt family-kben és explicit flow-kban már erős lehet,
* de természetes, többértelmű, zajos, reflektív vagy hirtelen váltó magyar inputnál még félreroute-olhat,
* rossz sablonba csúszhat,
* workframe-et téveszthet,
* vagy ack-collapse jellegű gyenge fallbackba eshet.

Ez nem apró UX-hiba, hanem a Gate 2 interpretációs kapu egyik fő oka.

### Jelenlegi állapotkulcs

A pontos pillanatnyi állapotot **nem** ez a dokumentum rögzíti véglegesen, hanem a **06\_Current\_State\_Matrix.md**.
Ez a North Star csak a baseline természetét mondja ki.

## 6\. A Syntaris fő rendszerrétegei

### 6.1 Kognitív mag

A központi policy, state, reasoning orchestration és igazságmodell.

### 6.2 Interpretációs / szándékbányászati réteg

A zajos inputból kinyeri:

* a lehetséges szándékokat,
* a workframe-jelölteket,
* a thread-jelölteket,
* a style-constraint-eket,
* és a szükséges evidence / memory lookup igényt.

### 6.3 Memóriarendszer

Nem homogén memóriahalmaz, hanem több réteg:

* stable explicit memory,
* temporary scoped state,
* evidence-backed memory,
* conclusion memory,
* artifact-linked memory,
* később long-horizon személyes modell.

### 6.4 Hot / warm / cold memory- és munkatér-modell

* **Hot**: az aktuális turn és munkamemória.
* **Warm**: gyorsan előhívható állapotok, indexek, threadek, kivonatok.
* **Cold**: nyers logok, archív artifactok, hosszabb távú háttértár.

### 6.5 Thread rendszer

A rendszernek tudnia kell:

* mikor ugyanannak a szálnak a folytatása zajlik,
* mikor történt hirtelen váltás,
* mikor kér a user előző szálat,
* mikor akar összehasonlítást,
* mikor térne vissza egy régi fonalhoz.

### 6.6 Workframe és munkamenet-réteg

A rendszernek nem csak tartalmat, hanem munkakeretet is értenie kell.
Legalább az alábbi fő workframe-eket kell kezelni:

* casual\_chat,
* focused\_work,
* planning,
* recall,
* compare,
* evidence\_intake,
* source\_query,
* identity\_relationship,
* maintenance,
* decision\_support,
* mode\_control.

### 6.7 Decision-readiness réteg

Nem minden kérés egyforma.
A rendszernek tudnia kell, hogy:

* kész-e már döntést támogatni,
* hiányzik-e még információ,
* csak gondolkodási segítséget kér a user,
* vagy kifejezetten következő lépést vár.

### 6.8 Evidence governance

Különbséget kell tenni:

* raw source,
* chunkolt source,
* kivonat,
* kulcssorok,
* source-grounded állítás,
* inferred állítás,
* unresolved kérdés között.

### 6.9 Conclusion és applicability réteg

A rendszernek tudnia kell:

* milyen következtetés alakult ki,
* ez mennyire bizonyos,
* milyen környezetben alkalmazható,
* mikor évül el,
* és mikor kell lecserélni.

### 6.10 Identity / relationship réteg

Külön kell kezelni:

* owner-azonosság,
* system-azonosság,
* explicit relationship frame,
* és ezek személyes, de konzervatív felszíni megjelenítését.

### 6.11 Presence / conversation surface

A felszín célja:

* természetes beszélgetési élmény,
* jó re-entry,
* kevés dry fallback,
* workframe-hez illeszkedő stílus,
* menümentes működés,
* őszinte bizonytalanság.

### 6.12 Saját workspace shell / megjelenítő panel

Nem elsődleges kapu, hanem későbbi réteg.
Csak akkor érdemes mélyíteni, ha a kognitív és source-gerinc már megbízható.

### 6.13 Környezeti és eszközkezelési híd

Read-only bridge, majd később permissioned action bridge.
Nem előzheti meg a kognitív kaput.

### 6.14 Artifact / source registry

Első osztályú forrásobjektumok:

* raw paste,
* once-file import,
* local text file,
* később további artifact-fajták.

### 6.15 Action / session execution engine

Későbbi réteg.
Nem indulhat el a kognitív kapu és a permission/risk foundation előtt.

### 6.16 Permission / risk matrix

Külön, explicit rendszer a nagyobb kockázatú műveletekhez.

### 6.17 Audit / journal / replay réteg

Minden lényeges source-read, state update, döntés és végrehajtás visszanézhető kell legyen.

### 6.18 Adapter / capability layer

Az adapterek nem saját kis szigetek, hanem a központi state- és truth-modellhez kötött capability-k.

### 6.19 Event / watcher layer

Későbbi always-on irány.

### 6.20 Model-assisted cognition és A/B orchestration

* **A-modell**: interpretáció, ambiguity handling, candidate generation, extraction.
* **B-modell**: verbalization, response shaping, stílus.
* később critic/verifier is lehetséges.

### 6.21 Eval / self-check / regression intelligence

A rendszernek tudnia kell mérni magát, és merge előtt ellenőrizhetőnek kell lennie.

### 6.22 Architecture hygiene / maintenance loop

A rendszer egészének karbantarthatónak kell maradnia.
Nincs giant brain file, nincs patch-szintű káosz, nincs dokumentálatlan kerülőút.

## 7\. Fejlesztési szabály: Codex és rendszerszintű ticketek

### 7.1 A Codex szerepe

A Codex végrehajtó fejlesztő.
A North Star és a dokumentumcsomag alapján dolgozik.
Nem írhat át hallgatólagosan projektirányt.

### 7.2 Kötelező rendszerscope minden komolyabb ticketnél

Egy komolyabb ticket nem csak a látható UI vagy a közvetlen bugfix helye.
Át kell nézni az érintett:

* contracts,
* orchestration,
* persistence,
* reply,
* trace,
* CLI/operator boundary,
* docs,
* tests
  láncot.

### 7.3 Egyetlen fájl sem maradhat le

A PR summarynak és a propagation reportnak tartalmaznia kell:

* changed,
* reviewed unchanged,
* removed,
* deferred with reason
  fájlokat.

### 7.4 A lokális futás a valódi bíró

Summary sosem elég.
A merge előtti valódi bíró:

* célzott pytest,
* teljes pytest,
* compileall,
* init-db,
* trace-last,
* snapshot,
* és valós inputos smoke.

## 8\. Kötelező ticket-szabvány

Minden rendszerszintű ticketnek tartalmaznia kell legalább:

* miért ez a következő lépés,
* mi a pontos hiba vagy kapu,
* mit kell megőrizni,
* mit tilos elrontani,
* mely rétegeket kötelező átnézni,
* milyen validáció kell,
* mi az acceptance,
* milyen file-coverage map kötelező a PR végén.

## 9\. Kapus roadmap rövid kivonat

A részletes, kötelező sorrendet a **03** dokumentum rögzíti.
Itt csak a rövid, legmagasabb szintű logika szerepel.

### 9.1 Gate 0 — jelenlegi alap

A determinisztikus alaprétegek nagy része már létezik.

### 9.2 Gate 1 — REBUILD-035 és a forrásgerinc lezárása

A source/artifact registry, read-only local file bridge és audit-journal baseline.

### 9.3 Gate 2 — Interpretációs / kognitív kapu

A következő kötelező főkapu.
Zajos magyar input, multi-intent, chat-lock, anti-hijack, ack-collapse guard, style obedience, őszinte unknown handling.

### 9.4 Gate 3 — korai interpretációs modellpilot, ha szükséges

Csak akkor, ha Gate 2 determinisztikusan már tisztán fel van térképezve és a modell valóban a következő lépés.

### 9.5 Gate 4 — presence mélyítése és korai shell-hasznosság

Csak stabilabb interpretáció után.

### 9.6 Gate 5 — permissioned execution foundation

### 9.7 Gate 6 — long-horizon személyes modell és always-on rétegek

### 9.8 Gate 7 — érett multi-model orchestration

## 10\. Explicit stop-feltételek

A fejlesztésnek meg kell állnia vagy ticketet kell váltania, ha:

* a rendszer menüzni kezd a normál felszínen,
* ack-collapse lép fel ismert direkt kérdésekre,
* a style-constraint-et megsérti explicit tiltás ellenére,
* forráshonesty sérül,
* az interpretáció és a visible reply elszakad egymástól,
* az A-pilot úgy kerülne be, hogy determinisztikus maghibákat fedne el,
* a kód és a dokumentumkészlet eltér, és ez nincs feloldva.

## 11\. Explicit non-goalok jelenleg

Jelenleg nem cél még:

* a teljes shellélmény mély kidolgozása,
* write-capable action bridge,
* külső app-automáció,
* korai execution engine látványos bővítése,
* a természetes kötetlen beszélgetés problémáinak elfedése puszta stílusjavítással,
* „okosnak tűnő”, de bizonyíthatatlan működés.

## 12\. Végső rövid összefoglalás

A Syntaris végcélja egy természetes, személyes, magyarul jól működő kognitív társ-rendszer.
A rendszer központja nem a szép szöveg, hanem a megértés.

A jelenlegi állapot már nem prototípus-vázlat, de még nem általánosan stabil élő társ.
A Gate 1 forrásgerinc lezárt, merge-elt baseline.

A jelenlegi aktív főirány a Gate 2 interpretációs / kognitív kapu.

Amíg ez nincs meg, a rendszer nem léphet tovább nagyobb felszíni vagy végrehajtási ambíciók felé.

