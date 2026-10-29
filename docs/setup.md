# Setup & Running Guide

## 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Git

---

## 2. Backend Setup

```bash
# 1. Activate virtual environment
.\venv\Scripts\activate   # Windows PowerShell
# or: source venv/bin/activate (Linux/macOS)

# 2. Install Python dependencies
pip install -r backend/requirements.txt

# 3. Start Backend FastAPI Server
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 3. Frontend Setup

```bash
# 1. Install Node dependencies
cd frontend
npm install

# 2. Start Vite Development Server
npm run dev

# 3. Build for Production
npm run build
```

---

## 4. Running Automated Tests

```bash
# Run backend pytest suite
.\venv\Scripts\python.exe -m pytest backend/tests
```
