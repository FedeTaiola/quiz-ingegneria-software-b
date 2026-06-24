from __future__ import annotations

"""
DATABASE CROCETTE — Ingegneria del Software B (UniBS)
======================================================
Script refactorizzato con funzioni separate, pronto per essere
usato sia da terminale che come backend Flask (Step 2).

Sistema di punteggio:
  - Risposta corretta  → +1 punto
  - Risposta sbagliata → -0.5 punti (penalità del professore)
  - Saltata (n)        →  0 punti
  - Punteggio minimo clampato a 0
"""

import os
import sys
import time
import json
import hashlib
import random

import pandas as pd

# ---------------------------------------------------------------------------
# Costanti
# ---------------------------------------------------------------------------
SCRIPT_DIR         = os.path.dirname(os.path.abspath(__file__))
EXCEL_NAME         = "domande_ingegneria_software_b.xlsx"
EXCEL_PATH         = os.path.join(SCRIPT_DIR, EXCEL_NAME)
RESULTS_FILE       = os.path.join(SCRIPT_DIR, "quiz_history.json")
WRONG_ANSWERS_FILE = os.path.join(SCRIPT_DIR, "wrong_answers.json")
QUESTION_STATS_FILE = os.path.join(SCRIPT_DIR, "question_stats.json")

NUM_DOMANDE        = 9
PUNTI_CORRETTA     = 1.0
PENALITA_SBAGLIATA = 0.5

# Codici ANSI
GREEN  = "\033[92m"
RED    = "\033[91m"
BLUE   = "\033[94m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

# ---------------------------------------------------------------------------
# Funzioni core (riusabili dal backend Flask)
# ---------------------------------------------------------------------------

def carica_domande(excel_path: str = EXCEL_PATH) -> list[dict]:
    """
    Legge il file Excel e restituisce una lista di dizionari con:
      - domanda   : str
      - risposte  : dict { 'a': testo, 'b': testo, ... }
      - corretta  : str  ('a' | 'b' | 'c' | 'd')
    """
    if not os.path.exists(excel_path):
        raise FileNotFoundError(
            f"File Excel non trovato: {excel_path}\n"
            f"Assicurati che '{EXCEL_NAME}' sia nella stessa cartella dello script."
        )

    try:
        df = pd.read_excel(excel_path, header=None)
    except Exception as e:
        raise RuntimeError(f"Errore nella lettura del file Excel: {e}")

    df.columns = ["Domanda", "Risposte", "Corretta"]
    df = df.dropna(subset=["Domanda", "Risposte", "Corretta"]).reset_index(drop=True)

    domande = []
    for _, row in df.iterrows():
        testo_domanda = str(row["Domanda"]).strip()
        corretta      = str(row["Corretta"]).strip().lower()

        # Parsing risposte: split su newline, pulizia, poi dizionario {lettera: testo}
        righe = [r.strip() for r in str(row["Risposte"]).replace("\r\n", "\n").replace("\r", "\n").split("\n") if r.strip()]
        risposte_dict = {}
        for riga in righe:
            if len(riga) >= 3 and riga[0].isalpha() and riga[1] == ".":
                lettera = riga[0].lower()
                testo   = riga[2:].strip()
                risposte_dict[lettera] = testo

        # Scarta la domanda se non ha risposte parsabili o la risposta corretta non è tra le opzioni
        if not risposte_dict or corretta not in risposte_dict:
            continue

        domande.append({
            "id":       calcola_id_domanda(testo_domanda, risposte_dict, corretta),
            "domanda":  testo_domanda,
            "risposte": risposte_dict,
            "corretta": corretta,
        })

    if not domande:
        raise ValueError("Nessuna domanda valida trovata nel file Excel.")

    return domande


def calcola_id_domanda(domanda: str, risposte: dict[str, str], corretta: str) -> str:
    """Crea un identificatore stabile per una domanda."""
    payload = {
        "domanda": domanda.strip(),
        "risposte": {k: risposte[k] for k in sorted(risposte)},
        "corretta": corretta.strip().lower(),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def carica_statistiche_domande() -> dict[str, int]:
    """Restituisce un conteggio di quante volte ogni domanda è stata mostrata."""
    if not os.path.exists(QUESTION_STATS_FILE):
        return {}

    with open(QUESTION_STATS_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {}

    if isinstance(data, dict):
        return {str(k): int(v) for k, v in data.items()}

    return {}


def salva_statistiche_domande(stats: dict[str, int]) -> None:
    with open(QUESTION_STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def registra_domande_mostrate(domande: list[dict]) -> None:
    """Incrementa il contatore di esposizione per le domande mostrate."""
    stats = carica_statistiche_domande()
    for domanda in domande:
        domanda_id = domanda["id"]
        stats[domanda_id] = stats.get(domanda_id, 0) + 1
    salva_statistiche_domande(stats)


def mescola_risposte(domanda: dict) -> dict:
    """Restituisce la domanda con risposte e lettera corretta rimescolate."""
    opzioni = list(domanda["risposte"].items())
    random.shuffle(opzioni)

    lettere = ["a", "b", "c", "d", "e", "f"]
    nuove_risposte: dict[str, str] = {}
    nuova_corretta = None

    for idx, (vecchia_lettera, testo) in enumerate(opzioni):
        lettera = lettere[idx]
        nuove_risposte[lettera] = testo
        if vecchia_lettera == domanda["corretta"]:
            nuova_corretta = lettera

    if nuova_corretta is None:
        nuova_corretta = domanda["corretta"]

    return {
        **domanda,
        "risposte": nuove_risposte,
        "corretta": nuova_corretta,
    }


def _pesi_domande(domande: list[dict], stats: dict[str, int]) -> list[float]:
    pesi = []
    for domanda in domande:
        conteggio = stats.get(domanda["id"], 0)
        pesi.append(1.0 / (conteggio + 1))
    return pesi


def seleziona_domande_pesate(domande: list[dict], n: int) -> list[dict]:
    """
    Selezione senza duplicati:
    - priorità alle domande mai viste;
    - poi alle meno frequenti, con peso inverso al numero di esposizioni.
    """
    n = min(n, len(domande))
    if n <= 0:
        return []

    stats = carica_statistiche_domande()
    unseen = [d for d in domande if stats.get(d["id"], 0) == 0]
    selected: list[dict] = []

    if unseen:
        take = min(n, len(unseen))
        selected.extend(random.sample(unseen, take))

    remaining = n - len(selected)
    if remaining <= 0:
        return selected

    pool = [d for d in domande if d not in selected]
    while pool and remaining > 0:
        weights = _pesi_domande(pool, stats)
        chosen = random.choices(pool, weights=weights, k=1)[0]
        selected.append(chosen)
        pool.remove(chosen)
        remaining -= 1

    return selected


def seleziona_domande(domande: list[dict], n: int = NUM_DOMANDE) -> list[dict]:
    """
    Restituisce n domande senza duplicati, privilegiando quelle meno viste.
    """
    return seleziona_domande_pesate(domande, n)


def calcola_punteggio(risposte_utente: list[dict]) -> dict:
    """
    Riceve una lista di dizionari con:
      { 'corretta': 'b', 'data': 'a' | 'n' }  (n = saltata)

    Restituisce:
      {
        'corrette':  int,
        'sbagliate': int,
        'saltate':   int,
        'punteggio': float,   # clampato a 0
        'totale':    int,
      }
    """
    corrette  = 0
    sbagliate = 0
    saltate   = 0
    punteggio = 0.0

    for r in risposte_utente:
        data     = r.get("data", "n")
        corretta = r.get("corretta", "")

        if data == "n":
            saltate += 1
        elif data == corretta:
            corrette  += 1
            punteggio += PUNTI_CORRETTA
        else:
            sbagliate += 1
            punteggio -= PENALITA_SBAGLIATA

    punteggio = max(0.0, punteggio)

    return {
        "corrette":  corrette,
        "sbagliate": sbagliate,
        "saltate":   saltate,
        "punteggio": round(punteggio, 2),
        "totale":    len(risposte_utente),
    }


def salva_risultati(risultato: dict, durata_minuti: float) -> None:
    """
    Appende i risultati della sessione al file JSON storico.
    """
    entry = {
        **risultato,
        "durata_minuti": round(durata_minuti, 2),
        "data":          time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    storico = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            try:
                storico = json.load(f)
            except json.JSONDecodeError:
                storico = []

    storico.append(entry)

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(storico, f, ensure_ascii=False, indent=2)


def salva_domande_sbagliate(sessione: list[dict]) -> None:
    """
    Appende le domande sbagliate della sessione al file JSON dedicato.
    sessione: lista di { domanda, risposte, corretta, data }
    Solo le domande con risposta errata (non saltate) vengono salvate.
    """
    sbagliate = [
        s for s in sessione
        if s.get("data") not in ("n", s.get("corretta"))
    ]

    if not sbagliate:
        return

    storico = []
    if os.path.exists(WRONG_ANSWERS_FILE):
        with open(WRONG_ANSWERS_FILE, "r", encoding="utf-8") as f:
            try:
                storico = json.load(f)
            except json.JSONDecodeError:
                storico = []

    for s in sbagliate:
        storico.append({
            "domanda":           s["domanda"],
            "risposta_data":     s["data"],
            "risposta_corretta": s["corretta"],
            "data":              time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    with open(WRONG_ANSWERS_FILE, "w", encoding="utf-8") as f:
        json.dump(storico, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Interfaccia terminale (invariata rispetto alla versione precedente)
# ---------------------------------------------------------------------------

def run_quiz_terminale() -> None:
    """Esegue il quiz in modalità terminale interattiva."""

    try:
        tutte_le_domande = carica_domande()
    except (FileNotFoundError, RuntimeError, ValueError) as e:
        print(f"\n{RED}Errore:{RESET} {e}")
        sys.exit(1)

    domande = seleziona_domande(tutte_le_domande)
    domande = [mescola_risposte(d) for d in domande]
    registra_domande_mostrate(domande)
    n       = len(domande)

    print(f"\n\nInizio Quiz — {n} domande\n")
    print(f"  ✅ Risposta corretta  → +{PUNTI_CORRETTA} punto")
    print(f"  ❌ Risposta sbagliata → -{PENALITA_SBAGLIATA} punti (penalità)")
    print(f"  ⏭️  Salta (n)          →  0 punti\n")

    sessione   = []
    start_time = time.time()

    for i, domanda_obj in enumerate(domande, start=1):
        domanda  = domanda_obj["domanda"]
        risposte = domanda_obj["risposte"]
        corretta = domanda_obj["corretta"]
        opzioni  = list(risposte.keys())

        print(f"── Domanda {i}/{n} ──")
        print(f"{domanda}\n")
        for lettera, testo in risposte.items():
            print(f"  {lettera}. {testo}")
        print("\n  n. Non voglio rispondere")
        print("  q. Esci dal quiz")

        valide = opzioni + ["n", "q"]

        while True:
            scelta = input(f"\nRisposta ({'/'.join(valide)}): ").strip().lower()
            if scelta in valide:
                break
            print(f"  Inserisci una delle opzioni: {', '.join(valide)}")

        if scelta == "q":
            print(f"\n{YELLOW}Hai scelto di uscire dal quiz.{RESET}")
            sys.exit(0)

        sessione.append({
            "domanda":  domanda,
            "risposte": risposte,
            "corretta": corretta,
            "data":     scelta,
        })

        if scelta == "n":
            print(f"\n{BLUE}Saltata. La risposta corretta era: {corretta}{RESET}\n")
        elif scelta == corretta:
            print(f"\n{GREEN}Corretto! +{PUNTI_CORRETTA} punto{RESET}\n")
        else:
            print(f"\n{RED}Sbagliato! -{PENALITA_SBAGLIATA} punti. La risposta corretta era: {corretta}{RESET}\n")

    # ── Risultati finali ──
    durata_minuti = (time.time() - start_time) / 60
    risultato     = calcola_punteggio([{"corretta": s["corretta"], "data": s["data"]} for s in sessione])

    print("=" * 50)
    print(f"  Corrette:  {risultato['corrette']}/{n}")
    print(f"  Sbagliate: {risultato['sbagliate']}")
    print(f"  Saltate:   {risultato['saltate']}")
    print(f"  Punteggio: {risultato['punteggio']:.2f} / {n}")
    print(f"  Durata:    {durata_minuti:.2f} minuti")
    print("=" * 50)

    salva_risultati(risultato, durata_minuti)
    salva_domande_sbagliate(sessione)
    print(f"\nRisultati salvati in '{RESULTS_FILE}'.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_quiz_terminale()
