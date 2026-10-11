import pytest
from fastapi.testclient import TestClient
from contextlib import asynccontextmanager

from app import db
from app.config import settings
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    database = tmp_path / "requests-test.db"
    monkeypatch.setattr(db, "settings", settings.__class__(
        environment=settings.environment,
        host=settings.host,
        port=settings.port,
        database_url=f"sqlite:///{database.as_posix()}",
    ))
    db.initialize(seed=False)
    with db.session() as connection:
        db.seed_database(connection)
    @asynccontextmanager
    async def no_lifespan(_app):
        yield

    monkeypatch.setattr(app.router, "lifespan_context", no_lifespan)
    with TestClient(app) as test_client:
        yield test_client


def test_health_and_seeded_directories(client):
    assert client.get("/health").json() == {"status": "ok", "database": "ok"}
    assert len(client.get("/users").json()) == 4
    assert len(client.get("/categories").json()) == 4
    assert len(client.get("/statuses").json()) == 4


def test_create_request_and_filter_it(client):
    response = client.post(
        "/requests",
        json={
            "title": "Тестовая заявка",
            "description": "Описание для автоматического теста.",
            "category_id": 1,
            "requester_id": 1,
            "priority": "high",
        },
    )
    assert response.status_code == 201
    created = response.json()
    assert created["status"] == "Новая"
    assert created["priority"] == "high"

    assert client.get("/requests", params={"q": "автоматического"}).json()[0]["id"] == created["id"]
    assert client.get("/requests", params={"priority": "high"}).json()[0]["id"] == created["id"]
    assert client.get(f"/requests/{created['id']}").json()["title"] == "Тестовая заявка"


def test_validation_and_missing_references_return_consistent_errors(client):
    invalid = client.post(
        "/requests",
        json={"title": "x", "description": "short", "category_id": 1, "requester_id": 1},
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "validation_error"

    missing_category = client.post(
        "/requests",
        json={
            "title": "Неверная категория",
            "description": "Описание достаточно длинное.",
            "category_id": 999,
            "requester_id": 1,
        },
    )
    assert missing_category.status_code == 404
    assert missing_category.json()["error"]["code"] == "reference_not_found"


def test_status_transition_and_archive(client):
    created = client.post(
        "/requests",
        json={
            "title": "Проверка статуса",
            "description": "Проверяем допустимые переходы.",
            "category_id": 1,
            "requester_id": 1,
        },
    ).json()

    initial_count = len(client.get("/requests").json())
    assert client.patch(
        f"/requests/{created['id']}/status", json={"status_id": 2, "actor_id": 2}
    ).json()["status"] == "В работе"
    forbidden = client.patch(
        f"/requests/{created['id']}/status", json={"status_id": 1, "actor_id": 2}
    )
    assert forbidden.status_code == 422
    assert forbidden.json()["error"]["code"] == "invalid_transition"

    assert client.delete(f"/requests/{created['id']}").status_code == 204
    assert len(client.get("/requests", params={"include_archived": "false"}).json()) == initial_count - 1
    assert client.get("/requests", params={"include_archived": "true"}).json()[0]["archived"] is True
