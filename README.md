# WorkSphere

WorkSphere is an internal employee, project, and task manager built with React, Vite, FastAPI, SQLAlchemy 2, and MySQL. The frontend and API run as separate development services. Dashboard counts and lists are loaded from the API.

## Architecture

- `frontend/` is a React single page application. Axios requests use the `VITE_API_BASE_URL` setting.
- `backend/` exposes REST endpoints and uses SQLAlchemy models for employees, projects, and tasks.
- MySQL is the configured application database. Tests use a private in-memory SQLite database and never connect to MySQL.
- At API startup, SQLAlchemy creates missing WorkSphere tables in the configured database. It does not drop or alter existing tables. Use a migration tool before introducing production schema changes.

## Requirements

- Python 3.12 or newer
- Node.js 20 or newer and npm
- MySQL 8 (or a compatible MySQL server)

## Project layout

```text
worksphere/
├── backend/
│   ├── app/             # Settings, database, models, schemas, API
│   ├── tests/           # Pytest suite using in-memory SQLite
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/api/         # Shared Axios client and service functions
│   ├── src/App.jsx      # Navigation, dashboard, and management pages
│   ├── .env.example
│   └── package.json
└── .gitignore
```

## Database setup

Create a dedicated database and user. Do not point WorkSphere at a database used by another application.

```sql
CREATE DATABASE worksphere CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'worksphere_user'@'localhost' IDENTIFIED BY 'replace_with_a_local_password';
GRANT ALL PRIVILEGES ON worksphere.* TO 'worksphere_user'@'localhost';
```

Copy `backend/.env.example` to `backend/.env`, then set `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USERNAME`, and `DATABASE_PASSWORD`. Set `CORS_ORIGINS` to the exact local frontend origin (default `http://localhost:5173`). Do not commit `.env` files.

## Run the backend

From `worksphere/backend`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

The API listens on `http://localhost:8000`. Interactive API documentation is available at `http://localhost:8000/docs` (ReDoc at `/redoc`). Health check: `GET /api/health`.

## Run the frontend

In a second terminal, from `worksphere/frontend`:

```powershell
Copy-Item .env.example .env
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`. Set `VITE_API_BASE_URL` in `frontend/.env` if the API is hosted elsewhere. Production assets can be built with `npm run build`.

## Tests

From `worksphere/backend`, after installing the backend requirements:

```powershell
python -m pytest -q
```

The suite overrides the application database dependency with an isolated in-memory SQLite database for each test. It covers health, employee/project/task CRUD, validation, missing resources, duplicate email addresses, invalid references, and dashboard counts.

## API overview

- `GET /api/health`
- `GET|POST /api/employees`, `GET|PUT|DELETE /api/employees/{employee_id}`
- `GET|POST /api/projects`, `GET|PUT|DELETE /api/projects/{project_id}`
- `GET|POST /api/tasks`, `GET|PUT|DELETE /api/tasks/{task_id}`
- `GET /api/dashboard/stats`, `GET /api/dashboard/recent-activity`

Collection endpoints support `page` and `page_size`; employee filters include `search` and `department`, project filters include `search` and `status`, and task filters include `search`, `status`, `priority`, `project_id`, and `employee_id`. Results include `items`, `total`, `page`, and `page_size`.

## Build and publish the frontend image

The GitHub Actions workflow at `.github/workflows/publish-frontend.yml` runs on every push to `master` (and can also be started manually). It builds the React production bundle inside `frontend/Dockerfile`, packages it with Nginx, and pushes two tags to Docker Hub: `latest` and `sha-<commit>`.

In the GitHub repository, open **Settings → Secrets and variables → Actions** and add:

- Secret `DOCKERHUB_TOKEN`: a Docker Hub access token with permission to push to the image repository.
- Variable `DOCKERHUB_USERNAME`: your Docker Hub username or organization name.
- Variable `DOCKERHUB_REPOSITORY`: the Docker Hub repository name, for example `worksphere-frontend`.
- Variable `VITE_API_BASE_URL`: the API base URL that browsers should call, including `/api` (for example `https://api.example.com/api`). This is embedded in the frontend at build time; do not use `localhost` for a remotely accessed deployment.

The resulting image is `${DOCKERHUB_USERNAME}/${DOCKERHUB_REPOSITORY}:latest`. The container serves the frontend on port 80; for local inspection, run it with `docker run --rm -p 8080:80 <image>` and visit `http://localhost:8080`.
