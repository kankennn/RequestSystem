import sqlite3
from typing import Any
from .db import session

REQUEST_SELECT = """SELECT r.*,c.name AS category,s.name AS status,u.full_name AS requester,a.full_name AS assignee
FROM requests r JOIN categories c ON c.id=r.category_id JOIN statuses s ON s.id=r.status_id
JOIN users u ON u.id=r.requester_id LEFT JOIN users a ON a.id=r.assignee_id"""


class RequestRepository:
    def list_requests(self, q=None, status_id=None, category_id=None, priority=None, include_archived=False):
        filters, values = [], []
        if not include_archived:
            filters.append("r.archived=0")
        if q:
            filters.append("(CAST(r.id AS TEXT) LIKE ? OR r.title LIKE ? OR r.description LIKE ?)")
            values.extend([f"%{q}%"] * 3)
        for column, value in (("r.status_id", status_id), ("r.category_id", category_id), ("r.priority", priority)):
            if value is not None:
                filters.append(f"{column}=?"); values.append(value)
        sql = REQUEST_SELECT + (" WHERE " + " AND ".join(filters) if filters else "") + " ORDER BY r.created_at DESC,r.id DESC"
        with session() as db:
            return [dict(row) for row in db.execute(sql, values)]

    def get(self, request_id: int):
        with session() as db:
            row = db.execute(REQUEST_SELECT + " WHERE r.id=?", (request_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def require(db, table: str, object_id: int, label: str):
        if table not in {"users", "categories", "statuses", "requests"}:
            raise ValueError("Invalid reference")
        if not db.execute(f"SELECT 1 FROM {table} WHERE id=?", (object_id,)).fetchone():
            raise ValueError(f"{label} not found")

    def create(self, data):
        with session() as db:
            self.require(db, "categories", data["category_id"], "Category")
            self.require(db, "users", data["requester_id"], "Requester")
            if data.get("assignee_id"):
                self.require(db, "users", data["assignee_id"], "Assignee")
            status = db.execute("SELECT id FROM statuses WHERE name=?", ("Новая",)).fetchone()
            cur = db.execute("""INSERT INTO requests(title,description,category_id,status_id,requester_id,assignee_id,priority)
                VALUES(?,?,?,?,?,?,?)""", (data["title"].strip(), data["description"].strip(), data["category_id"],
                status["id"], data["requester_id"], data.get("assignee_id"), data["priority"]))
            return self._get(db, cur.lastrowid)

    def update(self, request_id: int, data: dict, actor_id: int = 1):
        data = {k: v for k, v in data.items() if v is not None or k == "assignee_id"}
        with session() as db:
            current = self._get(db, request_id)
            if not current:
                return None
            for key, table in (("category_id", "categories"), ("status_id", "statuses"), ("assignee_id", "users")):
                if key in data and data[key] is not None:
                    self.require(db, table, data[key], key.removesuffix("_id").title())
            changes = {k: v for k, v in data.items() if k in {"title", "description", "category_id", "status_id", "assignee_id", "priority"}}
            for key, value in changes.items():
                if current.get(key) != value:
                    db.execute("INSERT INTO request_history(request_id,actor_id,field,old_value,new_value) VALUES(?,?,?,?,?)",
                               (request_id, actor_id, key, str(current.get(key)), str(value)))
            if changes:
                assignments = ",".join(f"{key}=?" for key in changes)
                db.execute(f"UPDATE requests SET {assignments},updated_at=CURRENT_TIMESTAMP WHERE id=?", (*changes.values(), request_id))
            return self._get(db, request_id)

    def archive(self, request_id: int):
        with session() as db:
            cur = db.execute("UPDATE requests SET archived=1,updated_at=CURRENT_TIMESTAMP WHERE id=? AND archived=0", (request_id,))
            return cur.rowcount > 0

    def comments(self, request_id: int):
        with session() as db:
            return [dict(r) for r in db.execute("SELECT c.*,u.full_name AS author FROM comments c JOIN users u ON u.id=c.author_id WHERE request_id=? ORDER BY c.id", (request_id,))]

    def add_comment(self, request_id: int, author_id: int, body: str):
        with session() as db:
            self.require(db, "requests", request_id, "Request")
            self.require(db, "users", author_id, "Author")
            cur = db.execute("INSERT INTO comments(request_id,author_id,body) VALUES(?,?,?)", (request_id, author_id, body.strip()))
            row = db.execute("SELECT c.*,u.full_name AS author FROM comments c JOIN users u ON u.id=c.author_id WHERE c.id=?", (cur.lastrowid,)).fetchone()
            return dict(row)

    @staticmethod
    def _get(db: sqlite3.Connection, request_id: int):
        row = db.execute(REQUEST_SELECT + " WHERE r.id=?", (request_id,)).fetchone()
        return dict(row) if row else None


class DirectoryRepository:
    QUERIES = {
        "users": "SELECT id,full_name,email,role,is_active FROM users ORDER BY full_name",
        "statuses": "SELECT id,name FROM statuses ORDER BY id",
        "categories": "SELECT id,name,description FROM categories ORDER BY name",
    }

    def list(self, name: str):
        if name not in self.QUERIES:
            raise ValueError("Unsupported directory")
        with session() as db:
            return [dict(row) for row in db.execute(self.QUERIES[name])]
