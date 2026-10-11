"""Manual smoke checklist for the local API. Start uvicorn before running."""
import json
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8000"


def call(method, path, body=None, expected=200):
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    request = Request(BASE + path, data=data, method=method,
                      headers={"Content-Type": "application/json"} if data else {})
    try:
        with urlopen(request, timeout=5) as response:
            code, raw = response.status, response.read()
    except HTTPError as exc:
        code, raw = exc.code, exc.read()
    assert code == expected, f"{method} {path}: expected {expected}, got {code}: {raw!r}"
    result = json.loads(raw) if raw else None
    print(f"PASS {method:6} {path:48} -> {code}")
    return result


call("GET", "/health")
rows = call("GET", "/requests")
assert len(rows) >= 10
assert call("GET", "/requests?" + urlencode({"q": "монитор"}))
assert call("GET", "/requests?status_id=1")
call("GET", "/requests?category_id=1&priority=high")
call("GET", "/requests/1")
assert len(call("GET", "/users")) >= 4
assert len(call("GET", "/statuses")) >= 4
assert len(call("GET", "/categories")) >= 4
created = call("POST", "/requests", {"title": "Smoke test request", "description": "Created by the manual API check.",
              "category_id": 1, "requester_id": 1, "priority": "normal"}, 201)
request_id = created["id"]
call("PATCH", f"/requests/{request_id}", {"priority": "high", "title": "Updated smoke request"})
call("PATCH", f"/requests/{request_id}/status", {"status_id": 2, "actor_id": 2})
call("POST", f"/requests/{request_id}/comments", {"author_id": 2, "body": "Checked comment flow."}, 201)
assert len(call("GET", f"/requests/{request_id}/comments")) == 1
call("POST", "/requests", {"title": "x", "description": "bad", "category_id": 1, "requester_id": 1}, 422)
call("GET", "/requests/999999", expected=404)
call("DELETE", f"/requests/{request_id}", expected=204)
assert all(item["id"] != request_id for item in call("GET", "/requests"))
assert any(item["id"] == request_id for item in call("GET", "/requests?include_archived=true"))
print("All smoke checks passed.")
