from __future__ import annotations

from syntaris.orchestration.text_normalize import clean_display_text, normalize_hungarian_for_match
from syntaris.contracts.runtime import (
    AnswerStrategy,
    ClaimKind,
    AnswerStrategySelection,
    ComparisonPack,
    DecompositionPlan,
    EvidencePack,
    ObjectiveFrame,
    OwnerIdentityProfile,
    PersonalMemoryView,
    MemoryQueryKind,
    ScopedStateStatus,
    PersonalEntryKind,
    RecallResolution,
    ResponsePlan,
    ResponsePlanKind,
    ResponsePlanSection,
    RuntimeContext,
    SynthesisPlan,
    ThreadFocusPack,
    TimeContext,
    TurnInterpretation,
    WorkframeState,
    ThreadWeaveState,
)


def _synthesis_sections(synthesis: SynthesisPlan) -> list[ResponsePlanSection]:
    return [
        ResponsePlanSection(title=section.key, lines=section.lines)
        for section in synthesis.sections
        if section.lines
    ]


def _direct_should_use_synthesis(objective: ObjectiveFrame, decomposition: DecompositionPlan, synthesis: SynthesisPlan) -> bool:
    _ = synthesis
    if objective.kind.value in {"mixed_multi_part", "status_check", "diagnose", "compare", "next_step"}:
        return True
    if decomposition.multi_part:
        return True
    target_kinds = {"status_check", "diagnose", "compare", "next_step"}
    return any(unit.objective_kind.value in target_kinds for unit in decomposition.units)


def _daypart_greeting(daypart: str) -> str:
    mapping = {
        "reggel": "Jó reggelt",
        "delelott": "Szép délelőttöt",
        "delutan": "Szép délutánt",
        "este": "Jó estét",
        "ejjel": "Jó estét",
    }
    return mapping.get(daypart, "Szia")


def _gap_phrase(gap_kind: str, gap_minutes: int | None) -> str | None:
    if gap_kind == "short":
        return "Pár perce beszéltünk utoljára."
    if gap_kind == "same_day_long":
        if gap_minutes is not None and gap_minutes >= 120:
            return "Eltelt pár óra a legutóbbi üzenet óta."
        return "Eltelt egy kis idő a legutóbbi üzenet óta."
    if gap_kind == "cross_day":
        return "Tegnap óta nem folytattuk."
    return None


def _continuity_resume_line(gap_kind: str) -> str:
    if gap_kind in {"immediate", "short"}:
        return "Látom a mostani irányt, onnan folytathatjuk."
    if gap_kind == "same_day_long":
        return "A mai előzmény még megvan, de megerősítheted, maradjon-e ez az irány."
    if gap_kind == "cross_day":
        return "A tegnapi irányt nem kezelem automatikusan aktívnak, de vissza tudjuk venni, ha kéred."
    return "Innen tudunk továbblépni."


def _personal_entry_lines(signal: PersonalEntryKind, display_name: str, focus: str | None, direction: str | None, time_context: TimeContext | None = None, workframe_state: WorkframeState | None = None) -> list[str]:
    if signal == PersonalEntryKind.GREETING:
        greet = _daypart_greeting(time_context.daypart.value) if time_context is not None else "Szia"
        if workframe_state is not None and workframe_state.objective_status.value == "active" and workframe_state.objective_text:
            return [
                f"{greet}{display_name}. Vissza tudunk kapcsolni a mostani szálra: {clean_display_text(workframe_state.objective_text)}.",
                "Mondhatod azt is, hogy: folytassuk innen.",
            ]
        return [f"{greet}{display_name}. Miben segítsek most?"]
    if signal == PersonalEntryKind.SELF_INTRO:
        return [f"Szia{display_name}. Örülök, hogy így mutatkoztál be — miben induljunk el most?"]
    if signal == PersonalEntryKind.OWNER_FRAMING:
        return [f"Szia{display_name}. Értem, hogy te tervezed és fejleszted a rendszert. Mi legyen a mai konkrét fókusz?"]
    if signal == PersonalEntryKind.PERSONAL_CHAT_INTAKE:
        return [f"Rendben{display_name}, most beszélgető módra váltunk. Mi az, ami most leginkább foglalkoztat?"]
    if signal == PersonalEntryKind.CONCRETE_HELP_INTAKE:
        return ["Rendben, menjünk konkrétan ezen: írd le röviden, hol akadtál el, és onnan lépünk tovább."]
    if signal == PersonalEntryKind.FOCUS_SETTING_INTAKE:
        if focus:
            return [f"Jó irány, a mai fókusz legyen {clean_display_text(focus)}. Mi legyen az első konkrét lépés?"]
        if direction:
            return [f"Rendben, most a {clean_display_text(direction)} irányra állunk rá. Melyik konkrét ponttal kezdjük?"]
        return ["Rendben, fókuszra álltunk. Melyik konkrét ponttal kezdjük?"]
    if signal == PersonalEntryKind.RESUME_INTAKE:
        lead = _continuity_resume_line(time_context.gap_kind.value) if time_context is not None else "Innen tudunk továbblépni."
        if workframe_state is not None and workframe_state.objective_status.value == "active" and workframe_state.objective_text:
            return [f"Oké, vegyük fel innen a fonalat. {lead} Aktív célként ezt látom: {clean_display_text(workframe_state.objective_text)}."]
        return [f"Oké, vegyük fel innen a fonalat. {lead}"]
    if signal == PersonalEntryKind.RETURN_ENTRY:
        gap = _gap_phrase(time_context.gap_kind.value, time_context.gap_minutes) if time_context is not None else None
        base = f"Jó újra itt{display_name}."
        if workframe_state is not None and workframe_state.objective_status.value == "active" and workframe_state.objective_text:
            objective = clean_display_text(workframe_state.objective_text)
            blocker = f" Fő blokkernél ezt látom: {clean_display_text(workframe_state.blocker_text)}." if workframe_state.blocker_text else ""
            if gap:
                return [f"{base} {gap} Folytathatjuk a korábbi munkát: {objective}.{blocker}"]
            return [f"{base} Folytathatjuk a korábbi munkát: {objective}.{blocker}"]
        if gap:
            return [f"{base} {gap} Mivel folytassuk?"]
        return [f"{base} Mivel folytassuk?"]
    return ["Rendben, visszakapcsoltam ide. Folytassuk innen — most beszélgessünk, vagy oldjunk meg egy konkrét feladatot?"]


def _memory_query_lines(query: MemoryQueryKind, memory: PersonalMemoryView) -> list[str]:
    def status_label(status: ScopedStateStatus | None) -> str:
        if status == ScopedStateStatus.ACTIVE:
            return "aktív"
        if status == ScopedStateStatus.STALE:
            return "már csak részben aktív"
        return "lejárt"

    if query == MemoryQueryKind.WHO_AM_I:
        if memory.owner_name:
            return [f"A megadott adataid alapján {memory.owner_name} vagy."]
        return ["Ezt még nem tudom biztosan, mert nem mondtad ki egyértelműen a neved."]
    if query == MemoryQueryKind.WHO_ARE_YOU:
        system_name = memory.system_name or "Syntaris"
        role_text = f" A kimondott szerepem: {memory.system_role}." if memory.system_role else ""
        return [f"{system_name} vagyok, a determinisztikus személyes kognitív rendszered.{role_text}"]
    if query == MemoryQueryKind.RELATIONSHIP:
        lines: list[str] = ["A kapcsolatunk jelenlegi explicit kerete: owner ↔ személyes kognitív rendszer."]
        if memory.owner_name:
            lines.append(f"Te {memory.owner_name} vagy az owner oldalon.")
        if memory.owner_relation == "creator":
            lines.append("Explicit állításod alapján te tervezed és fejleszted ezt a rendszert.")
        if memory.system_name:
            lines.append(f"A rendszer-nevemként ezt rögzítetted: {memory.system_name}.")
        if memory.system_role:
            lines.append(f"A szerepemnek ezt mondtad: {memory.system_role}.")
        if lines:
            return lines
        return ["A kapcsolatunkról még csak annyit tudok biztosan, amit explicit mondtál — ezt még nem rögzítettük."]
    if query == MemoryQueryKind.SYSTEM_ROLE:
        if memory.system_role:
            return [f"A kimondott szerepem: {memory.system_role}."]
        return ["A szerepemről még nincs egyértelmű, explicit állításod eltárolva."]
    if query == MemoryQueryKind.HOW_HELP:
        lines = ["Ebben tudok segíteni determinisztikus, bizonyítékhoz kötött módban:"]
        lines.append("• tisztázni, pontosan hol tartunk és mi a következő megalapozott lépés")
        lines.append("• visszahozni a jelenlegi/előző szál röviden, ha van hozzá mentett kontextus")
        lines.append("• szétválasztani a biztos forrást a következtetéstől")
        if memory.system_role:
            lines.append(f"• a kimondott szerepem szerint: {memory.system_role}")
        lines.append("Nem találok ki állapotot: csak explicit vagy ténylegesen megőrzött kontextusra támaszkodom.")
        return lines
    if query == MemoryQueryKind.CURRENT_FOCUS:
        if memory.current_focus and memory.current_focus_status == ScopedStateStatus.ACTIVE:
            return [f"A mostani fókusz aktívan: {clean_display_text(memory.current_focus)}."]
        if memory.current_direction and memory.current_direction_status == ScopedStateStatus.ACTIVE:
            return [f"A mostani irány aktívan: {clean_display_text(memory.current_direction)}."]
        if memory.current_focus:
            return [f"A legutóbbi fókusz: {clean_display_text(memory.current_focus)}, de ez most {status_label(memory.current_focus_status)}."]
        if memory.current_direction:
            return [f"A legutóbbi irány: {clean_display_text(memory.current_direction)}, de ez most {status_label(memory.current_direction_status)}."]
        return ["Mostani fókuszt még nem állítottál be explicit módon."]
    if query == MemoryQueryKind.CURRENT_DIRECTION:
        if memory.current_direction and memory.current_direction_status == ScopedStateStatus.ACTIVE:
            return [f"Most erről akartál beszélni: {clean_display_text(memory.current_direction)}."]
        if memory.current_direction:
            return [f"Legutóbb erről akartál beszélni: {clean_display_text(memory.current_direction)}, de ez most {status_label(memory.current_direction_status)}."]
        return ["Mostani beszélgetési irányt még nem adtál meg explicit módon."]
    if query == MemoryQueryKind.ACTIVE_STATE:
        relevant = memory.scoped_state.recent_items
        if relevant:
            lines = ["Mostanról ennyi maradt releváns:"]
            for item in relevant[:3]:
                lines.append(
                    f"• {item.kind.value.replace('_', ' ')}: {clean_display_text(item.value)} ({status_label(item.status)})"
                )
            return lines
        if memory.scoped_state.items:
            latest = memory.scoped_state.items[0]
            return [f"A legutóbbi ideiglenes állapot ({clean_display_text(latest.value)}) már nem aktív."]
        return ["Most nincs aktív ideiglenes fókusz vagy irány rögzítve."]
    if query == MemoryQueryKind.WHAT_KNOWN_CERTAIN:
        lines: list[str] = ["Ami rólad biztosan látszik (explicit állítás alapján):"]
        if memory.owner_name:
            lines.append(f"• Név (explicit): {memory.owner_name}")
        if memory.owner_relation:
            relation = "creator" if memory.owner_relation == "creator" else memory.owner_relation
            lines.append(f"• Kapcsolat (explicit): {relation}")
        if memory.system_role:
            lines.append(f"• Rendszer-szerep (explicit): {memory.system_role}")
        if len(lines) == 1:
            return ["Még nincs olyan explicit állításod eltárolva, amit biztos tényként vissza tudok mondani."]
        return lines
    if query == MemoryQueryKind.WHAT_INFERRED:
        return ["Rólad jelenleg nem tartok fenn külön, bizonyított következtetés-listát; amit biztosnak mondok, az explicit állításból jön."]
    if query == MemoryQueryKind.TEMPORARY_VS_CERTAIN:
        lines: list[str] = ["Szétválasztva:"]
        if memory.owner_name or memory.system_name or memory.owner_relation or memory.system_role:
            lines.append("• Biztos (stabil, explicit):")
            if memory.owner_name:
                lines.append(f"  - név: {memory.owner_name}")
            if memory.system_name:
                lines.append(f"  - rendszer neve: {memory.system_name}")
            if memory.owner_relation:
                lines.append(f"  - kapcsolat: {memory.owner_relation}")
            if memory.system_role:
                lines.append(f"  - szerep: {memory.system_role}")
        else:
            lines.append("• Biztos (stabil, explicit): még nincs.")

        if memory.scoped_state.recent_items:
            lines.append("• Ideiglenes (idővel elévül):")
            for item in memory.scoped_state.recent_items[:3]:
                lines.append(f"  - {item.kind.value.replace('_', ' ')}: {clean_display_text(item.value)} ({status_label(item.status)})")
        elif memory.scoped_state.items:
            lines.append("• Ideiglenes: volt ilyen, de már lejárt.")
        else:
            lines.append("• Ideiglenes: jelenleg nincs.")
        lines.append("• Feltételezés/inferencia: nincs külön biztosként kezelt tétel.")
        return lines

    lines: list[str] = []
    if memory.owner_name:
        lines.append(f"• Név (explicit): {memory.owner_name}")
    if memory.system_name:
        lines.append(f"• Rendszer név (explicit): {memory.system_name}")
    if memory.owner_relation:
        relation = "creator" if memory.owner_relation == "creator" else memory.owner_relation
        lines.append(f"• Kapcsolat (explicit): {relation}")
    if memory.system_role:
        lines.append(f"• Szerep (explicit): {memory.system_role}")
    if memory.current_focus:
        lines.append(f"• Mostani fókusz ({status_label(memory.current_focus_status)}): {clean_display_text(memory.current_focus)}")
    elif memory.current_direction:
        lines.append(f"• Mostani irány ({status_label(memory.current_direction_status)}): {clean_display_text(memory.current_direction)}")
    return lines or ["Még nincs olyan explicit állításod eltárolva, amit biztos tényként vissza tudok mondani."]


def _claim_capture_lines(interpretation: TurnInterpretation) -> list[str]:
    captures = interpretation.claim_capture
    by_kind = {item.kind: item.value for item in captures}

    if interpretation.pattern_name == "claim_correction" and ClaimKind.OWNER_NAME in by_kind:
        return [f"Köszönöm a javítást, a nevedet {clean_display_text(by_kind[ClaimKind.OWNER_NAME])} néven rögzítettem."]

    if ClaimKind.SYSTEM_NAME in by_kind:
        return [f"Rögzítettem a rendszer-nevemet: {clean_display_text(by_kind[ClaimKind.SYSTEM_NAME])}. Így fogok hivatkozni magamra."]
    if ClaimKind.SYSTEM_ROLE in by_kind:
        return [f"Rögzítettem: a szerepemnek ezt mondtad — {clean_display_text(by_kind[ClaimKind.SYSTEM_ROLE])}."]
    if ClaimKind.OWNER_NAME in by_kind and ClaimKind.OWNER_RELATION in by_kind:
        return [
            f"Rögzítettem: te {clean_display_text(by_kind[ClaimKind.OWNER_NAME])} vagy, és te tervezed/fejleszted a rendszert.",
            "Ettől indulva owner-aware módon folytatom.",
        ]
    if ClaimKind.OWNER_NAME in by_kind:
        return [f"Rögzítettem a nevedet: {clean_display_text(by_kind[ClaimKind.OWNER_NAME])}. Így foglak megszólítani."]
    if ClaimKind.OWNER_RELATION in by_kind and by_kind[ClaimKind.OWNER_RELATION] == "creator":
        return ["Rögzítettem: explicit állításod szerint te tervezed és fejleszted a rendszert."]
    if ClaimKind.CURRENT_FOCUS in by_kind:
        return [f"Rögzítettem a mostani fókuszt: {clean_display_text(by_kind[ClaimKind.CURRENT_FOCUS])}."]
    if ClaimKind.CURRENT_DIRECTION in by_kind:
        direction_value = by_kind[ClaimKind.CURRENT_DIRECTION]
        if direction_value.startswith("állapot:"):
            return [f"Jelezted az ideiglenes állapotodat, ezt most így kezelem: {clean_display_text(direction_value)}."]
        return [f"Rögzítettem a mostani irányt: {clean_display_text(direction_value)}."]

    return ["Rögzítettem az explicit állításodat."]





def _ingest_intent_lines(message: str) -> list[str] | None:
    lower = normalize_hungarian_for_match(message).lower()
    if "bemasolok" in lower and any(term in lower for term in ("hosszabb konzolkimenet", "hosszabb log", "traceback", "konzol")):
        return [
            "Rendben, várom a nyers forrásblokkot.",
            "A következő üzenetben küldheted a teljes több soros konzol/log szöveget; azt nyers evidenciaként kezelem.",
        ]
    return None

def _workframe_lines(workframe_state: WorkframeState) -> list[str]:
    lines: list[str] = [f"Munkakeret: {workframe_state.workframe.value}."]
    if workframe_state.objective_status.value == "active" and workframe_state.objective_text:
        lines.append(f"Aktív cél: {clean_display_text(workframe_state.objective_text)}.")
    elif workframe_state.objective_status.value == "proposed" and workframe_state.objective_text:
        lines.append(f"Javasolt cél: {clean_display_text(workframe_state.objective_text)} (még nem végleges).")
    elif workframe_state.objective_status.value in {"none", "related_context"}:
        lines.append("Aktív cél: nincs még egyértelműen rögzítve.")

    if workframe_state.blocker_status.value in {"explicit", "implied"} and workframe_state.blocker_text:
        prefix = "Fő blokkert" if workframe_state.blocker_status.value == "explicit" else "Lehetséges blokkert"
        lines.append(f"{prefix} látok: {clean_display_text(workframe_state.blocker_text)}.")
    elif workframe_state.blocker_status.value in {"uncertainty_or_missing_info", "none"}:
        lines.append("Fő blokkert nem látok biztosan rögzítve.")

    if workframe_state.next_step_lines:
        lines.append("Következő lépés:")
        for step in workframe_state.next_step_lines:
            lines.append(f"- {clean_display_text(step)}")
    elif workframe_state.next_step_status.value == "none":
        lines.append("Következő lépés: még nincs megalapozottan rögzítve.")
    lines.append(f"Hiányzó információ: {workframe_state.missing_info_status.value}.")
    lines.append(f"Nyitott kérdés: {workframe_state.open_question_status.value}.")
    lines.append(f"Döntési állapot: {workframe_state.decision_state.value}.")
    return lines









def _evidence_query_flags(message: str) -> dict[str, bool]:
    lower = normalize_hungarian_for_match(message).lower()
    evidence_context = any(term in lower for term in (
        "forras", "log", "konzol", "traceback", "kimenet", "stack", "exception", "hiba",
    ))
    return {
        "asks_summary": "mi a lenyeg ebbol" in lower or (evidence_context and ("mi a lenyeg" in lower or "osszefoglal" in lower)),
        "asks_error": "mi benne a valodi hiba" in lower or (evidence_context and ("valodi hiba" in lower or "fo hiba" in lower or "mi a hiba" in lower)),
        "asks_support": "mi biztosan latszik ebbol" in lower or (evidence_context and "forras mit mond" in lower),
        "asks_inference": "mi csak kovetkeztetes" in lower or (evidence_context and "kovetkeztetes" in lower),
        "asks_important": "melyik resz a fontos" in lower or (evidence_context and "fontos resz" in lower),
        "asks_blocker": "ebbol mi a blocker" in lower or "ebbol mi a blokker" in lower or (evidence_context and ("mi a blocker" in lower or "mi blokkol" in lower or "mi a blokker" in lower)),
        "asks_missing": "mihez kell meg adat a log alapjan" in lower or (evidence_context and ("mihez kell meg adat" in lower or "mi hianyzik" in lower)),
        "asks_recall": "korabbi konzol" in lower or "korabbi log" in lower or "abbol a konzolbol" in lower,
    }


def _source_awareness_lines(message: str, evidence_pack: EvidencePack) -> list[str] | None:
    lower = normalize_hungarian_for_match(message).lower()
    asks = any(
        phrase in lower
        for phrase in (
            "mibol dolgozol most",
            "melyik fajlt hasznaltad",
            "sorold fel a mostani forrasokat",
            "ez most raw blokk vagy helyi fajl",
        )
    )
    if not asks:
        return None
    ingest = evidence_pack.ingest
    if ingest is None:
        return ["Most nincs aktív, beolvasott forrásom."]

    origin = None
    kind_hint = None
    for ref in ingest.evidence_source_references:
        if ref.source_label == "artifact_origin" and origin is None:
            origin = clean_display_text(ref.excerpt)
        if ref.source_label == "artifact_kind" and kind_hint is None:
            kind_hint = clean_display_text(ref.excerpt)
    if origin:
        if kind_hint == "once_file_import":
            kind = "once-file import (helyi fájl)"
        elif kind_hint == "local_text_file":
            kind = "helyi fájl"
        elif kind_hint == "raw_paste":
            kind = "raw_paste"
        else:
            kind = "helyi fájl" if "/" in origin or "\\" in origin else "fájlforrás"
        reuse_line = ""
        if ingest.ingest_status.value != "raw_text_evidence":
            reuse_line = " (korábban beolvasott artifact)"
        return [f"Most ebből dolgozom{reuse_line}: {origin}", f"Forrás típusa: {kind}."]


    if ingest.ingest_status.value == "raw_text_evidence":
        return ["Most a legutóbbi nyers forrásblokk alapján dolgozom.", "Forrás típusa: raw_paste."]
    if ingest.artifact_ids:
        return [f"Most korábban beolvasott artifactból dolgozom: {ingest.artifact_ids[0]}"]
    return ["Most nincs aktív, beolvasott forrásom."]


def _evidence_grounded_lines(message: str, evidence_pack: EvidencePack, workframe_state: WorkframeState | None) -> list[str] | None:
    ingest = evidence_pack.ingest
    if ingest is None or ingest.ingest_status.value != "raw_text_evidence":
        return None
    flags = _evidence_query_flags(message)
    if not any(flags.values()):
        return None

    key_lines = [clean_display_text(line) for line in ingest.extracted_key_lines]
    direct = [f"• {line}" for line in key_lines[:4]]
    inferred = [f"• {clean_display_text(line)}" for line in ingest.evidence_summary[:3]]
    unresolved = [f"• {clean_display_text(line)}" for line in ingest.unresolved_evidence[:2]]

    error_lines = [line for line in key_lines if any(tok in line.lower() for tok in ("traceback", "error", "exception", "valueerror", "runtimeerror", "failed", "exit code"))]
    warning_lines = [line for line in key_lines if "warn" in line.lower()]
    path_lines = [line for line in key_lines if any(tok in line.lower() for tok in (".py", "/", "\\"))]

    if flags["asks_error"]:
        return [
            "A valódi hiba (forrás alapján):",
            *([f"• {line}" for line in error_lines[:3]] or ["• Nincs egyetlen domináns hiba-sor, több jel vegyesen látszik."]),
            "Következtetés (forrásból):",
            *(inferred or ["• A hiba pontos oka részben következtetés marad."]),
            "Ami még nincs alátámasztva:",
            *(unresolved or ["• További futási környezet/adat kellhet a végleges okhoz."]),
        ]

    if flags["asks_inference"]:
        return [
            "Mi csak következtetés (nem közvetlen forrássor):",
            *(inferred or ["• Nincs külön következtetési tétel, csak közvetlen forrássorok látszanak."]),
            "Közvetlen forrás-sorok (külön kezelve):",
            *(direct or ["• Nincs kivont közvetlen sor."]),
        ]

    if flags["asks_important"]:
        cluster: list[str] = []
        cluster.extend(error_lines[:2])
        cluster.extend(path_lines[:1])
        if not cluster:
            cluster = key_lines[:3]
        return [
            "A fontos rész (forrásból):",
            *[f"• {line}" for line in cluster[:4]],
            "Miért ez a fontos blokk:",
            "• Itt jelenik meg a hibajel + a futási hely/nyomvonal együtt.",
        ]

    if flags["asks_blocker"]:
        blocker_line = None
        if workframe_state is not None and workframe_state.blocker_text:
            blocker_line = clean_display_text(workframe_state.blocker_text)
        elif error_lines:
            blocker_line = error_lines[0]
        if blocker_line:
            support = "közvetlenül látszik" if any(tok in blocker_line.lower() for tok in ("traceback", "error", "exception", "exit code", "failed")) else "inkább következtetés"
            return [
                f"Valószínű blocker: {blocker_line}",
                f"Forrás-támasz: {support}.",
                "Hiányzó adat a biztos lezáráshoz:",
                *(unresolved or ["• Reprodukciós lépés vagy teljes stack-kontextus segítene."]),
            ]
        return ["Nem látok forrásból megalapozott blokkert ebben a logban."]

    if flags["asks_missing"]:
        return [
            "A log alapján még hiányozhat:",
            *(unresolved or ["• Konkrét környezeti/konfig részlet a hiba reprodukciójához."]),
        ]

    if flags["asks_recall"]:
        return [
            "A korábbi konzolból ez derült ki:",
            *(direct or ["• Nincs kivont közvetlen forrás-sor."]),
            "Rövid következtetés:",
            *(inferred or ["• A hiba okát a forrás részben, de nem teljesen bizonyítja."]),
        ]

    if flags["asks_support"] or flags["asks_summary"]:
        lines = ["A forrás alapján:", "Közvetlenül látszik:", *(direct or ["• Nincs erős közvetlen sor kivonva."])]
        if flags["asks_summary"]:
            lines.extend(["Következtetés (forrásból):", *(inferred or ["• Nincs stabil következtetés."])])
        if warning_lines:
            lines.extend(["Figyelmeztetések:", *[f"• {line}" for line in warning_lines[:2]]])
        lines.extend(["Ami még nincs alátámasztva:", *(unresolved or ["• Jelenleg nincs külön unresolved tétel."])])
        return lines

    return None


def _no_evidence_lines(message: str, evidence_pack: EvidencePack) -> list[str] | None:
    flags = _evidence_query_flags(message)
    if not any(flags.values()):
        return None
    ingest = evidence_pack.ingest
    if ingest is not None and ingest.ingest_status.value == "raw_text_evidence":
        return None
    return [
        "Ehhez a kérdéshez még nincs korábban ténylegesen ingesztált nagy forrásblokk.",
        "Illessz be egy több soros log/traceback szöveget (pl. talk --once-file vagy talk --once-stdin úton), és abból forrásalapon válaszolok.",
    ]


def _current_ingest_ack_lines(evidence_pack: EvidencePack, evidence_ingest_from_current_turn: bool) -> list[str] | None:
    ingest = evidence_pack.ingest
    if not evidence_ingest_from_current_turn or ingest is None or ingest.ingest_status.value != "raw_text_evidence":
        return None
    kept = sum(1 for chunk in ingest.chunked_evidence if chunk.disposition.value == "kept_chunk")
    return [
        "Rendben, a nyers log/konzol blokkot evidenciaként beemeltem.",
        f"Kivonat: {kept} releváns chunk, {len(ingest.extracted_key_lines)} kulcssor.",
        "Most már tudok válaszolni belőle: mi a hiba / mi biztos / mi csak következtetés.",
    ]




_STYLE_SIGNAL_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("no_list", ("nem kerek listat", "ne listazz", "ne listaz", "csak reagalj normalisan", "normalisan reagalj")),
    ("brief", ("roviden", "rovid valasz", "tomoren", "roviden mondd", "roviden mondd")),
    ("no_certainty_split", ("ne bontsd biztosra", "ne bontsd biztos", "ne bontsd feltetelezesre", "ne bontsd biztosra meg feltetelezesre")),
    ("casual_only", ("most ne dolgozzunk", "csak beszelgessunk", "csak beszelgetunk", "csak dumaljunk", "csak reagalj normalisan", "beszelgesunk", "pls")),
)


def _extract_style_constraints(message: str) -> list[str]:
    n = normalize_hungarian_for_match(message).lower()
    found: list[str] = []
    for name, patterns in _STYLE_SIGNAL_PATTERNS:
        if any(pattern in n for pattern in patterns):
            found.append(name)
    if ("beszelg" in n or "dumal" in n) and "casual_only" not in found:
        found.append("casual_only")
    if "rovid" in n and "brief" not in found:
        found.append("brief")
    return found


def _is_direct_question(message: str) -> bool:
    n = normalize_hungarian_for_match(message).lower()
    return "?" in message or any(
        n.startswith(prefix)
        for prefix in ("mi ", "mit ", "hogyan", "hol ", "mikor", "emlekszel", "hol tartottunk", "mire jutottunk")
    )


def _enforce_style_constraints(lines: list[str], constraints: list[str]) -> list[str]:
    out = list(lines)
    if "no_certainty_split" in constraints:
        banned = (
            "ami biztos",
            "ami nyitott",
            "ami inkabb",
            "ami bizonytalan",
            "mi tamaszthato ala biztosan",
            "mi marad feltetelezes",
            "feltetelezes vagy nyitott",
            "feltetelezes",
            "bizonytalan",
        )
        filtered: list[str] = []
        for line in out:
            norm = normalize_hungarian_for_match(line).lower()
            if any(b in norm for b in banned):
                continue
            filtered.append(line)
        out = filtered
    if "brief" in constraints and len(out) > 3:
        out = out[:3]
    if "no_list" in constraints or "casual_only" in constraints:
        flattened: list[str] = []
        for line in out:
            cleaned = line.lstrip("•- ").strip()
            if cleaned:
                flattened.append(cleaned)
        if flattened:
            out = [" ".join(flattened)]
    return out


def _is_hijack_prone(message: str) -> bool:
    n = normalize_hungarian_for_match(message).lower()
    trigger_count = sum(1 for token in ("biztos", "most", "fontos", "emlekszel", "hol tartottunk", "folytassuk innen") if token in n)
    return trigger_count >= 2 and len(n.split()) >= 5


def _is_reflective_personal_input(message: str) -> bool:
    n = normalize_hungarian_for_match(message).lower()
    return any(term in n for term in ("faradt vagyok", "kimerult vagyok", "szetesek", "nehez nap", "stresszes vagyok"))


def _reflective_fallback_lines(message: str) -> list[str] | None:
    if not _is_reflective_personal_input(message):
        return None
    if "faradt vagyok" in normalize_hungarian_for_match(message).lower():
        return ["Azt mondod, fáradt vagy most. Maradhatunk rövid, kímélő tempóban, vagy léphetünk egy nagyon kicsit tovább."]
    return ["Értem, ez most megterhelőnek hangzik. Ha szeretnéd, maradjunk röviden itt, vagy menjünk egy apró, könnyű következő lépéssel."]


def _needs_brief_recap(message: str) -> bool:
    n = normalize_hungarian_for_match(message).lower()
    return any(
        phrase in n
        for phrase in (
            "mit mondtam eddig errol",
            "emlekszel mire jutottunk",
            "mire jutottunk roviden",
            "eddig errol roviden",
        )
    )


def _brief_recap_lines(focus: ThreadFocusPack | None) -> list[str] | None:
    if focus is None or not focus.focus_lines:
        return None
    prioritized = [line for line in focus.focus_lines if line.key.startswith("recap_point_")]
    if not prioritized:
        prioritized = focus.focus_lines
    picked = [clean_display_text(line.text) for line in prioritized if clean_display_text(line.text)][:3]
    if not picked:
        return None
    lines = ["Röviden itt tartunk:"]
    lines.extend(picked)
    return lines


def _natural_workframe_answer(message: str, state: WorkframeState) -> list[str] | None:
    n = normalize_hungarian_for_match(message).lower()
    if "mi a kovetkezo lepes" in n or "mit kell most tenni" in n:
        if state.next_step_lines:
            return [f"A következő jó lépés most: {clean_display_text(state.next_step_lines[0])}"]
        if state.blocker_text:
            return [f"Először ezt érdemes tisztázni: {clean_display_text(state.blocker_text)}"]
        return ["Most még nincs stabilan rögzített következő lépés; ha adsz egy célmondatot, azonnal szűkítem."]
    if "mi a blocker" in n or "mi blokkol" in n or "mi a fo problema" in n:
        if state.blocker_text:
            return [f"A fő blokker most röviden: {clean_display_text(state.blocker_text)}"]
        return ["Most nincs egyértelműen rögzített fő blokker."]
    return None

def _decision_readiness_lines(state: WorkframeState) -> list[str]:
    return [
        f"Hiányzó információ állapot: {state.missing_info_status.value}.",
        *(f"- {clean_display_text(line)}" for line in state.missing_info_lines),
        f"Nyitott kérdés állapot: {state.open_question_status.value}.",
        *(f"- {clean_display_text(line)}" for line in state.open_question_lines),
        f"Feltételezés/evidencia állapot: {state.assumption_status.value}.",
        *(f"- {clean_display_text(line)}" for line in state.assumption_lines),
        f"Döntési állapot: {state.decision_state.value}.",
        *(f"- {clean_display_text(line)}" for line in state.decision_lines),
        f"Bizonyíték-rés állapot: {state.evidence_gap_status.value}.",
        *(f"- {clean_display_text(line)}" for line in state.evidence_gap_lines),
    ]

def _history_lines(state: WorkframeState) -> list[str]:
    lines: list[str] = ["Korábbi állapot alapján:"]
    if state.objective_status.value == "active" and state.objective_text:
        lines.append(f"- Aktív cél: {clean_display_text(state.objective_text)}")
    else:
        lines.append("- Aktív cél: korábban sem volt biztosan rögzítve.")
    if state.blocker_text:
        lines.append(f"- Fő probléma: {clean_display_text(state.blocker_text)}")
    else:
        lines.append("- Fő probléma: nem volt egyértelműen rögzítve.")
    if state.next_step_lines:
        lines.append(f"- Következő lépés: {clean_display_text(state.next_step_lines[0])}")
    else:
        lines.append("- Következő lépés: nem volt megalapozottan rögzítve.")
    return lines


def _certainty_lines(state: WorkframeState) -> list[str]:
    sure: list[str] = []
    uncertain: list[str] = []
    if state.objective_status.value == "active" and state.objective_text:
        sure.append(f"Aktív cél: {clean_display_text(state.objective_text)}")
    elif state.objective_status.value == "proposed" and state.objective_text:
        uncertain.append(f"Cél-javaslat: {clean_display_text(state.objective_text)}")

    if state.blocker_status.value == "explicit" and state.blocker_text:
        sure.append(f"Blokker: {clean_display_text(state.blocker_text)}")
    elif state.blocker_text:
        uncertain.append(f"Lehetséges blokker: {clean_display_text(state.blocker_text)}")

    if state.next_step_status.value in {"grounded"} and state.next_step_lines:
        sure.append(f"Következő lépés: {clean_display_text(state.next_step_lines[0])}")
    elif state.next_step_lines:
        uncertain.append(f"Javasolt következő lépés: {clean_display_text(state.next_step_lines[0])}")

    lines = ["Ami biztos:"]
    lines.extend([f"• {item}" for item in sure] or ["• Nincs biztosan rögzített állítás."])
    lines.append("Ami nyitott:")
    lines.append("Ami inkább javaslat/feltételezés:")
    lines.extend([f"• {item}" for item in uncertain] or ["• Jelenleg nincs külön javaslatként megjelölt tétel."])
    return lines

def build_response_plan(
    context: RuntimeContext,
    interpretation: TurnInterpretation,
    recall: RecallResolution,
    strategy: AnswerStrategySelection,
    comparison_pack: ComparisonPack,
    objective: ObjectiveFrame,
    decomposition: DecompositionPlan,
    evidence_pack: EvidencePack,
    synthesis: SynthesisPlan,
    focus: ThreadFocusPack | None = None,
    followup_target: str | None = None,
    owner_identity: OwnerIdentityProfile | None = None,
    personal_memory: PersonalMemoryView | None = None,
    time_context: TimeContext | None = None,
    has_previous_thread: bool = False,
    workframe_state: WorkframeState | None = None,
    workframe_queries: object | None = None,
    workframe_updates: object | None = None,
    historical_workframe_state: WorkframeState | None = None,
    thread_weave_state: ThreadWeaveState | None = None,
    thread_weave_query_family: str | None = None,
    thread_weave_update_kind: str | None = None,
    thread_weave_query_message: str | None = None,
    evidence_ingest_from_current_turn: bool = False,
) -> ResponsePlan:
    interpretation_text = thread_weave_query_message or ""
    style_constraints = _extract_style_constraints(interpretation_text)
    chat_lock_active = "casual_only" in style_constraints
    chat_lock_strength = "strong" if chat_lock_active else "none"
    direct_answer_required = _is_direct_question(interpretation_text)
    anti_hijack_guarded = _is_hijack_prone(interpretation_text)

    def _mkplan(*, kind: ResponsePlanKind, sections: list[ResponsePlanSection], followup_prompt: str | None = None, focus_used: bool = False) -> ResponsePlan:
        adjusted_sections = [ResponsePlanSection(title=s.title, lines=_enforce_style_constraints(s.lines, style_constraints)) for s in sections]
        if "no_certainty_split" in style_constraints and not any(sec.lines for sec in adjusted_sections):
            adjusted_sections = [ResponsePlanSection(title="style_override", lines=["Rendben, bontás nélkül röviden elmondom."])]
        direct_answer_present = any(any(line.strip() and line.strip().lower() not in {"rendben.", "ok.", "oke."} for line in sec.lines) for sec in adjusted_sections)
        clarification_needed = kind == ResponsePlanKind.CLARIFICATION
        ack_collapse_risk = direct_answer_required and not direct_answer_present and not clarification_needed
        reply_shape = "casual" if ("no_list" in style_constraints or "casual_only" in style_constraints) else ("structured" if kind in {ResponsePlanKind.STRUCTURED, ResponsePlanKind.UNCERTAINTY_LABELED} else "direct")
        final_workframe = workframe_state.workframe.value if workframe_state is not None else None
        is_brief_recap = any(section.title == "brief_recap" for section in adjusted_sections)
        return ResponsePlan(
            kind=kind,
            sections=adjusted_sections,
            followup_prompt=followup_prompt,
            focus_used=focus_used,
            style_constraints=style_constraints,
            chat_lock_active=chat_lock_active,
            chat_lock_strength=chat_lock_strength,
            direct_answer_required=direct_answer_required,
            direct_answer_present=direct_answer_present,
            clarification_needed=clarification_needed,
            clarification_reason=(strategy.clarification_need.cause if clarification_needed else None),
            anti_hijack_guarded=anti_hijack_guarded,
            ack_collapse_risk=ack_collapse_risk,
            final_workframe=final_workframe,
            final_thread_arbitration=("has_previous" if has_previous_thread else "continue_active"),
            reply_shape=reply_shape,
            recap_source_turn_count=(focus.source_metadata.source_turn_count if (is_brief_recap and focus is not None) else None),
            recap_included_turn_count=(focus.source_metadata.included_turn_count if (is_brief_recap and focus is not None) else None),
        )

    if thread_weave_state is not None and thread_weave_update_kind is not None:
        if thread_weave_update_kind == "detour_declared":
            lines = ["Rendben, ezt kitérő/mellékszál jelzésként rögzítem."]
            if thread_weave_state.detour_thread_key:
                lines.append(f"Kitérő téma: {clean_display_text(thread_weave_state.detour_thread_key)}")
            if thread_weave_state.main_thread_key:
                lines.append(f"Aktív főszál marad: {clean_display_text(thread_weave_state.main_thread_key)}")
            lines.append(f"Thread lifecycle: {thread_weave_state.thread_lifecycle.value}.")
            return _mkplan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="thread_weave_update", lines=lines)], focus_used=focus is not None)
        if thread_weave_update_kind == "park_declared":
            return _mkplan(
                kind=ResponsePlanKind.STRUCTURED,
                sections=[ResponsePlanSection(title="thread_weave_update", lines=[
                    "Rendben, ezt parkolt szálként kezelem.",
                    f"Thread lifecycle: {thread_weave_state.thread_lifecycle.value}.",
                    f"Állapot-karbantartás: {thread_weave_state.temporary_state_lifecycle.value}.",
                ])],
                focus_used=focus is not None,
            )
        if thread_weave_update_kind == "close_declared":
            return _mkplan(
                kind=ResponsePlanKind.STRUCTURED,
                sections=[ResponsePlanSection(title="thread_weave_update", lines=[
                    "Rendben, ezt lezárt részként kezelem.",
                    f"Thread lifecycle: {thread_weave_state.thread_lifecycle.value}.",
                ])],
                focus_used=focus is not None,
            )
        if thread_weave_update_kind == "return_to_main_declared":
            lines = ["Rendben, ezt főszálra-visszatérésként kezelem."]
            if thread_weave_state.main_thread_key:
                lines.append(f"Főszál megerősítve: {clean_display_text(thread_weave_state.main_thread_key)}")
            if thread_weave_state.detour_thread_key:
                lines.append(f"A kitérő megmarad háttérként: {clean_display_text(thread_weave_state.detour_thread_key)}")
            lines.append(f"Thread lifecycle: {thread_weave_state.thread_lifecycle.value}.")
            return _mkplan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="thread_weave_update", lines=lines)], focus_used=focus is not None)

    if thread_weave_state is not None and thread_weave_query_family is not None:
        if thread_weave_query_family == "thread_relation_query":
            message = (thread_weave_query_message or "").lower()
            lines = [f"Szál-kapcsolat: {thread_weave_state.relation.value}."]
            if "mellekszal" in message or "kitero" in message:
                if thread_weave_state.detour_thread_key:
                    lines.append(f"Mellékszál/kitérő: {clean_display_text(thread_weave_state.detour_thread_key)}")
                else:
                    lines.append("Most nincs egyértelműen rögzített mellékszál.")
                if thread_weave_state.main_thread_key:
                    lines.append(f"Főszál ettől még: {clean_display_text(thread_weave_state.main_thread_key)}")
            elif "foszal" in message:
                if thread_weave_state.main_thread_key:
                    lines.append(f"Főszál: {clean_display_text(thread_weave_state.main_thread_key)}")
                if thread_weave_state.detour_thread_key:
                    lines.append(f"Utolsó kitérő: {clean_display_text(thread_weave_state.detour_thread_key)}")
            else:
                if thread_weave_state.main_thread_key:
                    lines.append(f"Főszál: {clean_display_text(thread_weave_state.main_thread_key)}")
                if thread_weave_state.detour_thread_key:
                    lines.append(f"Kitérő: {clean_display_text(thread_weave_state.detour_thread_key)}")
            return _mkplan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="thread_relation", lines=lines)], focus_used=focus is not None)

        if thread_weave_query_family == "conclusion_query":
            lines = [
                f"Konklúzió állapot: {thread_weave_state.conclusion_status.value}.",
                f"Konklúzió érvényesség: {thread_weave_state.conclusion_validity.value}.",
                f"Állapot-karbantartás: {thread_weave_state.temporary_state_lifecycle.value}.",
            ]
            if thread_weave_state.conclusion_text:
                lines.append(f"Levonható tanulság (szál-szövésből): {clean_display_text(thread_weave_state.conclusion_text)}")
            else:
                lines.append("Még nincs elég erős, megalapozott konklúzió rögzítve.")
            return _mkplan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="conclusion", lines=lines)], focus_used=focus is not None)

        if thread_weave_query_family == "applicability_query":
            lines = [
                f"Mostani alkalmazhatóság: {thread_weave_state.applicability_status.value}.",
                f"Thread lifecycle: {thread_weave_state.thread_lifecycle.value}.",
                f"Állapot-karbantartás: {thread_weave_state.temporary_state_lifecycle.value}.",
            ]
            if thread_weave_state.conclusion_text:
                lines.append(f"Kiinduló konklúzió: {clean_display_text(thread_weave_state.conclusion_text)}")
            if thread_weave_state.applicability_reason:
                lines.append(clean_display_text(thread_weave_state.applicability_reason))
            return _mkplan(kind=ResponsePlanKind.UNCERTAINTY_LABELED, sections=[ResponsePlanSection(title="applicability", lines=lines)], focus_used=focus is not None)
    ingest_ack = _current_ingest_ack_lines(evidence_pack, evidence_ingest_from_current_turn)
    if ingest_ack is not None:
        return _mkplan(
            kind=ResponsePlanKind.STRUCTURED,
            sections=[ResponsePlanSection(title="evidence_ingest_ack", lines=ingest_ack)],
            focus_used=focus is not None,
        )

    source_awareness = _source_awareness_lines(interpretation_text, evidence_pack)
    if source_awareness is not None:
        return _mkplan(
            kind=ResponsePlanKind.STRUCTURED,
            sections=[ResponsePlanSection(title="source_awareness", lines=source_awareness)],
            focus_used=focus is not None,
        )

    grounded_lines = _evidence_grounded_lines(interpretation_text, evidence_pack, workframe_state)
    if grounded_lines is not None:
        return _mkplan(
            kind=ResponsePlanKind.STRUCTURED,
            sections=[ResponsePlanSection(title="source_grounded_evidence", lines=grounded_lines)],
            focus_used=focus is not None,
        )
    no_evidence = _no_evidence_lines(interpretation_text, evidence_pack)
    if no_evidence is not None:
        return _mkplan(
            kind=ResponsePlanKind.UNCERTAINTY_LABELED,
            sections=[ResponsePlanSection(title="no_evidence_ingested", lines=no_evidence)],
            focus_used=focus is not None,
        )
    ingest_intent = _ingest_intent_lines(interpretation_text)
    if ingest_intent is not None:
        return _mkplan(
            kind=ResponsePlanKind.STRUCTURED,
            sections=[ResponsePlanSection(title="evidence_ingest_intent", lines=ingest_intent)],
            focus_used=focus is not None,
        )

    if _needs_brief_recap(interpretation_text):
        recap_lines = _brief_recap_lines(focus)
        if recap_lines is not None:
            return _mkplan(
                kind=ResponsePlanKind.RECALL,
                sections=[ResponsePlanSection(title="brief_recap", lines=recap_lines)],
                focus_used=focus is not None,
            )

    if interpretation.memory_query is not None and personal_memory is not None:
        return _mkplan(
            kind=ResponsePlanKind.STRUCTURED,
            sections=[ResponsePlanSection(title="explicit_memory", lines=_memory_query_lines(interpretation.memory_query, personal_memory))],
            focus_used=focus is not None,
        )

    if workframe_state is not None and workframe_queries is not None:
        if getattr(workframe_queries, "asks_current_objective", False):
            lines = [f"A mostani cél: {clean_display_text(workframe_state.objective_text)}."] if workframe_state.objective_status.value == "active" and workframe_state.objective_text else ["Most nincs egyértelműen rögzített aktív cél."]
            return _mkplan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="current_objective", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_queries, "asks_current_work", False):
            lines = [f"Mostani munkakeret: {workframe_state.workframe.value}."]
            if workframe_state.objective_status.value == "active" and workframe_state.objective_text:
                lines.append(f"Aktív cél: {clean_display_text(workframe_state.objective_text)}.")
            else:
                lines.append("Aktív cél még nincs egyértelműen rögzítve.")
            return _mkplan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="current_work", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_queries, "asks_current_posture", False):
            return _mkplan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="current_posture", lines=[f"Mostani munkakeret: {workframe_state.workframe.value}."])], focus_used=focus is not None)
        if getattr(workframe_queries, "asks_current_blocker", False):
            lines = [f"Mostani fő probléma: {clean_display_text(workframe_state.blocker_text)}."] if workframe_state.blocker_text else ["Most nincs egyértelműen rögzített fő probléma."]
            return _mkplan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="current_blocker", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_queries, "asks_current_next_step", False):
            lines = [f"Mostani következő lépés: {clean_display_text(workframe_state.next_step_lines[0])}"] if workframe_state.next_step_lines else ["Most nincs megalapozottan rögzített következő lépés."]
            return _mkplan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="current_next_step", lines=lines)], focus_used=focus is not None)
        if any((getattr(workframe_queries, "asks_history_objective", False), getattr(workframe_queries, "asks_history_blocker", False), getattr(workframe_queries, "asks_history_next_step", False))):
            state = historical_workframe_state or workframe_state
            return _mkplan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="historical_state", lines=_history_lines(state))], focus_used=focus is not None)
        if getattr(workframe_queries, "asks_certainty_split", False) or getattr(workframe_queries, "asks_next_step_certainty", False):
            return _mkplan(kind=ResponsePlanKind.UNCERTAINTY_LABELED, sections=[ResponsePlanSection(title="certainty_split", lines=_certainty_lines(workframe_state))], focus_used=focus is not None)
        if any((
            getattr(workframe_queries, "asks_missing_info", False),
            getattr(workframe_queries, "asks_open_questions", False),
            getattr(workframe_queries, "asks_assumptions", False),
            getattr(workframe_queries, "asks_decision_state", False),
            getattr(workframe_queries, "asks_evidence_gaps", False),
            getattr(workframe_queries, "asks_progress_block_reason", False),
        )):
            return _mkplan(kind=ResponsePlanKind.UNCERTAINTY_LABELED, sections=[ResponsePlanSection(title="decision_readiness", lines=_decision_readiness_lines(workframe_state))], focus_used=focus is not None)

    if interpretation.kind.value == "personal_entry" and interpretation.personal_entry is not None:
        signal = interpretation.personal_entry
        name = signal.owner_name or (owner_identity.owner_name if owner_identity is not None else None)
        display_name = f" {name}" if name else ""
        lines = _personal_entry_lines(signal.kind, display_name, signal.declared_focus, signal.declared_direction, time_context, workframe_state)
        return _mkplan(
            kind=ResponsePlanKind.PERSONAL_ENTRY,
            sections=[ResponsePlanSection(title="personal_entry", lines=lines)],
            focus_used=focus is not None,
        )


    if workframe_state is not None and workframe_updates is not None:
        if getattr(workframe_updates, "declares_work", False):
            lines = ["Rendben, ezt most aktív munkaszálként kezelem."]
            if workframe_state.objective_status.value == "active" and workframe_state.objective_text:
                lines.append(f"Aktív cél: {clean_display_text(workframe_state.objective_text)}.")
            else:
                lines.append("Aktív cél még nincs kimondva, ezt pontosíthatjuk.")
            return _mkplan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="workframe_update", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_updates, "declares_objective", False):
            if workframe_state.objective_status.value == "active" and workframe_state.objective_text:
                lines = [f"Rendben, az aktív célt rögzítem: {clean_display_text(workframe_state.objective_text)}."]
            else:
                lines = ["Értettem, célról beszélünk, de még pontosítás kell az aktív cél rögzítéséhez."]
            return _mkplan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="objective_update", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_updates, "declares_chat", False):
            lines = ["Rendben, most beszélgető módban maradunk."]
            natural = _natural_workframe_answer(interpretation_text, workframe_state)
            if natural is not None:
                lines.extend(natural)
            elif workframe_state.objective_status.value == "active" and workframe_state.objective_text:
                lines.append(f"A korábbi aktív célt megőrzöm háttér-kontinuitásnak: {clean_display_text(workframe_state.objective_text)}.")
            return _mkplan(kind=ResponsePlanKind.PERSONAL_ENTRY, sections=[ResponsePlanSection(title="chat_update", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_updates, "declares_blocker_explicit", False):
            lines = ["Rendben, ezt explicit fő blokkert állításként rögzítem."]
            if workframe_state.blocker_text:
                lines.append(f"Fő blokker: {clean_display_text(workframe_state.blocker_text)}.")
            if workframe_state.objective_status.value == "active" and workframe_state.objective_text:
                lines.append(f"Aktív cél változatlanul: {clean_display_text(workframe_state.objective_text)}.")
            return _mkplan(kind=ResponsePlanKind.STRUCTURED, sections=[ResponsePlanSection(title="blocker_update", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_updates, "hedged_blocker", False):
            lines = ["Ezt lehetséges blokkerként kezelem, még nem biztos állításként."]
            if workframe_state.blocker_text:
                lines.append(f"Jelölt blokker: {clean_display_text(workframe_state.blocker_text)}.")
            return _mkplan(kind=ResponsePlanKind.UNCERTAINTY_LABELED, sections=[ResponsePlanSection(title="hedged_blocker", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_updates, "hedged_objective", False):
            lines = ["Értem, ez egy lehetséges cél-javaslat, még nem végleges aktív cél."]
            if workframe_state.objective_text:
                lines.append(f"Javasolt cél: {clean_display_text(workframe_state.objective_text)}.")
            return _mkplan(kind=ResponsePlanKind.UNCERTAINTY_LABELED, sections=[ResponsePlanSection(title="hedged_objective", lines=lines)], focus_used=focus is not None)
        if getattr(workframe_updates, "hedged_next_step", False):
            lines = ["Ezt javasolt következő lépésként kezelem, nem biztos döntésként."]
            if workframe_state.next_step_lines:
                lines.append(f"Lehetséges következő lépés: {clean_display_text(workframe_state.next_step_lines[0])}")
            return _mkplan(kind=ResponsePlanKind.UNCERTAINTY_LABELED, sections=[ResponsePlanSection(title="hedged_next_step", lines=lines)], focus_used=focus is not None)

    if interpretation.claim_capture:
        return _mkplan(
            kind=ResponsePlanKind.ORDINARY,
            sections=[ResponsePlanSection(title="claim_capture", lines=_claim_capture_lines(interpretation))],
            focus_used=focus is not None,
        )
    if workframe_state is not None and workframe_queries is not None and (getattr(workframe_queries, "asks_blocker", False) or getattr(workframe_queries, "asks_next_step", False) or getattr(workframe_queries, "asks_plan", False)):
        natural = _natural_workframe_answer(interpretation_text, workframe_state)
        if natural is not None:
            return _mkplan(
                kind=ResponsePlanKind.ORDINARY,
                sections=[ResponsePlanSection(title="workframe_natural", lines=natural)],
                focus_used=focus is not None,
            )
        return _mkplan(
            kind=ResponsePlanKind.STRUCTURED,
            sections=[ResponsePlanSection(title="workframe", lines=_workframe_lines(workframe_state))],
            focus_used=focus is not None,
        )


    if interpretation.kind.value == "compare_previous" and not has_previous_thread:
        return _mkplan(
            kind=ResponsePlanKind.CLARIFICATION,
            sections=[ResponsePlanSection(title="compare_previous_missing", lines=["Még nincs előző szál, ezért nem tudok megalapozott összehasonlítást adni."])],
            focus_used=focus is not None,
        )

    if strategy.strategy == AnswerStrategy.CLARIFICATION:
        question = strategy.clarification_question.question if strategy.clarification_question else (recall.clarification_message or "Pontosíts kérlek.")
        return _mkplan(
            kind=ResponsePlanKind.CLARIFICATION,
            sections=[ResponsePlanSection(title="clarification", lines=[question])],
            focus_used=focus is not None,
        )

    if objective.kind.value == "clarify":
        return _mkplan(
            kind=ResponsePlanKind.CLARIFICATION,
            sections=[ResponsePlanSection(title="clarification", lines=["Pontosíts kérlek röviden, mit hasonlítsak vagy melyik szálra gondolsz."])],
            focus_used=focus is not None,
        )

    if strategy.strategy in {AnswerStrategy.RECALL_ANSWER, AnswerStrategy.RESUME_ANSWER} and recall.resolved and recall.snapshot is not None:
        limit = max(1, context.config.conversation.recall_line_limit)
        selected = recall.snapshot.snapshot_lines[-limit:]
        lead = "Röviden itt tartottunk:" if interpretation.kind.value.startswith("recall") else f"Visszahoztam a(z) {recall.snapshot.thread_key} szálat."
        lines = [lead]
        for line in selected:
            lines.append(f"• #{line.turn_index}: {clean_display_text(line.user_message)} → {clean_display_text(line.assistant_reply)}")
        followup = "Innen menjünk tovább?" if context.config.conversation.response_followup_enabled else None
        return _mkplan(
            kind=ResponsePlanKind.RECALL if interpretation.kind.value.startswith("recall") else ResponsePlanKind.RESUME,
            sections=[ResponsePlanSection(title="recall_summary", lines=lines)],
            followup_prompt=followup,
            focus_used=focus is not None,
        )

    if strategy.strategy in {AnswerStrategy.STRUCTURED_ANSWER, AnswerStrategy.UNCERTAINTY_LABELED_ANSWER}:
        sections = _synthesis_sections(synthesis)
        if not sections:
            sections = [ResponsePlanSection(title="ordinary", lines=["Rendben."])]
        kind = ResponsePlanKind.STRUCTURED if strategy.strategy != AnswerStrategy.UNCERTAINTY_LABELED_ANSWER else ResponsePlanKind.UNCERTAINTY_LABELED
        return _mkplan(kind=kind, sections=sections, focus_used=focus is not None)

    if strategy.strategy == AnswerStrategy.DIRECT_ANSWER:
        reflective = _reflective_fallback_lines(interpretation_text)
        if reflective is not None:
            return _mkplan(
                kind=ResponsePlanKind.ORDINARY,
                sections=[ResponsePlanSection(title="reflective", lines=reflective)],
                focus_used=focus is not None,
            )
        natural = _natural_workframe_answer(interpretation_text, workframe_state) if workframe_state is not None else None
        if natural is not None:
            return _mkplan(
                kind=ResponsePlanKind.ORDINARY,
                sections=[ResponsePlanSection(title="workframe_natural", lines=natural)],
                focus_used=focus is not None,
            )
        if chat_lock_active:
            lines = ["Rendben, maradjunk kötetlen beszélgetésben."]
        elif _direct_should_use_synthesis(objective, decomposition, synthesis):
            sections = _synthesis_sections(synthesis)
            if sections:
                return _mkplan(
                    kind=ResponsePlanKind.STRUCTURED,
                    sections=sections,
                    focus_used=focus is not None,
                )
            lines = ["Rendben, menjünk röviden tovább ezen."]
        elif followup_target:
            lines = [f"Rendben, innen folytatjuk: {clean_display_text(followup_target)}"]
        elif interpretation.relative_time_terms and not chat_lock_active:
            joined = ", ".join(interpretation.relative_time_terms)
            lines = [f"Értem az időhivatkozásokat ({clean_display_text(joined)}). Mondd, pontosan mire fókuszáljunk."]
        else:
            if direct_answer_required:
                lines = ["Rövid válasz: ezt a kérdést meg tudom válaszolni, de kérlek pontosítsd egy fél mondatban, mire kérdezel rá a leginkább."]
            else:
                lines = ["Rendben, itt vagyok veled."]
        return _mkplan(
            kind=ResponsePlanKind.ORDINARY,
            sections=[ResponsePlanSection(title="ordinary", lines=lines)],
            focus_used=focus is not None,
        )

    if strategy.strategy == AnswerStrategy.CORRECTION_REDIRECT:
        lines = ["Rendben, korrigálok és átirányítom a választ a kért irányra."]
        if "előző" in interpretation.kind.value or comparison_pack.winner_kind.value in {"correction_redirect", "resume"}:
            lines.append("Az előző szálhoz igazodva folytatom.")
        return _mkplan(
            kind=ResponsePlanKind.CORRECTION_REDIRECT,
            sections=[ResponsePlanSection(title="correction_redirect", lines=lines)],
            focus_used=focus is not None,
        )

    ordinary_lines: list[str] = []
    reflective = _reflective_fallback_lines(interpretation_text)
    if reflective is not None:
        ordinary_lines.extend(reflective)
    if followup_target:
        ordinary_lines.append(f"Rendben, innen folytatjuk: {clean_display_text(followup_target)}")
    return _mkplan(
        kind=ResponsePlanKind.ORDINARY,
        sections=[ResponsePlanSection(title="ordinary", lines=ordinary_lines)],
        focus_used=focus is not None,
    )
