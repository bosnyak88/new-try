# Terminology and Naming Standard

- Dokumentum státusz: **kanonikus fogalomtár és névszabvány**
- Dátum: **2026-03-15**
- Fő kapcsolatok: **01, 09, 10, 13**

## Dokumentum célja

Ez a dokumentum lezárja a projekt kulcsfogalmait és elnevezési szabályait.
Célja, hogy ugyanaz a szó mindenhol ugyanazt jelentse.

## 1. Fő fogalmak

### Owner
A rendszer emberi tulajdonosa és elsődleges felhasználója.
Jelenlegi projektkörnyezetben: Árpi.

### System / Syntaris
A fejlesztett személyes kognitív társ-rendszer.

### Turn
Egy bemeneti egység és az ahhoz tartozó teljes feldolgozás.

### Utterance unit
A turnön belüli kisebb értelmezési egység.

### Thread
Egy folytonos témaszál vagy munkaszál.

### Workframe
Annak a típusa, ami épp történik: chat, munka, recall, compare, stb.

### Current source
Az a forrás vagy artifact, amelyből a rendszer most aktívan dolgozik.

### Historical source
Korábbi forrás, amelyhez explicit vagy indokolt módon nyúl vissza.

### Artifact
Első osztályú forrásobjektum, azonosítóval és metadata-val.

### Evidence
A forráshoz köthető, alátámasztható anyag.

### Grounded claim
Forrásból közvetlenül alátámasztható állítás.

### Inferred claim
Következtetett állítás.

### Conclusion
Levezetett következtetés, applicability-vel együtt értelmezve.

### Applicability
Annak megjelölése, hogy egy conclusion milyen kontextusban használható.

### Chat-lock
Ideiglenes erősítés arra, hogy a casual/workframe ne csússzon vissza másik módba.

### Anti-hijack guard
Védelem a téves sablonhijack ellen.

### Ack-collapse
Az a hibaminta, amikor a rendszer tartalom helyett üres nyugtázásba omlik.

### Truth-first
A rendszer csak annyit állít, amennyi indokolt.

## 2. Elnevezési szabályok

### Dokumentumnevek
- számozott prefix,
- beszédes név,
- szükség esetén verzió,
- ékezet megengedett a dokumentumcímben, fájlnévben lehetőleg konzisztens magyar/ASCII kompromisszum.

### Capability-nevek
Legyenek rövidek, konkrétak és státuszozhatók.
Példa: `Current source visibility`, `Chat-lock persistence`.

### Gate-nevek
Mindig `Gate N` formában jelenjenek meg, rövid funkcióleírással.

### ADR-ek
Mindig `ADR-XXX` mintát kövessenek.

## 3. Tiltott homályos elnevezések

Kerülendő:
- „agy”, ha nem világos, melyik rétegről van szó,
- „memória” pontosítás nélkül,
- „mód” workframe helyett, ha semantikailag többről van szó,
- „megértette” olyan helyzetben, ahol csak candidate-szintű interpretáció történt.

## 4. Rövid végső összefoglalás

Ha egy fogalom többféleképpen is értelmezhető, ezt a dokumentumot kell használni a lezárására.


## Delta Journal

- 2026-03-15 | REBUILD-036 | checked, no change | Miért: új mezők a meglévő naming mintát követik, terminológia nem változott.

- 2026-03-15 | REBUILD-036 finisher | checked, no change | Miért: terminológia nem változott, csak routing/preference viselkedés.
