# Runbook: Validation and Reproduction

- Dokumentum státusz: **living doc / operátori kézikönyv**
- Dátum: **2026-03-15**
- Fő kapcsolatok: **00, 05, 06, 11, 15**

## Dokumentum célja

Ez a dokumentum a kanonikus gyakorlati menetet írja le:
- hogyan kell tiszta validációs kört indítani,
- hogyan kell hibát reprodukálni,
- hogyan kell logot rögzíteni,
- és mi a merge előtti minimális operátori rend.

## 1. Alapszabályok

1. Ne a live DB-n validálj, ha gate-szintű smoke-ról van szó.
2. Mindig friss temp DB + temp sandbox roots legyen a kanonikus tiszta kör.
3. Teljes logot kell visszaadni, nem csak végső következtetést.
4. A summary nem bizonyíték.
5. Rendszerszintű ticket csak docs-sync + Fájlfrissítési jelentés mellett tekinthető teljesnek.

## 2. Kanonikus fresh-run eljárás

### 2.1 Temp környezet létrehozása
- hozz létre új temp sandbox rootot,
- hozz létre új temp DB pathot,
- állítsd a környezetet ezekre,
- ne használd a régi futásból maradt DB-t.

### 2.2 Inicializálás
- `python -m syntaris.cli --config "$CFG" init-db`

### 2.3 Kötelező minimál validáció
- célzott pytest,
- teljes pytest,
- compileall,
- smoke kör,
- szükség esetén live kör,
- trace-last,
- thread-snapshot --current.

## 3. Speciális precedence / env leakage ellenőrzés

Ha a ticket érinti:
- config loadert,
- runtime DB path feloldást,
- allowed roots feloldást,
- compat aliasokat / env override-okat,

akkor kötelező legalább egy külön proof kör, ahol:
- ambient compat env változók **aktívak**,
- a teszt vagy a runtime mégsem szennyeződik el,
- az explicit temp config / temp DB / temp roots izoláció megmarad.

Kanonikus alapelv:
- a primary env override-ok kanonikusabbak,
- a compat aliasok nem írhatják felül az explicit temp konfigurációt.

## 4. Kanonikus logrögzítés

A lognak tartalmaznia kell:
- futtatott parancsok pontos sorát,
- teljes stdout/stderr kimenetet,
- hiba esetén a teljes stacket vagy kontrollált hibakimenetet,
- live kör esetén a teljes párbeszédet,
- a végén trace/snapshot releváns kimeneteit.

## 5. Kontaminált kör felismerése

Kontaminált a validáció, ha például:
- nem friss DB-n ment,
- nem egyértelmű, milyen forrás maradt bent korábbról,
- az aktuális forrás helyett régi source-artifact válhat currentté,
- a reset menet nem igazolható,
- ambient env változók miatt a temp config/test izoláció sérül.

Ilyenkor a kör csak részleges bizonyíték, és friss temp körrel meg kell ismételni.

## 6. Hiba reprodukciós sablon

Minden reprodukálható hiba leírása tartalmazza:
- környezet,
- branch/commit/PR kontextus,
- pontos parancsok,
- minimális input,
- várt viselkedés,
- tényleges viselkedés,
- trace/snapshot állapot,
- merge-javaslat vagy ticket-javaslat.

## 7. PR-validáció minimális operátori checklista

- [ ] célzott pytest
- [ ] releváns regressziók
- [ ] teljes pytest
- [ ] compileall
- [ ] init-db
- [ ] ticket-specifikus smoke
- [ ] ha kell: live smoke
- [ ] trace-last
- [ ] thread-snapshot --current
- [ ] teljes log mentve
- [ ] summary összevetve a loggal
- [ ] docs frissítési igény ellenőrizve
- [ ] Fájlfrissítési jelentés megléte ellenőrizve

## 8. Live körök használata

Live kör kötelező különösen, ha a ticket érinti:
- casual chat,
- presence,
- identity/relationship,
- workframe-tartás,
- style obedience,
- direct question robustness.

## 9. Ticketzárási dokumentumszinkron

Rendszerszintű merge után kötelező ellenőrizni és frissíteni, ha érintettek:
- `06_Current_State_Matrix.md`
- `07_Capability_Catalog_v1.md`
- `08_Architecture_Decision_Record_Log.md`
- `09_Canonical_Contracts_and_Schemas.md`
- `10_System_Map_and_Dependency_Guide.md`
- `11_Eval_Scorecard_and_Thresholds.md`
- `12_Runbook_Validation_and_Reproduction.md`
- `13_Data_and_Memory_Governance.md`
- `14_Terminology_and_Naming_Standard.md`

## 10. Kötelező Fájlfrissítési jelentés

Minden rendszerszintű ticket summary végén kötelező külön blokkban szerepeltetni:

### Fájlfrissítési jelentés
- módosított kódfájlok,
- frissített kanonikus dokumentumok,
- átnézett, de változatlan living docok,
- releváns, de szándékosan nem frissített fájlok és indokuk.

Enélkül a ticket nem tekinthető teljesnek.

## 11. Tiltott operátori rövidítések

- summary alapján merge-et mondani teljes log nélkül,
- bizonytalan clean-run helperre építeni, ha nem igazolt,
- kontaminált DB-t tiszta körként kezelni,
- részlogból általános következtetést levonni,
- dokumentumszinkron nélkül lezártnak tekinteni rendszerszintű PR-t.

## 12. Rövid végső összefoglalás

A runbook célja, hogy a validáció reprodukálható és tiszta legyen.
Ha a kör nem bizonyíthatóan tiszta, nem szabad végső ítéletet alapozni rá.


## Delta Journal

- 2026-03-15 | REBUILD-036 | Reprodukciós kör hozzáadva: tiszta temp config+DB, ticket smoke lista, live smoke, trace-last/thread-snapshot ellenőrzés | Miért: kontaminációmentes bizonyítás.

- 2026-03-15 | REBUILD-036 finisher | Finisher-run log és problémás-turn trace/snapshot proof kör hozzáadva | Miért: reply/trace/snapshot koherencia bizonyítása.

- 2026-03-15 | REBUILD-037 | Runbook kiegészítés: recap A/B/C szekvencia smoke + trace-last/snapshot proof log | Miért: reprodukálható recap quality bizonyítás.
