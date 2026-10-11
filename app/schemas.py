from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

Priority = Literal["low", "normal", "high", "urgent"]


class RequestCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=5, max_length=5000)
    category_id: int = Field(gt=0)
    requester_id: int = Field(gt=0)
    assignee_id: int | None = Field(default=None, gt=0)
    priority: Priority = "normal"


class RequestUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, min_length=5, max_length=5000)
    category_id: int | None = Field(default=None, gt=0)
    status_id: int | None = Field(default=None, gt=0)
    assignee_id: int | None = Field(default=None, gt=0)
    priority: Priority | None = None


class StatusChange(BaseModel):
    status_id: int = Field(gt=0)
    actor_id: int = Field(gt=0)


class CommentCreate(BaseModel):
    author_id: int = Field(gt=0)
    body: str = Field(min_length=1, max_length=2000)


class RequestRead(BaseModel):
    id: int
    title: str
    description: str
    category_id: int
    category: str
    status_id: int
    status: str
    requester_id: int
    requester: str
    assignee_id: int | None
    assignee: str | None
    priority: str
    created_at: datetime
    updated_at: datetime
    archived: bool
