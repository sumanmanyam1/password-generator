# PassGen — Password Generator

A local password generator with a **Python engine**, a **Flask API**, and an
**attractive React frontend**. Everything runs on your own machine.

## Project structure

```
passwordgenerator/
├── backend/
│   ├── core/              # Password logic (generation, strength, storage)
│   │   ├── generator.py
│   │   ├── strength_analyzer.py
│   │   └── storage.py
│   ├── cli/
│   │   └── passgen.py     # Original command-line tool
│   ├── api/
│   │   └── app.py         # Flask API (used by the frontend)
│   ├── data/
│   │   └── passwords.txt  # Your saved passwords (plain text, perms 600)
│   └── requirements.txt
├── frontend/              # React + Vite web app
│   └── src/
│       ├── App.jsx
│       ├── App.css
│       └── api.js
├── docs/                  # Guides and CLI docs
├── run_backend.sh
└── run_frontend.sh
```

## Run it locally (two terminals)

**Terminal 1 — backend API:**

```bash
./run_backend.sh
# → http://127.0.0.1:5000
```

**Terminal 2 — frontend:**

```bash
./run_frontend.sh
# → http://127.0.0.1:5173   ← open this in your browser
```

The frontend proxies `/api/*` requests to the Flask backend, so you only need
to open the frontend URL.

### Manual commands (if you prefer)

Backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python api/app.py
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## The original CLI still works

```bash
cd backend
python cli/passgen.py list
python cli/passgen.py generate --label github --length 20
```

## Web app features

- **Generate** — length slider, toggle uppercase/digits/symbols, live strength
  meter, copy-to-clipboard, and optional save with a label.
- **Analyze** — paste any password and get a score, crack-time estimate, and
  detailed feedback.
- **Vault** — list saved labels, reveal/copy passwords, and delete entries.

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Service check |
| POST | `/api/generate` | Generate (optionally save) |
| POST | `/api/bulk` | Generate many |
| POST | `/api/analyze` | Strength analysis |
| GET | `/api/passwords` | List saved labels |
| GET | `/api/passwords/<label>` | Reveal a saved password |
| DELETE | `/api/passwords/<label>` | Delete an entry |

## Security note

Passwords are generated with Python's `secrets` module (cryptographically
secure). Storage is **plain text** in `backend/data/passwords.txt` with `600`
permissions — readable by your user only, but not encrypted. The API binds to
`127.0.0.1`, so it is not exposed to your network.
```
