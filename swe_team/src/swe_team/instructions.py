"""
instructions.py - User Project Requirements
============================================
Define your project requirements here. The crew will read this file
and build your application according to these specifications.

HOW TO USE:
1. Edit the REQUIREMENTS variable below with your project description
2. Run: .\run.ps1 (or python -m swe_team.main)
3. The crew will build your project in swe_team/output/

TIPS:
- Be specific about features, endpoints, and UI requirements
- Include technology preferences if you have any
- Define validation rules and edge cases
- Specify what success looks like
"""

# ==============================================================================
# PROJECT REQUIREMENTS
# ==============================================================================
# Edit this variable with your project description
# Use multi-line strings (triple quotes) for readability

REQUIREMENTS = """
# Task Tracker - Fullstack Project Specification

## Project Overview
Build a simple task management application with a REST API backend and a web frontend. 
Users can create, read, update, and delete tasks.

## Technology Stack
- **Backend**: Node.js + Express
- **Database**: SQLite (file-based, no setup needed)
- **Frontend**: Vanilla HTML/CSS/JavaScript (no frameworks)
- **Storage**: File system for data persistence

## Backend Requirements

### API Endpoints
1. `GET /api/tasks` - Get all tasks
2. `GET /api/tasks/:id` - Get a specific task
3. `POST /api/tasks` - Create a new task
4. `PUT /api/tasks/:id` - Update a task
5. `DELETE /api/tasks/:id` - Delete a task

### Task Model
```json
{
  "id": 1,
  "title": "Complete project",
  "description": "Build the task tracker app",
  "status": "pending",
  "priority": "high",
  "createdAt": "2024-01-15T10:30:00Z"
}
```

### Validation Rules
- `title`: Required, 1-100 characters
- `description`: Optional, max 500 characters
- `status`: Must be one of: "pending", "in-progress", "completed"
- `priority`: Must be one of: "low", "medium", "high"

### Database Setup
- Use SQLite with a single `tasks` table
- Initialize database on first run if it doesn't exist
- Include sample data seeding function

## Frontend Requirements

### Pages/Views
1. **Task List** - Display all tasks in a table/cards
2. **Task Form** - Create/edit tasks with validation
3. **Task Details** - View individual task with edit/delete options

### Features
- Filter tasks by status (all, pending, in-progress, completed)
- Sort tasks by priority or date
- Visual indicators for priority levels (colors)
- Responsive design (mobile-friendly)
- Form validation with error messages

### UI Requirements
- Clean, modern interface
- Loading states for API calls
- Success/error notifications
- Confirm before deleting tasks

## Testing Criteria for Your Agent

### Must Complete
- ✅ Backend server runs on port 3000
- ✅ All 5 API endpoints work correctly
- ✅ Database persists data between server restarts
- ✅ Frontend connects to backend successfully
- ✅ Can create, view, update, and delete tasks

### Bonus Challenges
- Error handling for invalid data
- CORS configuration for API
- Search functionality
- Task completion timestamps
- Export tasks to JSON

## Success Metrics
Your agent should be able to:
1. Set up the project structure
2. Install necessary dependencies
3. Implement all backend endpoints
4. Create a functional frontend
5. Write a README with setup instructions
6. Handle edge cases gracefully
"""

# ==============================================================================
# ADDITIONAL CONFIGURATION (Optional)
# ==============================================================================

# API Base URL for frontend (if different from default)
API_BASE_URL = 'http://localhost:3000'

# Custom output directory (if different from default 'output')
# OUTPUT_DIR = None  # None uses default 'output' directory

# Additional context or constraints
CONSTRAINTS = """
- Must run in Docker (nikolaik/python-nodejs image)
- Must work offline (no cloud dependencies for MVP)
- Must be implementable by AI agents autonomously
"""

# ==============================================================================
# EXAMPLES - Uncomment and modify to use
# ==============================================================================

# EXAMPLE 1: Simple CRUD API
# REQUIREMENTS = """
# Build a simple REST API for managing books with endpoints:
# - GET /api/books - List all books
# - POST /api/books - Add a new book
# - PUT /api/books/:id - Update a book
# - DELETE /api/books/:id - Delete a book
# 
# Use FastAPI + SQLite. Include validation and error handling.
# """

# EXAMPLE 2: UI-Focused Application
# REQUIREMENTS = """
# Create a weather dashboard that displays:
# - Current weather conditions
# - 5-day forecast
# - Temperature graphs
# 
# Use a free weather API and create a beautiful dark-mode UI.
# Frontend should be React with responsive design.
# """

# EXAMPLE 3: Data Processing Tool
# REQUIREMENTS = """
# Build a CSV data analyzer that:
# - Accepts CSV file uploads
# - Shows data statistics (mean, median, mode)
# - Generates visualizations (charts)
# - Allows filtering and sorting
# 
# Use Python (pandas, matplotlib) for backend.
# Simple HTML/JS frontend for uploads and display.
# """

# ==============================================================================
# VALIDATION
# ==============================================================================

def validate_requirements() -> bool:
    """
    Validate that requirements are properly defined.
    
    Returns:
        bool: True if valid, raises ValueError if not
    """
    if not REQUIREMENTS or not REQUIREMENTS.strip():
        raise ValueError(
            "REQUIREMENTS is empty! Please define your project in instructions.py"
        )
    
    if len(REQUIREMENTS.strip()) < 50:
        raise ValueError(
            "REQUIREMENTS is too short! Please provide more details about your project."
        )
    
    return True


# Auto-validate when imported
if __name__ != "__main__":
    validate_requirements()


# ==============================================================================
# HELPER FUNCTION
# ==============================================================================

def get_requirements_summary() -> str:
    """Get a brief summary of the requirements for logging."""
    lines = [line.strip() for line in REQUIREMENTS.split('\n') if line.strip()]
    # Get first non-comment line that looks like a title
    for line in lines:
        if line.startswith('#') and len(line) > 2:
            return line.strip('#').strip()
    return "Custom Project"
