from contextlib import asynccontextmanager
from fastapi import FastAPI
import app.db.base as db
from fastapi.middleware.cors import CORSMiddleware
from app.utils.exceptions import generic_error_handle
from app.modules.auth.router import router as auth_router
from app.modules.forms.router import router as forms_router
from app.core.config import ALLOW_ORIGINS

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

# Routers
prefix = "/api/v1"
app.include_router(auth_router, prefix=prefix)
app.include_router(forms_router, prefix=prefix)