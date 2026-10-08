# KanMind Backend

Backend REST API für die KanMind Anwendung (gebaut mit Django und Django REST Framework).

## Setup & Lokaler Start

1. Virtuelle Umgebung aktivieren & Abhängigkeiten installieren:
   ```bash
   cd backend
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Datenbank-Migrationen ausführen:
   ```bash
   python manage.py migrate
   ```

3. Server starten:
   ```bash
   python manage.py runserver
   ```

4. Tests ausführen:
   ```bash
   python manage.py test
   ```

## Verfügbare API Endpunkte

- `POST /api/auth/register/` - Registrierung eines neuen Benutzers (liefert Auth Token zurück)
- `POST /api/auth/login/` - Login per Benutzername oder E-Mail & Passwort
- `POST /api/auth/logout/` - Logout (löscht Token, benötigt Header `Authorization: Token <key>`)
- `GET /api/auth/user/` - Profil des angemeldeten Benutzers abrufen (geschützt)
- `GET /api/contacts/` - Liste aller Kontakte abrufen (geschützt)
- `POST /api/contacts/` - Neuen Kontakt erstellen (geschützt)
- `GET /api/contacts/<id>/` - Einzelnen Kontakt abrufen (geschützt)
- `PUT / PATCH /api/contacts/<id>/` - Kontakt aktualisieren (geschützt)
- `DELETE /api/contacts/<id>/` - Kontakt löschen (geschützt)
- `GET /api/tasks/` - Liste aller Tasks abrufen (geschützt)
- `POST /api/tasks/` - Neuen Task erstellen mit Assignees, Prio & Status (geschützt)

## Bisherige Schritte

### Tag 1: Projekt-Setup
- Django Projekt initialisiert mit DRF und CORS Headers
- Einstellungen für `.env` und `requirements.txt` aufgesetzt

### Tag 2: Custom User Modell
- App `core` erstellt
- `CustomUser` Modell angelegt mit `email` (unique) und `color` (Avatar-Farbe)
- `AUTH_USER_MODEL` in `settings.py` konfiguriert und Admin angepasst
- Migrationen erstellt und auf SQLite angewendet

### Tag 3: User Registrierung
- `RegistrationSerializer` mit Passwort-Abgleich und Validierung erstellt
- `RegistrationView` unter `/api/auth/register/` integriert (gibt Token direkt zurück)

### Tag 4: Login & Logout
- `LoginSerializer` für Anmeldung via Username oder E-Mail implementiert
- `LoginView` (`/api/auth/login/`) und `LogoutView` (`/api/auth/logout/`) gebaut
- Unit- und Integrationstests in `core/tests.py` hinzugefügt

### Tag 5: Protected Routes & Profil-Endpunkt
- `UserDetailSerializer` zur sauberen Formatierung der Benutzerdaten angelegt
- `UserProfileView` (`GET /api/auth/user/`) mit `IsAuthenticated` Permission Guard erstellt
- Integrationstests für gültige und ungültige/fehlende Tokens in `core/tests.py` ergänzt

### Tag 6: Contacts Endpunkte & Modell
- `Contact` Modell (`name`, `email`, `phone`, `color`, `created_at`) in `core/models.py` erstellt
- Migration `0002_contact` erstellt und angewendet
- `ContactSerializer` sowie CRUD Endpunkte (`ContactListCreateView`, `ContactDetailView`) gebaut
- Integrationstests für Kontakt-Erstellung, Liste, Update und Löschung in `core/tests.py` hinterlegt

### Tag 7: Task Modell & Erstellung (`POST /api/tasks/`)
- `Task` Modell (`title`, `description`, `due_date`, `priority`, `status`, `category`, `assigned_to`, `created_by`) in `core/models.py` angelegt
- Migration `0003_task` generiert und angewendet
- `TaskSerializer` (mit geschachtelter `assigned_to_details` Ausgabe) & `TaskListCreateView` implementiert
- Integrationstests für Task-Erstellung & Zuordnung von Kontakten in `core/tests.py` hinzugefügt (22 Tests bestanden)
