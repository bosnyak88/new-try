# Data and Memory Governance

- Dokumentum státusz: **kanonikus memória- és adatkezelési governance**
- Dátum: **2026-03-15**
- Fő kapcsolatok: **01, 06, 07, 09, 14**

## Dokumentum célja

Ez a dokumentum szabályozza, hogyan kezel a Syntaris adatot és memóriát.
A célja, hogy a személyes rendszer ne váljon kontrollálatlan adattárrá, és ne keveredjen össze az ideiglenes állapot a stabil személyes tudással.

## 1. Alapelv

A memória nem homogén.
A különböző állításoknak, megfigyeléseknek, forrásoknak és következtetéseknek külön életciklusuk van.

## 2. Fő memóriaosztályok

### 2.1 Stable explicit memory
Olyan, explicit, viszonylag stabil információ, amely hosszabb távra releváns.
Példák:
- owner neve,
- system neve,
- projekt-alapelvek,
- tartósan fontos preferenciák,
- projekt- és pénzügyi láncok, ha ezek explicit és folyamatosan relevánsak.

### 2.2 Temporary scoped state
Rövid vagy középtávú állapot.
Példák:
- jelenlegi blocker,
- aktuális objective,
- mostani beszélgetési mód,
- közeli ideiglenes állapot.

### 2.3 Evidence-backed memory
Konkrét forráshoz kötött megfigyelés.
Csak a forrással együtt értelmezhető erősen.

### 2.4 Conclusion memory
Levezetett következtetés, amely forrásból és állapotból született.
Mindig legyen hozzá:
- forrás,
- bizonyossági szint,
- applicability kontextus.

### 2.5 Artifact-linked memory
Olyan memória vagy állapot, amely konkrét artifacthoz kapcsolódik.

### 2.6 Long-horizon personal model
Későbbi réteg.
Nem épülhet kontrollálatlanul a jelenlegi casual inputból.

## 3. Írási szabályok

### 3.1 Egyetlen laza mondatból nem lesz stabil személyes tény
A rendszer nem inferálhat tartós személyes jellemzőt egyetlen spontán casual mondatból.

### 3.2 Explicit megerősítés erősít
Az explicit, ismétlődő vagy következetesen visszatérő állítások erősíthetik a memóriát.

### 3.3 Forrás nélküli stabil memória tiltott
Ha nincs elég bizonyíték, a rendszer nem írhat stabil memóriát.

## 4. Megőrzési és TTL szabályok

### 4.1 Hosszú távon megőrzendő kategóriák
- projektláncok,
- pénzügyi/admin folytonosság,
- owner/system identitás,
- explicit, tartós projektpreferenciák.

### 4.2 Provisional / TTL kategóriák
- napi hangulat,
- átmeneti testi/lelki állapot,
- alkalmi beszélgetési rezdülések,
- nem megerősített rutinok.

### 4.3 Sensitive / review-igényes kategóriák
Bármely érzékeny, nagy hatású vagy félreértésre hajlamos személyes adat csak óvatosan és review-kompatibilisen kezelhető.

## 5. Konfliktuskezelés

Ha két memóriaelem ütközik:
- az újabb explicit és jobban bizonyított állítás erősebb lehet,
- de a régi nem törölhető néma módon trace nélkül,
- provenance-t meg kell őrizni.

## 6. Applicability szabály

Nem elég valamit tudni, azt is tudni kell, hogy:
- mikor érvényes,
- mire alkalmazható,
- meddig áll meg.

## 7. Casual beszélgetés és memória

A casual beszélgetésben elhangzó személyes tartalom nem válhat automatikusan stabil memóriává.
A rendszer feladata itt inkább:
- értelmesen reagálni,
- szükség esetén megkérdezni,
- és csak indokolt esetben erősíteni a memóriát.

## 8. Source-honesty és memória

A memory write nem írhatja felül a source-honesty elvet.
Ha egy állítás forráshoz kötött és gyenge, akkor a memória is így kell hogy őrizze.

## 9. Rövid végső összefoglalás

A Syntaris memóriája réteges, bizonyítékhoz kötött és kontrollált.
Nem cél a mindent elraktározó, ellenőrizetlen emlékezet.


## Delta Journal

- 2026-03-15 | REBUILD-036 | checked, no change | Miért: ticket nem módosította state retention/governance szabályokat.

- 2026-03-15 | REBUILD-036 finisher | checked, no change | Miért: ticket nem érintett retention/governance szabályt.
