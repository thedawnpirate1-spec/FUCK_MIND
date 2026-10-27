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

The API implements exactly the endpoints of the KanMind endpoint documentation. All endpoints except registration and login require the header `Authorization: Token <token>` (the `Bearer` prefix is accepted as well).

### Authentication

| Method | Endpoint | Protection | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/registration/` | Public | Register a new user (`fullname`, `email`, `password`, `repeated_password`); returns `token`, `fullname`, `email`, `user_id` |
| `POST` | `/api/login/` | Public | Login with `email` and `password`; returns `token`, `fullname`, `email`, `user_id` |
| `GET` | `/api/email-check/?email=...` | Token | Return the user (`id`, `email`, `fullname`) registered with this email (`404` if unknown) |

### Boards

| Method | Endpoint | Protection | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/boards/` | Token | Boards the user owns or is a member of, with `member_count`, `ticket_count`, `tasks_to_do_count`, `tasks_high_prio_count`, `owner_id` |
| `POST` | `/api/boards/` | Token | Create a board (`title`, `members` as user ids); the requesting user becomes the owner |
| `GET` | `/api/boards/{board_id}/` | Owner / member | Board with `owner_id`, `members` and `tasks` |
| `PATCH` | `/api/boards/{board_id}/` | Owner / member | Update `title` and `members`; returns `owner_data` and `members_data` |
| `DELETE` | `/api/boards/{board_id}/` | Owner | Delete the board including its tasks and comments |

### Tasks

| Method | Endpoint | Protection | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/tasks/assigned-to-me/` | Token | Tasks where the user is the assignee |
| `GET` | `/api/tasks/reviewing/` | Token | Tasks where the user is the reviewer |
| `POST` | `/api/tasks/` | Board member | Create a task; `status`: `to-do`, `in-progress`, `review`, `done`; `priority`: `low`, `medium`, `high`; assignee and reviewer must be board members |
| `PATCH` | `/api/tasks/{task_id}/` | Board member | Update a task; the board of a task cannot be changed |
| `DELETE` | `/api/tasks/{task_id}/` | Task creator / board owner | Delete a task |

### Comments

| Method | Endpoint | Protection | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/tasks/{task_id}/comments/` | Board member | Comments of a task, oldest first |
| `POST` | `/api/tasks/{task_id}/comments/` | Board member | Add a comment (`content`); the author is the requesting user |
| `DELETE` | `/api/tasks/{task_id}/comments/{comment_id}/` | Comment author | Delete a comment |

### Status codes

`400` invalid data, `401` not authenticated, `403` not allowed (e.g. not a member of the board), `404` resource not found, `500` internal server error.

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

### Day 15: Alignment with the Endpoint Documentation
* Reduced the API to the endpoints of the endpoint documentation (`/api/registration/`, `/api/login/`, `/api/email-check/`, boards, tasks, comments)
* Removed contacts, subtasks, `/api/auth/*` and the task list/detail `GET` endpoints, including the models and admin entries
* Board list/create now return `member_count`, `ticket_count`, `tasks_to_do_count`, `tasks_high_prio_count` and `owner_id`; board detail returns `owner_id`, `members` and `tasks`; board update returns `owner_data` and `members_data`
* Limited task status to `to-do`, `in-progress`, `review`, `done` and priority to `low`, `medium`, `high`; assignee and reviewer must be board members
* Task deletion is limited to the task creator and the board owner; comments can only be deleted by their author
* Rewrote the test suite and regenerated the Postman collection (49 requests with assertions)
