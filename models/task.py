"""
Task model: thin data-class + serialisation helpers.
"""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Task:
    title: str
    scheduled_time: str          # "HH:MM"
    frequency: str = "daily"
    description: Optional[str] = None
    priority: int = 1
    is_active: int = 1
    id: Optional[int] = None
    created_at: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_row(row) -> "Task":
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            scheduled_time=row["scheduled_time"],
            frequency=row["frequency"],
            priority=row["priority"],
            is_active=row["is_active"],
            created_at=row["created_at"],
        )


@dataclass
class TaskHistory:
    task_id: int
    completed_at: str
    completion_hour: Optional[int] = None
    was_on_time: Optional[int] = None
    notes: Optional[str] = None
    id: Optional[int] = None

    def to_dict(self):
        return asdict(self)
