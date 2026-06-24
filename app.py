"""
app.py — Backend Flask per DATABASE CROCETTE (Ingegneria del Software B)
=========================================================================
Espone le API REST che il frontend HTML/JS usa per:
  GET  /api/domande          → carica N domande casuali per la sessione
  POST /api/sessione/avvia   → avvia una nuova sessione, restituisce id
  POST /api/risposta         → invia la risposta a una domanda
  GET  /api/risultati        → restituisce i risultati della sessione corrente
  GET  /api/storico          → storico delle sessioni passate

Avvio rapido:
  pip install flask
  python app.py
Poi apri http://localhost:5000
"""

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
import os
import uuid
import time

# Import delle funzioni core già scritte nel modulo principale
from quiz_engine import (
    carica_domande,
    seleziona_domande,
    mescola_risposte,
    registra_domande_mostrate,
    calcola_punteggio,
    salva_risultati,
    salva_domande_sbagliate,
    NUM_DOMANDE,
    RESULTS_FILE,
    WRONG_ANSWERS_FILE,
    SCRIPT_DIR,
)

import json

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")

# ---------------------------------------------------------------------------
# Sessioni in memoria  { session_id: { domande, risposte_utente, start_time } }
# ---------------------------------------------------------------------------
sessioni: dict = {}


# ---------------------------------------------------------------------------
# Serve il frontend (index.html) alla root
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# ---------------------------------------------------------------------------
# API: avvia una nuova sessione e restituisce le domande
# ---------------------------------------------------------------------------
@app.route("/api/sessione/avvia", methods=["POST"])
def avvia_sessione():
    """
    Body JSON opzionale: { "num_domande": 9 }
    Risposta: { "session_id": "...", "domande": [...], "totale": N }
    """
    body = request.get_json(silent=True) or {}
    n = int(body.get("num_domande", NUM_DOMANDE))

    try:
        tutte = carica_domande()
    except Exception as e:
        return jsonify({"errore": str(e)}), 500

    domande = seleziona_domande(tutte, n)
    session_id = str(uuid.uuid4())

    domande_sessione = [mescola_risposte(d) for d in domande]

    sessioni[session_id] = {
        "domande":        domande_sessione,
        "risposte_utente": [],   # { domanda, risposte, corretta, data }
        "start_time":     time.time(),
    }

    registra_domande_mostrate(domande)

    # Serializza le domande per il client (non esporre la risposta corretta)
    domande_client = []
    for i, d in enumerate(domande_sessione):
        domande_client.append({
            "index":    i,
            "domanda":  d["domanda"],
            "risposte": d["risposte"],   # legacy payload
            "opzioni": [
                {"lettera": lettera, "testo": testo}
                for lettera, testo in d["risposte"].items()
            ],
        })

    return jsonify({
        "session_id": session_id,
        "domande":    domande_client,
        "totale":     len(domande),
    })


# ---------------------------------------------------------------------------
# API: invia la risposta a una singola domanda
# ---------------------------------------------------------------------------
@app.route("/api/risposta", methods=["POST"])
def registra_risposta():
    """
    Body JSON: { "session_id": "...", "index": 3, "risposta": "b" }
    risposta può essere una lettera ('a','b','c','d') oppure 'n' (salta)
    Risposta: { "corretta": bool | null, "risposta_corretta": "b", "feedback": "..." }
    """
    body = request.get_json(silent=True) or {}
    session_id = body.get("session_id")
    index      = body.get("index")
    risposta   = str(body.get("risposta", "n")).strip().lower()

    if session_id not in sessioni:
        return jsonify({"errore": "Sessione non trovata o scaduta."}), 404

    sessione  = sessioni[session_id]
    domande   = sessione["domande"]

    try:
        index = int(index)
    except (TypeError, ValueError):
        return jsonify({"errore": "Indice domanda non valido."}), 400

    if index < 0 or index >= len(domande):
        return jsonify({"errore": "Indice domanda non valido."}), 400

    domanda_obj = domande[index]
    corretta    = domanda_obj["corretta"]
    opzioni_valide = list(domanda_obj["risposte"].keys()) + ["n"]

    if risposta not in opzioni_valide:
        return jsonify({"errore": f"Risposta non valida. Opzioni: {opzioni_valide}"}), 400

    # Salva la risposta dell'utente per questa domanda
    sessione["risposte_utente"].append({
        "domanda":  domanda_obj["domanda"],
        "risposte": domanda_obj["risposte"],
        "corretta": corretta,
        "data":     risposta,
    })

    # Feedback immediato
    if risposta == "n":
        esito = None
        feedback = f"Saltata. La risposta corretta era: {corretta.upper()}"
    elif risposta == corretta:
        esito = True
        feedback = "Corretto! +1 punto"
    else:
        esito = False
        feedback = f"Sbagliato! -0.5 punti. La risposta corretta era: {corretta.upper()}"

    return jsonify({
        "corretta":           esito,       # True / False / null (saltata)
        "risposta_corretta":  corretta,
        "testo_corretto":     domanda_obj["risposte"].get(corretta, ""),
        "feedback":           feedback,
    })


# ---------------------------------------------------------------------------
# API: risultati finali della sessione
# ---------------------------------------------------------------------------
@app.route("/api/risultati", methods=["GET"])
def risultati():
    """
    Query param: ?session_id=...
    Risposta: { corrette, sbagliate, saltate, punteggio, totale, durata_minuti,
                domande_sbagliate: [...] }
    """
    session_id = request.args.get("session_id")
    if session_id not in sessioni:
        return jsonify({"errore": "Sessione non trovata."}), 404

    sessione = sessioni[session_id]
    risposte = sessione["risposte_utente"]
    durata   = (time.time() - sessione["start_time"]) / 60

    risultato = calcola_punteggio([
        {"corretta": r["corretta"], "data": r["data"]} for r in risposte
    ])

    # Dettaglio domande sbagliate da mostrare al frontend
    sbagliate_detail = []
    for r in risposte:
        if r["data"] != "n" and r["data"] != r["corretta"]:
            sbagliate_detail.append({
                "domanda":           r["domanda"],
                "risposta_data":     r["data"],
                "testo_risposta_data": r["risposte"].get(r["data"], ""),
                "risposta_corretta": r["corretta"],
                "testo_risposta_corretta": r["risposte"].get(r["corretta"], ""),
            })

    # Salva su file
    salva_risultati(risultato, durata)
    salva_domande_sbagliate(risposte)

    # Rimuovi la sessione dalla memoria
    del sessioni[session_id]

    return jsonify({
        **risultato,
        "durata_minuti":    round(durata, 2),
        "sbagliate_detail": sbagliate_detail,
    })


# ---------------------------------------------------------------------------
# API: storico sessioni passate
# ---------------------------------------------------------------------------
@app.route("/api/storico", methods=["GET"])
def storico():
    storico_data = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            try:
                storico_data = json.load(f)
            except json.JSONDecodeError:
                storico_data = []
    return jsonify(storico_data)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import webbrowser
    port = int(os.environ.get("PORT", "5000"))
    url = f"http://localhost:{port}"
    print(f"\nBackend Flask avviato su {url}")
    print("   Premi CTRL+C per fermare il server.\n")
    webbrowser.open(url)
    app.run(debug=False, port=port)
