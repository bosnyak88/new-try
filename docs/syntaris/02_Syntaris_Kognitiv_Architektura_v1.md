# Syntaris kognitív architektúra v1

- Dokumentum státusz: **kanonikus architektúra-specifikáció**
- Verzió: **v1**
- Dátum: **2026-03-15**
- Fő kapcsolatok: **01, 03, 05, 09, 10, 11, 13, 14**

## Dokumentum célja

Ez a dokumentum a Syntaris kognitív magjának működési modelljét írja le.
A célja nem az, hogy a konkrét kódszerkezetet lemásolja, hanem az, hogy a fejlesztőcsapat számára egyértelművé tegye:
- milyen inputprofilra kell tervezni,
- milyen többlépcsős feldolgozás szükséges,
- milyen belső védelmek kötelezőek,
- hol jöhet be később modellréteg,
- és milyen kognitív minőség számít „átmentnek”.

## 1. A valós inputprofil

A Syntaris nem steril, egyértelmű, jól formázott promptokra készül.
A valós inputprofil jellemzői:
- napi több ezer mondat vagy mondatpár,
- gyakori hosszú monológok,
- beszélgetés / munka / ötlet / kérdés / emlékezés / panasz / önreflexió keveredése,
- gyakori hirtelen téma- vagy workframe-váltás,
- hibás mondatszerkezet,
- elütések,
- hiányos szavak,
- rossz toldalékok,
- emberi gépelési hibák,
- félbehagyott gondolatok,
- utalás egy korábbi szálra explicit címkézés nélkül,
- később hangvezérlésből érkező, még zajosabb, átirattá alakított input.

A rendszernek erre kell optimalizálnia, nem steril tesztmondatokra.

## 2. A felszín és a belső működés szétválasztása

### A felszínen elfogadható
- természetes válasz,
- rövid állapotjelzés, ha a feldolgozás tényleg zajlik,
- rövid tisztázó kérdés, ha valóban kell,
- workframe-hez illeszkedő stílus,
- őszinte „nem értem eléggé” vagy „ebből ennyit látok biztosan”.

### A felszínen nem elfogadható
- belső menüzés,
- pipeline-lépések kiírása,
- route-nevek,
- technikai magyarázkodás,
- certainty/evidence sablon olyan helyzetben, amikor a user egyszerű reakciót vagy beszélgetést kért,
- generikus ack-only válasz, például „Rendben.” direkt kérdésre.

## 3. A külső turn-feldolgozási ciklus

A rendszer minden turnt legalább az alábbi logikai szakaszok mentén kell hogy feldolgozzon.
A konkrét implementáció lehet optimalizáltabb vagy részben összevont, de a funkcionális tartalomnak léteznie kell.

### 3.1 Input capture és normalizálás
Feladata:
- a nyers input átvétele,
- whitespace és alap normalizáció,
- ékezet / elütés / szokatlan íráskép robusztus kezelése,
- egyszerű formai jelzések leválasztása,
- szükség esetén nyelvi jelleg felismerése.

Követelmény:
A normalizálás nem szabad, hogy elveszítse a user szándékát vagy stíluskérését.

### 3.2 Utterance-segmentation és több szándék előkészítése
Feladata:
- egy hosszú üzenetből több lehetséges egység azonosítása,
- felismerni, ha egy turnön belül több szándék van,
- megőrizni, hogy ezek ugyanazon nagyobb turn részei.

Példa:
„fáradt vagyok, de közben kíváncsi is, hol tartasz, és igazából csak beszélgetnék”
— ebben lehet egyszerre:
- személyes állapotjelzés,
- státuszkérdés,
- workframe-kérés.

### 3.3 Jelkinyerés
Feladata:
- workframe-jelzések,
- thread-utalások,
- forrásutalások,
- stíluskérések,
- identity / relationship jelzések,
- explicit tiltások,
- időhivatkozások,
- döntési bizonytalanság,
- kérdésjelleg,
- érzelmi vagy reflektív súly jelenlétének felismerése.

Követelmény:
Jel nem egyenlő route-tal.
A rendszernek nem szabad egyetlen szó alapján vakon rossz family-be ugrania.

### 3.4 Workframe-jelöltek előállítása
Lehetséges workframe-jelöltek például:
- casual_chat,
- focused_work,
- recall,
- compare,
- evidence_intake,
- source_query,
- planning,
- maintenance,
- identity_relationship,
- decision_support,
- mode_control.

Követelmény:
Nem egyetlen „mód” van mindig, hanem jelöltek és prioritás.

### 3.5 Thread-jelöltek előállítása
A rendszernek meg kell próbálnia eldönteni:
- ez a jelenlegi szál folytatása,
- visszautalás előző szálra,
- új szál nyitása,
- kevert vagy bizonytalan helyzet.

Követelmény:
A thread-szelekció nem írhatja felül a user explicit workframe-kérését.
Egy „szia” vagy „csak beszélgessünk” nem kényszeríthető rá automatikusan egy régi munkaszálra.

### 3.6 Memória- és evidence-visszakeresés
A rendszernek el kell dönteni, hogy mihez kell visszanyúlnia:
- current thread state,
- prior thread,
- stable memory,
- temporary state,
- current source artifact,
- historical artifact,
- conclusion / applicability réteg.

Követelmény:
A keresésnek forráshűnek kell maradnia.
Nem használhat történeti evidenciát aktuálisnak álcázva.

### 3.7 Problémabontás
A rendszernek fel kell bontania a user-turnt legalább az alábbi szempontok mentén:
- mit akar most valójában,
- mire reagálni kell közvetlenül,
- mi csak háttérinformáció,
- van-e hiányzó adat,
- kell-e tisztázó kérdés,
- van-e explicit formai kérés,
- mi a legfontosabb azonnali válaszmag.

### 3.8 Candidate-pack és prioritásos döntés
A kognitív mag itt állítja elő a lehetséges értelmezések csomagját.
Ez tartalmazhat:
- workframe-jelöltet,
- thread-jelöltet,
- releváns state-elemeket,
- style-constraint-eket,
- required source / evidence kontextust,
- prioritási javaslatot.

A döntés célja nem a tökéletes bizonyosság, hanem a legjobb, ellenőrizhetően indokolt irány kiválasztása.

### 3.9 Self-check / contradiction check / retry
Kötelező belső kontroll:
- sért-e explicit user-kérést,
- sért-e source-honesty szabályt,
- ellentmond-e a jelenlegi state-nek,
- túl gyenge vagy túl általános-e a választerv,
- ack-collapse felé tart-e,
- téves sablonhijack történt-e,
- érdemes-e másik jelöltet elővenni.

Ha az első döntés nyilvánvalóan rossz, a rendszernek másik utat kell keresnie.

### 3.10 Response plan
A response plan a felszíni válasz mögötti szerkezet.
Legalább ezekről kell tudnia:
- melyik workframe szerint válaszol,
- mi a direct answer mag,
- milyen stílus / forma kötelező,
- kell-e kérdezni,
- kell-e forráshivatkozási különbségtétel,
- kell-e rövid állapotjelző,
- frissül-e valamilyen state.

### 3.11 Verbalization
A verbalization célja nem a logika megismétlése, hanem a természetes felszín előállítása.
A verbalizationnak tiszteletben kell tartania:
- a user explicit formakérését,
- a workframe-et,
- a bizonytalansági szintet,
- a forráshonesty-t,
- és azt, hogy a felhasználó nem belső taxonómiát akar látni.

### 3.12 State update, audit és trace
A turn végén a rendszernek:
- frissítenie kell a releváns state-eket,
- el kell mentenie a szükséges trace-t,
- auditálnia kell a source / artifact műveleteket,
- és konzisztenst kell maradnia a visible reply-jal.

## 4. A fontos belső védelmek

### 4.1 Chat-mode lock / persistence
Ha a user expliciten azt kéri, hogy csak beszélgetni akar, vagy nem akar strukturált választ, ezt nem szabad egyetlen következő turnben elveszíteni.

Követelmény:
- a chat-lock ideiglenesen erősebb legyen, mint a gyenge munkaszál-visszahúzás,
- az explicit formai tiltás megmaradjon,
- a casual workframe-et csak erős új jel törhesse meg.

### 4.2 Anti-hijack guard
A rendszer nem csúszhat rossz sablonba csak azért, mert meglát egy szót, például:
- „biztos”,
- „most”,
- „fontos”,
- „emlékszel”.

Követelmény:
A lokális szótrigger nem írhatja felül az egész turn jelentését.

### 4.3 Ack-collapse guard
Direkt kérdésekre nem szabad puszta „Rendben.” vagy hasonló tartalom nélküli nyugtázással válaszolni.

Merge-stop kategóriás hiba, ha a rendszer ismert, direkt, válaszolható kérdésekre üres ackba omlik.

### 4.4 Explicit formakérés elsőbbsége
Ha a user azt mondja:
- ne listázz,
- ne bontsd biztos/bizonytalanra,
- röviden mondd,
- csak reagálj normálisan,
akkor ez elsőbbséget élvez a default sablonokkal szemben.

### 4.5 Őszinte nem-értés
Ha a rendszer nem érti eléggé a user-turnt, jobb egy őszinte, rövid bizonytalanságjelzés, mint egy magabiztos félreértés.

## 5. A munkamemória és az erőforrás-modell

### 5.1 Miért kell RAM
A többlépcsős interpretációhoz forró munkatér kell, ahol ideiglenesen tartható:
- az aktuális turn bontása,
- a candidate-pack,
- a workframe-jelöltek,
- a thread-jelöltek,
- a style-constraint-ek,
- az ideiglenes döntések,
- a self-check eredményei.

### 5.2 Miért kell CPU
A determinisztikus orchestration, a state- és evidence-visszakeresés, a scoring, az audit és a self-check CPU-intenzív lehet, különösen sok rövid turn esetén.

### 5.3 Miért kell GPU
A későbbi modellréteghez kell:
- interpretációs segítség,
- ambiguity handling,
- candidate generation,
- verbalization.

### 5.4 Nem minden él RAM-ban
A hot/warm/cold modell kötelező:
- hot: aktuális turn és közeli aktív munkatér,
- warm: thread-indexek, summaries, gyorsan visszahívható state,
- cold: archív artifactok és nyers logok.

## 6. Hol jön be a modellréteg

### 6.1 Mi várható el modell nélkül
Modellek nélkül is elvárható:
- a determinisztikus truth-first működés,
- a thread / workframe / evidence alapszintű fegyelme,
- a style-constraint megtartása ismert family-kben,
- a forráshonesty,
- a nem-hazudó fallback.

### 6.2 Mi az, ami modell nélkül várhatóan gyenge marad
Valószínűleg gyenge marad modell nélkül:
- erősen zajos, többértelmű, hosszú magyar input,
- finom multi-intent kibontás,
- reflektív, félig kimondott szándékok felismerése,
- kötetlen beszélgetés természetessége,
- nagy változatosságú stílus- és kontextusváltás.

### 6.3 Miért nem szabad ettől függetlenül elengedni a magot
Az A- vagy B-modell nem javíthatja ki azt, ami a determinisztikus magban elromlott.
A következő hibák maghibák, nem modellhiány:
- chat-lock elvesztése,
- explicit tiltás megsértése,
- ack-collapse,
- forráshonesty sérülés,
- current/historical source összemosása,
- reply és trace/state drift.

### 6.4 A korai A-oldali pilot feltétele
A korai A-oldali pilot csak akkor nyitható meg, ha:
- a Gate 2 problématér determinisztikusan már jól fel van térképezve,
- a fő maghibák külön vannak választva a valódi interpretációs plafontól,
- és a pilot kifejezetten az interpretációs ugrás mérésére szolgál.

A pilot **nem** használható arra, hogy a determinisztikus maghibákat elfedje.

## 7. Mi számít átment interpretációnak

A kognitív kapu akkor tekinthető közel átmentnek, ha a rendszer:
- zajos magyar input mellett sem omlik össze,
- egy turnön belül több szándékot is kezelni tud,
- jól tartja a chat/workframe állapotot,
- nem menüzik ki a belső logikát,
- explicit formakérést megtart,
- direkt kérdésekre nem ack-loopozik,
- tud őszintén bizonytalannak lenni,
- és valós inputon jobban teljesít, mint steril family-promptokon kívül.

## 8. Mit nem szabad összekeverni

### Nem ugyanaz
- a szép felszíni válasz és a valódi megértés,
- a modell által produkált jobb megfogalmazás és a helyes workframe-választás,
- a régi thread visszahívása és a helyes current-thread megtartása,
- a structured evidence answer és a casual beszélgetés,
- a „van valamilyen válasz” és az „őszintén jó válasz”.

## 9. Rövid végső összefoglalás

A Syntaris kognitív architektúrája többlépcsős, zajtűrő, önellenőrző rendszerként van megcélozva.
A user ebből ideálisan csak természetes felszínt lát.

A következő nagy fejlesztési fókusz nem a shell és nem az execution, hanem az, hogy ez a kognitív lánc valós, emberi, hibás, kevert magyar inputon is stabilabbá váljon.
