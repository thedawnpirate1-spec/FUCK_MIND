# KanMind Backend

Backend REST API for the KanMind Kanban Board application, built with Django and Django REST Framework.

## Setup and Local Development

Follow these steps to set up and run the backend locally from scratch.

### 1. Clone the repository
```bash
git clone https://github.com/thedawnpirate1-spec/FUCK_MIND.git
cd FUCK_MIND
```

### 2. Navigate to the backend directory
```bash
cd backend
```

### 3. Create and activate a virtual environment
Create a virtual environment:
```bash
python -m venv venv
```

Activate the virtual environment:
* On Windows (PowerShell):
  ```powershell
  .\venv\Scripts\activate
  ```
* On Windows (Command Prompt):
  ```cmd
  .\venv\Scripts\activate.bat
  ```
* On macOS / Linux:
  ```bash
  source venv/bin/activate
  ```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure environment variables
Create a `.env` file in the `backend/` directory by copying the example file:
* On Windows:
  ```cmd
  copy .env.example .env
  ```
* On macOS / Linux:
  ```bash
  cp .env.example .env
  ```

The `.env.example` file contains pre-configured defaults for local development.

### 6. Run database migrations
```bash
python manage.py migrate
```

### 7. (Optional) Create an admin superuser and seed demo data
Create an administrative user:
```bash
python manage.py createsuperuser
```

Initialize sample boards, tasks, and users for testing:
```bash
python manage.py seed_frontend
```

### 8. Run the test suite
Verify that all unit and integration tests pass:
```bash
python manage.py test
```

### 9. Start the development server
```bash
python manage.py runserver
```
The API is now running at `http://127.0.0.1:8000/`.

## Interactive API Documentation

Once the development server is running, the following interactive documentation tools are available:

* **Swagger UI:** `http://127.0.0.1:8000/api/docs/` (Interactive API explorer and testing tool)
* **ReDoc:** `http://127.0.0.1:8000/api/redoc/` (Structured technical specification)
* **OpenAPI Schema (JSON/YAML):** `http://127.0.0.1:8000/api/schema/`
* **Postman Collection:** The collection file is located at `postman/KanMind_API.postman_collection.json` and can be imported directly into Postman.

## API Endpoints Overview

### Authentication

| Method | Endpoint | Protection | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register/` | Public | Register a new user and return an auth token |
| `POST` | `/api/auth/login/` | Public | Login via username or email and password |
| `POST` | `/api/auth/logout/` | Token / Bearer | Log out and delete active authentication token |
| `GET` | `/api/auth/user/` | Token / Bearer | Retrieve profile data of authenticated user |

### Contacts

| Method | Endpoint | Protection | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/contacts/` | Token / Bearer | Retrieve list of all contacts |
| `POST` | `/api/contacts/` | Token / Bearer | Create a new contact |
| `GET` | `/api/contacts/<id>/` | Token / Bearer | Retrieve single contact details |
| `PUT` / `PATCH` | `/api/contacts/<id>/` | Token / Bearer | Update a contact |
| `DELETE` | `/api/contacts/<id>/` | Token / Bearer | Delete a contact |

### Tasks (Kanban Board)

| Method | Endpoint | Protection | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/tasks/` | Token / Bearer | Retrieve tasks (filter by `status`, `priority`, `search`, `assigned_to`, `board`) |
| `POST` | `/api/tasks/` | Token / Bearer | Create a task (supports nested subtasks) |
| `GET` | `/api/tasks/<id>/` | Token / Bearer | Retrieve task details including subtasks, assignees, and reviewer |
| `PUT` / `PATCH` | `/api/tasks/<id>/` | Token / Bearer | Update task (status transitions, priority, assignees) |
| `DELETE` | `/api/tasks/<id>/` | Token / Bearer | Delete task (cascades associated subtasks) |

### Subtasks

| Method | Endpoint | Protection | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/subtasks/` | Token / Bearer | Retrieve subtasks (filterable with `?task=<task_id>`) |
| `POST` | `/api/subtasks/` | Token / Bearer | Create a subtask for a task |
| `GET` | `/api/subtasks/<id>/` | Token / Bearer | Retrieve single subtask details |
| `PUT` / `PATCH` | `/api/subtasks/<id>/` | Token / Bearer | Update subtask (toggle `is_completed` status) |
| `DELETE` | `/api/subtasks/<id>/` | Token / Bearer | Delete a subtask |

### Boards and Comments

| Method | Endpoint | Protection | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/boards/` | Token / Bearer | List all boards for the authenticated user |
| `POST` | `/api/boards/` | Token / Bearer | Create a new board with members |
| `GET` | `/api/boards/<id>/` | Token / Bearer | Retrieve board details with linked tasks and members |
| `PUT` / `PATCH` | `/api/boards/<id>/` | Token / Bearer | Update board title and member list |
| `DELETE` | `/api/boards/<id>/` | Token / Bearer | Delete a board |
| `GET` | `/api/tasks/assigned-to-me/` | Token / Bearer | Retrieve tasks assigned to current user for dashboard |
| `GET` | `/api/tasks/reviewing/` | Token / Bearer | Retrieve tasks in review for current user |
| `GET` | `/api/email-check/` | Token / Bearer | Check user availability for board invitations (`?email=...`) |
| `GET` | `/api/tasks/<id>/comments/` | Token / Bearer | Retrieve comments for a task |
| `POST` | `/api/tasks/<id>/comments/` | Token / Bearer | Create a comment on a task |
| `DELETE` | `/api/tasks/<task_id>/comments/<id>/` | Token / Bearer | Delete comment by author |

## Frontend Integration

This repository contains the backend service. It is designed to work with decoupled frontend applications, such as the Developer Akademie KanMind client or custom web applications.

To connect a frontend:
1. Ensure the backend server is running at `http://127.0.0.1:8000`.
2. Configure your frontend API base URL to `http://127.0.0.1:8000`.
3. If connecting from another port or domain, add the origin to `CORS_ALLOWED_ORIGINS` in your `.env` file.

## Production Deployment Guidelines

When deploying to a production environment (such as a Linux VPS, Render, Railway, or Heroku), consider the following configuration checklist:

1. **Security and Environment Variables:**
   * Set `DEBUG=False` in your production `.env` file.
   * Generate a random, cryptographically secure `SECRET_KEY`.
   * Configure allowed domains in `ALLOWED_HOSTS` (e.g. `ALLOWED_HOSTS=api.example.com,example.com`).
   * Restrict CORS origin domains: `CORS_ALLOW_ALL_ORIGINS=False` and `CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com`.

2. **Production Application Server (WSGI / ASGI):**
   * Use an application server such as Gunicorn or Uvicorn:
     ```bash
     pip install gunicorn
     gunicorn kanmind_backend.wsgi:application --bind 0.0.0.0:8000
     ```

3. **Static File Handling:**
   * Collect static assets for admin interface and Swagger UI:
     ```bash
     python manage.py collectstatic --noinput
     ```
   * Serve static files via WhiteNoise or a reverse proxy such as Nginx.

4. **Production Database:**
   * PostgreSQL is recommended for production environments:
     ```bash
     pip install psycopg2-binary
     ```
   * Configure `DATABASES` in `settings.py` or provide the connection string via environment variables.

## Project History (14-Day Roadmap)

### Day 1: Project Setup
* Initialized Django project with Django REST Framework and CORS headers
* Configured `.env` loader and `requirements.txt`

### Day 2: Custom User Model
* Created `core` application
* Implemented `CustomUser` model with unique email and avatar color field
* Configured `AUTH_USER_MODEL` in settings and registered model in admin
* Created and applied initial database migrations

### Day 3: User Registration
* Implemented `RegistrationSerializer` with password confirmation and validation
* Added `RegistrationView` at `/api/auth/register/` returning auth tokens directly

### Day 4: Login and Logout
* Implemented `LoginSerializer` supporting login via username or email
* Built `LoginView` and `LogoutView` endpoints
* Added test cases in `core/tests.py`

### Day 5: Protected Routes and User Profile
* Implemented `UserDetailSerializer` for profile serialization
* Created `UserProfileView` guarded with `IsAuthenticated` permission
* Added integration tests for valid, invalid, and missing tokens

### Day 6: Contact Management
* Created `Contact` model with fields for name, email, phone, and color
* Built `ContactSerializer` and CRUD views (`ContactListCreateView`, `ContactDetailView`)
* Added test coverage for contact creation, listing, updating, and deletion

### Day 7: Task Model and Creation
* Created `Task` model supporting titles, descriptions, due dates, priorities, categories, and contacts
* Built `TaskSerializer` with nested details and `TaskListCreateView`
* Added tests for task creation and contact assignment

### Day 8: Task Filtering
* Added query parameter filtering in `TaskListCreateView` (`status`, `priority`, `search`, `assigned_to`, `board`)
* Added unit test cases for filter parameters

### Day 9: Task Updates
* Implemented `TaskDetailView` supporting `PUT` and `PATCH` requests
* Added support for status transitions and partial updates
* Added test cases for update operations

### Day 10: Subtasks Management
* Created `Subtask` model with completion state persistence
* Built `SubtaskSerializer`, `SubtaskListCreateView`, and `SubtaskDetailView`
* Integrated nested subtask serialization into `TaskSerializer`
* Added test cases for subtask lifecycle and task nesting

### Day 11: Task Deletion and Cascade Handling
* Verified `TaskDetailView` deletion flow returning `204 NO CONTENT`
* Verified cascade deletion of associated subtasks while preserving assigned contacts
* Added integration tests for cascading deletion

### Day 12: Global Error Handling and CORS Policies
* Implemented central `custom_exception_handler` in `core/exceptions.py`
* Standardized JSON error responses for 400, 401, 403, 404, and 500 status codes
* Configured custom 404 and 500 handlers returning JSON payloads
* Added configurable CORS policies with credentials support

### Day 13: Authentication Headers and Edge Cases
* Implemented `FlexibleTokenAuthentication` supporting both `Token` and `Bearer` prefixes
* Added nested creation and updates for subtasks within task payloads
* Handled edge cases: empty date strings, null contacts, whitespace trimming, and status normalization
* Created Postman collection covering all endpoints

### Day 14: Swagger and OpenAPI Documentation
* Integrated `drf-spectacular` for OpenAPI 3 schema generation
* Added interactive Swagger UI at `/api/docs/` and ReDoc at `/api/redoc/`
* Verified documentation endpoints and complete test suite (all 68 tests passing)
* Prepared deployment guidelines and documentation
