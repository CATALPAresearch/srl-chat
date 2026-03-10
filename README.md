# SRL Chat

An AI agent that conducts structured interviews with students about their self-regulated learning strategies, based on Zimmerman & Martinez-Pons' Self-Regulated Learning Interview Schedule.

> Zimmerman, B. J., & Martinez-Pons, M. M. (1986). _Development of a Structured Interview for Assessing Student Use of Self-Regulated Learning Strategies._ American Educational Research Journal, 23(4), 614–628. https://doi.org/10.2307/1163093

The application runs as a Flask API backed by PostgreSQL and Ollama. It can be used in three modes:

| Mode             | Description                                                |
| ---------------- | ---------------------------------------------------------- |
| **Standalone**   | Browser UI at `http://localhost:5000` — no Moodle required |
| **LTI Provider** | Embedded inside Moodle via LTI 1.0 launch                  |
| **Docker**       | Production-ready setup with Docker Compose                 |

---

## Prerequisites

| Dependency | Version | Purpose                                          |
| ---------- | ------- | ------------------------------------------------ |
| Python     | 3.12    | API backend                                      |
| Poetry     | ≥ 1.8   | Python dependency management                     |
| Node.js    | ≥ 18    | Frontend build                                   |
| PostgreSQL | ≥ 16    | Database                                         |
| pgvector   | —       | PostgreSQL vector extension (for RAG embeddings) |
| Ollama     | —       | Local LLM inference                              |

### Install PostgreSQL + pgvector (macOS)

```bash
brew install postgresql@17 pgvector
brew link --overwrite postgresql@17
brew services start postgresql@17
```

Create the database:

```bash
createdb srl_chat
psql -d srl_chat -c "CREATE EXTENSION IF NOT EXISTS vector"
```

### Install Ollama

```bash
brew install ollama
ollama serve          # start the server (runs on port 11434)
ollama pull phi3:latest
```

---

## Project structure

```
srl-chat/
├── api/                        # Flask backend
│   ├── main.py                 # Entrypoint
│   ├── lti.py                  # LTI blueprint (/lti/launch, /lti/ui)
│   ├── lti_client.py           # LTI test client (simulates Moodle launch)
│   ├── app_config.py           # Flask config (reads .env)
│   ├── db_setup.py             # DB seed with embeddings
│   ├── db_setup_no_embed.py    # DB seed without embeddings (local dev)
│   ├── .env                    # Local dev environment variables
│   ├── app/
│   │   ├── __init__.py         # Flask app factory
│   │   ├── routes.py           # API + static file routes
│   │   ├── core.py             # Conversation state machine
│   │   ├── llm.py              # Ollama client
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── steps.py            # Interview step definitions
│   │   ├── actions.py          # Logging actions enum
│   │   ├── config/             # Interview JSON configs
│   │   └── db_utils/crud.py    # DB helpers
│   └── static/lti/             # LTI frontend assets
│       ├── index.html
│       ├── app-lazy.js         # Webpack AMD bundle (copy of amd/build/)
│       └── core/               # AMD stubs (ajax.js, localstorage.js)
├── frontend/                   # Vue.js 2 source
│   ├── src/
│   ├── index.html              # Standalone HTML
│   ├── core/                   # AMD stubs for standalone mode
│   ├── webpack.config.js
│   └── package.json
├── amd/build/                  # Webpack build output
├── discord/                    # Discord bot (separate service)
├── RAG/                        # Embedding & evaluation scripts
├── .env                        # Docker Compose environment
├── env.example                 # Template for .env
├── docker-compose.yml          # Production Docker setup
└── develop.docker-compose.yml  # Development Docker setup
```

---

## Environment files

There are **two** `.env` files with different purposes:

| File                  | Used by                    | Purpose                                                   |
| --------------------- | -------------------------- | --------------------------------------------------------- |
| `.env` (project root) | Docker Compose             | Read by `docker-compose.yml` for container environment    |
| `api/.env`            | Flask (Poetry / local dev) | Read by `app_config.py` via `dotenv` when running locally |

For **local development without Docker**, only `api/.env` matters.
For **Docker Compose**, only the root `.env` matters.

### Key variables in `api/.env`

```ini
BASE_URL=http://localhost:11434/       # Ollama server URL
MODEL=phi3:latest                      # LLM model name
PG_HOST=localhost                      # PostgreSQL host
PG_USER=postgres                       # PostgreSQL user
PG_PORT=5432
PG_PASSWORD=postgres
PG_DB=srl_chat
DISABLE_LLM=false                      # Set true to skip LLM calls (dry-run)
INTERVIEW_PROTOCOL=interview_default   # Which interview config to use
SECRET_KEY=dev_secret_key_123          # Flask session secret
```

---

## Database setup

There are two setup scripts:

| Script                 | Use case                                                                                             |
| ---------------------- | ---------------------------------------------------------------------------------------------------- |
| `db_setup.py`          | Full setup including **strategy embeddings** (requires a HuggingFace API token in `EMBEDDING_TOKEN`) |
| `db_setup_no_embed.py` | Setup **without embeddings** — use this for local dev when you only need the interview agent         |

Run from the `api/` directory:

```bash
cd api
poetry run python db_setup_no_embed.py    # local dev (no embeddings)
# OR
poetry run python db_setup.py             # full setup with embeddings
```

---

## 1. Standalone mode (local development)

### Install dependencies

```bash
# Backend
cd api
poetry install

# Frontend
cd ../frontend
npm install
```

### Build the frontend

```bash
cd frontend
npx webpack --mode development
```

This outputs `amd/build/app-lazy.min.js`. Copy it to the LTI static directory too:

```bash
cp amd/build/app-lazy.min.js api/static/lti/app-lazy.js
```

### Seed the database

```bash
cd api
poetry run python db_setup_no_embed.py
```

### Start the server

```bash
cd api
poetry run python main.py
```

Open **http://localhost:5000** in your browser. Click "Start Chat" to begin the SRL interview.

### Test with curl

```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Start a conversation
curl -X POST http://localhost:5000/startConversation \
  -H "Content-Type: application/json" \
  -d '{"language": "en", "client": "discord", "userid": "testuser1"}'

# Send a reply
curl -X POST http://localhost:5000/reply \
  -H "Content-Type: application/json" \
  -d '{"message": "I usually summarise my notes and use mind maps.", "client": "discord", "userid": "testuser1"}'

# Reset a conversation
curl -X POST http://localhost:5000/resetConversation \
  -H "Content-Type: application/json" \
  -d '{"client": "discord", "userid": "testuser1"}'
```

---

## 2. LTI mode (Moodle integration)

The application provides an LTI 1.0 Tool Provider. Moodle launches the tool via `POST /lti/launch`, which stores the user session and redirects to `/lti/ui`, serving the Vue.js chat interface.

### How it works

1. Moodle sends a POST to `https://<your-host>/lti/launch` with LTI parameters (`context_id`, `user_id`, etc.)
2. Flask stores the user in the session and redirects to `/lti/ui`
3. `/lti/ui` serves `api/static/lti/index.html`, which loads the AMD bundle via RequireJS
4. The AMD stubs in `api/static/lti/core/` replace Moodle's `core/ajax` and `core/localstorage` modules

### Configure Moodle

In Moodle, add an **External Tool** activity:

| Setting          | Value                            |
| ---------------- | -------------------------------- |
| Tool URL         | `https://<your-host>/lti/launch` |
| Consumer Key     | _(your key)_                     |
| Shared Secret    | _(your secret)_                  |
| Launch Container | Embed / New Window               |

> **Important:** Moodle typically runs on HTTPS. The Flask server must also be on HTTPS (or behind a reverse proxy) to avoid mixed-content blocking in browsers.

### Test locally with the LTI client

The `lti_client.py` script simulates a Moodle LTI launch:

```bash
cd api
poetry run python lti_client.py
```

This sends a POST to `http://localhost:5000/lti/launch` with sample LTI parameters and prints the HTML response.

---

## 3. Docker Compose

### Development

Uses `develop.docker-compose.yml` with hot-reload and a local PostgreSQL container:

```bash
cp env.example .env
# Edit .env: set BASE_URL, MODEL, PG_PASSWORD, etc.

docker compose -f develop.docker-compose.yml up postgres-dev api-dev
```

### Production

Uses `docker-compose.yml` with gunicorn:

```bash
cp env.example .env
# Edit .env for production values

docker compose build --no-cache
docker compose up -d
```

---

## API endpoints

| Method | Path                 | Description                                    |
| ------ | -------------------- | ---------------------------------------------- |
| `GET`  | `/`                  | Standalone web UI                              |
| `POST` | `/startConversation` | Begin a new SRL interview                      |
| `POST` | `/reply`             | Send a user message and get the agent response |
| `POST` | `/resetConversation` | Archive and reset a conversation               |
| `POST` | `/lti/launch`        | LTI 1.0 launch endpoint (Moodle POST)          |
| `GET`  | `/lti/ui`            | LTI chat interface                             |

### Request / response format

```json
// POST /startConversation
{
  "language": "en",       // "de" or "en"
  "client": "discord",    // client identifier
  "userid": "testuser1"   // unique user ID
}

// POST /reply
{
  "message": "I use mind maps and flashcards.",
  "client": "discord",
  "userid": "testuser1"
}

// POST /resetConversation
{
  "client": "discord",
  "userid": "testuser1"
}
```

---

## License

See [LICENSE.txt](LICENSE.txt).
