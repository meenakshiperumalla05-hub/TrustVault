# TrustVault

Secure document sharing with authentication, document-level permissions, private file storage and an audit trail.

## Features

- JWT authentication with Argon2 password hashing.
- Admin, Owner and Viewer roles.
- Document upload, listing, search, metadata updates, download and deletion.
- Document-level READ and EDIT permissions.
- Owners can grant and revoke access.
- Backend authorization for document operations.
- Audit events for authentication, document activity, permission changes and denied access.
- SHA-256 file integrity verification during download.
- File type, content and size validation.
- Admin audit activity API.
- React and TypeScript frontend.

## Technology Stack

- Frontend: React, TypeScript, Vite, Axios.
- Backend: Python, FastAPI, SQLAlchemy.
- Database: PostgreSQL.
- Authentication: JWT and Argon2.
- Testing: Pytest and HTTPX.

## Project Structure

```text
trustvault/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── security/
│   │   ├── rbac/
│   │   └── services/
│   ├── tests/
│   ├── storage/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   └── package.json
├── README.md
├── THREATS.md
└── PROMPTS.md
```

## Local Development

### Prerequisites

- Python 3.11 or later.
- Node.js and npm.
- PostgreSQL.
- Git.

### 1. Configure PostgreSQL

Create a PostgreSQL database named `trustvault` and a database user with the required schema permissions.

### 2. Configure the Backend

From the project root:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configure `backend/.env` with your local database connection and a strong randomly generated JWT secret.

Do not commit `.env`.

### 3. Create Database Tables

From the backend directory:

```powershell
.\.venv\Scripts\python.exe .\create_tables.py
```

### 4. Start the Backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

- Health: http://127.0.0.1:8001/health
- API documentation: http://127.0.0.1:8001/docs

### 5. Start the Frontend

Open another PowerShell window:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev -- --host 127.0.0.1
```

Open http://127.0.0.1:5173/

### 6. Run Backend Tests

From the backend directory:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Run the integrated security checks with the backend running on port 8001:

```powershell
.\.venv\Scripts\python.exe .\run_security_checks.py
```

The script prompts for local Admin and Viewer test credentials. Do not publish these credentials.

### 7. Build and Lint the Frontend

From the frontend directory:

```powershell
npm.cmd run build
npm.cmd run lint
```

## API Overview

| Area | Endpoint | Purpose |
|---|---|---|
| Authentication | POST /auth/register | Register a Viewer account |
| Authentication | POST /auth/login | Obtain an access token |
| Authentication | GET /auth/me | Get current user |
| Documents | POST /documents/upload | Upload a document |
| Documents | GET /documents | List and search accessible documents |
| Documents | GET /documents/{id} | View document metadata |
| Documents | GET /documents/{id}/download | Download an authorized document |
| Documents | PUT /documents/{id} | Update document metadata |
| Documents | POST /documents/{id}/share | Grant document permission |
| Documents | GET /documents/{id}/permissions | List document permissions |
| Documents | DELETE /documents/{id}/share/{user_id} | Revoke permission |
| Documents | DELETE /documents/{id} | Delete an owned document |
| Admin | GET /admin/audit-logs | Retrieve audit activity |

See the interactive API documentation for request and response schemas.

## Security Notes and Limitations

- This challenge implementation is not yet production-ready.
- Replace all development secrets before deployment.
- Rotate credentials that may have been exposed during development.
- Never expose the storage directory as a static or public web directory.
- Authorize every document read and mutation on the backend.
- Do not put confidential documents or real user credentials in development seed data.
- Use HTTPS in production.
- Configure production CORS origins explicitly.
- Configure durable private file storage before deployment. Do not rely on an ephemeral hosting filesystem.
- Audit retrieval and event recording have been tested; tamper-resistant audit storage is not yet established.
- Upload validation is implemented; dedicated malicious-file rejection tests remain necessary.
- Frontend lint currently reports React warnings that should be reviewed.

## Current Validation Status

- Frontend production build: passed.
- Backend automated tests: 1 passed.
- Integrated security checks: 14 passed.
- Frontend lint: 0 errors, 4 warnings.
- Production deployment: pending.
- Final documentation and submission review: in progress.

## License

Add the appropriate license before distributing this project.