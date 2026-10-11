# REST API

Base URL: `http://127.0.0.1:8000`. Interactive OpenAPI documentation: `/docs`; JSON schema: `/openapi.json`.

## Endpoints

| Method | Path | Query/body | Success | Error cases |
|---|---|---|---|---|
| GET | `/health` | — | 200 | 503 if SQLite unavailable |
| GET | `/requests` | `q`, `status_id`, `category_id`, `priority`, `include_archived` | 200 JSON array | 422 invalid filters |
| GET | `/requests/{id}` | ID | 200 object | 404 |
| POST | `/requests` | `title`, `description`, `category_id`, `requester_id`, optional `assignee_id`, `priority` | 201 object | 404 missing reference, 422 invalid body |
| PATCH | `/requests/{id}` | Any editable fields | 200 object | 404, 422 invalid status transition/body |
| PATCH | `/requests/{id}/status` | `status_id`, `actor_id` | 200 object | 404, 422 invalid transition |
| DELETE | `/requests/{id}` | ID | 204 archived | 404 |
| GET/POST | `/requests/{id}/comments` | GET —; POST `author_id`, `body` | 200 / 201 | 404, 422 |
| GET | `/users` | — | 200 array | — |
| GET | `/statuses` | — | 200 array | — |
| GET | `/categories` | — | 200 array | — |

API errors use FastAPI's `detail` envelope. Domain-specific errors have `code` and `message`; request validation errors return 422. Database exceptions are logged server-side and return a generic 500 response without leaking SQL or file paths.

## Example create request

```http
POST /requests HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{"title":"Не работает принтер","description":"Принтер включён, но задание не печатается.","category_id":1,"requester_id":1,"priority":"high"}
```

The response is HTTP 201 and contains the created request, the initial `Новая` status and timestamps. `DELETE` performs soft archive so request history is retained.

## Status transitions

`Новая` → `В работе` or `Закрыта`; `В работе` → `Выполнена` or `Закрыта`; `Выполнена` → `Закрыта` or back to `В работе`; `Закрыта` is terminal. The service layer enforces the same rule for both PATCH routes.

## Demo security limitations

This lab build has no authentication or role authorization. IDs for requester, actor and comment author are accepted from the request for demonstration. Do not expose this version publicly with real personal data. Production deployment requires authentication, authorization, HTTPS, rate limiting, and secret management.
