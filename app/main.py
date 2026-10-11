from contextlib import asynccontextmanager
import logging
import sqlite3
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from .db import initialize, session
from .repository import DirectoryRepository
from .schemas import CommentCreate, RequestCreate, RequestRead, RequestUpdate, StatusChange
from .services import RequestService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("request_system")


@asynccontextmanager
async def lifespan(_app):
    initialize()
    yield


app = FastAPI(title="Система учёта заявок API", version="1.0.0",
              description="REST API учебной системы. Демо-пользователи и заявки являются тестовыми.", lifespan=lifespan)
service = RequestService()
directories = DirectoryRepository()
app.mount("/ui", StaticFiles(directory="prototype", html=True), name="ui")


@app.exception_handler(sqlite3.Error)
async def database_error_handler(_request, exc):
    logger.exception("Database error", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": {"code": "database_error", "message": "Ошибка хранилища данных"}})


@app.exception_handler(HTTPException)
async def http_error_handler(_request, exc):
    detail = exc.detail
    if not isinstance(detail, dict) or "code" not in detail or "message" not in detail:
        detail = {"code": "http_error", "message": str(detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": detail}, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request, exc):
    details = [{"field": ".".join(str(part) for part in item["loc"]), "message": item["msg"]} for item in exc.errors()]
    return JSONResponse(status_code=422, content={"error": {"code": "validation_error", "message": "Некорректные данные запроса", "details": details}})


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/ui/")


@app.get("/health", tags=["system"], summary="Проверить доступность приложения и БД")
def health():
    try:
        with session() as db:
            db.execute("SELECT 1")
        return {"status": "ok", "database": "ok"}
    except Exception as exc:
        logger.exception("Health check failed")
        raise HTTPException(503, detail={"code": "unavailable", "message": "Хранилище недоступно"}) from exc


@app.get("/requests", response_model=list[RequestRead], tags=["requests"], summary="Список и фильтрация заявок")
def list_requests(q: str | None = Query(None, min_length=1, max_length=160), status_id: int | None = Query(None, gt=0),
                  category_id: int | None = Query(None, gt=0), priority: str | None = Query(None, pattern="^(low|normal|high|urgent)$"),
                  include_archived: bool = False):
    return service.list(q=q, status_id=status_id, category_id=category_id, priority=priority, include_archived=include_archived)


@app.get("/requests/{request_id}", response_model=RequestRead, tags=["requests"], summary="Получить заявку по ID")
def get_request(request_id: int):
    row = service.get(request_id)
    if row is None:
        raise HTTPException(404, detail={"code": "not_found", "message": "Заявка не найдена"})
    return row


@app.post("/requests", response_model=RequestRead, status_code=201, tags=["requests"], summary="Создать заявку")
def create_request(payload: RequestCreate):
    try:
        return service.create(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(404, detail={"code": "reference_not_found", "message": str(exc)}) from exc


@app.patch("/requests/{request_id}", response_model=RequestRead, tags=["requests"], summary="Редактировать заявку")
def update_request(request_id: int, payload: RequestUpdate):
    try:
        row = service.update(request_id, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(404, detail={"code": "reference_not_found", "message": str(exc)}) from exc
    if row is None:
        raise HTTPException(404, detail={"code": "not_found", "message": "Заявка не найдена"})
    return row


@app.patch("/requests/{request_id}/status", response_model=RequestRead, tags=["requests"], summary="Изменить статус заявки")
def change_status(request_id: int, payload: StatusChange):
    try:
        row = service.change_status(request_id, payload.status_id, payload.actor_id)
    except ValueError as exc:
        raise HTTPException(422, detail={"code": "invalid_transition", "message": str(exc)}) from exc
    if row is None:
        raise HTTPException(404, detail={"code": "not_found", "message": "Заявка не найдена"})
    return row


@app.delete("/requests/{request_id}", status_code=204, tags=["requests"], summary="Архивировать заявку")
def archive_request(request_id: int):
    if not service.archive(request_id):
        raise HTTPException(404, detail={"code": "not_found", "message": "Заявка не найдена"})
    return Response(status_code=204)


@app.get("/requests/{request_id}/comments", tags=["comments"], summary="Получить комментарии заявки")
def list_comments(request_id: int):
    if service.get(request_id) is None:
        raise HTTPException(404, detail={"code": "not_found", "message": "Заявка не найдена"})
    return service.repository.comments(request_id)


@app.post("/requests/{request_id}/comments", status_code=201, tags=["comments"], summary="Добавить комментарий")
def add_comment(request_id: int, payload: CommentCreate):
    try:
        return service.repository.add_comment(request_id, payload.author_id, payload.body)
    except ValueError as exc:
        raise HTTPException(404, detail={"code": "reference_not_found", "message": str(exc)}) from exc


@app.get("/users", tags=["directories"], summary="Справочник пользователей")
def list_users():
    return directories.list("users")


@app.get("/statuses", tags=["directories"], summary="Справочник статусов")
def list_statuses():
    return directories.list("statuses")


@app.get("/categories", tags=["directories"], summary="Справочник категорий")
def list_categories():
    return directories.list("categories")
