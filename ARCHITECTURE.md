# 🏗️ CampusGuard AI — Architecture

This document describes the technical design of CampusGuard AI: how the frontend and backend communicate, how data is stored, how file uploads are handled, and how the AI matching pipeline works.

---

## System Overview

```
┌─────────────────────────────────────────────────────┐
│                    Browser (Client)                  │
│                                                      │
│   frontend/index.html                                │
│   ├── Tailwind CSS (CDN)                             │
│   └── Vanilla JavaScript (Fetch API)                 │
└──────────────────┬──────────────────────────────────┘
                   │  HTTP / REST (JSON + multipart)
                   ▼
┌─────────────────────────────────────────────────────┐
│               Flask Application (Python)             │
│                                                      │
│   backend/app.py                                     │
│   ├── REST API routes  (/api/*)                      │
│   ├── Static file serving  (/, /uploads/*)           │
│   ├── AI Matching Engine                             │
│   └── ORM (Flask-SQLAlchemy)                         │
└──────────┬──────────────────────┬───────────────────┘
           │                      │
           ▼                      ▼
  ┌─────────────────┐   ┌──────────────────────┐
  │  campusguard.db  │   │  uploads/ directory   │
  │  (SQLite file)   │   │  (image files)        │
  └─────────────────┘   └──────────────────────┘
```

---

## 1. Frontend — Single-Page Application

The entire frontend lives in **one file**: `frontend/index.html`. There is no build step, no npm, and no bundler.

### How it works

- **Sections** (Dashboard, Report Lost, Report Found, AI Matches, Browse) are all rendered in the same HTML page as hidden `<section>` elements. Navigation calls `showSection(name)` which toggles visibility using CSS classes.
- **API calls** are made via the native `Fetch API`. The base URL is set to `window.location.origin`, so the same code works both locally (`http://localhost:5000`) and in production (`https://campusguard-ai.onrender.com`).
- **State** is held entirely in JavaScript variables — no framework, no virtual DOM.
- **Theme** (light/dark) is persisted in `localStorage` under the key `cg_theme`.

### Key JavaScript Functions

| Function | Purpose |
|---|---|
| `submitReport(event, type)` | Submits a lost/found form via `multipart/form-data` POST |
| `loadDashboard()` | Fetches `/api/stats` and recent reports; renders stat cards |
| `loadMatches()` | Fetches `/api/matches` and renders confidence-scored pairs |
| `loadBrowse()` | Fetches all reports; supports client-side filtering and search |
| `sendChat()` | Sends a message to `/api/chat` and appends GuardBot's reply |
| `resolveItem(id)` | PATCH `/api/reports/:id/resolve` and refreshes UI |
| `buildCard(item)` | Renders an item card with emoji, category badge, and image |

---

## 2. Backend — Flask REST API

The backend is a single Python file `backend/app.py` that:

1. Serves the frontend static files
2. Exposes a JSON REST API under `/api/`
3. Handles file uploads to the local `uploads/` folder
4. Runs the AI matching engine on every new submission
5. Reads/writes to a SQLite database via SQLAlchemy

### Flask Configuration

```python
app = Flask(__name__, static_folder="../frontend", static_url_path="")
```

This tells Flask to serve `frontend/index.html` when any non-API route is hit — so a single Flask process handles both the API and the UI.

### Route Map

```
GET  /                         → serves frontend/index.html
GET  /<path>                   → serves static files from frontend/
GET  /uploads/<filename>       → serves uploaded images from uploads/

GET  /api/health               → health check
POST /api/reports              → create a new report (+ run AI matching)
GET  /api/reports?type=...     → list active reports
PATCH /api/reports/:id/resolve → mark a report as resolved
GET  /api/matches              → list all AI matches
GET  /api/matches/:id          → matches for one item
GET  /api/stats                → dashboard counts
POST /api/chat                 → GuardBot chat
```

### CORS

`Flask-CORS` is applied globally, allowing the frontend to be served from any origin (useful during local development when frontend and backend run on different ports).

---

## 3. Data Storage — SQLite

The database is a single file `backend/campusguard.db`, auto-created on first run via:

```python
with app.app_context():
    db.create_all()
```

### Tables

#### `item_reports`

| Column | Type | Description |
|---|---|---|
| `id` | STRING (UUID) | Primary key |
| `report_type` | STRING | `"lost"` or `"found"` |
| `item_name` | STRING | Short name of the item |
| `category` | STRING | Detected or user-selected category |
| `description` | TEXT | Full description for AI matching |
| `location` | STRING | Where the item was lost/found |
| `date_time` | STRING | ISO datetime string |
| `contact` | STRING | Optional contact info |
| `image_url` | STRING | Filename in `uploads/` (nullable) |
| `status` | STRING | `"active"` or `"resolved"` |
| `created_at` | DATETIME | Auto-set on insert |

#### `matches`

| Column | Type | Description |
|---|---|---|
| `id` | STRING (UUID) | Primary key |
| `lost_item_id` | STRING (FK) | References `item_reports.id` |
| `found_item_id` | STRING (FK) | References `item_reports.id` |
| `confidence` | FLOAT | Score from 0.0 to 1.0 |
| `created_at` | DATETIME | Auto-set on insert |

### Production Note

For production use, replace SQLite with a PostgreSQL URL by setting the `DATABASE_URL` environment variable. The `render.yaml` includes a placeholder for this.

---

## 4. File Uploads

Images are uploaded as `multipart/form-data` from the form's `<input type="file">` field.

### Upload Flow

```
Browser
  │
  │  POST /api/reports  (multipart/form-data)
  │  Content fields: item_name, description, location, ...
  │  File field:     image (PNG/JPG/GIF/WEBP, max 8 MB)
  ▼
Flask (submit_report)
  │
  ├── Validate extension (allowed_file)
  ├── Generate UUID filename  (e.g. a3f9...jpg)
  ├── Save to  backend/uploads/<uuid>.jpg
  └── Store filename in  item_reports.image_url
  
Later:
  GET /uploads/<uuid>.jpg  →  send_from_directory(uploads/)
```

### Security

- `secure_filename()` (Werkzeug) strips path traversal characters.
- Extensions are validated against an allowlist: `{png, jpg, jpeg, gif, webp}`.
- Max upload size is enforced at 8 MB via `MAX_CONTENT_LENGTH`.
- Filenames are replaced with a UUID — original filenames are never stored or served.

---

## 5. AI Matching Pipeline

### Trigger

The matching engine runs **synchronously** inside the `POST /api/reports` handler, immediately after a new item is saved to the database.

### Pipeline Steps

```
New item saved
      │
      ▼
run_matching(new_item)
      │
      ├── Query all active items of the OPPOSITE type
      │
      ├── For each candidate:
      │     compute_confidence(lost_item, found_item)
      │         ├── Jaccard(description tokens)  × 0.40
      │         ├── Jaccard(item_name tokens)    × 0.25
      │         ├── category_match (0 or 1)      × 0.20
      │         └── location_score               × 0.15
      │
      ├── If score ≥ 0.15 AND no duplicate match exists:
      │     INSERT into matches table
      │
      └── db.session.commit()
```

### Jaccard Similarity

```
Jaccard(A, B) = |A ∩ B| / |A ∪ B|
```
where A and B are sets of lowercase alphanumeric tokens, with common stop words removed.

### Location Score

Counts shared word tokens between two location strings, capped at 1.0 after 3 shared tokens. This rewards items in the same building or zone without requiring an exact string match.

---

## 6. Deployment Architecture (Render.com)

```
Internet
    │
    ▼
Render Web Service
    ├── Build:  pip install -r requirements.txt
    ├── Start:  gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
    ├── Env:    PYTHON_VERSION=3.11.0
    ├── Disk:   /opt/render/project/src/uploads  (1 GB persistent volume)
    └── DB:     campusguard.db  (on disk, or swap DATABASE_URL to Postgres)
```

Gunicorn runs 2 worker processes. The persistent disk ensures uploaded images survive redeployments. For higher traffic, replace SQLite with a managed PostgreSQL instance and add more workers.

---

## 7. Request / Response Lifecycle (Example: Submit Lost Report)

```
1. User fills form in browser and clicks "Submit"

2. JavaScript (submitReport) builds a FormData object and calls:
   POST http://localhost:5000/api/reports
   Content-Type: multipart/form-data

3. Flask receives the request in submit_report():
   a. Reads form fields (item_name, description, location, ...)
   b. Auto-detects category if "auto" was selected
   c. Validates required fields
   d. Saves uploaded image to uploads/ with a UUID name
   e. Creates an ItemReport row in SQLite
   f. Calls run_matching() → computes scores → inserts Match rows
   g. Returns JSON: { "message": "...", "item": { ... } }

4. Browser receives 201 response:
   a. Shows success toast
   b. Resets the form
   c. Navigates to the AI Matches section
```
