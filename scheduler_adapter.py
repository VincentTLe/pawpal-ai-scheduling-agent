from __future__ import annotations

from typing import Any

from pawpal_system import Owner, Pet, Scheduler, Task


RECURRENCE_MAP = {
    "once": "none",
    "none": "none",
    "daily": "daily",
    "weekly": "weekly",
    "monthly": "none",
}


def _as_positive_int(value: Any, default: int) -> int:
    if isinstance(value, int) and value > 0:
        return value
    return default


def _normalize_choice(value: Any, allowed: set[str], default: str) -> str:
    if isinstance(value, str) and value in allowed:
        return value
    return default


def _task_to_dict(task: Task) -> dict[str, Any]:
    return {
        "pet": task.pet_name,
        "task": task.name,
        "duration_minutes": task.duration_minutes,
        "priority": task.priority,
        "time_of_day": task.time_of_day,
        "recurrence": task.recurrence,
        "start_time": task.start_time,
    }


def _build_owner_from_plan(structured_plan: dict[str, Any]) -> Owner:
    owner = Owner(name=str(structured_plan.get("owner_name") or "User"))

    for pet_data in structured_plan.get("pets", []):
        if not isinstance(pet_data, dict):
            continue

        pet = Pet(
            name=str(pet_data.get("name") or "Pet"),
            species=str(pet_data.get("type") or "pet"),
        )

        for task_data in pet_data.get("tasks", []):
            if not isinstance(task_data, dict):
                continue

            recurrence = RECURRENCE_MAP.get(str(task_data.get("recurrence", "once")), "none")
            task = Task(
                name=str(task_data.get("name") or "General pet check-in"),
                duration_minutes=_as_positive_int(task_data.get("duration"), 10),
                priority=_normalize_choice(
                    task_data.get("priority"),
                    {"high", "medium", "low"},
                    "medium",
                ),
                time_of_day=_normalize_choice(
                    task_data.get("time_of_day"),
                    {"morning", "afternoon", "evening", "anytime"},
                    "anytime",
                ),
                recurrence=recurrence,  # type: ignore[arg-type]
            )
            pet.add_task(task)

        owner.add_pet(pet)

    return owner


def schedule_structured_plan(structured_plan: dict[str, Any]) -> dict[str, Any]:
    """
    Convert AI-produced structured JSON into PawPal objects and schedule it.

    The AI parser proposes tasks. The deterministic Scheduler remains the
    source of truth for ordering, fitting tasks into available time, and
    conflict reporting.
    """
    available_minutes = _as_positive_int(structured_plan.get("available_minutes"), 60)
    owner = _build_owner_from_plan(structured_plan)
    all_tasks = owner.get_all_tasks()

    scheduler = Scheduler(available_minutes=available_minutes)
    plan = scheduler.generate_plan(all_tasks)
    conflicts = scheduler.check_conflicts(all_tasks)

    scheduled_tasks = [_task_to_dict(task) for task in plan.scheduled]
    skipped_tasks = [
        {
            **_task_to_dict(task),
            "reason": reason,
        }
        for task, reason in plan.excluded
    ]

    scheduled_minutes = sum(task["duration_minutes"] for task in scheduled_tasks)
    summary = (
        f"Scheduled {len(scheduled_tasks)} of {len(all_tasks)} task(s), "
        f"using {scheduled_minutes} of {available_minutes} available minutes."
    )

    return {
        "scheduled_tasks": scheduled_tasks,
        "skipped_tasks": skipped_tasks,
        "conflicts": conflicts,
        "summary": summary,
    }
