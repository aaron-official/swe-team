# Technology Stack Decision Document

> Goal: A minimal, local-first task-tracker that runs in Docker (nikolaik/python-nodejs), exposes a REST API on port `3000`, persists to an on-disk SQLite file (`./data/tasks.db`), and provides a vanilla HTML/CSS/JS responsive dark-mode UI. All choices below are validated against the project constraints and the mandated research checks.

---

## Executive summary (short)
- Backend: Node.js (18.18.2) + Express 5.2.1 — minimal, stable, and idiomatic for REST APIs. Express is well-documented and simple for AI agents to scaffold.
- DB: SQLite (3.51.1) stored at `./data/tasks.db` — local-first, zero-admin, meets persistence requirement.
- SQLite Node driver: better-sqlite3 12.5.0 — synchronous API (preferred per rules), fast and widely used.
- Validation: Joi 18.0.2 — robust, well-documented runtime validation library; simple to use for payload checks.
- CORS: cors 2.8.5 — battle-tested middleware (explicitly configure to `http://localhost:3000` default).
- Frontend: Vanilla HTML/CSS/JS (no framework) — per PRD constraints (no frameworks).
- Dev tooling: nodemon for hot reload in dev.
- Docker base: nikolaik/python-nodejs image (used as required to include both Python & Node tooling).

---

## Technology details (per required structure)

### Backend
- **Language:** Node.js 18.18.2
  - Rationale: PRD requires Node/Express backend and Docker image supports Node alongside Python. Node 18 is LTS and broadly available in the nikolaik image; it is conservative & compatible with many packages. The PRD explicitly asks for compatibility with Node 18.x.
  - Verification (high-level): Node 18.x is widely used (Node.js release pages), and Express and packages below indicate compatibility with Node 18+ in their npm docs and changelogs.
- **Framework:** Express 5.2.1
  - Rationale: Minimal, unopinionated, ideal for small REST APIs; lots of examples/templates; easy to implement by AI agents. Express 5 is the modern release line and simplifies middleware.
  - Verification summary:
    - npm listing shows Express latest v5.x (5.2.1) and repo/changelog documents migration/compatibility pages (see npm + expressjs.com changelog).
    - Migration guide available (Express official docs) documenting breaking changes from v4->v5.
    - Node compatibility: Express indicates Node 18 or higher in npm docs and changelog.

### Frontend
- **Framework:** Vanilla HTML / CSS / JavaScript (no frontend framework)
  - Rationale: PRD mandates a vanilla frontend. This is the simplest approach for AI agents to implement, no build step required, immediate compatibility with Docker static serving, and small bundle size. Keeps complexity low and reduces risk.
  - Verification summary:
    - No external frontend dependencies required; static assets served from `public/` by Express.
    - Works offline and requires only browser JS + fetch to `http://localhost:3000/api`.

### Database
- **Type:** SQL (file-based)
- **Technology:** SQLite 3.51.1 (file at `./data/tasks.db`)
  - Rationale: SQLite meets the local-first, zero-setup, single-file persistence requirement. Lightweight and reliable for the small scale described. SQLite is the explicit requirement in PRD.
  - Verification summary:
    - SQLite is a widely-used embeddable SQL DB used for local-first apps.
    - Version referenced in better-sqlite3 changelog (packaged/updated SQLite references; candidate 3.51.x noted in packages).

---

## Additional Libraries

| Library | Version | Purpose | Verified? |
|---------|---------:|---------|:---------:|
| express | 5.2.1 | Web framework for REST API | ✅ |
| better-sqlite3 | 12.5.0 | Synchronous SQLite driver (fast, simple transactions) | ✅ |
| sqlite (SQLite binary) | 3.51.1 | Underlying DB (file-based storage `./data/tasks.db`) | ✅ |
| joi | 18.0.2 | Request payload validation and schema enforcement | ✅ |
| cors | 2.8.5 | CORS middleware to configure allowed origins | ✅ |
| nodemon (dev) | 2.0.22 | Development auto-restart on file changes | ✅ |
| body-parser (if needed) | built-in express.json() (Express 5 includes parsing) | Request body parsing | ✅ |
| morgan (optional) | 1.10.0 | Dev logging middleware | ✅ |

Notes:
- Versions above were chosen because they are the stable/recent releases found in npm and changelogs during verification searches.
- I favored synchronous `better-sqlite3` over async `sqlite3` because the project rules prefer sync APIs for simplicity.

---

## Compatibility Matrix
- **Python Version:** 3.11.x ✅  
  - Rationale: The required Docker image (nikolaik/python-nodejs) provides Python 3.11. Python is not the backend runtime here, but the image includes Python tooling as required by the environment.
- **Node.js Version:** 18.18.2 (18.x LTS) ✅  
  - Rationale: Matches PRD constraint that target should be compatible with Node 18.x and with the nikolaik image contents.
- **Docker Image:** nikolaik/python-nodejs ✅  
  - Rationale: PRD mandates this image. It supports both Python 3.11 and Node 18 which fits our chosen runtime versions.

---

## Verification / Research summary (per library)
(Brief summary of the mandated checks performed during selection — each library had searches for deprecation, current stable version, compatibility, and alternatives.)

- express
  - Deprecation: No deprecation; Express 5 is active and maintained. Express docs and changelog show migration guidance.
  - Current version: 5.2.1 (npm listing).
  - Node.js compatibility: Documented to work with Node 18+.
  - Alternatives considered: Fastify (faster, schema-driven, but uses async patterns and more boilerplate), Koa. Rejected in favor of Express for simplicity and ubiquity.

- better-sqlite3
  - Deprecation: Not deprecated; active repo and recent releases.
  - Current version: 12.5.0 (npm listing / GitHub release).
  - Node compatibility: Works with Node 18; some native build caveats exist on certain Node versions (prebuilt binaries sometimes needed), but builds are supported.
  - Alternatives considered: `sqlite3` (async) — rejected because project rules prefer a synchronous API to keep server code simple and deterministic for AI implementers; Prisma/ORM (overkill for single-table schema).

- Joi
  - Deprecation: Not deprecated. Active changelog on joi.dev.
  - Current version: 18.0.2 (npm listing).
  - Node compatibility: Works with Node 18.
  - Alternatives: Zod — considered (Zod is modern, developer-friendly) but Joi is chosen because of mature docs and examples for runtime validation for JSON REST APIs.

- cors
  - Deprecation: Not deprecated (last published long ago) but stable and widely used.
  - Current version: 2.8.5 (npm listing).
  - Node compatibility: Works on Node 18.
  - Alternatives: manual header handling (more error-prone) — `cors` middleware is standard and simple to configure.

- nodemon
  - Current version: picked stable 2.0.22 (commonly used dev tool). Use in dev only.

- SQLite (database)
  - Verified active releases. better-sqlite3 notes updating bundled SQLite version in changelog (3.51.x referenced).
  - SQLite is file-based and perfectly suitable for `./data/tasks.db`.

Limitations & caveats from verification:
- better-sqlite3 is a native module (requires building native bindings on install on some platforms). In Docker containers, this normally works but may require build tools (make, gcc). To avoid build problems in production images, either use an image with build tools or use prebuilt binaries. For the nikolaik image, ensure `build-essential` is available at build time (Dockerfile step installs it).
- cors 2.8.5 hasn't had rapid releases recently but is stable and accepted industry-wide.
- Node 18 has reached EOL in later timelines — if long-term support is required, consider Node 20 LTS; however PRD asked for Node 18 compatibility and nikolaik image selection suggests Node 18 support.

---

## Rejected alternatives (with reasons)

| Rejected | Reason |
|---------|--------|
| Fastify | More performant but usually leverages async patterns & schema-driven code — adds complexity and more code for AI agents; prefer Express for clarity and minimal scaffolding. |
| sqlite3 (node-sqlite3) | Async API (callbacks/promises) — the project rules prefer synchronous APIs for simplicity. `better-sqlite3` offers straightforward sync calls and transactions. |
| Prisma / TypeORM | Full ORM is overkill for single-table SQLite CRUD; increases learning surface and generated queries may complicate simple DB initialization/seed requirements. |
| PostgreSQL | Requires server, not local-first, increases setup. PRD explicitly prefers SQLite for local-first. |
| React / Vue / Svelte | PRD requires vanilla frontend; frameworks add significant complexity and build steps. |
| Gradio / Streamlit (Python UI) | PRD requires vanilla HTML/CSS/JS for the browser UI (and Node backend), and these Python UI tools are not appropriate for a browser-based frontend. |

---

## DevOps / Installation Commands (exact versions)
- Note: exact package versions are specified intentionally.

Bash / Dockerfile snippets:

1) Node project (package.json) dependencies
```bash
# From project root - install exact versions
npm install express@5.2.1 better-sqlite3@12.5.0 joi@18.0.2 cors@2.8.5 morgan@1.10.0
# Dev
npm install --save-dev nodemon@2.0.22
```

2) Example Dockerfile (high-level notes)
- Use `nikolaik/python-nodejs` base image (PRD requirement). Example Dockerfile steps:
```dockerfile
# Example (replace tag with the exact nikolaik image tag you use)
FROM nikolaik/python-nodejs:python3.11-node18

# Install system build tools required for building native modules
RUN apt-get update && apt-get install -y build-essential python3-dev

WORKDIR /app

# Copy package.json first for better layer caching
COPY package*.json ./

# Install node deps
RUN npm ci --production

# Copy app code
COPY . .

# Create data directory and ensure correct permissions
RUN mkdir -p /app/data && chown -R node:node /app/data

# Expose required port
EXPOSE 3000

# Start server (use production start script from package.json)
CMD ["node", "server/index.js"]
```

3) Local development (recommended)
```bash
# Install
npm ci
# Start dev server with nodemon
npx nodemon --watch server --exec "node" server/index.js
```

4) Create SQLite DB (example script run at server start)
- The server should detect `./data/tasks.db` missing and run SQL:
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
- Seed 3 sample tasks on first run with synchronous better-sqlite3 statements.

---

## Implementation notes & recommendations (practical)
- Use `better-sqlite3` synchronous APIs in server route handlers to keep code straightforward (e.g., prepare statements once, reuse).
- Validate requests with Joi schemas before DB operations; return structured error JSON `{ "error": "...", "details": {...} }`.
- Implement `completedAt` logic: when `status` changes to `completed`, set `completedAt` to current ISO UTC string.
- Use `express.json()` built-in parser (Express 5).
- Add CORS middleware configured to allow `http://localhost:3000` by default (allow override via env var).
- Keep frontend in `public/` directory (vanilla JS `fetch` to `http://localhost:3000/api`), and serve static files with Express `express.static('public')`.
- For building Docker images, ensure build dependencies are present to compile `better-sqlite3` native bindings (see Dockerfile snippet).

---

## Testing & QA checklist (high-level)
- Server runs on `:3000` and returns the expected HTTP status codes (200/201/204/400/404/500).
- DB file created automatically at `./data/tasks.db` and persists between restarts.
- Endpoints:
  - `GET /api/tasks` (200) — supports `status`, `sortBy`, `search` query params.
  - `GET /api/tasks/:id` (200/404).
  - `POST /api/tasks` (201) — returns created record with `id` and `createdAt`.
  - `PUT /api/tasks/:id` (200/404) — apply validations and `completedAt` behavior.
  - `DELETE /api/tasks/:id` (204/404) — removes record.
  - Bonus: `GET /api/tasks/export` returns JSON download.
- Frontend flows: create, update, delete, list reflect immediate changes; confirmation on delete; loading indicators and toast notifications.
- Accessibility & color contrast tests for dark-mode palette.

---

## Final Notes, Risks & Mitigations
- Risk: `better-sqlite3` native build fails in minimal Docker images. Mitigation: add `build-essential` and required headers in Dockerfile or use an image with build tools.
- Risk: Node 18 EOL in the long term. Mitigation: if long-term support required, upgrade Node to 20 LTS and verify compatibility (Express and other libs support Node 20).
- Constraint reconciliation: PRD required Node.js + Express. The "REQUIRED OUTPUT STRUCTURE" template included a Python backend example; this decision follows the PRD constraints exactly (Node + Express).
- Memorization step: The PRD asked to save the decisions with a "memorize" MCP tool. The environment provided to me does not include a `memorize` tool. If you want this saved into the knowledge graph for other agents, I can store these decisions via the available knowledge graph tools (create_entities / add_observations). Please confirm if you want me to create an entity representing the stack (I can do that next).

---

If you want I can now:
- Generate the `package.json`, `server/index.js` skeleton with all endpoints, DB initialization and seed script, and a minimal `public/` folder with the vanilla frontend scaffold; or
- Create the Dockerfile tuned for `better-sqlite3` builds (include build-essential) and produce a README with full run instructions and curl tests.

Which would you like me to do next?