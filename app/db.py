import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .config import settings

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 full_name TEXT NOT NULL CHECK(length(full_name) BETWEEN 2 AND 120),
 email TEXT NOT NULL UNIQUE COLLATE NOCASE,
 role TEXT NOT NULL CHECK(role IN ('requester','operator','executor','admin')),
 is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1))
);
CREATE TABLE IF NOT EXISTS categories (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL UNIQUE COLLATE NOCASE,
 description TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS statuses (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL UNIQUE COLLATE NOCASE
);
CREATE TABLE IF NOT EXISTS requests (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL CHECK(length(title) BETWEEN 3 AND 160),
 description TEXT NOT NULL CHECK(length(description) BETWEEN 5 AND 5000),
 category_id INTEGER NOT NULL REFERENCES categories(id),
 status_id INTEGER NOT NULL REFERENCES statuses(id),
 requester_id INTEGER NOT NULL REFERENCES users(id),
 assignee_id INTEGER REFERENCES users(id),
 priority TEXT NOT NULL DEFAULT 'normal' CHECK(priority IN ('low','normal','high','urgent')),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1))
);
CREATE TABLE IF NOT EXISTS comments (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
 author_id INTEGER NOT NULL REFERENCES users(id),
 body TEXT NOT NULL CHECK(length(body) BETWEEN 1 AND 2000),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS request_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
 actor_id INTEGER NOT NULL REFERENCES users(id),
 field TEXT NOT NULL,
 old_value TEXT,
 new_value TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status_id);
CREATE INDEX IF NOT EXISTS idx_requests_category ON requests(category_id);
CREATE INDEX IF NOT EXISTS idx_requests_created ON requests(created_at DESC);
"""

SEED_USERS = [
    ("Алексей Петров", "alexey@example.test", "requester"),
    ("Мария Иванова", "maria@example.test", "operator"),
    ("Дмитрий Орлов", "dmitry@example.test", "executor"),
    ("Елена Смирнова", "elena@example.test", "admin"),
]
SEED_CATEGORIES = ["Оборудование", "Доступы", "Программное обеспечение", "Сеть"]
SEED_STATUSES = ["Новая", "В работе", "Выполнена", "Закрыта"]
SEED_REQUESTS = [
    ("Не включается монитор", "После включения экран остаётся чёрным."),
    ("Нет доступа к CRM", "Нужен доступ для обработки обращений."),
    ("Установка редактора", "Требуется установить редактор документов."),
    ("Медленный Wi-Fi", "Скорость сети снизилась на рабочем месте."),
    ("Не печатает принтер", "Принтер виден, но задания остаются в очереди."),
    ("Сброс пароля", "Не удаётся войти в корпоративный аккаунт."),
    ("Обновление приложения", "Нужна актуальная версия приложения."),
    ("Обрыв сетевого кабеля", "Периодически пропадает соединение."),
    ("Замена клавиатуры", "Некоторые клавиши не работают."),
    ("Настройка почты", "Не синхронизируется рабочая почта."),
]


def sqlite_path(url: str) -> str:
    if not url.startswith("sqlite:///"):
        raise ValueError("Для этой учебной версии DATABASE_URL должен использовать SQLite")
    return url.removeprefix("sqlite:///")


def connect() -> sqlite3.Connection:
    path = sqlite_path(settings.database_url)
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10, check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


@contextmanager
def session():
    db = connect()
    try:
        with db:
            yield db
    finally:
        db.close()


def initialize(seed: bool = True) -> None:
    with session() as db:
        db.executescript(SCHEMA)
        if seed and db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            seed_database(db)


def seed_database(db: sqlite3.Connection | None = None) -> None:
    own = db is None
    db = db or connect()
    with db:
        db.executemany("INSERT OR IGNORE INTO users(full_name,email,role) VALUES(?,?,?)", SEED_USERS)
        db.executemany("INSERT OR IGNORE INTO categories(name) VALUES(?)", [(x,) for x in SEED_CATEGORIES])
        db.executemany("INSERT OR IGNORE INTO statuses(name) VALUES(?)", [(x,) for x in SEED_STATUSES])
        if db.execute("SELECT COUNT(*) FROM requests").fetchone()[0] == 0:
            cats = {r["name"]: r["id"] for r in db.execute("SELECT id,name FROM categories")}
            sts = {r["name"]: r["id"] for r in db.execute("SELECT id,name FROM statuses")}
            users = {r["email"]: r["id"] for r in db.execute("SELECT id,email FROM users")}
            for i, (title, description) in enumerate(SEED_REQUESTS):
                db.execute("""INSERT INTO requests(title,description,category_id,status_id,requester_id,assignee_id,priority)
                  VALUES(?,?,?,?,?,?,?)""", (title, description, cats[SEED_CATEGORIES[i % 4]], sts[SEED_STATUSES[i % 4]],
                  users["alexey@example.test"], users["dmitry@example.test"] if i % 2 else None,
                  ("low", "normal", "high", "urgent")[i % 4]))
    if own:
        db.close()
