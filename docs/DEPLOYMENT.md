# Samanvay (समन्वय) – Deployment Guide

Complete guide to deploying **Samanvay** to production:
- **Backend API**: [Render](https://render.com) (FastAPI + SQLite / PostgreSQL)
- **Frontend SPA**: [Vercel](https://vercel.com) (React + Vite)

---

## 1. Backend Deployment on Render

### Option A: 1-Click Blueprint (Recommended)

1. Push your repository to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com), click **New +** > **Blueprint**.
3. Select your repository.
4. Render will detect [`render.yaml`](../render.yaml) automatically and configure:
   - **Service Name**: `samanvay-api`
   - **Runtime**: Python 3.11
   - **Root Directory**: `backend`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
5. Click **Apply**.
6. When deployment finishes, copy your backend URL (e.g., `https://samanvay-api.onrender.com`).

---

### Option B: Manual Web Service Setup

If you prefer configuring manually in the Render dashboard:

1. Click **New +** > **Web Service**.
2. Connect your GitHub repository.
3. Configure the following fields:
   - **Name**: `samanvay-api`
   - **Region**: Choose closest to you (e.g., *Singapore* or *Frankfurt*)
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`
4. Add the following **Environment Variables**:

| Variable | Value | Description |
|---|---|---|
| `PYTHON_VERSION` | `3.11.0` | Python runtime version |
| `APP_ENV` | `production` | Production environment mode |
| `DEBUG` | `false` | Disable debug stack traces |
| `SECRET_KEY` | *(Click "Generate")* | 32+ character random secret key |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Add your Vercel URL once deployed |
| `CORS_ORIGIN_REGEX` | `https://.*\.vercel\.app` | Matches all Vercel previews & production |
| `AUTO_SEED` | `true` | Automatically seeds demo data on fresh DB |
| `DEMO_MODE` | `true` | Enables role chips and showcase demo cases |

*(Optional PostgreSQL Database)*:
If you attach a Render PostgreSQL instance, Render automatically provides `DATABASE_URL`. The backend automatically converts `postgres://` to `postgresql://` and seeds tables.

5. Click **Create Web Service**.
6. Once deployed, test the health check in your browser:
   `https://<your-render-app>.onrender.com/health` -> `{"status":"healthy","environment":"production"}`

---

## 2. Frontend Deployment on Vercel

1. Go to the [Vercel Dashboard](https://vercel.com/dashboard) and click **Add New...** > **Project**.
2. Import your GitHub repository.
3. In **Project Settings**:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click *Edit* and select `frontend`
   - **Build Command**: `npm run build` *(default)*
   - **Output Directory**: `dist` *(default)*
4. Expand **Environment Variables** and add:

| Name | Value | Example |
|---|---|---|
| `VITE_API_BASE_URL` | Your Render backend URL | `https://samanvay-api.onrender.com` |

> **Note**: Do not add a trailing `/api`. Even if you accidentally do, the frontend client automatically normalizes the base URL.

5. Click **Deploy**.
6. Vercel will build and deploy your app. The included [`frontend/vercel.json`](../frontend/vercel.json) automatically handles single-page application (SPA) routing, rewriting deep paths like `/institutions/:id`, `/complaints`, and `/desk` to `index.html`.

---

## 3. Connecting Frontend & Backend

Once your Vercel app is live:
1. Note your Vercel production domain (e.g., `https://samanvay-aicte.vercel.app`).
2. Go back to your **Render Web Service** > **Environment**.
3. Update `ALLOWED_ORIGINS` to include your Vercel domain:
   ```
   https://samanvay-aicte.vercel.app,http://localhost:3000,http://localhost:5173
   ```
   *(Note: The built-in `CORS_ORIGIN_REGEX=https://.*\.vercel\.app` already allows all `*.vercel.app` domains out of the box).*

---

## 4. Post-Deployment Verification Checklist

1. **Backend Health Check**:
   - Visit `https://<your-backend>.onrender.com/health` -> Status 200 OK
   - Visit `https://<your-backend>.onrender.com/docs` -> Interactive Swagger UI
2. **Frontend App**:
   - Open your Vercel URL -> Login page renders with quick-fill chips.
   - Click **RB Officer (R.K. Sharma)** -> Logs in and lands directly on **My Desk**.
   - Navigate to **Institutions** -> Click **ABC Institute of Technology** -> **EDA page** loads with 12-month trends, category donut, bureau distribution, ageing buckets, and active overlaps.
   - Click **Overlaps** -> Open a Coordination Room -> Joint decision modal renders cleanly.
3. **Deep Links**:
   - Refresh the browser on `/institutions/<id>` or `/complaints` -> SPA routing works without 404.
