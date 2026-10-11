from .repository import DirectoryRepository, RequestRepository

ALLOWED_TRANSITIONS = {
    "Новая": {"В работе", "Закрыта"},
    "В работе": {"Выполнена", "Закрыта"},
    "Выполнена": {"Закрыта", "В работе"},
    "Закрыта": set(),
}


class RequestService:
    def __init__(self, repository=None):
        self.repository = repository or RequestRepository()
        self.directories = DirectoryRepository()

    def list(self, **filters):
        return self.repository.list_requests(**filters)

    def get(self, request_id):
        return self.repository.get(request_id)

    def create(self, data):
        return self.repository.create(data)

    def update(self, request_id, data, actor_id=1):
        # Keep state transitions in the service so API clients cannot bypass rules.
        if data.get("status_id") is not None:
            status_id = data.pop("status_id")
            current = self.get(request_id)
            if current is None:
                return None
            target = next((x["name"] for x in self.directories.list("statuses") if x["id"] == status_id), None)
            if target is None:
                raise ValueError("Status not found")
            if target != current["status"] and target not in ALLOWED_TRANSITIONS[current["status"]]:
                raise ValueError(f"Transition from '{current['status']}' to '{target}' is not allowed")
        return self.repository.update(request_id, data, actor_id)

    def archive(self, request_id):
        return self.repository.archive(request_id)

    def change_status(self, request_id, status_id, actor_id):
        current = self.get(request_id)
        if current is None:
            return None
        status = next((x["name"] for x in self.directories.list("statuses") if x["id"] == status_id), None)
        if status is None:
            raise ValueError("Status not found")
        if status != current["status"] and status not in ALLOWED_TRANSITIONS[current["status"]]:
            raise ValueError(f"Transition from '{current['status']}' to '{status}' is not allowed")
        return self.repository.update(request_id, {"status_id": status_id}, actor_id)
