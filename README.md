# SRL Chat

SRL Chat is a conversational AI agent that conducts structured interviews with students about their self-regulated learning (SRL) strategies. It guides students through a multi-step dialogue, asking about the strategies they use across different study contexts, then detects and classifies those strategies and asks about usage frequency. The interview protocol is based on Zimmerman & Martinez-Pons' Self-Regulated Learning Interview Schedule.

> Zimmerman, B. J., & Martinez-Pons, M. M. (1986). _Development of a Structured Interview for Assessing Student Use of Self-Regulated Learning Strategies._ American Educational Research Journal, 23(4), 614-628. https://doi.org/10.2307/1163093

## Features

- Multi-step interview agent (intro, strategy detection, probing, frequency rating, summary)
- Strategy detection via LLM chain-of-thought reasoning or RAG-based cosine similarity (configurable)
- Configurable interview protocols via JSON files and the `INTERVIEW_PROTOCOL` env variable
- Bilingual support (English/German) with extensible translation system
- SRL-O survey module with Likert-scale questionnaire, stored in the database
- Full dialogue persistence: every student message and every agent response is stored per turn
- Structured activity logging to the database (user, unix timestamp, action, value, user agent, IP, context, strategy, turn, step, HTTP status)
- Detected strategies and frequency ratings stored per user, context, and interview answer
- Three deployment modes: standalone browser UI, LTI 1.0 integration with Moodle, Docker Compose
- LTI 1.0 Tool Provider for embedding inside LMS courses (e.g. Moodle, Illias) 
- Discord bot integration (optional, separate service)

## Prerequisites

| Dependency | Version | Purpose                                          |
| ---------- | ------- | ------------------------------------------------ |
| Python     | 3.12    | Backend                                          |
| Poetry     | >= 1.8  | Python dependency management                     |
| Node.js    | >= 18   | Frontend build                                   |
| PostgreSQL | >= 16   | Database                                         |
| pgvector   | -       | PostgreSQL vector extension (for RAG embeddings) |
| Ollama     | -       | Local LLM inference                              |

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
ollama serve
ollama pull phi3:latest
```

---

## Project structure

```
srl-chat/
├── backend/                    # Flask backend (Poetry project)
│   ├── main.py                 # Entrypoint
│   ├── pyproject.toml          # Python dependencies
│   ├── app/
│   │   ├── __init__.py         # Flask app factory, DB init, blueprint registration
│   │   ├── config.py           # Flask config (reads .env)
│   │   ├── routes.py           # API + static file + survey routes
│   │   ├── core.py             # Conversation state machine
│   │   ├── llm.py              # Ollama LLM client
│   │   ├── rag.py              # RAG-based strategy detection (pgvector)
│   │   ├── steps.py            # Interview step definitions
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── actions.py          # LogAction enum
│   │   ├── logging_utlis.py    # Structured activity logging
│   │   ├── lti.py              # LTI blueprint (/lti/launch, /lti/ui)
│   │   ├── lti_client.py       # LTI test client
│   │   └── database/           # DB CRUD helpers, setup scripts
│   ├── config/                 # JSON configuration files
│   │   ├── interview/          # Interview protocol variants
│   │   ├── prompts.json        # LLM prompt templates
│   │   ├── translations.json   # UI translations (en/de)
│   │   ├── survey_srl-o.json   # SRL-O questionnaire definition
│   │   └── learning_strategies.json
│   ├── static/lti/             # LTI frontend assets (webpack output)
│   ├── certs/                  # TLS certificates (for LTI)
│   └── logs/                   # Rotating log files
├── frontend/                   # Vue.js 2 source
│   ├── src/
│   │   ├── components/         # AgentChat, LLMChat, RAGChat, SurveyView, ...
│   │   ├── router/             # Vue Router (hash mode)
│   │   └── store/              # Vuex store
│   ├── index.html              # Standalone HTML shell
│   └── webpack.config.js       # AMD library target -> backend/static/lti/
├── discord/                    # Discord bot (optional, separate service)
├── tests/                      # pytest test suite + evaluation data
├── scripts/                    # Utility scripts (docx conversion, strategy merge)
├── docs/                       # Documentation
├── docker-compose.yml          # Production Docker setup
├── develop.docker-compose.yml  # Development Docker setup
└── env.example                 # Template for .env
```

---

## Environment variables

There are two `.env` files:

| File                  | Used by                    | Purpose                            |
| --------------------- | -------------------------- | ---------------------------------- |
| `.env` (project root) | Docker Compose             | Container environment variables    |
| `backend/.env`        | Flask (Poetry / local dev) | Read by `app/config.py` via dotenv |

For local development without Docker, only `backend/.env` matters.

### Key variables

```ini
BASE_URL=http://localhost:11434/       # Ollama server URL
MODEL=phi3:latest                      # LLM model name
PG_HOST=localhost
PG_USER=postgres
PG_PORT=5432
PG_PASSWORD=postgres
PG_DB=srl_chat
DISABLE_LLM=false                      # Set true to skip LLM calls (dry-run)
SECRET_KEY=dev_secret_key_123          # Flask session secret
INTERVIEW_PROTOCOL=interview_default   # Interview config (file in config/interview/)
USE_RAG_STRATEGY=false                 # Use RAG-based strategy detection instead of LLM
RAG_EMBEDDING_MODEL=nomic-embed-text   # Ollama embedding model for RAG
```

---

## Database setup

Two setup scripts are available in `backend/app/database/`:

| Script              | Use case                                                                    |
| ------------------- | --------------------------------------------------------------------------- |
| `setup.py`          | Full setup including strategy embeddings (requires Ollama nomic-embed-text) |
| `setup_no_embed.py` | Setup without embeddings (local dev, interview agent only)                  |

```bash
cd backend
poetry run python -m app.database.setup_no_embed    # local dev
# OR
poetry run python -m app.database.setup             # full setup with embeddings
```

---

## 1. Standalone mode (local development)

### Install dependencies

```bash
# Backend
cd backend
poetry install

# Frontend
cd ../frontend
npm install
```

### Build the frontend

```bash
cd frontend
npm run build
```

This outputs `app-lazy.js` directly into `backend/static/lti/`.

### Seed the database

```bash
cd backend
poetry run python -m app.database.setup_no_embed
```

### Start the server

```bash
cd backend
poetry run python main.py
```

Open http://localhost:5000 in your browser. The tabs provide access to:

- Agent Chat (SRL interview)
- LLM Chat (direct LLM conversation)
- Document Chat (RAG-based)
- Survey (SRL-O questionnaire)

---

## 2. LTI mode (Moodle integration)

The application provides an LTI 1.0 Tool Provider. Moodle launches the tool via `POST /lti/launch`, which stores the user session and redirects to `/lti/ui`.

### Configure Moodle

In Moodle, add an External Tool activity:

| Setting          | Value                            |
| ---------------- | -------------------------------- |
| Tool URL         | `https://<your-host>/lti/launch` |
| Consumer Key     | _(your key)_                     |
| Shared Secret    | _(your secret)_                  |
| Launch Container | Embed / New Window               |

The Flask server must be on HTTPS (or behind a reverse proxy) to avoid mixed-content blocking.

### Test locally with the LTI client

```bash
cd backend
poetry run python -m app.lti_client
```

---

## 3. Docker Compose

### Development

```bash
cp env.example .env
# Edit .env with your values
docker compose -f develop.docker-compose.yml up postgres-dev api-dev
```

### Production

```bash
cp env.example .env
# Edit .env for production values
docker compose build --no-cache
docker compose up -d
```

---

## API endpoints

| Method | Path                   | Description                                    |
| ------ | ---------------------- | ---------------------------------------------- |
| `GET`  | `/`                    | Standalone web UI                              |
| `POST` | `/startConversation`   | Begin a new SRL interview                      |
| `POST` | `/reply`               | Send a user message and get the agent response |
| `POST` | `/resetConversation`   | Archive and reset a conversation               |
| `GET`  | `/translations/<lang>` | Get UI translations for a language             |
| `GET`  | `/user_language/`      | Get a user's language                          |
| `POST` | `/lti/launch`          | LTI 1.0 launch endpoint                        |
| `GET`  | `/lti/ui`              | LTI chat interface                             |
| `GET`  | `/survey/<id>`         | Get survey definition JSON                     |
| `POST` | `/survey/<id>/submit`  | Submit survey responses                        |
| `GET`  | `/survey/<id>/results` | Get all responses for a survey                 |

### Request / response format

```json
// POST /startConversation
{ "language": "en", "client": "discord", "userid": "testuser1" }

// POST /reply
{ "message": "I use mind maps and flashcards.", "client": "discord", "userid": "testuser1" }

// POST /resetConversation
{ "client": "discord", "userid": "testuser1" }

// POST /survey/srl-o/submit
{ "userid": "testuser1", "client": "standalone", "language": "en", "responses": { "oase_1": 4, "oase_2": 5 } }
```

---

## Data model

The key database tables and what they store:

| Table                  | Purpose                                                              |
| ---------------------- | -------------------------------------------------------------------- |
| `users`                | User identity (id + client) and language                             |
| `languages`            | Supported languages (en, de)                                         |
| `contexts`             | Study contexts from the interview protocol                           |
| `strategy`             | Strategy codes (e.g. 001-001)                                        |
| `strategy_translation` | Strategy names and descriptions per language                         |
| `interview_answer`     | Every student message, per turn/context/step                         |
| `llm_response`         | Every agent response, per turn/context/step                          |
| `user_strategy`        | Detected strategies per user, context, and frequency                 |
| `strategy_evaluation`  | Aggregated strategy evaluation per user                              |
| `state`                | Current conversation state (step, turn, context)                     |
| `activity_log`         | Structured event log (timestamp, action, value, user agent, IP, ...) |
| `survey_responses`     | Submitted survey answers as JSON                                     |
| `strategy_embedding`   | RAG embeddings (pgvector, 768-dim)                                   |

---

## License

See [LICENSE.txt](LICENSE.txt).
