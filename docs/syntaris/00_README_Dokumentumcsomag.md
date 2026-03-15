# Syntaris Master Dokumentációs Csomag



* Csomag státusz: **kanonikus, fejlesztést vezérlő dokumentum**
* Csomag verzió: **Master Pack v1.0**
* Dátum: **2026-03-15**
* Projekt: **Syntaris**
* Tulajdonos / owner: **Árpi**
* Dokumentumkészlet célja: **egyértelmű, teljes, visszakereshető fejlesztési irányítás**



## A csomag célja

Ez a csomag a Syntaris teljes, kanonikus, fejlesztést vezérlő dokumentumkészlete.
Nem inspirációs jegyzet, nem marketinganyag, nem laza ötletgyűjtemény, hanem a projekt elsődleges irányító csomagja.

A csomag célja, hogy:

* egy **top szintű fejlesztőcsapat** is ugyanarra az értelmezésre jusson belőle,
* a rendszer architektúrája, prioritásai, kapui, stop-feltételei és minőségi követelményei **egyértelműek** legyenek,
* a fejlesztés alatt **ne maradjon kimaradt réteg, csendes eltérés vagy félreértett szándék**,
* minden fontos állítás, döntés és munkaszabály **valamelyik kanonikus dokumentumból visszaszármaztatható** legyen.

## A csomag használati elve

A csomag nem egyetlen dokumentumból áll, mert a projekt nem egyetlen nézőpontból irányítható.
A dokumentumok együtt alkotnak teljes rendszert.

A csomag tudatosan külön választja szét:

* a **víziót és alapelveket**,
* a **kognitív architektúrát**,
* a **kapus roadmapet**,
* a **jelenlegi állapotot**,
* a **támogatott képességeket**,
* a **döntésnaplót**,
* a **kanonikus contractokat és sémákat**,
* a **rendszertérképet**,
* a **mérőszámokat és küszöböket**,
* a **runbookot**,
* a **memóriakormányzást**,
* és a **terminológiát**.

## Dokumentum-precedencia és tekintélyrend

Ha két dokumentum között látszólag feszültség van, az alábbi tekintélyrend dönt:

1. **01\_Syntaris\_North\_Star\_v4.md** — a projekt identitása, alapelvei, tiltásai és fő célja.
2. **03\_Syntaris\_Kapus\_Roadmap\_es\_Kilepesi\_Feltetelek\_v1.md** — a kötelező sorrend, a kapuk és a stop-feltételek.
3. **06\_Current\_State\_Matrix.md** — a pillanatnyi rendszerállapot kanonikus képe.
4. **07\_Capability\_Catalog\_v1.md** — mi támogatott most, mi részleges, mi tiltott, mi későbbi.
5. **09\_Canonical\_Contracts\_and\_Schemas.md** — a semantikai contractok és állapotmezők.
6. **14\_Terminology\_and\_Naming\_Standard.md** — a fogalmak végső jelentése és elnevezési szabálya.
7. A többi dokumentum ezek részletező, operatív vagy kapcsolódó nézőpontja.

## Dokumentumlista és szerepek

### 00\_README\_Dokumentumcsomag.md

A csomag indexe, használati rendje, precedenciája és karbantartási szabályai.

### 01\_Syntaris\_North\_Star\_v4.md

A legmagasabb szintű irányadó dokumentum.
Leírja, mi a Syntaris, mi nem, milyen alapelvekre épül, milyen minőségi mércéje van, és milyen kapuk mentén fejlődhet.

### 02\_Syntaris\_Kognitiv\_Architektura\_v1.md

A kognitív feldolgozás külső és belső modellje.
Leírja a valós inputprofilt, a turn-feldolgozási ciklust, a belső védelmeket, a modellek helyét és az interpretációs kapu technikai mélységét.

### 03\_Syntaris\_Kapus\_Roadmap\_es\_Kilepesi\_Feltetelek\_v1.md

A fejlesztés kötelező sorrendje.
Leírja, melyik kapu után mi jöhet, minek mi az exit criteria-ja, és mit tilos előrébb hozni.

### 04\_Syntaris\_Runtime\_es\_Eroforras\_Profil\_v1.md

A referencia hardverprofil, RAM/CPU/GPU szerepek, hot/warm/cold munkatérmodell, teljesítmény-szemlélet és a referencia runtime környezet.

### 05\_Syntaris\_Validacios\_es\_Golden\_Scenario\_Protokoll\_v1.md

A validáció kanonikus rendje.
Leírja a fresh-run szabályt, a valós inputos körök jelentőségét, a merge-stop hibákat, a smoke-logikát és a golden scenario családokat.

### 06\_Current\_State\_Matrix.md

A jelenlegi rendszerállapot élő mátrixa.
Ez mondja ki, hogy mi merged, mi partial, mi aktív, mi blokkoló ismert hiba, és épp melyik kapu az aktív.

### 07\_Capability\_Catalog\_v1.md

A képességkatalógus.
Pontosan felsorolja, hogy a rendszer jelenleg mit tud, mit részlegesen tud, mit nem tud még, és mit tilt a projekt.

### 08\_Architecture\_Decision\_Record\_Log.md

A fő architekturális döntések kanonikus naplója.
Minden olyan döntés ide kerül, amely hosszabb távon irányt szab a rendszernek.

### 09\_Canonical\_Contracts\_and\_Schemas.md

A semantikai contract- és sémaanyag.
Ez a dokumentum mondja meg, milyen állapotoknak, mezőknek és logikai egységeknek kell létezniük, akkor is, ha a konkrét kódbeli mezőnevek eltérnek.

### 10\_System\_Map\_and\_Dependency\_Guide.md

A rendszertérkép és a dependency guide.
Leírja, melyik réteg micsoda, mi hívhat mit, és mit tilos megkerülni.

### 11\_Eval\_Scorecard\_and\_Thresholds.md

A mérési rendszer.
Megadja a minőségi scorecardot, a gate-szintű küszöböket, a piros vonalakat és azt, hogy mikor számít egy képesség valószínűleg átmentnek.

### 12\_Runbook\_Validation\_and\_Reproduction.md

Az operátori és fejlesztői runbook.
Leírja a friss validációs köröket, a reprodukciós menetet, a logrögzítést és a PR-validáció kézi lépéseit.

### 13\_Data\_and\_Memory\_Governance.md

A memória- és adatkezelési kormányzás.
Pontosan szabályozza a memóriafajtákat, az írási / megerősítési / TTL / felülírási és érzékenységi szabályokat.

### 14\_Terminology\_and\_Naming\_Standard.md

A fogalomtár és névszabvány.
Lezárja a projekt kulcsfogalmait és a belső elnevezési szabályokat.

### 15\_Traceability\_Map.md

A követelmény-visszavezetési térkép.
Megmutatja, hogy a projekt fő követelményei és döntései mely dokumentumokban és melyik fejezetekben vannak rögzítve.

## Melyik kérdésre melyik dokumentum válaszol?

### „Mi a Syntaris végső célja?”

Olvasd: **01**

### „Milyen sorrendben szabad fejleszteni?”

Olvasd: **03**

### „Most ténylegesen hol tart a rendszer?”

Olvasd: **06**

### „Mit támogat jelenleg a rendszer és mi csak terv?”

Olvasd: **07**

### „Mi a hivatalos jelentése a workframe / thread / artifact / evidence kifejezéseknek?”

Olvasd: **14**, majd szükség esetén **09**

### „Mik a kötelező state-ek, trace-elemek, snapshot-összetevők?”

Olvasd: **09**

### „Miért ilyen a gate sorrend?”

Olvasd: **03**, majd **08**

### „Melyik modul miért felel és mi hívhat mit?”

Olvasd: **10**

### „Mi a referencia hardver és runtime szemlélet?”

Olvasd: **04**

### „Milyen validáció kell merge előtt?”

Olvasd: **05**, majd **12**

### „Milyen memória írható, mikor, mennyi időre, milyen bizonyíték kell hozzá?”

Olvasd: **13**

### „Milyen minőségi küszöb kell Gate 2 kilépéséhez?”

Olvasd: **11**, majd **03**

## Kötelező fejlesztési fegyelem

### 1\. Nincs hallgatólagos eltérés

Ha a kód, a dokumentáció és a validáció eltér egymástól, azt explicit módon fel kell oldani.
Nincs olyan, hogy „majd később dokumentáljuk”.

### 2\. A Codex nem csak kódot ír

A Codexnek és minden automatizált fejlesztési körnek kötelezően vezetnie kell a living docokat és az érintett kanonikus anyagokat.

### 3\. Minden rendszerszintű merge után kötelező frissíteni

Legalább az alábbiakat, ha érintettek:

* **06\_Current\_State\_Matrix.md**
* **07\_Capability\_Catalog\_v1.md**
* **08\_Architecture\_Decision\_Record\_Log.md**
* **09\_Canonical\_Contracts\_and\_Schemas.md**
* **10\_System\_Map\_and\_Dependency\_Guide.md**
* **11\_Eval\_Scorecard\_and\_Thresholds.md**
* **12\_Runbook\_Validation\_and\_Reproduction.md**
* **13\_Data\_and\_Memory\_Governance.md**
* **14\_Terminology\_and\_Naming\_Standard.md**

### 4\. Egy PR nem kész, ha a dokumentumok nincsenek szinkronban

Egy rendszerszintű PR akkor tekinthető késznek, ha:

* a kód átmegy a kötelező validáción,
* a releváns dokumentumok frissültek,
* a State Matrix és a Capability Catalog pontos,
* az ADR log tartalmazza a döntés szintjéhez tartozó bejegyzést,
* és nincs néma hiány a dokumentációs láncban.

## Karbantartási modell

### Living docs

Az alábbi dokumentumok kötelezően élőek:

* 06\_Current\_State\_Matrix.md
* 07\_Capability\_Catalog\_v1.md
* 08\_Architecture\_Decision\_Record\_Log.md
* 11\_Eval\_Scorecard\_and\_Thresholds.md
* 12\_Runbook\_Validation\_and\_Reproduction.md

### Ritkábban változó, de kanonikus dokumentumok

* 01\_Syntaris\_North\_Star\_v4.md
* 02\_Syntaris\_Kognitiv\_Architektura\_v1.md
* 03\_Syntaris\_Kapus\_Roadmap\_es\_Kilepesi\_Feltetelek\_v1.md
* 04\_Syntaris\_Runtime\_es\_Eroforras\_Profil\_v1.md
* 05\_Syntaris\_Validacios\_es\_Golden\_Scenario\_Protokoll\_v1.md
* 09\_Canonical\_Contracts\_and\_Schemas.md
* 10\_System\_Map\_and\_Dependency\_Guide.md
* 13\_Data\_and\_Memory\_Governance.md
* 14\_Terminology\_and\_Naming\_Standard.md

## Jelenlegi kanonikus állapot röviden

A dokumentumcsomag jelenlegi állítása szerint:

* a **determinista alaprétegek nagy része már létezik**,
* a Gate 1 (REBUILD-035 / 035b / 035c) lezárt, merge-elt baseline,
* a jelenlegi aktív főirány a Gate 2 interpretációs / kognitív kapu,
* a rendszer **nem tekinthető általánosan stabil, szabad kötetlen live beszélgető rendszernek**,
* a jelenlegi live casual hibák valósak és dokumentáltak,
* az **A-oldali pilot** csak akkor nyitható meg, ha Gate 2 determinisztikusan már tisztán feltérképezett és bizonyítottan a modell adja a következő szükséges ugrást,
* és az A-oldali pilot **nem fedhet el determinisztikus maghibákat**.

## Rövid végső összefoglalás

Ez a csomag a Syntaris fejlesztésének hivatalos, kanonikus, teljes dokumentációs magja.
A célja nem az, hogy rövid legyen, hanem az, hogy fejlesztés közben se kelljen találgatni.

Ha kérdés merül fel a fejlesztés során, a kérdésre a csomagon belül valahol lennie kell válasznak.
Ha nincs, akkor a csomag még nem teljes — és frissíteni kell.

