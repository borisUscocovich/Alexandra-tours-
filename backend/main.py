from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Try to import settings, or fallback to defaults
try:
    from backend.core.config import get_settings
    settings = get_settings()
except ImportError:
    class Settings:
        PROJECT_NAME = "Alexandra V2"
        VERSION = "2.0.0"
        ALLOWED_ORIGINS = ["*"]
    settings = Settings()

from backend.api.routes import router as api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for demo interactions
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Include Routes
app.include_router(api_router, prefix="/api")

# Serve Frontend
# We assume the frontend directory is one level up from backend
CLIENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.exists(CLIENTS_DIR):
    app.mount("/", StaticFiles(directory=CLIENTS_DIR, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    # Listen on 0.0.0.0 to be accessible from mobile/network
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
