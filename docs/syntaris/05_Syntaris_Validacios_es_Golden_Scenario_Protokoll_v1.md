# Syntaris validációs és golden scenario protokoll v1

- Dokumentum státusz: **kanonikus validációs protokoll**
- Verzió: **v1**
- Dátum: **2026-03-15**
- Fő kapcsolatok: **01, 03, 06, 11, 12**

## Dokumentum célja

Ez a dokumentum rögzíti, mi számít érvényes validációnak a Syntarisnál.
A fő cél, hogy a rendszer ne summary alapján tűnjön jónak, hanem valós futáson is megfeleljen.

## 1. Alapelv

A Syntarisnál a valódi bíró nem a PR summary, hanem a lokális futás és a valós log.

## 2. Validációs piramis

### 2.1 Determinisztikus unit / integration regresszió
A family- és invariáns alapú tesztek.
Kötelező, de önmagában nem elég.

### 2.2 Célzott smoke kör
Az adott tickethez kötött kézi és félautomata forgatókönyvek.

### 2.3 Teljes tesztkör
Teljes pytest, compileall, init-db.

### 2.4 Valós emberi inputos kör
A steril promptokon túlmenő, természetes, zajos, emberi nyelvű teszt.
Gate 2-től kezdve kötelező stratégiai validációs réteg.

### 2.5 Kanonikus fresh-run / reset eljárás
Ez az egyetlen hivatalos tiszta kör:
1. új temp DB path,
2. új temp sandbox roots,
3. init-db,
4. csak ezután smoke és live kör.

A validáció **nem** épülhet bizonytalan clean-run helperre, ha annak léte vagy viselkedése nem igazolt az adott branchben.

## 3. Kötelező validációs elvek

### 3.1 Truth-first validáció
A validációnak külön figyelnie kell arra, hogy:
- nem használt-e a rendszer régi forrást aktuálisnak álcázva,
- nem állít-e többet, mint amit tud,
- nem driftel-e a trace és a reply.

### 3.2 No silent drift validáció
Minden komolyabb változásnál nézni kell:
- state,
- trace,
- reply,
- docs,
- capability claim,
- current state matrix,
- file coverage map
konzisztenciáját.

### 3.3 Real-language validáció
Nem elég a mesterséges, rövid, tiszta tesztmondat.
A rendszernek valódi, emberi, hibás, kevert inputon is vizsgálhatónak kell lennie.

### 3.4 Surface honesty
Ha a user egyszerű reakciót kér, a rendszer nem csúszhat át strukturált technikai sablonba.

## 4. Golden scenario családok

### 4.1 Casual emberi beszélgetés
Különösen olyan inputok, mint:
- „most ne dolgozzunk, csak beszélgessünk egy kicsit”,
- „nem kérek listát, csak reagálj normálisan”,
- „kicsit fáradt vagyok”,
- „nem is tudom pontosan mit akarok most”.

### 4.2 Mixed-mode turn
Egyetlen turnben több szándék:
- kérdés + állapotjelzés + bizonytalanság + workframe-váltás.

### 4.3 Identity / relationship
Owner / system név, szerep, kapcsolat, és ennek state/trace koherenciája.

### 4.4 Recall / previous-thread / compare
Előző szál, összehasonlítás, visszatérés, thread continuity.

### 4.5 Evidence ingest és forráshonesty
Sikeres ingest, sikertelen ingest, current vs historical source, explicit historical reuse.

### 4.6 Style-constraint obedience
Az explicit stíluskérés kötelező megtartása.
Példa:
- ne listázz,
- ne bontsd biztos/bizonytalanra,
- röviden,
- csak reagálj.

### 4.7 Unknown handling
Ha valami nem ismert vagy nincs elég adat, a rendszer őszintén mondja ki.

### 4.8 Fáradt / reflektív / személyes input
A rendszer ne technikai sablonnal reagáljon személyes, reflektív közlésre.

### 4.9 Zajos magyar input
Elütések, rossz toldalék, hiányos mondat, hirtelen váltás.

### 4.10 Voice-szerű input előkészítő szcenáriók
Félig írott, beszédszerű, töredezett, gyors inputminták.

## 5. Merge előtti minimális kapu

Minimum szükséges:
- célzott pytest,
- releváns regressziók,
- teljes pytest,
- compileall,
- init-db,
- célzott smoke,
- szükség esetén live kör,
- trace-last,
- snapshot,
- és teljes log visszaadása értékelésre.

## 6. Mi számít piros zászlónak

Merge-stop hibák például:
- ack-collapse direkt kérdésekre,
- explicit style-constraint megsértése,
- source-honesty sérülés,
- current/historical source csere explicit jelzés nélkül,
- chat-lock elvesztése egyértelmű user-kérés ellenére,
- route-nevek vagy menüzés kiszivárgása a felszínre,
- reply és state/trace jelentős szétcsúszása.

## 7. Mit kell külön mérni az interpretációs kapunál

### 7.1 Nem elég a family-tesztek zöldsége
A Gate 2-nél a steril family-tesztek önmagukban nem elegendők.

### 7.2 Kötelező élő próbakategóriák
- casual chat,
- mixed-mode input,
- noisy HU input,
- style-constraint obedience,
- unknown handling,
- personal / reflective input,
- direct question robustness.

### 7.3 Pass / fail logika
Gate 2 akkor tekinthető átmentnek, ha:
- a scorecard fő mutatói a küszöb fölött vannak,
- a valós live körök nem mutatnak rendszeres ack-loopot vagy sablonhijacket,
- és a dokumentált red-line hibák nincsenek jelen.

## 8. Dokumentációs és PR-fegyelem

Minden rendszerszintű PR-hez kell:
- pontos summary,
- validációs parancslista,
- teljes log,
- file-coverage map,
- és a living docs frissítése.

## 9. Rövid végső összefoglalás

A Syntarisnál a validáció nem egy zöld pipa, hanem több rétegű bizonyítás.
A rendszer akkor érett, ha a kód, a trace, a state, a docs és a valós inputos működés együtt állnak össze.
