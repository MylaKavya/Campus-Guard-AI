# 🛡️ CampusGuard AI — Lost & Found Assistant

> **AI-powered campus lost & found platform.** Report lost or found items, let the AI engine automatically compute similarity matches, and reunite students with their belongings.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)](https://flask.palletsprojects.com)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3-38bdf8?logo=tailwindcss)](https://tailwindcss.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003b57?logo=sqlite)](https://sqlite.org)
[![Deploy on Render](https://img.shields.io/badge/Deploy-Render-46e3b7?logo=render)](https://render.com)

---

## 📌 Problem Statement

Every day on a university campus, students misplace phones, laptops, keys, wallets, ID cards, and more. The traditional approach — a notice board or a WhatsApp group — is slow, unstructured, and ineffective. There is no centralised way to:

- Submit a lost/found report with structured details and photos
- Automatically discover whether a lost item matches a found report
- Track resolution status or get notified of high-confidence matches

---

## 💡 Solution

**CampusGuard AI** is a full-stack web application that provides:

- A **structured reporting form** for both lost and found items
- An **AI matching engine** that computes weighted similarity scores between reports in real time
- A **GuardBot chat assistant** that answers student queries about the platform
- A **live dashboard** with stats and recent activity
- A **browseable, searchable catalogue** of all active reports
- **Dark mode**, **mobile responsiveness**, and **image upload** support

---

## 🤖 Artificial Intelligence

CampusGuard AI uses a **custom rule-based similarity engine** — no external AI API required. Every time a new report is submitted, the engine automatically compares it against all active reports of the opposite type and generates a confidence score.

### Matching Algorithm

The confidence score is a weighted combination of four signals:

| Signal | Weight | Method |
|---|---|---|
| Description similarity | **40%** | Jaccard index on word tokens |
| Item name similarity | **25%** | Jaccard index on word tokens |
| Category match | **20%** | Binary (same category = 1.0) |
| Location proximity | **15%** | Shared keyword count (capped at 3 tokens) |

```
confidence = 0.40 × desc_score
           + 0.25 × name_score
           + 0.20 × category_score
           + 0.15 × location_score
```

Matches with `confidence ≥ 0.15` (15%) are stored. The UI classifies them as:

- 🟢 **High** — ≥ 70%
- 🟡 **Medium** — 40–69%
- ⚫ **Low** — < 40%

### Auto Category Detection

When a user selects "Auto-detect", the backend applies **regex keyword matching** on the item name + description to assign one of 15 categories (phone, laptop, keys, wallet, bag, ID card, headphones, bottle, book, glasses, umbrella, clothing, jewelry, charger, tablet).

### GuardBot Chat Assistant

A lightweight rule-based NLP assistant answers student queries about:
- How to submit reports
- Current platform statistics
- How the matching algorithm works
- How to mark items as resolved

---

## ✨ Features

| Feature | Description |
|---|---|
| 📋 Report Lost Item | Structured form: name, category, description, location, date/time, contact, image |
| 📦 Report Found Item | Same form — links automatically against lost reports |
| 🤖 AI Matches | Real-time similarity scoring, filterable by minimum confidence |
| 🔍 Browse & Search | Full-text search across all active reports with type filter |
| 🏠 Dashboard | Live stats (lost / found / resolved / matches) + recent activity |
| 🤖 GuardBot | Chat assistant with quick-reply buttons |
| 🌙 Dark Mode | Persistent theme preference via localStorage |
| 📱 Mobile Responsive | Full Tailwind responsive layout |
| 🖼️ Image Upload | Drag-and-drop, 8 MB limit, stored on disk |
| ✅ Resolve Reports | Mark items as found/returned and remove from active listings |

---

## 🏗️ Tech Stack

### Backend
| Technology | Role |
|---|---|
| **Python 3.11** | Runtime |
| **Flask 3.0** | Web framework & REST API |
| **Flask-SQLAlchemy** | ORM |
| **SQLite** | Database (file-based, zero config) |
| **Werkzeug** | Secure file uploads |
| **Gunicorn** | Production WSGI server |
| **Flask-CORS** | Cross-origin request handling |

### Frontend
| Technology | Role |
|---|---|
| **HTML5 + Vanilla JS** | Single-page application (no build step) |
| **Tailwind CSS (CDN)** | Utility-first styling |
| **Fetch API** | REST calls to the Flask backend |

### Infrastructure
| Technology | Role |
|---|---|
| **Render.com** | Hosting (free tier, with persistent disk) |
| **Vercel** | Alternative frontend deployment |

---

## 📁 Folder Structure

```
campusguard-ai/
├── backend/
│   ├── app.py              # Flask app, REST API, AI engine, static serving
│   ├── seed_data.py        # Demo data seeder (run once)
│   ├── requirements.txt    # Python dependencies
│   ├── Procfile            # Gunicorn start command for Render
│   ├── campusguard.db      # SQLite database (auto-created)
│   └── uploads/            # Uploaded item images (auto-created)
├── frontend/
│   └── index.html          # Single-page frontend (HTML + Tailwind + JS)
├── render.yaml             # Render.com deployment config
├── vercel.json             # Vercel deployment config
└── README.md
```

---

## 🚀 Setup & Running Locally

### Prerequisites
- Python 3.11+
- pip

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. (Optional) Seed demo data

```bash
python seed_data.py
```

### 3. Start the server

```bash
python app.py
```

### 4. Open in browser

```
http://localhost:5000
```

The Flask server serves both the API and the frontend from a single process.

---

## 🌐 Deploying to Render (Free Public URL)

1. Push this repository to GitHub
2. Sign up at [render.com](https://render.com)
3. Click **New → Web Service** and connect your GitHub repo
4. Render auto-detects `render.yaml` — click **Create Web Service**
5. Your app is live at `https://campusguard-ai.onrender.com`

See [ARCHITECTURE.md](ARCHITECTURE.md) for a full technical breakdown.

---

## 📄 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/reports` | Submit a lost/found report (multipart/form-data) |
| `GET` | `/api/reports?type=lost\|found` | List active reports |
| `PATCH` | `/api/reports/:id/resolve` | Mark a report as resolved |
| `GET` | `/api/matches` | All AI-computed matches |
| `GET` | `/api/matches/:id` | Matches for a specific item |
| `GET` | `/api/stats` | Dashboard statistics |
| `POST` | `/api/chat` | GuardBot chat message |
| `GET` | `/uploads/:filename` | Serve uploaded images |

---

## 📚 Additional Docs

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design, data flow, and storage details
- [BOB_USAGE.md](BOB_USAGE.md) — How IBM Bob AI assisted in building this project

---

## 📝 License

MIT License — free to use, modify, and distribute.
