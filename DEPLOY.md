# Balanced News Aggregator: Deployment Guide

This document covers running the Aggregator locally for development and deploying it to production.

## Prerequisites
- Node.js (v18+)
- Python (3.12+)
- A valid `GROQ_API_KEY`

## Local Development (Simulating iPhone Safari)

1. **Set Environment Variables**:
   In `backend/`, create a file named `.env` and add:
   ```bash
   GROQ_API_KEY="your_groq_api_key_here"
   ```

2. **Start the Backend**:
   ```bash
   cd backend
   source venv/bin/activate
   pip install -r requirements.txt # (Ensure dependencies are installed)
   export GROQ_API_KEY="your_key"
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Start the Frontend (PWA)**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:3000` in your browser. Open Developer Tools (F12), toggle the Device Toolbar (Ctrl+Shift+M), and select "iPhone 14/15 Pro" to view the mobile-first styling.

## Production Deployment

### Backend (FastAPI on Render / Heroku / WSGI)
- Use a production WSGI server like `gunicorn`:
  `gunicorn -k uvicorn.workers.UvicornWorker main:app`
- Ensure `GROQ_API_KEY` is added to the cloud provider's Secrets/Environment Variables manager.
- Point the database URL to a managed PostgreSQL instance instead of SQLite for persistence and concurrent writes.

### Frontend (Next.js on Vercel)
- The Next.js frontend is optimized for deployment on Vercel.
- Run `npm run build` followed by `npm start`.
- In `frontend/app/page.tsx`, update the `API_BASE` constant to point to your deployed backend URL instead of `localhost`.
- The PWA configuration (`next-pwa`) will automatically generate the service workers during the build step, enabling "Add to Home Screen" functionality on iOS/Android devices.
