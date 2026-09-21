# 🤖 Bob Usage — How IBM Bob Helped Build CampusGuard AI

[IBM Bob](https://www.ibm.com/products/bob) is an AI-powered software engineering assistant built into the development environment. This document describes how Bob was used throughout the development of CampusGuard AI.

---

## What is IBM Bob?

IBM Bob is a coding assistant that lives inside your IDE. It can read your entire codebase, answer questions about it, write new code, edit existing files, run terminal commands, and help you think through architecture decisions — all without leaving your editor.

---

## How Bob Was Used in This Project

### 1. 🏗️ Project Setup & Scaffolding

Bob helped set up the initial project structure:

- Suggested the `backend/` + `frontend/` split with Flask serving both
- Created the initial `app.py` with Flask, SQLAlchemy, and CORS wiring
- Generated `requirements.txt` with the correct dependency versions
- Wrote the `Procfile` for Gunicorn with the right worker/timeout flags
- Created `render.yaml` and `vercel.json` for deployment with correct configs

> **Prompt used:**  
> *"Set up a Flask backend that also serves a single HTML frontend. Use SQLAlchemy with SQLite. Include a Procfile for Gunicorn."*

---

### 2. 🤖 AI Matching Engine

The core AI feature — the weighted Jaccard similarity matcher — was designed and implemented with Bob's help:

- Bob designed the 4-signal weighted confidence formula (description, name, category, location)
- Implemented the `jaccard()` function with stop-word filtering
- Wrote the `location_score()` function with shared-token counting
- Built the `run_matching()` pipeline that triggers on every new report submission
- Added duplicate match prevention logic

> **Prompt used:**  
> *"Write an AI matching engine that compares lost and found reports. Use Jaccard similarity on descriptions and item names, with a binary category match and a location overlap score. Weight them 40/25/20/15."*

---

### 3. 🗄️ Database Models

Bob wrote both SQLAlchemy models (`ItemReport` and `Match`) including:

- UUID primary keys using Python's `uuid` module
- The `to_dict()` serializer methods for JSON API responses
- Foreign key relationships between matches and reports
- The `CATEGORY_EMOJI` mapping and `detect_category()` regex engine

---

### 4. 🌐 REST API Routes

All eight REST API endpoints were scaffolded and implemented by Bob:

- `POST /api/reports` — multipart form handling, file upload, matching trigger
- `GET /api/reports` — filtered queries with SQLAlchemy
- `PATCH /api/reports/:id/resolve` — status update
- `GET /api/matches` — confidence-filtered match listing with JOIN
- `GET /api/stats` — aggregate count queries
- `POST /api/chat` — GuardBot rule-based NLP handler

---

### 5. 🎨 Frontend (index.html)

Bob built the complete single-page frontend:

- Full responsive Tailwind CSS layout with dark mode
- Dashboard with live stat cards and recent activity feeds
- Lost & Found report forms with drag-and-drop image upload and preview
- AI Matches view with confidence badges (High/Medium/Low) and a slider filter
- Browse section with real-time client-side search and type filter
- Item detail modal with resolve button
- GuardBot floating chat widget with typing indicator and quick-reply chips
- Toast notifications and skeleton loading states

---

### 6. 🌱 Demo Data Seeder

Bob wrote `seed_data.py` with 8 realistic sample reports (phones, laptops, keys, bags, ID cards, glasses) that intentionally cross-match, so the AI engine produces visible results on a fresh install.

---

### 7. 📁 Documentation

Bob wrote all three documentation files:

| File | What Bob wrote |
|---|---|
| `README.md` | Full project overview, AI explanation, feature table, API reference, setup guide |
| `ARCHITECTURE.md` | System diagram, data flow, DB schema, upload pipeline, matching pipeline |
| `BOB_USAGE.md` | This file |

---

### 8. 🚀 Deployment Help

Bob explained exactly how to deploy the project publicly:

- Identified that `render.yaml` was already present and correctly configured
- Gave step-by-step instructions for connecting GitHub to Render.com
- Explained the difference between Render (better for Flask + SQLite + disk) and Vercel (better for frontend-only)
- Clarified why opening `index.html` directly as a file (`file:///`) breaks the app vs. going through `http://localhost:5000`

---

### 9. 🐛 Debugging & Q&A

During development, Bob was used to answer questions such as:

- *"Why is the frontend not opening in the browser?"* → explained the server needs to be running and you must use `http://localhost:5000`
- *"How do I get a public link without running the program locally?"* → explained Render.com free-tier deployment

---

## Summary

| Area | Bob's Contribution |
|---|---|
| Project structure | Designed and scaffolded |
| AI engine | Designed algorithm + full implementation |
| Database models | Full implementation |
| REST API | All 8 endpoints |
| Frontend SPA | Complete HTML/CSS/JS |
| Seed data | Sample dataset with cross-matching items |
| Deployment config | render.yaml + vercel.json |
| Documentation | README, ARCHITECTURE, BOB_USAGE |
| Debugging | Answered runtime and deployment questions |

Bob served as a **pair programming partner** throughout — from the first line of `app.py` to the deployment step and final documentation. The entire project was built interactively inside the IBM Bob IDE assistant.
