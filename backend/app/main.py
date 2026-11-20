"""Точка входа серверной части модуля «Управление структурой портала»."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import router



@asynccontextmanager
async def lifespan(app: FastAPI):
    """При запуске сервера создать таблицы базы данных, если их ещё нет."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Новостной портал – управление структурой", lifespan=lifespan)
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    """Вернуть понятное сообщение о первой ошибке ввода вместо технического списка."""
    first = exc.errors()[0]
    message = str(first.get("msg", "Ошибка ввода")).removeprefix("Value error, ")
    return JSONResponse(status_code=422, content={"detail": message})


# Собранная клиентская часть (папка frontend/dist) отдаётся тем же сервером.
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        return FileResponse(DIST / "index.html")
