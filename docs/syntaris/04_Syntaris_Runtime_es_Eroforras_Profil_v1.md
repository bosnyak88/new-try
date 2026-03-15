# Syntaris runtime és erőforrás profil v1

- Dokumentum státusz: **kanonikus referencia runtime-profil**
- Verzió: **v1**
- Dátum: **2026-03-15**
- Fő kapcsolatok: **01, 02, 03, 10, 12**

## Dokumentum célja

Ez a dokumentum leírja, milyen referencia hardver- és runtime szemléletre épül jelenleg a Syntaris.
Nem örök, platformfüggetlen igazság, hanem a projekt jelenlegi realitásához kötött irányadó profil.

## 1. Jelenlegi referencia hardverprofil

### Jelenlegi ismert irány
- GPU: **RTX 4060 8 GB VRAM**
- RAM: jelenleg **16 GB**, bővíthető **32 GB** vagy **64 GB** felé
- CPU: a projekt jelenlegi céljaihoz **erős, elegendő kategóriájú**
- Helyi modell indulópont: **8B osztály**, mert ez reálisan illeszkedik a 4060 8 GB-hoz

### Következtetés
A referencia profil nem enterprise clusterre, hanem erős, lokális, személyes futtatásra van szabva.

## 2. Miért nem mindegy a hardver elosztása

A Syntarisnál nem elég azt mondani, hogy „van egy modell”.
A rendszer több komponensből áll:
- determinisztikus orchestration,
- memory/state kezelés,
- source/artifact munka,
- később modellinferencia,
- később voice és folyamatosabb háttérterhelés.

Ezért külön kell kezelni a RAM, CPU és GPU szerepét.

## 3. A RAM szerepe

### 3.1 Mire kell a RAM
A RAM nem csak adatcache, hanem aktív munkatér.
Kell a következőkhöz:
- hot state,
- turn közbeni candidate-pack,
- multi-intent bontási eredmények,
- thread-jelöltek,
- workframe-jelöltek,
- gyors indexek,
- warm summaries,
- artifact metadata cache,
- később voice és model orchestration kiegészítő állapotai.

### 3.2 Miért lesz egyre fontosabb
Ahogy nő:
- a source/artifact réteg,
- a több turnös state,
- a journaling,
- a többmodellos pipeline,
az igény RAM-ra is nő.

### 3.3 Gyakorlati ajánlás
- **16 GB**: elindulásra használható, de hamar szűk lehet.
- **32 GB**: egészségesebb középtávú cél a kognitív és source rétegekhez.
- **64 GB**: kényelmesebb hosszú távú fejlesztői és always-on irányhoz.

## 4. A CPU szerepe

### 4.1 Mire kell a CPU
A CPU végzi a legtöbb determinisztikus munkát:
- normalizálás,
- segmentation,
- candidate scoring,
- state lookup,
- trace és audit írás,
- artifact indexelés,
- refusal guardok,
- self-check,
- maintenance,
- validációs futások jelentős része.

### 4.2 Következmény
A CPU nem háttérszereplő. 
A Syntarisnál a CPU a kognitív gerinc egyik fő futtatótere.

## 5. A GPU szerepe

### 5.1 Mire kell a GPU
A GPU elsősorban a modellréteghez kell:
- interpretációs segítség,
- ambiguity handling,
- candidate generation,
- verbalization,
- később critic/verifier vagy más model-assisted lépések.

### 5.2 Miért 8B a jelenlegi indulópont
Az RTX 4060 8 GB miatt a 8B körüli modellméret a reális első állomás.
Ez nem azért van, mert ez a végső plafon, hanem mert ez illeszkedik jelenleg a helyi géphez.

### 5.3 Miért nem szabad mindent a modellre tolni
A GPU és a modell nem oldhatja meg:
- a rossz memory governance-t,
- a hibás workframe-kezelést,
- a forráshonesty sérülést,
- az ack-collapse problémát,
- a dokumentációs driftet.

## 6. Hot / warm / cold adatmodell

### 6.1 Hot layer
Azonnal szükséges, gyorsan változó munkatér:
- current turn,
- response planning state,
- candidate-pack,
- aktív workframe,
- közeli thread-context,
- rövid életű kontrollállapotok.

### 6.2 Warm layer
Gyorsan visszahívható, de nem minden turnben teljesen aktív:
- thread summaries,
- artifact indexek,
- recent source metadata,
- current objective/blocker state,
- relevant conclusions és applicability elemek.

### 6.3 Cold layer
Háttértáron élő, ritkábban előhívott rétegek:
- nyers logok,
- archív artifactok,
- történeti auditok,
- későbbi hosszú távú személyes memória.

## 7. Teljesítmény és felhasználói élmény

A felhasználó számára az a jó élmény, ha:
- a rendszer nem tűnik lomha vagy széteső pipeline-nak,
- a háttérkomplexitás nem ömlik rá,
- szükség esetén adhat rövid „gondolkodás folyamatban” jelzést,
- de nem menüzik és nem technikai dumpol.

A fő elv:
**a belső komplexitás nőhet, a felszíni terhelés nem.**

## 8. Voice és jövőbeli terhelés

A későbbi hangvezérlés és hangalapú interakció:
- még több inputot,
- még több zajt,
- még több félbehagyott vagy spontán szöveget,
- és potenciálisan fordítási / átirati réteget is hoz.

Ez különösen növeli majd:
- a RAM-igényt,
- a CPU terhelést,
- és a modellréteg hasznosságát.

Voice azonban nem lehet mentség arra, hogy az alap interpretációs kapu most gyenge maradjon.

## 9. Ajánlott működési szemlélet

### 9.1 Mostani reális cél
Stabil, lokális, determinisztikus mag + reális helyi modellpilot.

### 9.2 Későbbi skálázás
A skálázás ne csak nagyobb modellből álljon.
Legalább ilyen fontos:
- jobb orchestration,
- jobb memory governance,
- jobb caching,
- jobb artifact/source indexelés,
- és tiszta gate-elés.

### 9.3 Fontos alapelv
A hardver nem tervezési pótlék.
Az erőforrások segítik a rendszert, de a rossz architektúrát nem teszik jóvá.

## 10. Rövid végső összefoglalás

A jelenlegi referencia profil egy erős, lokális, 8B-osztályú induló rendszerre épül.
A CPU a determinisztikus maghoz kell, a RAM a többrétegű munkatérhez és state-hez, a GPU a modellréteghez.

Középtávon a 32 GB RAM erősen ajánlott, hosszabb távon a 64 GB kényelmesebb.
A rendszer fejlődésének fő gátja azonban jelenleg nem a puszta hardver, hanem az interpretációs és kognitív kapu minősége.
