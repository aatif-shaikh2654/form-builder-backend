from contextlib import asynccontextmanager
from fastapi import FastAPI
import app.db.base as db
from fastapi.middleware.cors import CORSMiddleware
from app.utils.exceptions import generic_error_handle
from app.core.config import ALLOW_ORIGINS
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Routes path
from app.health import router as health_router 
from app.modules.auth.router import router as auth_router
from app.modules.forms.router import router as forms_router
from app.modules.form_versioning.router import router as form_versioning_router
from app.modules.analytics.router import router as analytics_router
from app.modules.ai.router import router as ai_router


app = FastAPI()

# Middlewares
app.add_exception_handler(Exception, generic_error_handle)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS.split(","),
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)

# Uploads 
UPLOAD_DIR = Path("uploads").resolve()
app.mount(
    "/uploads",
    StaticFiles(directory=UPLOAD_DIR),
    name="uploads"
)

# Routers
prefix = "/api/v1"
app.include_router(health_router)
app.include_router(auth_router, prefix=prefix)
app.include_router(forms_router, prefix=prefix)
app.include_router(form_versioning_router, prefix=prefix)
app.include_router(analytics_router, prefix=prefix)
app.include_router(ai_router, prefix=prefix)