# Deployment Guide: Alexandra.tours

You have the domain `alexandra.tours`. To make your AI Concierge accessible worldwide 24/7, follow these steps.

## 1. Hosting the Backend (The Brain)
You need a server that runs Python (FastAPI). **Render** is recommended for ease of use.

1.  **Push your code to GitHub**.
    *   Create a repository named `alexandra-api`.
    *   Push the `backend/` folder and `requirements.txt`.
2.  **Create a Web Service on Render**.
    *   Connect your GitHub account.
    *   Select the `alexandra-api` repo.
    *   **Build Command**: `pip install -r backend/requirements.txt`
    *   **Start Command**: `uvicorn backend.main_v2:app --host 0.0.0.0 --port $PORT`
    *   Click **Deploy**.
    *   You will get a URL like: `https://alexandra-api.onrender.com`

## 2. Hosting the Frontend (The Visuals)
You need a static site host. **Netlify** is easiest.

1.  **Deploy to Netlify**.
    *   Drag and drop your `frontend/` folder into Netlify Drop.
    *   You will get a URL like `https://funny-name-123.netlify.app`.

## 3. Connecting Your Domain

### A. Pointing the Frontend (Visits)
*   Go to your Domain Registrar (where you bought `alexandra.tours`).
*   Go to **DNS Settings**.
*   Add a **CNAME Record**:
    *   Host: `www` (or `@`)
    *   Value: `funny-name-123.netlify.app` (Your Netlify URL)

### B. Pointing the Backend (API)
*   You probably want `api.alexandra.tours`.
*   Add a **CNAME Record**:
    *   Host: `api`
    *   Value: `alexandra-api.onrender.com` (Your Render URL)

## 4. Updates Required in Code

Once deployed, you must update two things:

1.  **ElevenLabs Agent**:
    *   Go to https://elevenlabs.io/app/conversational-ai
    *   Select your agent.
    *   Go to **Tools** -> `context` tool.
    *   Update the URL to: `https://api.alexandra.tours/api/tools/context` (or your Render URL if you didn't Map custom domain to API).

2.  **Frontend Code (`demo.html` / `index.html`)**:
    *   Currently, the Agent ID is hardcoded. That's fine.
    *   Ensure the tool definition in 11Labs matches the deployed backend structure.

## 5. SSL (HTTPS)
Netlify and Render provide HTTPS automatically. This is **required** for Microphone access.

---

### Troubleshooting
*   **Mic Error**: Ensure you are using `https://`.
*   **Agent Silent**: Check the Render logs to see if `/api/tools/context` is being called.
