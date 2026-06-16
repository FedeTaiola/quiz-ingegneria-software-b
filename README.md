# Database Crocette - Ingegneria del Software B

Mini sito locale per allenarsi con le domande a crocetta di Ingegneria del Software B.

Il progetto usa:

- un backend Python/Flask che legge il file Excel con le domande;
- una pagina web in `frontend/index.html`;
- salvataggio locale dello storico in file JSON generati automaticamente.

## Avvio rapido

Non aprire direttamente `frontend/index.html`: il sito ha bisogno del server Python.

### Windows

1. Installa Python 3.8 o superiore da <https://www.python.org/downloads/>.
2. Durante l'installazione spunta "Add Python to PATH".
3. Fai doppio click su `avvia_windows.bat`.
4. Il browser si apre su `http://localhost:5000`.

### macOS / Linux

1. Installa Python 3.8 o superiore.
2. Apri il Terminale nella cartella del progetto.
3. Esegui:

```bash
bash avvia_mac.sh
```

4. Il browser si apre su `http://localhost:5000`.

## Avvio manuale

Se gli script non funzionano, apri un terminale nella cartella del progetto ed esegui:

```bash
python -m pip install -r requirements.txt
python app.py
```

Su macOS/Linux, se `python` non esiste:

```bash
python3 -m pip install -r requirements.txt
python3 app.py
```

Poi apri `http://localhost:5000`.

## Struttura

```text
DATABASE CROCETTE/
├── app.py
├── DATABASE_CROCETTE_INGE_SW_B.py
├── doamnde ing B.xlsx
├── requirements.txt
├── avvia_windows.bat
├── avvia_mac.sh
├── frontend/
│   └── index.html
├── .gitignore
└── README.md
```

## File generati automaticamente

Questi file vengono creati durante l'uso e non vanno caricati su GitHub:

- `database_test.json`
- `domande_sbagliate.json`
- `__pycache__/`

Sono gia' esclusi in `.gitignore`.

## Problemi comuni

| Problema | Soluzione |
| --- | --- |
| `python` non trovato | Installa Python e aggiungilo al PATH |
| `ModuleNotFoundError` | Esegui `python -m pip install -r requirements.txt` |
| La pagina non carica le domande | Controlla che il server sia acceso e apri `http://localhost:5000` |
| File Excel non trovato | Lascia `doamnde ing B.xlsx` nella stessa cartella di `app.py` |
| Porta 5000 occupata | Avvia con `PORT=5001 python app.py` e apri `http://localhost:5001` |

## Note per GitHub

Prima di pubblicare il repository, carica questi file:

- codice Python;
- cartella `frontend`;
- file Excel delle domande;
- `requirements.txt`;
- script di avvio;
- `README.md`;
- `.gitignore`.

Non caricare file generati o cache.
