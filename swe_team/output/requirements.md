# Task Tracker - Product Requirements Document (PRD)

## 1. Executive Summary
We are building a lightweight, local-first task management web application that lets users create, read, update, and delete tasks via a REST API backend and a responsive frontend. Target users are individual developers, students, or small teams who want a simple, zero-setup task tracker that runs locally (or in a local Docker container) and persists data to an on-disk SQLite file. The key value proposition is a minimal, dependable task tracker that requires no cloud services, is easy to run (Docker), and provides a clean, accessible dark-mode UI with the core task management workflows implemented and tested.

- Target user persona: Individual contributor or small-team member who wants a simple, local task tracker with no cloud setup.
- Key value proposition: Zero-setup, local-first, persistent task management with a simple REST API and a clean vanilla-frontend.

---

## 2. Functional Requirements

Each feature below has an ID, user story, acceptance criteria (testable) and priority.

### F001 — Task CRUD API
- User Story: As a user, I want to create, read, update, and delete tasks via HTTP endpoints so that I can manage tasks programmatically or via the frontend.
- Endpoints (all JSON):
  - `GET /api/tasks` — list all tasks (supports query params `status`, `sortBy`, `search`)
  - `GET /api/tasks/:id` — get single task
  - `POST /api/tasks` — create a task
  - `PUT /api/tasks/:id` — update a task
  - `DELETE /api/tasks/:id` — delete a task
- Request/Response contract (example create):
```json
POST /api/tasks
{
  "title": "Build feature",
  "description": "Detailed text (optional)",
  "status": "pending",
  "priority": "high"
}
Response 201:
{
  "id": 1,
  "title": "...",
  "description": "...",
  "status": "pending",
  "priority": "high",
  "createdAt": "2024-01-15T10:30:00Z",
  "completedAt": null
}
```
- Acceptance Criteria:
  - Server runs on port `3000`.
  - `POST` returns `201` and newly created task with generated `id` and `createdAt`.
  - `GET /api/tasks` returns `200` and JSON array containing tasks persisted across server restarts.
  - `PUT` returns `200` and the updated task; invalid `id` returns `404`.
  - `DELETE` returns `204` on success and the task is removed from DB.
  - Validations (see V001) apply and invalid payloads return `400` with error details.
- Priority: MUST-HAVE

### F002 — Task Model & Validation
- User Story: As a user, I want the system to validate input so that data stays consistent and reliable.
- Task model fields:
  - `id` (integer, PK)
  - `title` (string, required, 1-100 chars)
  - `description` (string, optional, max 500 chars)
  - `status` (enum: `pending`, `in-progress`, `completed`)
  - `priority` (enum: `low`, `medium`, `high`)
  - `createdAt` (ISO 8601 UTC string)
  - `completedAt` (ISO 8601 UTC string or null) — *optional field included for completeness and bonus acceptance*
- Acceptance Criteria:
  - API rejects `title` missing or out-of-range with `400`.
  - API rejects `description` length > 500 with `400`.
  - API rejects invalid `status` or `priority` with `400` and lists allowed values.
  - When `status` is set to `completed`, `completedAt` is set to current UTC time.
- Priority: MUST-HAVE

### F003 — Database & Persistence
- User Story: As a user, I want tasks persisted between restarts so data is durable.
- Requirements:
  - SQLite used, single `tasks` table.
  - On first run, initialize DB and run seed function to create 3 sample tasks.
  - DB file located at `./data/tasks.db` (project root).
- Schema (SQL):
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
- Acceptance Criteria:
  - DB file created automatically if missing.
  - Data persists between server restarts and is readable.
- Priority: MUST-HAVE

### F004 — Frontend: Task List, Form, Details
- User Story: As a user, I want a web UI to view and manage tasks so I can interact without using API clients.
- Views:
  - Task List: table/card view with status filters, sorting controls, search box.
  - Task Form: create/edit with client-side validation and meaningful error messages.
  - Task Details: full task view with edit/delete controls and confirmation on delete.
- Acceptance Criteria:
  - Frontend uses vanilla HTML/CSS/JS, connects to backend `http://localhost:3000/api`.
  - Create/update/delete flows work end-to-end and reflect immediately in UI.
  - UI shows loading states for API calls and success/error notifications.
  - Confirmation modal before delete.
- Priority: MUST-HAVE

### F005 — Filtering, Sorting, Visuals
- User Story: As a user, I want to filter and sort tasks so I can find important tasks quickly.
- Requirements:
  - Filter by status: all, pending, in-progress, completed.
  - Sort by priority, createdAt (asc/desc).
  - Visual priority indicator colors and status badges.
- Acceptance Criteria:
  - Filter and sort work on the server or client consistently.
  - Visual indicators match color mapping in UI spec.
- Priority: SHOULD-HAVE

### F006 — Bonus: Error Handling, CORS, Export, Search
- User Story: As a power user, I want robust error handling, API CORS support, search, completion timestamps, and export to JSON so I can integrate & back up data.
- Acceptance Criteria:
  - API returns structured error JSON on failures (message, code).
  - Configurable CORS allowed origins; default: allow `http://localhost:3000`.
  - `GET /api/tasks?search=term` returns tasks with title/description matches.
  - `GET /api/tasks/export` returns JSON file with all tasks (download).
- Priority: NICE-TO-HAVE / SHOULD-HAVE for CORS & Error handling

---

## 3. Non-Functional Requirements

- Performance:
  - Typical API response time: < 200ms on local dev machine.
  - Throughput target: 100 requests/minute for MVP (local).
- Security:
  - Authentication: NONE for MVP (explicit decision).
  - Authorization: not required; single-user local app.
  - Data protection: store DB file with file system permissions; never send sensitive info.
  - Use HTTPS only if deployed behind a reverse proxy — not required for local Docker dev.
- Usability:
  - Accessibility: semantic HTML, keyboard navigable, proper labels, color contrast >= 4.5:1 for text.
  - Responsive: usable on mobile and desktop (see breakpoints).
  - Error UX: clear inline validation and toast notifications.
- Reliability:
  - Graceful error handling: API returns appropriate HTTP codes (200/201/204/400/404/500).
  - DB initialization must not crash on concurrent startup.
  - Uptime: local dev target not enforced; aim for stable startup and clean shutdown.

---

## 4. Technical Constraints

- Must run in Docker using the nikolaik/python-nodejs image.
- Backend: Node.js + Express, listen on port `3000`.
- Database: SQLite file at `./data/tasks.db`. No cloud dependencies.
- Frontend: Vanilla HTML/CSS/JS only (no frameworks).
- Must be implementable by AI agents autonomously (no manual configuration).
- Must work offline (no external APIs needed for MVP).
- Seed sample data on first run.

Container run example:
```bash
docker build -t task-tracker .
docker run --rm -p 3000:3000 -v $(pwd)/data:/app/data task-tracker
```

---

## 5. UI/UX Specifications

- Theme: **Dark mode** base colors:
  - Background primary: `#1a1a2e`
  - Background secondary / panels: `#16213e`
  - Accent color: `#00A3FF` (buttons, primary CTAs)
  - Text primary: `#E6EEF8`, muted text: `#A9B6C6`
  - Priority colors:
    - High: `#FF6B6B` (red)
    - Medium: `#FFD166` (amber)
    - Low: `#4EE1A0` (green)
- Layout patterns:
  - Desktop: left-aligned header, main content area with top toolbar (filters/sort/search), content grid with cards or table.
  - Mobile: single-column flow, collapsible filters in a top sheet.
  - Components: header bar, sidebar (optional collapsed), cards for tasks (title, status badge, priority chip, actions), modals for form and delete confirmation.
- Responsive breakpoints:
  - Mobile: <= 600px (single column)
  - Tablet: 601px–1024px (two columns / stacked)
  - Desktop: >1024px (table or multi-column cards)
- Interactions:
  - Loading spinner on list and form submit.
  - Toasts for success/error.
  - Confirm delete modal with explicit "Delete" button.

---

## 6. Out of Scope (MVP Exclusions)

- User authentication or multi-user accounts.
- Real-time sync (WebSockets).
- Remote/cloud DB or hosting.
- Third-party integrations (calendar, email).
- Rich text editor for description.
- Role-based access control.
- Advanced analytics/dashboards.

---

## 7. Autonomous Decision Log (Assumptions & Reasoning)

1. Authentication: *Assumed NONE for MVP.* Reason: user specified a simple app and Decision Framework sets "None (MVP)". Eliminates complexity for local-first app.
2. Include `completedAt`: *Added as optional field.* Reason: bonus asked for completion timestamps; having this field improves acceptance criteria and is low-cost to implement.
3. Frontend stack: *Vanilla HTML/CSS/JS.* Reason: user explicitly requested no frameworks.
4. DB file path: `./data/tasks.db`. Reason: consistent, predictable path for Docker volume mounting.
5. Port: `3000`. Reason: user’s testing criteria explicitly requires port 3000.
6. Docker image: `nikolaik/python-nodejs`. Reason: required by Technical Constraints.
7. CORS: *Not enabled by default beyond local dev allowance.* Reason: default local-only security; provide configuration for enabling as bonus.
8. Error responses: structured JSON `{ error: "...", details: {...} }`. Reason: testability and consistent frontend handling.
9. Seed data: *3 sample tasks on first run.* Reason: enables quick manual testing.
10. Search implementation: *Optional server-side `search` query param*. Reason: improves UX without major complexity.
11. Performance targets: `<200ms` local. Reason: realistic for SQLite + Express on local machine.
12. Accessibility: *WCAG color contrast target >= 4.5:1 for text.* Reason: ensure baseline accessibility.
13. Export endpoint: `GET /api/tasks/export` returns `application/json` file. Reason: supports backup/export requirement in bonus.

---

## API Error Codes (summary)
- 200 OK — successful GET/PUT
- 201 Created — successful POST
- 204 No Content — successful DELETE
- 400 Bad Request — validation failed (body: `{ error, details }`)
- 404 Not Found — resource not found
- 500 Internal Server Error — unexpected failure

---

## Acceptance / Success Criteria (project-level)
- Backend server runs on port 3000 and all 5 API endpoints pass integration tests.
- SQLite DB persists tasks between restarts and is auto-created and seeded.
- Frontend (vanilla) successfully interacts with backend for CRUD flows.
- Form validation and delete confirmation implemented.
- README with setup instructions and Docker commands included.
- Bonus (should-have): structured error handling and optional CORS and export features.

---

## Deliverables
- Source code with `server/` (Node/Express), `public/` (frontend), `data/` (DB), `Dockerfile`, and `README.md` with setup & test instructions.
- SQL schema and seed script.
- Postman/HTTPie snippets or curl examples for the 5 endpoints.
- Simple test checklist validating acceptance criteria.

---

If you want, I will:
- Produce the complete file tree and starter code skeleton (Dockerfile, package.json, Express server with endpoints and SQLite initialization).
- Or generate the README and sample curl tests next.

Would you like me to scaffold the project files now?