# Database Crocette - Ingegneria del Software B

Mini applicazione locale per allenarsi con le domande a crocetta di Ingegneria del Software B.

Il progetto include:

- un backend Python con Flask;
- un frontend web in `frontend/index.html`;
- il file Excel con le domande;
- il salvataggio locale di storico e domande sbagliate in JSON generati automaticamente.

## Cosa serve

- Python 3.8 o superiore
- il file Excel `domande_ingegneria_software_b.xlsx` nella stessa cartella di `app.py`

## Avvio rapido

Non aprire direttamente `frontend/index.html`: il progetto funziona tramite server locale.

### Windows

1. Installa Python da <https://www.python.org/downloads/>.
2. Durante l'installazione attiva `Add Python to PATH`.
3. Fai doppio click su `start_windows.bat`.
4. Il browser si aprirà su `http://localhost:5000`.

### macOS / Linux

1. Installa Python 3.
2. Apri il terminale nella cartella del progetto.
3. Esegui:

```bash
bash start_mac.sh
```

4. Il browser si aprirà su `http://localhost:5000`.

## Avvio manuale

Se preferisci eseguire tutto a mano:

```bash
python -m pip install -r requirements.txt
python app.py
```

Se `python` non è disponibile, prova:

```bash
python3 -m pip install -r requirements.txt
python3 app.py
```

Poi apri `http://localhost:5000`.

## Come funziona

1. Il backend legge le domande dal file Excel.
2. Il frontend richiede una nuova sessione al server.
3. Ogni sessione mostra 9 domande.
4. L'ordine delle opzioni viene mescolato a ogni quiz, così non si imparano le lettere a memoria.
5. Il backend favorisce le domande mai viste o viste meno spesso.
6. Le risposte vengono inviate una alla volta.
7. Alla fine il server calcola il punteggio e salva lo storico in locale.

## File presenti nel progetto

```text
DATABASE CROCETTE/
├── app.py
├── quiz_engine.py
├── domande_ingegneria_software_b.xlsx
├── requirements.txt
├── start_windows.bat
├── start_mac.sh
├── frontend/
│   └── index.html
├── .gitignore
└── README.md
```

## File generati automaticamente

Questi file vengono creati durante l'uso dell'applicazione e non vanno caricati su GitHub:

- `quiz_history.json`
- `wrong_answers.json`
- `question_stats.json`
- `__pycache__/`

Sono già esclusi in `.gitignore`.

## Come usarlo senza errori

Se una persona scarica il progetto e segue queste istruzioni:

1. ha Python installato;
2. lascia `domande_ingegneria_software_b.xlsx` nella cartella principale;
3. installa le dipendenze con `requirements.txt`;
4. avvia `app.py` oppure `start_windows.bat` / `start_mac.sh`;
5. apre `http://localhost:5000`;

allora può usare il quiz normalmente, rispondere alle domande, saltarle, vedere il risultato finale e consultare lo storico.

## Problemi comuni

| Problema | Soluzione |
| --- | --- |
| `python` non trovato | Installa Python e aggiungilo al PATH |
| `ModuleNotFoundError` | Esegui `python -m pip install -r requirements.txt` |
| Il sito non carica le domande | Controlla che il server sia avviato e usa `http://localhost:5000` |
| Il file Excel non viene trovato | Verifica che `domande_ingegneria_software_b.xlsx` sia nella stessa cartella di `app.py` |
| Le opzioni sembrano sempre uguali | Riavvia un nuovo quiz: l'ordine delle opzioni viene rimescolato a ogni sessione |
| Porta 5000 occupata | Avvia con `PORT=5001 python app.py` e apri `http://localhost:5001` |

## Nota importante

Se il file Excel cambia nome o viene spostato, il progetto non riesce a leggere le domande.
Quindi il nome e la posizione del file devono rimanere identici a quelli previsti dal codice.
