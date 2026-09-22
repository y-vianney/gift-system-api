# Gift System 🎁

A modern, secure, and professional Python platform for managing Secret Santa-style assignments with an **anonymous Santa-Child Letterbox** (asynchronous Q&A/chat), SQLite persistence, Fernet authenticated cryptography, and a sleek web application.

---

## Highlights

- 🎅 **Dual-Role Dashboard (Single Private Key)**: Each participant uses a single confidential key to view their assigned recipient (as Santa) and access their secret letterbox (as Child).
- ✉️ **Anonymous Letterbox**: Santa can ask questions anonymously to their Child to discover gift preferences without spoiling the surprise. The Child can reply directly.
- 🔒 **Strong Cryptography**: Keys are salted and hashed (SHA-256) in SQLite. Conversation threads are encrypted using Fernet (AES-128-CBC + HMAC-SHA256).
- ⚡ **Lightweight & Fast**: Built with FastAPI, SQLite3 (zero-maintenance embedded DB), and a responsive festive Web UI (Tailwind CSS).
- 🔄 **Backward Compatible**: Retains the legacy `POST /worker-name` endpoint and root-level compatibility shims (`api.py`, `cli.py`, `core.py`, `config.py`, `gs_smtp.py`).

---

## Project Structure

```text
src/gift_system/
├── core/                  # Core domain logic, models, cryptography, and matching
│   ├── crypto.py          # Fernet encryption, key derivation, salted hashing
│   ├── matching.py        # O(N) cyclic derangement algorithm (public/private pools)
│   └── models.py          # Domain dataclasses and Pydantic DTOs
├── storage/               # Persistence layer
│   ├── database.py        # SQLite schema management & connection pooling
│   └── repository.py      # CRUD queries for participants, assignments, messages
├── services/              # Business logic
│   ├── santa_service.py   # Assignment generation, sessions, email dispatch
│   └── chat_service.py    # Letterbox thread access, message encryption/decryption
├── api/                   # FastAPI Web & REST API
│   ├── routes/            # Modular route controllers (auth, chat, legacy)
│   └── app.py             # App factory, CORS, static UI routing
├── ui/
│   └── index.html         # Sleek, responsive, festive Single-Page Application
├── cli.py                 # Command-line interface
├── config.py              # Environment configuration
└── smtp.py                # Email sending helpers
```

---

## Setup

1. **Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate # Linux/macOS
   ```

2. **Install dependencies**:
   ```bash
   pip install -e .
   ```

3. **Configure Environment**:
   ```bash
   copy .env.example .env
   ```

4. **Prepare Employees**:
   Edit `data/employees.txt` using the format:
   ```text
   name|email|active|public
   ```
   Example:
   ```text
   Alice|alice@example.com|active|public
   Bob|bob@example.com|active|public
   Charlie|charlie@example.com|active|private
   Diana|diana@example.com|active|private
   ```

---

## Usage

### 1. Command-Line Interface (CLI)

- **Generate assignments**:
  ```bash
  python -m gift_system.cli build data/employees.txt
  ```
  *(To send notification emails directly, add `--send-emails`. To overwrite existing state, add `--force`)*

- **Check system status**:
  ```bash
  python -m gift_system.cli status
  ```

- **View assignment (as a participant)**:
  ```bash
  python -m gift_system.cli view
  ```

- **Chat / Letterbox in CLI**:
  ```bash
  python -m gift_system.cli chat
  ```

- **Start Web Application & API**:
  ```bash
  python -m gift_system.cli serve --port 8000
  ```

---

### 2. Web Application & REST API

Run the server:
```bash
uvicorn gift_system.api:app --reload
```
- Open `http://localhost:8000` in any browser to use the interactive festive dashboard.
- API Documentation is available at `http://localhost:8000/docs`.

#### Main Endpoints:
- `POST /api/auth/session` : Authenticates a private key and returns dual-role details.
- `GET /api/threads/{thread_id}/messages?key=...` : Reads encrypted messages in a thread.
- `POST /api/threads/{thread_id}/messages` : Posts a message as Santa or Child (and triggers instant WS broadcast).
- `POST /worker-name` : Legacy endpoint returning `{"worker_name": "..."}`.
- `GET /` : Health check or Web UI.

---

### 3. Real-Time WebSocket (Frontend Integration)

Connect to the lightweight WebSocket stream for instant, real-time message updates:

```text
WS /api/threads/{thread_id}/ws?key={participant_private_key}
```

#### Client Lifecycle:
1. **Connection handshake**: Server sends confirmation:
   ```json
   { "type": "connected", "thread_id": "thr_...", "role": "SANTA" }
   ```
2. **New message broadcast (Instant push)**:
   ```json
   {
     "type": "new_message",
     "message": {
       "id": 42,
       "sender_role": "SANTA",
       "content": "Bonjour ! As-tu des préférences de cadeaux ?",
       "created_at": "2026-09-17T20:00:00.000Z"
     }
   }
   ```
3. **Send message via WebSocket**:
   ```json
   { "content": "Je préfère les livres d'aventure !" }
   ```
4. **Heartbeat / Ping**:
   Send `{ "type": "ping" }` $\to$ receives `{ "type": "pong" }`.

#### Frontend (React / Vue / Vanilla JS) Example:
```javascript
const ws = new WebSocket(`wss://api.domain.com/api/threads/${threadId}/ws?key=${privateKey}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'new_message') {
    // Append message to chat or trigger refresh
    console.log('Nouveau message reçu:', data.message);
  }
};
```

---

## Running Tests

Run the test suite with `pytest`:
```bash
pytest -v
```
