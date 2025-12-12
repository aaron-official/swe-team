# Task Tracker — Complete Software Architecture Document

This document is the single source of truth for implementing the Task Tracker application described in the PRD (requirements.md). It is written to be actionable by developers or an autonomous agent. It uses only packages that exist in the provided lockfile (see VERSION-SPECIFIC NOTES). All decisions, file lists, model definitions, APIs, DB schema, configuration, and implementation checklist are explicit.

> NOTE (required): The PRD requires a Node.js + Express backend running on port `3000`. The lockfile shows the *actual installed* Node packages and versions available in the environment. This architecture is explicitly designed to use the installed package versions:
> - express@4.18.2
> - better-sqlite3@7.6.2
> - joi@17.4.2
> - cors@2.8.5
> - morgan@1.10.0
> - nodemon@2.0.22 (dev)
>
> The lockfile also noted a peer/unmet dependency warning for `sqlite3@^5.1.6`. The architecture uses `better-sqlite3` (present) and documents steps to address native build needs and peer warnings. See Section 7.

---

## 1. Project Structure

The project root must contain the following files and folders. The snippet below meets the requested `REQUIRED OUTPUT STRUCTURE` (kept verbatim) and then shows the full, expanded structure recommended for implementation.

```
output/ 
├── backend_app.py      # Main backend application
├── frontend_app.py     # Frontend/UI application (if Python-based)
├── models.py           # Data models (if needed)
├── utils.py            # Utility functions (if needed)
└── data/               # Data storage directory
    └── .gitkeep
```

Expanded implementation tree (recommended, exact filenames to implement Node/Express backend + vanilla frontend):

```
.
├── Dockerfile
├── README.md
├── package.json
├── package-lock.json
├── .dockerignore
├── server/
│   ├── index.js                # Entry point: starts Express server on PORT
│   ├── db.js                   # DB initialization + seed logic (better-sqlite3)
│   ├── routes/
│   │   └── tasks.js            # All /api/tasks route handlers
│   ├── validators.js           # Joi validation schemas and helpers
│   ├── errors.js               # Central error types & error handler middleware
│   └── logger.js               # morgan setup and custom logging (optional)
├── public/
│   ├── index.html              # Single-page UI (vanilla HTML)
│   ├── app.js                  # Frontend JS (fetch + UI logic)
│   └── styles.css              # Dark theme CSS + responsive layout
├── data/
│   ├── .gitkeep
│   └── tasks.db                # SQLite file (created at runtime)
├── scripts/
│   └── seed.js                 # (Optional) Node script to seed DB manually
└── tests/
    └── api_examples.md         # curl/httpie samples and test checklist
```

Files referenced by the PRD but kept for compatibility / mapping:
- `backend_app.py`, `frontend_app.py`, `models.py`, `utils.py` — included in repo root as *optional* adapters or docs. The implementation targets Node files under `server/`, but these Python filenames are present as placeholders with instructions/comments in README for portability.

---

## 2. Backend Architecture

The backend is a Node.js Express application. Implementation should use the installed versions from lockfile (express@4.18.2, better-sqlite3@7.6.2, joi@17.4.2, cors@2.8.5, morgan@1.10.0).

### 2.1 Main Application (server/index.js)

#### Imports (verify these are in lockfile)
```javascript
// server/index.js
const express = require('express');         // VERIFY: express@4.18.2 (lockfile)
const cors = require('cors');               // VERIFY: cors@2.8.5
const morgan = require('morgan');           // VERIFY: morgan@1.10.0
const { initDbAndSeed } = require('./db'); // local module
const tasksRouter = require('./routes/tasks');
const { errorHandler } = require('./errors');
```

High-level responsibilities:
- Create Express app
- Configure middleware (JSON body parsing, morgan logging, CORS)
- Mount routes at `/api/tasks`
- Add global error handler
- Listen on configured PORT (default: 3000)

Skeleton (explicit developer-ready code):
```javascript
// server/index.js
const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const { initDbAndSeed } = require('./db');
const tasksRouter = require('./routes/tasks');
const { errorHandler } = require('./errors');

const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;
const CORS_ORIGIN = process.env.CORS_ORIGIN || 'http://localhost:3000';

const app = express();

// Middleware
app.use(morgan('dev'));
app.use(express.json());
app.use(cors({ origin: CORS_ORIGIN }));

// Routes
app.use('/api/tasks', tasksRouter);

// Healthcheck
app.get('/healthz', (req, res) => res.status(200).json({ status: 'ok' }));

// Global error handler (must be last)
app.use(errorHandler);

// Start: ensure DB initialized before listening
initDbAndSeed()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`Task Tracker API listening on port ${PORT}`);
    });
  })
  .catch((err) => {
    console.error('Failed to initialize DB and seed:', err);
    process.exit(1);
  });

module.exports = app; // for testing
```

#### Data Models

We use a single `tasks` table in SQLite and a JavaScript/JSON representation called `Task`. We document both the DB schema and the runtime model.

SQL Schema (exact):
```sql
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL,
  priority TEXT NOT NULL,
  createdAt TEXT NOT NULL,
  completedAt TEXT
);
```

Runtime JSON Model (`Task`):
```javascript
/*
Task model (JSON representation)
{
  id: number,            // generated by DB
  title: string,         // 1..100 chars
  description: string|null, // optional, max 500 chars
  status: 'pending'|'in-progress'|'completed',
  priority: 'low'|'medium'|'high',
  createdAt: string,     // ISO 8601 UTC
  completedAt: string|null // ISO 8601 UTC or null
}
*/
```

Validation schema (Joi v17 syntax — explicit)
```javascript
// server/validators.js (conceptual)
const Joi = require('joi');

const STATUS_VALUES = ['pending', 'in-progress', 'completed'];
const PRIORITY_VALUES = ['low', 'medium', 'high'];

const createTaskSchema = Joi.object({
  title: Joi.string().min(1).max(100).required(),
  description: Joi.string().allow('', null).max(500).optional(),
  status: Joi.string().valid(...STATUS_VALUES).default('pending'),
  priority: Joi.string().valid(...PRIORITY_VALUES).default('medium'),
});

const updateTaskSchema = Joi.object({
  title: Joi.string().min(1).max(100).optional(),
  description: Joi.string().allow('', null).max(500).optional(),
  status: Joi.string().valid(...STATUS_VALUES).optional(),
  priority: Joi.string().valid(...PRIORITY_VALUES).optional(),
}).min(1); // require at least one field for updates
```

Notes:
- When status is set to `'completed'` (either on create or update), the server must set `completedAt = current UTC timestamp` if not provided. If status moves from `'completed'` to something else, `completedAt` should be set to `NULL`.
- All timestamps are stored and returned as ISO 8601 UTC strings (e.g., `2024-01-15T10:30:00Z`).

#### API Endpoints

For each endpoint we list method, path, description, request body shape, response shape, and status codes.

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|--------------|----------|
| GET | /api/tasks | List tasks. Supports query params: `status`, `sortBy`, `sortOrder`, `search`, `limit`, `offset` | None (query params only) | 200 OK: `[{Task}, ...]` |
| GET | /api/tasks/:id | Get single task by id | None | 200 OK: `Task` or 404 Not Found |
| POST | /api/tasks | Create a task | `{ title, description?, status?, priority? }` | 201 Created: `Task` |
| PUT | /api/tasks/:id | Update a task by id | `{ title?, description?, status?, priority? }` | 200 OK: `Task` or 404 Not Found |
| DELETE | /api/tasks/:id | Delete a task by id | None | 204 No Content or 404 Not Found |
| GET | /api/tasks/export | Export all tasks as JSON file (bonus) | None | 200 OK: `application/json` with full array and `Content-Disposition: attachment; filename="tasks-export.json"` |

Query param details for GET /api/tasks:
- `status` — one of `pending|in-progress|completed`
- `sortBy` — `priority|createdAt` (default: `createdAt`)
- `sortOrder` — `asc|desc` (default: `desc`)
- `search` — text; matches `title` OR `description` (case-insensitive, contains)
- `limit` — integer, default 100
- `offset` — integer, default 0

Response format for errors (consistent across endpoints):
```json
{
  "error": "Human readable message",
  "code": "error_code",       // e.g., "validation_error", "not_found", "internal_error"
  "details": { /* optional: field-level errors */ }
}
```

#### Function Signatures (explicit implementations required)

Below, function signatures are written in JavaScript (Node style) with JSDoc to explain arguments/returns/errors. Implementers must follow these precisely.

```javascript
/**
 * getDb()
 * Returns: BetterSqlite3 Database instance configured with WAL mode and busy timeout.
 * Throws: Error if database can't be opened.
 */
function getDb() {}

/**
 * initDbAndSeed()
 * Ensures DB file exists, creates tasks table if missing, and seeds 3 tasks if table empty.
 *
 * Returns: Promise<void>
 * Throws: Error on failure
 */
async function initDbAndSeed() {}

/**
 * listTasks(filters)
 * Args:
 *   filters: {
 *     status?: string,        // 'pending'|'in-progress'|'completed'
 *     search?: string,        // search term
 *     sortBy?: 'priority'|'createdAt',
 *     sortOrder?: 'asc'|'desc',
 *     limit?: number,
 *     offset?: number
 *   }
 * Returns: Promise<Array<Task>>
 * Throws: Error on DB failure
 */
async function listTasks(filters) {}

/**
 * getTaskById(id)
 * Args:
 *   id: number
 * Returns: Promise<Task>
 * Throws: NotFoundError if missing, Error for DB issues
 */
async function getTaskById(id) {}

/**
 * createTask(payload)
 * Args:
 *   payload: { title, description?, status?, priority? }
 * Returns: Promise<Task>  // with id and createdAt set
 * Throws: ValidationError for invalid payload, Error for DB issues
 */
async function createTask(payload) {}

/**
 * updateTask(id, payload)
 * Args:
 *   id: number
 *   payload: { title?, description?, status?, priority? }
 * Returns: Promise<Task>
 * Throws: NotFoundError if no row with id, ValidationError for invalid payload, Error for DB issues
 */
async function updateTask(id, payload) {}

/**
 * deleteTask(id)
 * Args:
 *   id: number
 * Returns: Promise<void> // resolves if deleted, throws NotFoundError if not present
 */
async function deleteTask(id) {}
```

Implementation notes:
- Use prepared statements via `better-sqlite3` for performance and safety.
- Use DB transactions for create/update/delete sequences.
- Use `datetime('now')` or server-side JS (new Date().toISOString()) for `createdAt` and `completedAt`. Prefer JS `new Date().toISOString()` for consistent UTC formatting.

---

## 3. Frontend Architecture (vanilla HTML/CSS/JS)

Frontend lives under `public/`. It is a single-page app using only vanilla JS and the Fetch API to call the backend at `http://localhost:3000/api`.

### 3.1 UI Components

- HeaderBar
  - Purpose: site title, dark-mode label, optional collapsed sidebar toggle.
  - Props/Inputs: none
  - Render: top horizontal bar with title and add-task button.

- Toolbar
  - Purpose: provide status filters, sort controls, search box.
  - Props: currentFilters, onChange callbacks
  - Render: select for status, select for sortBy, toggle for sortOrder, search input, create new task button

- TaskList
  - Purpose: list of TaskCard or table rows
  - Props: tasks array, loading boolean, onEdit(task), onDelete(task)
  - Render: grid of cards or table rows; each shows title, truncated description, status badge, priority chip (color-coded), createdAt, actions (edit, delete)

- TaskFormModal
  - Purpose: create or edit a task in a modal
  - Props: initialTask (nullable), onSubmit, onCancel
  - Render: form inputs (title, description, status, priority), submit & cancel buttons, client-side validation messages

- DeleteConfirmModal
  - Purpose: confirm destructive delete
  - Props: task, onConfirm, onCancel
  - Render: confirmation text, "Delete" (red) and "Cancel"

- Toasts
  - Purpose: show success/error notifications
  - Props: message, type ('success'|'error')
  - Render: floating toast in top-right

- LoadingSpinner
  - Purpose: show during API operations

Visual mapping to PRD colors (CSS variables in `styles.css`):
```css
:root {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --accent: #00A3FF;
  --text-primary: #E6EEF8;
  --text-muted: #A9B6C6;
  --priority-high: #FF6B6B;
  --priority-medium: #FFD166;
  --priority-low: #4EE1A0;
}
```

Accessibility:
- Use proper labels, ARIA attributes for modals, keyboard-focusable controls, semantic HTML.
- Contrast checked per PRD.

### 3.2 API Integration (frontend functions)

All frontend network calls target `http://localhost:3000/api/tasks`.

- apiFetchTasks(filters)
  - Endpoint: GET `/api/tasks?status=&sortBy=&sortOrder=&search=&limit=&offset=`
  - Request: no body
  - Response: JSON array of Task objects
  - Error Handling: if status >= 400, parse JSON and show `details` / `error` in toast.

- apiGetTask(id)
  - GET `/api/tasks/:id`
  - Response: Task object

- apiCreateTask(payload)
  - POST `/api/tasks`
  - Body: JSON `{ title, description, status, priority }`
  - Response: 201 Created Task

- apiUpdateTask(id, payload)
  - PUT `/api/tasks/:id`
  - Body: partial Task fields
  - Response: 200 OK Task

- apiDeleteTask(id)
  - DELETE `/api/tasks/:id`
  - Response: 204 No Content

- apiExportTasks()
  - GET `/api/tasks/export`
  - Response: application/json file — fetch and prompt download

Detailed client handling:
- Show spinner while request in flight, disable form submit to prevent duplicate posts.
- On success, update local UI state optimistically by replacing list or re-fetching tasks.
- On error, show toast with `error` text and field details if available.
- All fetch calls should include `headers: {'Content-Type': 'application/json'}` for POST/PUT.

Example frontend fetch wrapper (explicit):
```javascript
async function apiFetch(url, options = {}) {
  const res = await fetch(url, options);
  const contentType = res.headers.get('content-type') || '';
  let body = null;
  if (contentType.includes('application/json')) {
    body = await res.json();
  } else {
    body = await res.text();
  }
  if (!res.ok) {
    // body expected: { error, code, details }
    throw { status: res.status, body };
  }
  return body;
}
```

---

## 4. Data Flow Diagram

```
User Action → Frontend (public/index.html + app.js)
        → UI collects input & calls apiFetchTasks / apiCreateTask / apiUpdateTask / apiDeleteTask
        → HTTP Request → Backend (server/index.js → routes/tasks.js)
        → Processing (validation via Joi, DB access via better-sqlite3)
        → SQLite Data Store (data/tasks.db)
        ↓
 response ← transformed Task JSON ← Backend ← Frontend receives response and updates UI
```

Flow details:
- Frontend sends JSON payloads to `/api/tasks`.
- Backend validates inputs with Joi schemas.
- Backend runs DB operations in transactions using prepared statements (better-sqlite3 synchronous API).
- Backend returns structured JSON with status codes.
- Frontend treats responses and updates UI; re-fetch or apply minimal local mutation.

---

## 5. Error Handling Strategy

### Possible error categories and handling

1. Validation errors (client payload invalid)
   - Source: Joi schema validation
   - Handler: return HTTP 400
   - Response body:
     ```json
     {
       "error": "Validation failed",
       "code": "validation_error",
       "details": {
         "title": ["child \"title\" fails because [\"title\" length must be at least 1 characters]"]
       }
     }
     ```
   - Frontend: map `details` to inline form field error messages.

2. Not Found
   - Source: Attempt to GET/PUT/DELETE a task id that doesn't exist
   - Handler: return HTTP 404
   - Response body:
     ```json
     { "error": "Task not found", "code": "not_found" }
     ```

3. Database errors (I/O, locks)
   - Source: DB open failure, write errors
   - Handler: log internal error, return HTTP 500 with code `internal_error`
   - Response body:
     ```json
     { "error": "Internal Server Error", "code": "internal_error" }
     ```

4. Unexpected exceptions
   - Handler: same as DB errors.

5. CORS errors
   - Source: client origin not allowed
   - Handler: `cors` middleware will block; document default `CORS_ORIGIN` environment variable.

6. Concurrency / busy DB
   - better-sqlite3 is synchronous and recommended for local single-process usage. Use WAL mode, set `busyTimeout`, and ensure thread-safety by single server process.

### Error response format (strict)
All error responses MUST be JSON with keys:
- `error` (string): Human-friendly summary
- `code` (string): programmatic code
- `details` (optional object): field-level messages

Example:
```json
{
  "error": "Validation failed",
  "code": "validation_error",
  "details": { "title": "Title is required and must be 1-100 characters" }
}
```

Server must set `Content-Type: application/json` for errors.

---

## 6. Configuration

Environment variables (with defaults):

- `PORT` (default: `3000`) — The server listens on this port.
- `DB_PATH` (default: `./data/tasks.db`) — Path to SQLite DB file.
- `CORS_ORIGIN` (default: `http://localhost:3000`) — Allowed origin string, can be "*" if intentionally wide.
- `SEED_ON_INIT` (default: `true`) — Whether to seed DB with 3 sample tasks on first run (`"true"`/`"false"` as strings in Docker env).
- `NODE_ENV` (default: `development`) — standard.

Configuration file format:
- No config file required for MVP. Use environment variables and optionally a `.env` file (if using dotenv, but this repo **does not** include dotenv to obey lockfile constraint).

Example usage:
```bash
PORT=3000 DB_PATH=./data/tasks.db CORS_ORIGIN=http://localhost:3000 node server/index.js
```

Docker behavior:
- Dockerfile should expose port 3000 and create a volume mount for `./data` to persist `tasks.db`.

---

## 7. VERSION-SPECIFIC NOTES (lockfile-aware)

The architecture must be implemented exactly for the versions present in the lockfile. Below are explicit notes and code decisions based on those versions:

1. Express
   - Installed: `express@4.18.2`
   - Use the `express()` API, `app.use()` middleware, and `app.use(function(err, req, res, next) { ... })` error handler signature (four args). Do NOT use Express v5+ features (like router-level error handler changes, `app.handle` differences, or the new router parameter syntax).
   - For JSON body parsing use `express.json()`.

2. Joi
   - Installed: `joi@17.4.2`
   - Use `schema.validateAsync(value, options)` or `schema.validate(value)` with error parsing. The v17 API supports `validateAsync`. Schema definitions in this doc use v17 syntax (e.g., `Joi.string().min(1).max(100).required()`).
   - Return Joi validation messages to the frontend in `details` object.

3. better-sqlite3
   - Installed: `better-sqlite3@7.6.2`
   - API is synchronous. Use `const Database = require('better-sqlite3'); const db = new Database(DB_PATH, { fileMustExist: false });`
   - Set pragmas on open: `PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL;` and set busy timeout via `db.pragma('busy_timeout = 5000');` (Note: `db.pragma` expects strings; see docs for exact API).
   - Use prepared statements: `const stmt = db.prepare('SELECT ...'); stmt.all()` or `stmt.get()`; use `db.transaction()` for multi-statement atomic updates.

4. sqlite3 peer warning
   - The lockfile shows UNMET DEPENDENCY `sqlite3@^5.1.6` (peer) but does not have it installed. That might be a warning from npm resolution and does not prevent `better-sqlite3` usage typically. However, `better-sqlite3` may require native build tools (node-gyp, make, python, build-essential). Documented instructions in README must include:
     - If native build errors occur in Docker build, ensure build dependencies are present: `build-essential`, `python3`, `make`, and `g++` or use a base image with these installed.
     - If using Node 20, `better-sqlite3@7.6.2` should work, but if problems occur, recommendation: re-run `npm install` in an environment with proper build deps or switch to a binary-compatible image.

5. morgan and cors
   - Installed and used as middleware. `morgan('dev')` is fine for logs.

6. Node version
   - The lockfile mentions Node v20.11.0 in the environment where packages were installed. All code must be compatible with Node 20's features (but avoid experimental or breaking APIs).

7. No extra npm packages
   - Do not add other npm dependencies beyond those listed in the lockfile. For example, do not add `sqlite3`, `dotenv`, `express@5`, or any frontend build tool. The frontend uses vanilla JS.

8. Python-file names in Required Output Structure
   - The PRD requires Node.js backend, but the `REQUIRED OUTPUT STRUCTURE` included Python filenames (`backend_app.py` etc.). Include these files as placeholders in the repo root with documentation comments mapping to `server/index.js`. They must not be used as server entry points. Provide instructions in README.

---

## 8. Implementation Checklist

- [ ] File created: Dockerfile
- [ ] File created: package.json (with dependencies matching lockfile)
- [ ] Folder created: server/
  - [ ] server/index.js
  - [ ] server/db.js
  - [ ] server/routes/tasks.js
  - [ ] server/validators.js
  - [ ] server/errors.js
  - [ ] server/logger.js (optional)
- [ ] Folder created: public/
  - [ ] public/index.html
  - [ ] public/app.js
  - [ ] public/styles.css
- [ ] Folder created: data/ (with .gitkeep)
- [ ] Database file: data/tasks.db created automatically on first run
- [ ] DB schema applied and 3 sample tasks seeded on first initialization
- [ ] All endpoints implemented and tested:
  - [ ] GET /api/tasks
  - [ ] GET /api/tasks/:id
  - [ ] POST /api/tasks
  - [ ] PUT /api/tasks/:id
  - [ ] DELETE /api/tasks/:id
  - [ ] GET /api/tasks/export (bonus)
- [ ] Joi validation in place for create/update with proper 400 responses
- [ ] Error handling middleware returns structured JSON
- [ ] CORS enabled and configurable via `CORS_ORIGIN`
- [ ] Frontend uses `http://localhost:3000/api` endpoints and supports CRUD flows
- [ ] UI shows loading states, toast notifications, delete confirmation modal
- [ ] README contains Docker build & run commands and curl examples
- [ ] Tests / curl commands exist in `tests/api_examples.md`

---

## Detailed Implementation Guidance (copyable code templates)

Below are the exact code templates and SQL you can copy to implement the project. These are meant to be complete and unambiguous.

### package.json (exact dependencies to match lockfile)
```json
{
  "name": "task-tracker",
  "version": "1.0.0",
  "description": "Local-first task tracker",
  "main": "server/index.js",
  "scripts": {
    "start": "node server/index.js",
    "dev": "nodemon server/index.js"
  },
  "dependencies": {
    "better-sqlite3": "7.6.2",
    "cors": "2.8.5",
    "express": "4.18.2",
    "joi": "17.4.2",
    "morgan": "1.10.0"
  },
  "devDependencies": {
    "nodemon": "2.0.22"
  }
}
```

### server/db.js (DB init + seed)
```javascript
// server/db.js
const fs = require('fs');
const path = require('path');
const Database = require('better-sqlite3');

const DB_PATH = process.env.DB_PATH || path.resolve(__dirname, '../data/tasks.db');
const SEED_ON_INIT = (process.env.SEED_ON_INIT || 'true') === 'true';

function getDbInstance() {
  // Open DB (creates file if not exists)
  const dir = path.dirname(DB_PATH);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

  const db = new Database(DB_PATH);
  // Use WAL for better concurrency on reads
  db.pragma('journal_mode = WAL');
  db.pragma('synchronous = NORMAL');
  // busy timeout setting
  try {
    db.pragma('busy_timeout = 5000');
  } catch (e) {
    // older better-sqlite3 API differences: catch and ignore if unsupported
    console.warn('Unable to set busy_timeout pragma:', e && e.message);
  }
  return db;
}

function ensureSchema(db) {
  db.prepare(`
    CREATE TABLE IF NOT EXISTS tasks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      description TEXT,
      status TEXT NOT NULL,
      priority TEXT NOT NULL,
      createdAt TEXT NOT NULL,
      completedAt TEXT
    );
  `).run();
}

function seedIfEmpty(db) {
  const row = db.prepare('SELECT COUNT(1) as count FROM tasks').get();
  if (!row || row.count === 0) {
    const now = new Date().toISOString();
    const insert = db.prepare(`
      INSERT INTO tasks (title, description, status, priority, createdAt, completedAt)
      VALUES (@title, @description, @status, @priority, @createdAt, @completedAt)
    `);
    const tasks = [
      { title: 'Welcome to Task Tracker', description: 'This is a sample task.', status: 'pending', priority: 'medium', createdAt: now, completedAt: null },
      { title: 'Try editing this task', description: 'Use the edit button.', status: 'in-progress', priority: 'low', createdAt: now, completedAt: null },
      { title: 'Complete this task', description: 'Mark as completed to set completedAt.', status: 'completed', priority: 'high', createdAt: now, completedAt: now },
    ];
    const insertMany = db.transaction((tasksArr) => {
      for (const t of tasksArr) insert.run(t);
    });
    insertMany(tasks);
  }
}

async function initDbAndSeed() {
  return new Promise((resolve, reject) => {
    try {
      const db = getDbInstance();
      ensureSchema(db);
      if (SEED_ON_INIT) seedIfEmpty(db);
      // store DB instance on module for reuse
      module.exports.db = db;
      resolve();
    } catch (err) {
      reject(err);
    }
  });
}

module.exports = { initDbAndSeed, getDbInstance };
```

### server/validators.js (Joi schemas)
```javascript
// server/validators.js
const Joi = require('joi');

const STATUS_VALUES = ['pending', 'in-progress', 'completed'];
const PRIORITY_VALUES = ['low', 'medium', 'high'];

const createTaskSchema = Joi.object({
  title: Joi.string().min(1).max(100).required(),
  description: Joi.string().allow('', null).max(500).optional(),
  status: Joi.string().valid(...STATUS_VALUES).default('pending'),
  priority: Joi.string().valid(...PRIORITY_VALUES).default('medium'),
});

const updateTaskSchema = Joi.object({
  title: Joi.string().min(1).max(100).optional(),
  description: Joi.string().allow('', null).max(500).optional(),
  status: Joi.string().valid(...STATUS_VALUES).optional(),
  priority: Joi.string().valid(...PRIORITY_VALUES).optional(),
}).min(1);

module.exports = {
  createTaskSchema,
  updateTaskSchema,
  STATUS_VALUES,
  PRIORITY_VALUES,
};
```

### server/errors.js (centralized errors & middleware)
```javascript
// server/errors.js
class NotFoundError extends Error {
  constructor(message = 'Not Found') {
    super(message);
    this.name = 'NotFoundError';
    this.code = 'not_found';
    this.status = 404;
  }
}

class ValidationError extends Error {
  constructor(message = 'Validation Error', details = {}) {
    super(message);
    this.name = 'ValidationError';
    this.code = 'validation_error';
    this.status = 400;
    this.details = details;
  }
}

function errorHandler(err, req, res, next) {
  // Known error types
  if (err && err.status) {
    const payload = {
      error: err.message || 'Error',
      code: err.code || 'error',
    };
    if (err.details) payload.details = err.details;
    return res.status(err.status).json(payload);
  }
  // Unknown errors -> 500
  console.error(err); // server-side logging
  res.status(500).json({ error: 'Internal Server Error', code: 'internal_error' });
}

module.exports = { NotFoundError, ValidationError, errorHandler };
```

### server/routes/tasks.js (full route handlers)

This file is the most crucial. It must follow the exact request/response contracts. Use `module.exports = router` for mounting.

```javascript
// server/routes/tasks.js
const express = require('express');
const router = express.Router();
const { db, initDbAndSeed } = require('../db'); // db will be set after init
const { createTaskSchema, updateTaskSchema } = require('../validators');
const { ValidationError, NotFoundError } = require('../errors');

function getDb() {
  if (module.exports.__dbInstance) return module.exports.__dbInstance;
  // attempt to get from db module
  const dbModule = require('../db');
  if (dbModule.db) {
    module.exports.__dbInstance = dbModule.db;
    return dbModule.db;
  }
  // fallback: initialize (should not be needed in normal flow)
  return dbModule.getDbInstance();
}

function formatTaskRow(row) {
  return {
    id: row.id,
    title: row.title,
    description: row.description === null ? null : row.description,
    status: row.status,
    priority: row.priority,
    createdAt: row.createdAt,
    completedAt: row.completedAt === null ? null : row.completedAt,
  };
}

// GET /api/tasks
router.get('/', (req, res, next) => {
  try {
    const db = getDb();
    const { status, sortBy = 'createdAt', sortOrder = 'desc', search, limit = 100, offset = 0 } = req.query;
    const allowedSortBy = ['priority', 'createdAt'];
    const allowedSortOrder = ['asc', 'desc'];
    const sortColumn = allowedSortBy.includes(sortBy) ? sortBy : 'createdAt';
    const order = allowedSortOrder.includes(sortOrder.toLowerCase()) ? sortOrder.toUpperCase() : 'DESC';

    let sql = 'SELECT * FROM tasks';
    const clauses = [];
    const params = {};
    if (status) {
      clauses.push('status = @status');
      params['status'] = status;
    }
    if (search) {
      clauses.push('(title LIKE @search OR description LIKE @search)');
      params['search'] = `%${search}%`;
    }
    if (clauses.length) sql += ' WHERE ' + clauses.join(' AND ');
    sql += ` ORDER BY ${sortColumn} ${order} LIMIT @limit OFFSET @offset`;
    params['limit'] = Math.min(1000, parseInt(limit, 10) || 100);
    params['offset'] = parseInt(offset, 10) || 0;

    const stmt = db.prepare(sql);
    const rows = stmt.all(params);
    res.status(200).json(rows.map(formatTaskRow));
  } catch (err) {
    next(err);
  }
});

// GET /api/tasks/:id
router.get('/:id', (req, res, next) => {
  try {
    const db = getDb();
    const stmt = db.prepare('SELECT * FROM tasks WHERE id = ?');
    const row = stmt.get(parseInt(req.params.id, 10));
    if (!row) return next(new NotFoundError('Task not found'));
    res.status(200).json(formatTaskRow(row));
  } catch (err) {
    next(err);
  }
});

// POST /api/tasks
router.post('/', async (req, res, next) => {
  try {
    const value = await createTaskSchema.validateAsync(req.body, { abortEarly: false });
    const db = getDb();

    // handle completedAt logic
    let completedAt = null;
    if (value.status === 'completed') completedAt = new Date().toISOString();

    const now = new Date().toISOString();
    const insert = db.prepare(`
      INSERT INTO tasks (title, description, status, priority, createdAt, completedAt)
      VALUES (@title, @description, @status, @priority, @createdAt, @completedAt)
    `);
    const info = insert.run({
      title: value.title,
      description: value.description || null,
      status: value.status,
      priority: value.priority,
      createdAt: now,
      completedAt,
    });
    const id = info.lastInsertRowid;
    const row = db.prepare('SELECT * FROM tasks WHERE id = ?').get(id);
    res.status(201).json(formatTaskRow(row));
  } catch (err) {
    if (err.isJoi) {
      // build details from err.details
      const details = {};
      for (const d of err.details || []) {
        const key = d.path.join('.') || d.context.key || 'value';
        details[key] = d.message;
      }
      return next(new ValidationError('Validation failed', details));
    }
    next(err);
  }
});

// PUT /api/tasks/:id
router.put('/:id', async (req, res, next) => {
  try {
    const id = parseInt(req.params.id, 10);
    const db = getDb();
    // check existence
    const existing = db.prepare('SELECT * FROM tasks WHERE id = ?').get(id);
    if (!existing) return next(new NotFoundError('Task not found'));

    const value = await updateTaskSchema.validateAsync(req.body, { abortEarly: false });

    // determine completedAt changes
    let completedAt = existing.completedAt || null;
    if (value.status) {
      if (value.status === 'completed') {
        // set completedAt if not already set
        completedAt = existing.completedAt || new Date().toISOString();
      } else {
        // moving away from completed: nullify
        completedAt = null;
      }
    }

    const updated = Object.assign({}, existing, value, { completedAt });
    const stmt = db.prepare(`
      UPDATE tasks SET title=@title, description=@description, status=@status, priority=@priority, completedAt=@completedAt
      WHERE id=@id
    `);
    stmt.run({
      id,
      title: updated.title,
      description: updated.description === undefined ? existing.description : updated.description,
      status: updated.status,
      priority: updated.priority,
      completedAt: updated.completedAt,
    });
    const row = db.prepare('SELECT * FROM tasks WHERE id = ?').get(id);
    res.status(200).json(formatTaskRow(row));
  } catch (err) {
    if (err.isJoi) {
      const details = {};
      for (const d of err.details || []) {
        const key = d.path.join('.') || d.context.key || 'value';
        details[key] = d.message;
      }
      return next(new ValidationError('Validation failed', details));
    }
    next(err);
  }
});

// DELETE /api/tasks/:id
router.delete('/:id', (req, res, next) => {
  try {
    const id = parseInt(req.params.id, 10);
    const db = getDb();
    const info = db.prepare('DELETE FROM tasks WHERE id = ?').run(id);
    if (info.changes === 0) return next(new NotFoundError('Task not found'));
    res.status(204).send();
  } catch (err) {
    next(err);
  }
});

// GET /api/tasks/export
router.get('/export', (req, res, next) => {
  try {
    const db = getDb();
    const rows = db.prepare('SELECT * FROM tasks ORDER BY createdAt DESC').all();
    const tasks = rows.map(formatTaskRow);
    res.setHeader('Content-Disposition', 'attachment; filename="tasks-export.json"');
    res.setHeader('Content-Type', 'application/json');
    res.status(200).send(JSON.stringify(tasks, null, 2));
  } catch (err) {
    next(err);
  }
});

module.exports = router;
```

> Important: `routes/tasks.js` expects `server/db.js` to have been initialized and expose `db`. `server/index.js` calls `initDbAndSeed()` before listening which sets `module.exports.db` in `server/db.js`. The route file has logic to fallback to `getDbInstance()` if needed.

### public/index.html (skeleton and endpoints)
Provide a single-page UI that calls the API.

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Task Tracker</title>
  <link rel="stylesheet" href="/styles.css" />
</head>
<body>
  <header id="header">
    <h1>Task Tracker</h1>
    <button id="btn-new-task">New Task</button>
  </header>
  <main id="main">
    <section id="toolbar">
      <select id="filter-status">
        <option value="">All</option>
        <option value="pending">Pending</option>
        <option value="in-progress">In-Progress</option>
        <option value="completed">Completed</option>
      </select>
      <select id="sort-by">
        <option value="createdAt">Created</option>
        <option value="priority">Priority</option>
      </select>
      <button id="sort-order">Desc</button>
      <input id="search-box" placeholder="Search..." />
    </section>
    <section id="task-list"></section>
  </main>

  <!-- Modals & Toasts placeholders -->
  <div id="modal-root"></div>
  <div id="toast-root"></div>

  <script src="/app.js"></script>
</body>
</html>
```

### public/app.js (core flow — detailed enough to implement)

This file defines the UI operations and API calls. The sample below is a minimal, explicit, and fully implementable blueprint.

```javascript
// public/app.js
const API_BASE = '/api/tasks'; // Assumes server serves public/ at root and API at /api/tasks

async function apiFetch(url, opts) {
  const res = await fetch(url, opts);
  const ct = res.headers.get('content-type') || '';
  const body = ct.includes('application/json') ? await res.json() : await res.text();
  if (!res.ok) throw { status: res.status, body };
  return body;
}

async function fetchTasks(filters = {}) {
  const params = new URLSearchParams();
  if (filters.status) params.set('status', filters.status);
  if (filters.sortBy) params.set('sortBy', filters.sortBy);
  if (filters.sortOrder) params.set('sortOrder', filters.sortOrder);
  if (filters.search) params.set('search', filters.search);
  const url = `${API_BASE}?${params.toString()}`;
  return await apiFetch(url);
}

async function createTask(payload) {
  return await apiFetch(API_BASE, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload),
  });
}

async function updateTask(id, payload) {
  return await apiFetch(`${API_BASE}/${id}`, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload),
  });
}

async function deleteTask(id) {
  const res = await fetch(`${API_BASE}/${id}`, { method: 'DELETE' });
  if (res.status === 204) return null;
  const body = await res.json();
  if (!res.ok) throw { status: res.status, body };
}

function renderTaskList(tasks) {
  const root = document.getElementById('task-list');
  root.innerHTML = '';
  const ul = document.createElement('ul');
  ul.className = 'task-grid';
  tasks.forEach(t => {
    const li = document.createElement('li');
    li.className = 'task-card';
    li.innerHTML = `
      <div class="task-header">
        <h3>${escapeHtml(t.title)}</h3>
        <span class="priority" style="background:${priorityColor(t.priority)}">${t.priority}</span>
      </div>
      <p class="desc">${escapeHtml(t.description || '')}</p>
      <div class="meta">
        <span class="status">${t.status}</span>
        <span class="created">${t.createdAt}</span>
      </div>
      <div class="actions">
        <button data-action="edit" data-id="${t.id}">Edit</button>
        <button data-action="delete" data-id="${t.id}">Delete</button>
      </div>
    `;
    ul.appendChild(li);
  });
  root.appendChild(ul);
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (m) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m] || m));
}

function priorityColor(priority) {
  switch(priority) {
    case 'high': return '#FF6B6B';
    case 'medium': return '#FFD166';
    case 'low': return '#4EE1A0';
    default: return '#A9B6C6';
  }
}

// Wire up initial load
document.addEventListener('DOMContentLoaded', async () => {
  const filters = {};
  try {
    const tasks = await fetchTasks(filters);
    renderTaskList(tasks);
  } catch (err) {
    showToast('Failed to load tasks', 'error');
    console.error(err);
  }

  // Add event listeners for toolbar/search/new task etc. Implement modals as needed.
});

// Simple toast
function showToast(msg, type='success') {
  const root = document.getElementById('toast-root');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  root.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}
```

> The frontend code provided is explicit and minimal; implementers should finish UI wiring for add/edit/delete modals following the PRD UI/UX spec.

---

## 9. Seed Data

Seed the DB with the following 3 tasks if the table is empty. This is required behavior on first run.

1) id=auto, title: "Welcome to Task Tracker", description: "This is a sample task.", status: "pending", priority: "medium", createdAt: now, completedAt: null  
2) title: "Try editing this task", description: "Use the edit button.", status: "in-progress", priority: "low", createdAt: now, completedAt: null  
3) title: "Complete this task", description: "Mark as completed to set completedAt.", status: "completed", priority: "high", createdAt: now, completedAt: now

The seeding is implemented in `server/db.js` template above.

---

## 10. Testing & Curl Examples (copy-paste)

Assuming server is running on http://localhost:3000:

- Create task:
```bash
curl -X POST http://localhost:3000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Build feature","description":"Detailed text","status":"pending","priority":"high"}'
```

- List tasks:
```bash
curl http://localhost:3000/api/tasks
```

- Get single task:
```bash
curl http://localhost:3000/api/tasks/1
```

- Update task:
```bash
curl -X PUT http://localhost:3000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"completed"}'
```

- Delete task:
```bash
curl -X DELETE http://localhost:3000/api/tasks/1
```

- Export tasks:
```bash
curl -OJ http://localhost:3000/api/tasks/export
```

Acceptance tests to run manually or via CI:
- Start server, run POST, check 201 and that GET returns created object and DB persisted after restart.
- PUT on invalid id returns 404.
- POST with invalid title (empty) returns 400 with validation details.
- GET /api/tasks?search=term returns matching tasks.

---

## 11. Deployment & Docker

Minimal Dockerfile (explicit so a developer can reproduce):

```Dockerfile
# Dockerfile (explicit)
FROM node:20-bullseye-slim
WORKDIR /app

# Install build tools for better-sqlite3 native builds
RUN apt-get update && apt-get install -y build-essential python3 make g++ curl ca-certificates --no-install-recommends \
  && rm -rf /var/lib/apt/lists/*

COPY package.json package-lock.json ./
RUN npm ci --silent

COPY . .

# Expose port and data volume
VOLUME [ "/app/data" ]
EXPOSE 3000
CMD ["npm", "start"]
```

Run commands:
```bash
docker build -t task-tracker .
docker run --rm -p 3000:3000 -v $(pwd)/data:/app/data task-tracker
```

Note: The Dockerfile installs system build tools needed by `better-sqlite3` for native compilation. If your environment already has prebuilt binaries for better-sqlite3 for the Node version, builds may be faster.

---

## 12. Operational Considerations

- Logs: `morgan('dev')` prints to stdout. You can swap to file or structured logger later.
- Backups: Users can call `/api/tasks/export` and save the JSON. Document periodic backups of `data/tasks.db`.
- Security: No authentication as per PRD. Document that if enabling on open networks, you must add auth and HTTPS.
- Concurrency: Because `better-sqlite3` is synchronous, avoid running multiple Node worker processes pointing to the same DB file; prefer single-process server for local usage.
- Performance: For most uses (<100 req/min), synchronous better-sqlite3 is adequate. Use indices if needed (e.g., on `status` or `createdAt`) — add `CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);` if performance requires.

---

## 13. Additional Notes & Edge Cases

- Title trimming: server should trim whitespace from title before validation (recommended).
- Empty descriptions: store as NULL for consistency.
- CompletedAt behavior:
  - On create: if status === 'completed', set completedAt = now.
  - On update: if status changed to 'completed' and completedAt null → set completedAt = now. If status changed away from 'completed' → set completedAt = null.
- ID validation: ensure `id` path param is integer; return 400 if NaN.
- SQL injection: using prepared statements prevents injection.
- DB migration in future: simple version table required if schema evolves.

---

## 14. README (what to include)

Minimum README content:
- Project purpose (one-liner)
- Prerequisites (Docker)
- Run with Docker commands above
- Environment variables
- API endpoints and examples (use the curl examples above)
- How to seed DB manually (scripts/seed.js if present)
- Troubleshooting native build errors (install build-essential in Docker)
- Where to find frontend (http://localhost:3000/)

---

## 15. Implementation Handoff Checklist for Developers (step-by-step)

1. Create repository with files and folders as in the Project Structure.
2. Copy `package.json` content above (matching lockfile versions).
3. Implement `server/db.js`, `server/index.js`, `server/validators.js`, `server/errors.js`, `server/routes/tasks.js` exactly as templates.
4. Implement `public/` assets (index.html, app.js, styles.css).
5. Create `Dockerfile` and test `docker build` and `docker run`.
6. Confirm server responds on `http://localhost:3000/healthz` with `{status:'ok'}`.
7. Run curl create/list/get/update/delete tests.
8. Verify DB file exists at `./data/tasks.db` and persists after container restart.
9. Validate UI CRUD flow works end-to-end.

---

If you would like, I can now:
- Scaffold the repository files with the exact templates (server files, public files, Dockerfile, package.json) and write them to the `output/` directory.
- Or produce a detailed README and test checklist file.

Which next step do you want me to take?