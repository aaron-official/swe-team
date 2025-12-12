#!/usr/bin/env python3
"""
Task Tracker Backend (Python placeholder implementation)

Description: A production-quality Python backend that mirrors the Task Tracker API
(behaviour and contracts) described in the architecture document. This file
implements the same REST API surface as specified (GET/POST/PUT/DELETE/EXPORT)
and uses SQLite for persistence. It is intended as a fully working Python
implementation for local development and testing. For the canonical Node.js
implementation see server/ templates in the architecture document.

Author: AI Engineering Crew
Generated: 2025-12-12
"""
# ==============================================================================
# IMPORTS
# ==============================================================================
import os
import logging
import sqlite3
import json
import socket
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, root_validator, validator

# ==============================================================================
# CONFIGURATION
# ==============================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
HOST = "localhost"  # IMPORTANT: Always use localhost for host binding
PORT = int(os.getenv("PORT", "8080"))
DB_PATH = os.getenv("DB_PATH", "./data/tasks.db")
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:3000")
SEED_ON_INIT = (os.getenv("SEED_ON_INIT", "true").lower() == "true")

# Validation constants (as per architecture)
STATUS_VALUES = ("pending", "in-progress", "completed")
PRIORITY_VALUES = ("low", "medium", "high")

# ==============================================================================
# LOGGING SETUP
# ==============================================================================
logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger(__name__)

# ==============================================================================
# DATA MODELS (Pydantic)
# ==============================================================================
class TaskBase(BaseModel):
    """Base fields shared by create/update payloads."""

    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[Union[str, None]] = Field(None, max_length=500)
    status: Optional[str] = Field(None)
    priority: Optional[str] = Field(None)

    @validator("status")
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Ensure status is one of allowed values if provided."""
        if v is None:
            return v
        v = v.strip()
        if v not in STATUS_VALUES:
            raise ValueError(f"status must be one of {STATUS_VALUES}")
        return v

    @validator("priority")
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Ensure priority is one of allowed values if provided."""
        if v is None:
            return v
        v = v.strip()
        if v not in PRIORITY_VALUES:
            raise ValueError(f"priority must be one of {PRIORITY_VALUES}")
        return v

    @validator("title")
    def trim_title(cls, v: Optional[str]) -> Optional[str]:
        """Trim title to remove extraneous whitespace."""
        if v is None:
            return v
        return v.strip()

    @validator("description")
    def normalize_description(cls, v: Optional[Union[str, None]]) -> Optional[Union[str, None]]:
        """Normalize empty descriptions to None."""
        if v is None:
            return None
        s = v.strip()
        return s if s != "" else None


class TaskCreate(TaskBase):
    """Payload for creating a task. title is required."""

    title: str = Field(..., min_length=1, max_length=100)

    @root_validator
    def set_defaults(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Set default status and priority if not provided."""
        if values.get("status") is None:
            values["status"] = "pending"
        if values.get("priority") is None:
            values["priority"] = "medium"
        return values


class TaskUpdate(TaskBase):
    """Payload for updating a task. At least one field is required."""

    @root_validator
    def require_at_least_one_field(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure that at least one updatable field is present."""
        provided = [k for k, v in values.items() if v is not None]
        if not provided:
            raise ValueError("At least one field must be provided for update")
        return values


class TaskOut(BaseModel):
    """Task representation returned to clients."""

    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    createdAt: str
    completedAt: Optional[str]

# ==============================================================================
# ERROR TYPES
# ==============================================================================
class NotFoundError(Exception):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Not Found") -> None:
        super().__init__(message)
        self.message = message


class ValidationError(Exception):
    """Raised for validation problems with structured details."""

    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.details = details or {}
        self.message = message

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================
def find_available_port(start_port: int = 8080, max_attempts: int = 10) -> int:
    """Find an available TCP port on localhost starting at start_port.

    Args:
        start_port: Port to start searching from.
        max_attempts: Number of ports to try.

    Returns:
        An available port number (falls back to start_port on failure).
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            continue
    return start_port


def iso_now() -> str:
    """Return current time as ISO 8601 UTC string."""
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

# ==============================================================================
# DATABASE / BUSINESS LOGIC
# ==============================================================================
def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Open (or create) and return a sqlite3.Connection with recommended pragmas.

    Args:
        db_path: Relative path to the sqlite DB file.

    Returns:
        sqlite3.Connection instance with row factory set to sqlite3.Row.

    Raises:
        Exception: If the database cannot be opened or initialised.
    """
    try:
        dir_path = os.path.dirname(os.path.abspath(db_path))
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row
        # Pragmas for WAL mode and reasonable sync/busy timeout
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
        except Exception:
            # Some sqlite builds may ignore journal_mode change; ignore safely
            logger.debug("Could not set journal_mode to WAL; continuing")
        try:
            conn.execute("PRAGMA synchronous = NORMAL;")
        except Exception:
            logger.debug("Could not set synchronous pragma; continuing")
        # busy_timeout is set as a parameter in sqlite3 via sqlite3_busy_timeout pragma
        try:
            conn.execute("PRAGMA busy_timeout = 5000;")
        except Exception:
            logger.debug("Could not set busy_timeout pragma; continuing")
        return conn
    except Exception as exc:
        logger.exception("Failed to open database at %s", db_path)
        raise

def ensure_schema_and_seed(conn: sqlite3.Connection, seed_on_init: bool = SEED_ON_INIT) -> None:
    """Create schema if missing and optionally seed initial tasks.

    Args:
        conn: sqlite3.Connection to operate on.
        seed_on_init: Whether to seed sample tasks when table is empty.
    """
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                createdAt TEXT NOT NULL,
                completedAt TEXT
            );
            """
        )
        conn.commit()

        # Optional index for status (performance)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);")
        conn.commit()

        # Seed if empty
        row = conn.execute("SELECT COUNT(1) as cnt FROM tasks").fetchone()
        count = int(row["cnt"]) if row is not None else 0
        if seed_on_init and count == 0:
            now = iso_now()
            tasks = [
                ("Welcome to Task Tracker", "This is a sample task.", "pending", "medium", now, None),
                ("Try editing this task", "Use the edit button.", "in-progress", "low", now, None),
                ("Complete this task", "Mark as completed to set completedAt.", "completed", "high", now, now),
            ]
            cur = conn.cursor()
            cur.executemany(
                "INSERT INTO tasks (title, description, status, priority, createdAt, completedAt) VALUES (?, ?, ?, ?, ?, ?)",
                tasks,
            )
            conn.commit()
    except Exception:
        logger.exception("Failed ensuring schema or seeding DB")
        raise

def list_tasks(
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "createdAt",
    sort_order: str = "desc",
    limit: int = 100,
    offset: int = 0,
    conn: Optional[sqlite3.Connection] = None,
) -> List[Dict[str, Any]]:
    """List tasks using provided filters and pagination.

    Args:
        status: Filter by status.
        search: Search token to match title or description (contains, case-insensitive).
        sort_by: 'priority' or 'createdAt'
        sort_order: 'asc' or 'desc'
        limit: Maximum number of records to return.
        offset: Pagination offset.
        conn: Optional sqlite3.Connection. If None a new connection is created.

    Returns:
        A list of task dictionaries.
    """
    connection_created = False
    if conn is None:
        conn = get_db_connection()
        connection_created = True
    try:
        allowed_sort_by = ("priority", "createdAt")
        if sort_by not in allowed_sort_by:
            sort_by = "createdAt"
        order = "ASC" if sort_order.lower() == "asc" else "DESC"

        sql = "SELECT * FROM tasks"
        params: List[Any] = []
        clauses: List[str] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        if search:
            clauses.append("(LOWER(title) LIKE ? OR LOWER(COALESCE(description, '')) LIKE ?)")
            token = f"%{search.lower()}%"
            params.extend([token, token])
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += f" ORDER BY {sort_by} {order} LIMIT ? OFFSET ?"
        params.extend([min(1000, max(1, int(limit))), max(0, int(offset))])

        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        result: List[Dict[str, Any]] = []
        for r in rows:
            result.append(
                {
                    "id": int(r["id"]),
                    "title": r["title"],
                    "description": r["description"],
                    "status": r["status"],
                    "priority": r["priority"],
                    "createdAt": r["createdAt"],
                    "completedAt": r["completedAt"],
                }
            )
        return result
    except Exception:
        logger.exception("Failed to list tasks")
        raise
    finally:
        if connection_created:
            conn.close()

def get_task_by_id(task_id: int, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
    """Retrieve a single task by id.

    Args:
        task_id: Numeric ID of task.
        conn: Optional sqlite3.Connection.

    Returns:
        Task dictionary.

    Raises:
        NotFoundError: If the task does not exist.
    """
    connection_created = False
    if conn is None:
        conn = get_db_connection()
        connection_created = True
    try:
        cur = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        if row is None:
            raise NotFoundError("Task not found")
        return {
            "id": int(row["id"]),
            "title": row["title"],
            "description": row["description"],
            "status": row["status"],
            "priority": row["priority"],
            "createdAt": row["createdAt"],
            "completedAt": row["completedAt"],
        }
    except NotFoundError:
        raise
    except Exception:
        logger.exception("Failed to get task by id %s", task_id)
        raise
    finally:
        if connection_created:
            conn.close()

def create_task(payload: TaskCreate, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
    """Create a new task in the DB.

    Args:
        payload: TaskCreate payload (validated by Pydantic).
        conn: Optional sqlite3.Connection.

    Returns:
        The created task as a dict.
    """
    connection_created = False
    if conn is None:
        conn = get_db_connection()
        connection_created = True
    try:
        now = iso_now()
        completed_at = None
        if payload.status == "completed":
            completed_at = iso_now()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO tasks (title, description, status, priority, createdAt, completedAt) VALUES (?, ?, ?, ?, ?, ?)",
            (payload.title, payload.description, payload.status, payload.priority, now, completed_at),
        )
        conn.commit()
        task_id = cur.lastrowid
        return get_task_by_id(int(task_id), conn=conn)
    except Exception:
        logger.exception("Failed to create task")
        raise
    finally:
        if connection_created:
            conn.close()

def update_task(task_id: int, payload: TaskUpdate, conn: Optional[sqlite3.Connection] = None) -> Dict[str, Any]:
    """Update an existing task using provided payload.

    Args:
        task_id: ID of task to update.
        payload: TaskUpdate payload.
        conn: Optional sqlite3.Connection.

    Returns:
        The updated task.

    Raises:
        NotFoundError: If task does not exist.
    """
    connection_created = False
    if conn is None:
        conn = get_db_connection()
        connection_created = True
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        if row is None:
            raise NotFoundError("Task not found")

        # derive new values
        title = payload.title if payload.title is not None else row["title"]
        description = payload.description if ("description" in payload.__fields_set__ and payload.description is not None) else row["description"]
        status = payload.status if payload.status is not None else row["status"]
        priority = payload.priority if payload.priority is not None else row["priority"]

        # completedAt logic
        existing_completed = row["completedAt"]
        completed_at = existing_completed
        if payload.status is not None:
            if payload.status == "completed":
                if not existing_completed:
                    completed_at = iso_now()
            else:
                # moving away from completed
                completed_at = None

        cur.execute(
            "UPDATE tasks SET title = ?, description = ?, status = ?, priority = ?, completedAt = ? WHERE id = ?",
            (title, description, status, priority, completed_at, task_id),
        )
        conn.commit()
        return get_task_by_id(task_id, conn=conn)
    except NotFoundError:
        raise
    except Exception:
        logger.exception("Failed to update task %s", task_id)
        raise
    finally:
        if connection_created:
            conn.close()

def delete_task(task_id: int, conn: Optional[sqlite3.Connection] = None) -> None:
    """Delete a task by id. Raises NotFoundError if absent."""
    connection_created = False
    if conn is None:
        conn = get_db_connection()
        connection_created = True
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise NotFoundError("Task not found")
    except NotFoundError:
        raise
    except Exception:
        logger.exception("Failed to delete task %s", task_id)
        raise
    finally:
        if connection_created:
            conn.close()

# ==============================================================================
# API ENDPOINTS (FastAPI)
# ==============================================================================
app = FastAPI(title="Task Tracker API (Python)", version="1.0.0")

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN] if CORS_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle NotFoundError and return 404 JSON payload."""
    payload = {"error": exc.message or "Not Found", "code": "not_found"}
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=payload)

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle ValidationError and return 400 JSON payload with details."""
    payload: Dict[str, Any] = {"error": exc.message or "Validation failed", "code": "validation_error"}
    if exc.details:
        payload["details"] = exc.details
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=payload)

@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Generic handler for unexpected exceptions returning a 500 response."""
    logger.exception("Unhandled exception during request: %s %s", request.method, request.url)
    payload = {"error": "Internal Server Error", "code": "internal_error"}
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)

@app.on_event("startup")
def startup_event() -> None:
    """Open DB, ensure schema and optionally seed data on startup."""
    try:
        conn = get_db_connection()
        ensure_schema_and_seed(conn, seed_on_init=SEED_ON_INIT)
        conn.close()
        logger.info("Database initialized at %s", DB_PATH)
    except Exception:
        logger.exception("Failed during startup DB initialization")
        raise

@app.get("/healthz")
async def healthz() -> JSONResponse:
    """Healthcheck endpoint returning ok status."""
    return JSONResponse(status_code=200, content={"status": "ok"})

@app.get("/api/tasks", response_model=List[TaskOut])
async def api_list_tasks(
    status: Optional[str] = None,
    sortBy: str = "createdAt",
    sortOrder: str = "desc",
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[TaskOut]:
    """List tasks with optional filters and pagination.

    Query params follow the architecture document.
    """
    try:
        # basic validation for status and sort order
        if status is not None and status not in STATUS_VALUES:
            raise ValidationError("Invalid status filter", {"status": f"Must be one of {STATUS_VALUES}"})
        if sortBy not in ("priority", "createdAt"):
            sortBy = "createdAt"
        if sortOrder.lower() not in ("asc", "desc"):
            sortOrder = "desc"

        tasks = list_tasks(status=status, search=search, sort_by=sortBy, sort_order=sortOrder, limit=limit, offset=offset)
        return [TaskOut(**t) for t in tasks]
    except ValidationError:
        raise
    except Exception:
        logger.exception("Error listing tasks")
        raise

@app.get("/api/tasks/{task_id}", response_model=TaskOut)
async def api_get_task(task_id: int) -> TaskOut:
    """Get a single task by id. Returns 404 if not found."""
    try:
        if task_id <= 0:
            raise ValidationError("Invalid id parameter", {"id": "Must be a positive integer"})
        task = get_task_by_id(task_id)
        return TaskOut(**task)
    except ValidationError:
        raise
    except NotFoundError:
        raise
    except Exception:
        logger.exception("Error getting task %s", task_id)
        raise

@app.post("/api/tasks", status_code=201, response_model=TaskOut)
async def api_create_task(payload: TaskCreate) -> TaskOut:
    """Create a new task. Returns 201 with created task."""
    try:
        created = create_task(payload)
        return TaskOut(**created)
    except Exception as exc:  # explicit exception handler will convert to 500
        # Map Pydantic validation errors to our ValidationError if they appear
        if isinstance(exc, ValueError):
            raise ValidationError("Validation failed", {"payload": str(exc)})
        logger.exception("Error creating task")
        raise

@app.put("/api/tasks/{task_id}", response_model=TaskOut)
async def api_update_task(task_id: int, payload: TaskUpdate) -> TaskOut:
    """Update a task by id. Returns updated Task or 404 if missing."""
    try:
        if task_id <= 0:
            raise ValidationError("Invalid id parameter", {"id": "Must be a positive integer"})
        updated = update_task(task_id, payload)
        return TaskOut(**updated)
    except ValidationError:
        raise
    except NotFoundError:
        raise
    except Exception:
        logger.exception("Error updating task %s", task_id)
        raise

@app.delete("/api/tasks/{task_id}", status_code=204)
async def api_delete_task(task_id: int) -> Response:
    """Delete a task by id. Returns 204 No Content on success."""
    try:
        if task_id <= 0:
            raise ValidationError("Invalid id parameter", {"id": "Must be a positive integer"})
        delete_task(task_id)
        return Response(status_code=204)
    except ValidationError:
        raise
    except NotFoundError:
        raise
    except Exception:
        logger.exception("Error deleting task %s", task_id)
        raise

@app.get("/api/tasks/export")
async def api_export_tasks() -> Response:
    """Export all tasks as a JSON attachment."""
    try:
        conn = get_db_connection()
        tasks = list_tasks(conn=conn, limit=10000, offset=0)
        conn.close()
        filename = "tasks-export.json"
        content = json.dumps(tasks, indent=2)
        # Return as a FileResponse equivalent by writing to a temp file in-memory is not necessary;
        # FastAPI/Starlette FileResponse expects a file on disk. Use JSONResponse with headers to suggest download.
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/json",
        }
        return JSONResponse(content=json.loads(content), headers=headers)
    except Exception:
        logger.exception("Error exporting tasks")
        raise

# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    import uvicorn

    # Auto-find an available port if requested port is busy
    try:
        resolved_port = int(os.environ.get("PORT", str(find_available_port(start_port=PORT))))
    except Exception:
        resolved_port = PORT

    # IMPORTANT: Always use localhost, never 0.0.0.0 for local development
    uvicorn.run(app, host=HOST, port=resolved_port)