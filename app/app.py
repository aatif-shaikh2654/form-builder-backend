from contextlib import asynccontextmanager
from fastapi import FastAPI
import app.db.base as db
from app.utils.exceptions import generic_error_handle
from app.modules.auth.router import router as auth_router
from app.modules.forms.router import router as forms_router

# DB Create base
@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.create_base()
    yield

app = FastAPI(lifespan=lifespan)
# Middlewares
app.add_exception_handler(Exception, generic_error_handle)

# Routers
prefix = "/api/v1"
app.include_router(auth_router, prefix=prefix)
app.include_router(forms_router, prefix=prefix)