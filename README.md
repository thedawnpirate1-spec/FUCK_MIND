# KanMind Backend

Backend REST API für die KanMind Kanban Board Anwendung, gebaut mit Django und Django REST Framework.

## Setup und lokaler Start

1. Virtuelle Umgebung aktivieren und Abhängigkeiten installieren:
   ```bash
   cd backend
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Umgebungsvariablen anlegen:
   Erstelle eine `.env` Datei im Ordner `backend/` basierend auf `.env.example`:
   ```env
   SECRET_KEY=dein-geheimer-schluessel
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost
   CORS_ALLOW_ALL_ORIGINS=True
   ```

3. Datenbank-Migrationen ausführen:
   ```bash
   python manage.py migrate
   ```

4. Lokalen Entwicklungsserver starten:
   ```bash
   python manage.py runserver
   ```

5. Test-Suite ausführen:
   ```bash
   python manage.py test
   ```

## Interaktive API Dokumentation

Nach dem Start des Entwicklungsservers stehen folgende Dokumentations-Tools zur Verfügung:

* **Swagger UI:** `http://127.0.0.1:8000/api/docs/` (Interaktives Testen aller Endpunkte direkt im Browser)
* **ReDoc:** `http://127.0.0.1:8000/api/redoc/` (Strukturierte technische Spezifikation)
* **OpenAPI Schema (JSON/YAML):** `http://127.0.0.1:8000/api/schema/`
* **Postman Collection:** Die Datei `postman/KanMind_API.postman_collection.json` kann direkt in Postman importiert werden.

## API Endpunkte Übersicht

### Authentifizierung

| Methode | Endpunkt | Schutz | Beschreibung |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register/` | Öffentlich | Registrierung eines neuen Benutzers, liefert Auth-Token |
| `POST` | `/api/auth/login/` | Öffentlich | Login via Username/E-Mail und Passwort |
| `POST` | `/api/auth/logout/` | Token / Bearer | Abmelden und Löschen des aktiven Tokens |
| `GET` | `/api/auth/user/` | Token / Bearer | Profildaten des angemeldeten Benutzers abrufen |

### Kontakte

| Methode | Endpunkt | Schutz | Beschreibung |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/contacts/` | Token / Bearer | Liste aller Kontakte abrufen |
| `POST` | `/api/contacts/` | Token / Bearer | Neuen Kontakt anlegen |
| `GET` | `/api/contacts/<id>/` | Token / Bearer | Einzelnen Kontakt abrufen |
| `PUT` / `PATCH` | `/api/contacts/<id>/` | Token / Bearer | Kontakt bearbeiten |
| `DELETE` | `/api/contacts/<id>/` | Token / Bearer | Kontakt löschen |

### Tasks (Kanban Board)

| Methode | Endpunkt | Schutz | Beschreibung |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/tasks/` | Token / Bearer | Tasks abrufen (Filter: `status`, `priority`, `search`, `assigned_to`) |
| `POST` | `/api/tasks/` | Token / Bearer | Task erstellen (inklusive verschachtelter Subtasks) |
| `GET` | `/api/tasks/<id>/` | Token / Bearer | Task-Details inklusive Assignees und Subtasks abrufen |
| `PUT` / `PATCH` | `/api/tasks/<id>/` | Token / Bearer | Task bearbeiten (z.B. Drag & Drop Statuswechsel, Priorität) |
| `DELETE` | `/api/tasks/<id>/` | Token / Bearer | Task löschen (kaskadiert zugehörige Subtasks) |

### Subtasks

| Methode | Endpunkt | Schutz | Beschreibung |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/subtasks/` | Token / Bearer | Subtasks abrufen (filterbar mit `?task=<task_id>`) |
| `POST` | `/api/subtasks/` | Token / Bearer | Subtask für einen Task erstellen |
| `GET` | `/api/subtasks/<id>/` | Token / Bearer | Einzelnen Subtask abrufen |
| `PUT` / `PATCH` | `/api/subtasks/<id>/` | Token / Bearer | Subtask bearbeiten (z.B. Status `is_completed` toggeln) |
| `DELETE` | `/api/subtasks/<id>/` | Token / Bearer | Subtask löschen |

### Boards & Kommentare (Frontend-Integration)

| Methode | Endpunkt | Schutz | Beschreibung |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/boards/` | Token / Bearer | Liste aller Boards des Benutzers (inkl. Member-/Ticket-Zähler) |
| `POST` | `/api/boards/` | Token / Bearer | Neues Board mit Mitgliedern anlegen |
| `GET` | `/api/boards/<id>/` | Token / Bearer | Board-Details inklusive verknüpfter Tasks und Mitglieder abrufen |
| `PUT` / `PATCH` | `/api/boards/<id>/` | Token / Bearer | Board bearbeiten (Titel, Mitgliederliste) |
| `DELETE` | `/api/boards/<id>/` | Token / Bearer | Board löschen |
| `GET` | `/api/tasks/assigned-to-me/` | Token / Bearer | Eigene zugewiesene Tasks für das Dashboard abrufen |
| `GET` | `/api/tasks/reviewing/` | Token / Bearer | Tasks im Review für das Dashboard abrufen |
| `GET` | `/api/email-check/` | Token / Bearer | E-Mail-Adresse für Board-Einladungen prüfen (`?email=...`) |
| `GET` | `/api/tasks/<id>/comments/` | Token / Bearer | Kommentare eines Tasks abrufen |
| `POST` | `/api/tasks/<id>/comments/` | Token / Bearer | Neuen Kommentar zu einem Task erstellen |
| `DELETE` | `/api/tasks/<task_id>/comments/<id>/` | Token / Bearer | Eigenen Kommentar löschen |

## Deployment Leitfaden

Für das Ausrollen in einer Produktivumgebung (z.B. Linux VPS, Render, Railway, Heroku) sind folgende Schritte zu beachten:

1. **Sicherheit und Umgebungsvariablen:**
   * Setze `DEBUG=False` in der `.env` Datei.
   * Vergib einen sicheren, zufällig generierten `SECRET_KEY`.
   * Trage die Produktions-Domains in `ALLOWED_HOSTS` ein (z.B. `ALLOWED_HOSTS=api.kanmind.de,kanmind.de`).
   * Begrenze CORS auf deine Frontend-URL: `CORS_ALLOW_ALL_ORIGINS=False` und `CORS_ALLOWED_ORIGINS=https://kanmind.de`.

2. **Produktions-Webserver (WSGI/ASGI):**
   * Verwende einen Application Server wie Gunicorn oder Uvicorn:
     ```bash
     pip install gunicorn
     gunicorn kanmind_backend.wsgi:application --bind 0.0.0.0:8000
     ```

3. **Statische Dateien:**
   * Sammle statische Dateien (Admin, Swagger UI) für den Webserver:
     ```bash
     python manage.py collectstatic --noinput
     ```
   * Für einfaches Bereitstellen statischer Dateien kann WhiteNoise verwendet oder ein Nginx Reverse Proxy davor geschaltet werden.

4. **Produktions-Datenbank:**
   * Für Produktivbetrieb wird PostgreSQL empfohlen:
     ```bash
     pip install psycopg2-binary
     ```
   * Passe `DATABASES` in `settings.py` an oder binde die Verbindungs-URL über `dj-database-url` an.

## Bisherige Schritte (14-Tage Roadmap)

### Tag 1: Projekt-Setup
* Django Projekt initialisiert mit DRF und CORS Headers
* Einstellungen für `.env` und `requirements.txt` aufgesetzt

### Tag 2: Custom User Modell
* App `core` erstellt
* `CustomUser` Modell angelegt mit `email` (unique) und `color` (Avatar-Farbe)
* `AUTH_USER_MODEL` in `settings.py` konfiguriert und Admin angepasst
* Migrationen erstellt und auf SQLite angewendet

### Tag 3: User Registrierung
* `RegistrationSerializer` mit Passwort-Abgleich und Validierung erstellt
* `RegistrationView` unter `/api/auth/register/` integriert (gibt Token direkt zurück)

### Tag 4: Login & Logout
* `LoginSerializer` für Anmeldung via Username oder E-Mail implementiert
* `LoginView` (`/api/auth/login/`) und `LogoutView` (`/api/auth/logout/`) gebaut
* Unit- und Integrationstests in `core/tests.py` hinzugefügt

### Tag 5: Protected Routes & Profil-Endpunkt
* `UserDetailSerializer` zur sauberen Formatierung der Benutzerdaten angelegt
* `UserProfileView` (`GET /api/auth/user/`) mit `IsAuthenticated` Permission Guard erstellt
* Integrationstests für gültige und ungültige/fehlende Tokens in `core/tests.py` ergänzt

### Tag 6: Contacts Endpunkte & Modell
* `Contact` Modell (`name`, `email`, `phone`, `color`, `created_at`) in `core/models.py` erstellt
* Migration `0002_contact` erstellt und angewendet
* `ContactSerializer` sowie CRUD Endpunkte (`ContactListCreateView`, `ContactDetailView`) gebaut
* Integrationstests für Kontakt-Erstellung, Liste, Update und Löschung in `core/tests.py` hinterlegt

### Tag 7: Task Modell & Erstellung (`POST /api/tasks/`)
* `Task` Modell (`title`, `description`, `due_date`, `priority`, `status`, `category`, `assigned_to`, `created_by`) in `core/models.py` angelegt
* Migration `0003_task` generiert und angewendet
* `TaskSerializer` (mit geschachtelter `assigned_to_details` Ausgabe) & `TaskListCreateView` implementiert
* Integrationstests für Task-Erstellung & Zuordnung von Kontakten in `core/tests.py` hinzugefügt

### Tag 8: Task Filtering (`GET /api/tasks/`)
* Dynamic filtering in `TaskListCreateView` via Query Parameters implementiert (`?status=`, `?priority=`, `?search=`, `?assigned_to=`)
* Unit-Tests für alle Filtervariablen in `core/tests.py` hinzugefügt

### Tag 9: Task Updates (`PUT / PATCH /api/tasks/<id>/`)
* `TaskDetailView` unter `/api/tasks/<id>/` bereitgestellt
* Unterstützung für partial updates (`PATCH`) für Drag & Drop Statusübergänge und Prioritätsänderungen
* Unit-Tests für `GET`, `PUT` und `PATCH` in `core/tests.py` ergänzt

### Tag 10: Subtasks CRUD & Checkbox-State Persistenz (`/api/subtasks/`)
* `Subtask` Modell (`task`, `title`, `is_completed`, `created_at`) in `core/models.py` angelegt
* Migration `0004_subtask` generiert und angewendet
* `SubtaskSerializer`, `SubtaskListCreateView` und `SubtaskDetailView` erstellt
* Subtasks in `TaskSerializer` geschachtelt als `subtasks` Feld eingebunden
* Unit-Tests für Subtask-Erstellung, Filtering nach Task ID, Checkbox State-Toggling und geschachtelte Task-Ausgabe in `core/tests.py` hinzugefügt

### Tag 11: Task Deletion & Cascade Cleanups (`DELETE /api/tasks/<id>/`)
* `TaskDetailView` Deletion-Flow (`DELETE /api/tasks/<id>/`) mit Statuscode `204 NO CONTENT` verifiziert
* Automatische Kaskadierung auf verknüpfte Subtasks sichergestellt
* Datenintegrität abgesichert: Weder zugewiesene Kontakte noch der Ersteller werden beim Löschen des Tasks entfernt
* Subtask-Löschung ohne Nebeneffekte auf den übergeordneten Task verifiziert
* Integrationstests in `core/tests.py` hinzugefügt

### Tag 12: Globales Error Handling, Statuscodes & CORS Policies
* Zentralen `custom_exception_handler` in `core/exceptions.py` implementiert und in `REST_FRAMEWORK` registriert
* Einheitliche JSON-Fehlerausgaben für 400, 401, 403, 404 und unerwartete 500er Serverfehler
* Django Root-Handler `handler404` und `handler500` in `kanmind_backend/urls.py` auf JSON-Responses umgestellt
* CORS Policies gehärtet: Dynamische Steuerung via `.env`, Credentials-Support und explizite Header
* Umfassende Integrationstests für Error Handling & CORS in `core/tests.py` ergänzt

### Tag 13: Endpunkt-Integrationstests & Randfall-Absicherung
* `FlexibleTokenAuthentication` in `core/authentication.py` implementiert (unterstützt 'Token' und 'Bearer' Header flexibel und case-insensitiv)
* `TaskSerializer` um verschachtelte Erstellung von Subtasks erweitert (`create` und `update`)
* Payload-Randfälle abgesichert: Leerstrings bei Datumsfeldern (`due_date`), `null`-Werte bei `assigned_to`, Whitespace-Trimming und Normalisierung bei Status und Priorität
* Postman Collection in `postman/KanMind_API.postman_collection.json` für alle Endpunkte hinterlegt
* Integrationstests in `core/tests.py` für Header und Payload-Randfälle hinzugefügt

### Tag 14: Swagger/OpenAPI Doku, Code Cleanup & Deployment-Vorbereitung
* `drf-spectacular` integriert und in `requirements.txt` hinterlegt
* Interaktive Swagger UI (`/api/docs/`), ReDoc (`/api/redoc/`) und Schema-Endpunkt (`/api/schema/`) bereitgestellt
* Schema-Validierung für alle Views und Serializer optimiert (inklusive Auth-Views via `@extend_schema`)
* Tests für Dokumentations-Endpunkte in `core/tests.py` ergänzt (alle 61 Tests bestanden)
* `README.md` um Deployment-Leitfaden, Sicherheits-Checkliste und Dokumentations-Links erweitert
