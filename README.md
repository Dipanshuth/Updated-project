# 🛡️ AI Digital Memory Vault

> Reimagining Civilian Evidence — Upload, analyze, and preserve digital evidence with AI-powered analysis, tamper-proof blockchain hashing, and automated FIR generation.

## 🚀 Quick Start

### Frontend
Simply open `frontend/index.html` in your browser — no build tools needed!

```
frontend/index.html       → Landing page
frontend/dashboard.html   → Evidence dashboard
frontend/upload.html      → Upload evidence (audio recording + file upload + GPS)
frontend/incident.html    → Incident detail with timeline
frontend/report.html      → FIR report viewer
```

### Backend
```bash
# Navigate to backend
cd backend

# Install dependencies
pip install fastapi uvicorn sqlalchemy python-multipart fpdf2

# Run the server
python main.py
# or
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## 📁 Project Structure

```
ai-memory-vault-web/
├── frontend/
│   ├── index.html          ← Landing page / Home
│   ├── dashboard.html      ← Main evidence dashboard
│   ├── upload.html         ← Manual evidence upload
│   ├── incident.html       ← Incident detail + timeline
│   ├── report.html         ← FIR report viewer
│   ├── css/
│   │   └── style.css       ← All styles (dark teal theme)
│   └── js/
│       ├── app.js          ← Main logic
│       ├── upload.js       ← Upload + recording logic
│       └── timeline.js     ← Timeline rendering
├── backend/
│   ├── main.py             ← FastAPI app with all endpoints
│   ├── models.py           ← SQLAlchemy models (SQLite)
│   ├── routes/
│   │   ├── evidence.py
│   │   ├── auth.py
│   │   └── alerts.py
│   ├── services/
│   │   ├── ai_service.py   ← AI analysis (mock for Phase 1)
│   │   ├── hash_service.py ← SHA-256 hashing
│   │   └── pdf_service.py  ← FIR PDF generation
│   └── uploads/            ← Uploaded evidence files
└── README.md
```

## 🔌 API Endpoints

| Method | Endpoint                      | Description                    |
|--------|-------------------------------|--------------------------------|
| POST   | `/auth/setup`                 | Save user + emergency contacts |
| POST   | `/evidence/upload`            | Upload evidence file           |
| POST   | `/evidence/{id}/analyze`      | AI analysis (mock)             |
| GET    | `/evidence/{id}/timeline`     | Get analysis timeline          |
| GET    | `/evidence/{id}/report`       | Get FIR report                 |
| POST   | `/evidence/{id}/hash`         | Compute SHA-256 hash           |
| GET    | `/evidence/list`              | List all evidence records      |
| POST   | `/alerts/send`                | Send emergency alert           |

## 🎨 Design

- **Color Scheme**: Dark background `#0a0f14`, Teal accent `#00C9B1`, Card bg `#111820`
- **Font**: Inter (Google Fonts)
- **Theme**: Dark glassmorphism with teal accents

## ✨ Features (Phase 1)

- [x] 5 responsive HTML pages with dark teal UI
- [x] Audio recording in browser (MediaRecorder API)
- [x] Live waveform visualization (Web Audio API + Canvas)
- [x] GPS location capture (Geolocation API)
- [x] File drag & drop upload
- [x] FastAPI backend with all stub endpoints
- [x] SQLite database (zero setup)
- [x] SHA-256 evidence hashing
- [x] Mock AI analysis results
- [x] FIR report viewer with print support

## 🛠️ Tech Stack

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python, FastAPI, SQLAlchemy
- **Database**: SQLite
- **APIs**: MediaRecorder, Web Audio, Geolocation
- **AI** (Phase 2): Claude API
- **PDF** (Phase 2): fpdf2

---

*Built for Hackathon 2026 — AI Digital Memory Vault Team*
# Updated-project
