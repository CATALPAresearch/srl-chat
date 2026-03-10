# SRL Agent – LTI Integration Setup Guide

This document describes how to run the SRL Agent as an LTI external tool inside Moodle, with a local Ollama LLM backend.

---

## Architecture Overview

```
Moodle (Docker) → LTI POST launch → Flask (api/) → Ollama (local) → llama3.2
                                         ↕
                                   PostgreSQL (Docker)
```

- **Moodle** sends an LTI 1.1 launch request to Flask
- **Flask** serves the Vue.js chat UI and handles all API calls
- **Ollama** runs the LLM locally (llama3.2, ~2GB)
- **PostgreSQL** stores conversation state and user data

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | |
| Docker Desktop | Latest | For Moodle + PostgreSQL |
| Ollama | 0.17+ | https://ollama.com |
| Node.js | 18+ | Only needed to rebuild frontend |

---

## 1. Clone the Repository

```bash
git clone <repo-url>
cd srl-chat
git checkout issue-6-lti-ui
```

---

## 2. Install Ollama and Pull the Model

Download Ollama from https://ollama.com and install it.

Then pull the required model (this downloads ~2GB):

```bash
ollama pull llama3.2
```

Verify it works:

```bash
ollama run llama3.2 "Hallo, wer bist du?"
```

**Important:** Start Ollama **before** starting Docker to ensure it gets enough RAM.

---

## 3. Configure Environment Variables

Copy the example env file and fill in your values:

```bash
cp api/.env.example api/.env
```

Edit `api/.env`:

```env
SECRET_KEY=your-secret-key-here
PG_HOST=localhost
PG_PORT=5432
PG_USER=chat
PG_PASSWORD=example
PG_DB=srl_chat
DISABLE_LLM=false
INTERVIEW_PROTOCOL=interview_default
BASE_URL=http://localhost:11434
API_KEY=ollama
MODEL=llama3.2
```

---

## 4. Start PostgreSQL

```bash
docker run --name srl-postgres \
  -e POSTGRES_USER=chat \
  -e POSTGRES_PASSWORD=example \
  -e POSTGRES_DB=srl_chat \
  -p 5432:5432 \
  -d pgvector/pgvector:pg16
```

If the container already exists:

```bash
docker start srl-postgres
```

Create the `activity_log` table (required, not yet in migrations):

```bash
docker exec -it srl-postgres psql -U chat -d srl_chat -c "
CREATE TABLE IF NOT EXISTS activity_log (
    id VARCHAR PRIMARY KEY,
    timestamp BIGINT,
    user_id VARCHAR,
    user_client VARCHAR,
    action VARCHAR,
    value TEXT,
    user_agent VARCHAR,
    ip_address VARCHAR,
    context VARCHAR,
    strategy VARCHAR,
    turn INTEGER,
    step VARCHAR,
    http_status INTEGER
);"
```

---

## 5. Install Python Dependencies and Start Flask

```bash
cd api
pip install -r requirements.txt
python main.py
```

Flask will start on `http://0.0.0.0:5000`.

---

## 6. Start Moodle

```bash
cd <repo-root>/moodle   # or wherever your docker-compose.yml is
docker compose up -d
```

Wait 30–60 seconds for Moodle to initialize, then fix the `wwwroot` URL:

```bash
# Check current value first
docker exec moodle sh -c "grep 'wwwroot' /var/www/html/config.php"

# Only run this if it shows 'http://localhost' without :8080
docker exec moodle sh -c "sed -i 's|http://localhost|http://localhost:8080|g' /var/www/html/config.php"
```

Moodle is now accessible at `http://localhost:8080`.

Login credentials: `moodleuser` / `Admin1234!`

If login fails after restart, reset the password:

```bash
docker exec moodle php /var/www/html/admin/cli/reset_password.php \
  --username=moodleuser --password=Admin1234!
```

---

## 7. Find Your Docker Bridge IP

The LTI Tool URL must use the Docker bridge IP so Moodle (inside Docker) can reach Flask (on the host).

**On Windows:**

```powershell
ipconfig | findstr "172."
```

**On Linux/macOS:**

```bash
ip route | grep docker
# or
docker network inspect bridge | grep Gateway
```

Note this IP — you will need it in the next step.

---

## 8. Configure the LTI Tool in Moodle

1. Go to `http://localhost:8080` → log in
2. Navigate to **Site Administration → Plugins → Activity modules → External tool → Manage tools**
3. Click **Add tool manually** (or edit the existing SRL Agent tool)
4. Set the following:

| Field | Value |
|-------|-------|
| Tool name | SRL Agent |
| Tool URL | `http://<YOUR-BRIDGE-IP>:5000/lti/launch?v=2` |
| LTI version | LTI 1.0/1.1 |
| Consumer key | `moodle_key` |
| Shared secret | `geheimer_schluessel_123` |

Replace `<YOUR-BRIDGE-IP>` with the IP found in step 7 (e.g. `172.23.96.1`).

5. Save the tool
6. Add it to a course as an **External Tool** activity

---

## 9. Test the Integration

1. Navigate to the course in Moodle
2. Click the **SRL Agent** activity
3. Click **Start Interview**
4. Wait 15–30 seconds for the first LLM response (model loading time)
5. Type a message like *"Ich studiere Informatik"* and send

You should see a real German AI response in the chat UI.

---

## Startup Order (Important)

Always start services in this order to avoid RAM issues:

```
1. ollama serve          (or Ollama runs as background service)
2. docker start srl-postgres
3. docker compose up -d  (Moodle)
4. python main.py        (Flask)
```

---

## Troubleshooting

### "Moodle redirected you too many times"

The `wwwroot` in config.php has a duplicate `:8080`. Fix it:

```bash
docker exec moodle sh -c "grep 'wwwroot' /var/www/html/config.php"
# If it shows http://localhost:8080:8080, fix it:
docker exec moodle sh -c "sed -i 's|http://localhost:8080:8080|http://localhost:8080|g' /var/www/html/config.php"
```

### "Fehler beim Start des Interviews" (Error starting interview)

- Check Flask is running and reachable at `http://localhost:5000`
- Check Ollama is running: `ollama list`
- Check the bridge IP in the LTI Tool URL matches `ipconfig | findstr "172."`
- Check PostgreSQL is running: `docker ps | grep postgres`

### LLM returns empty responses

Ollama may be out of RAM. Stop Docker temporarily, test Ollama directly:

```bash
ollama run llama3.2 "Hallo"
```

If that works, the issue is RAM contention. Close other applications and try again.

### activity_log errors in Flask logs

These are non-critical logging warnings. The conversation still works. Run the SQL from step 4 to create the table if not done yet.

---

## Known Limitations

- LTI OAuth signature is not verified (known gap, planned for follow-up)
- The bridge IP changes on every Docker network restart and must be updated manually in Moodle
- Responses take 15–30 seconds due to CPU-only inference (no GPU)
- The built Vue.js bundle (`api/static/lti/app-lazy.js`) is committed to the repo so Node.js is not required to run the demo

---

## Rebuilding the Frontend (Optional)

Only needed if you modify Vue.js source files:

```bash
cd frontend
npm install
npm run build
cp amd/build/app-lazy.min.js ../api/static/lti/app-lazy.js
```
