#!/bin/bash
# ============================================================
# avvia_mac.sh — Avvia il quiz (macOS / Linux)
# ============================================================
# Uso: apri il Terminale, vai nella cartella del progetto e
#      esegui:  bash avvia_mac.sh
# ============================================================

cd "$(dirname "$0")"

echo ""
echo "=== Database Crocette — Ing. Software B ==="
echo ""

# Controlla se Python 3 è installato
if ! command -v python3 &>/dev/null; then
  echo "ERRORE: Python 3 non trovato."
  echo "Scaricalo da https://www.python.org/downloads/ e riprova."
  exit 1
fi

# Installa le dipendenze se mancanti
echo "Controllo dipendenze..."
python3 -m pip install --quiet -r requirements.txt

echo "Avvio del server..."
echo "Il browser si aprirà automaticamente su http://localhost:5000"
echo "Premi CTRL+C per fermare il server."
echo ""

python3 app.py
