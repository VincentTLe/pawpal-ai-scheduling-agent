"""
tests/test_pawpal.py
--------------------
Unit tests for the PawPal+ logic layer.
Run with:  python -m pytest
"""

from pawpal_system import Owner, Pet, Scheduler, Task


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    """Calling mark_complete() must flip status from 'pending' to 'completed'."""
    task = Task(name="Morning walk", duration_minutes=30, priority="high")
    assert task.status == "pending"

    task.mark_complete()

    assert task.status == "completed"


def test_mark_complete_is_idempotent():
    """Calling mark_complete() twice should not raise and status stays 'completed'."""
    task = Task(name="Feeding", duration_minutes=10)
    task.mark_complete()
    task.mark_complete()

    assert task.status == "completed"


def test_update_changes_fields():
    """update() should only overwrite the fields that are explicitly provided."""
    task = Task(name="Walk", duration_minutes=20, priority="low")
    task.update(name="Long walk", duration_minutes=45)

    assert task.name == "Long walk"
    assert task.duration_minutes == 45
    assert task.priority == "low"   # untouched


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

def test_add_task_increases_count():
    """Adding a task to a Pet must increase its task list length by 1."""
    pet = Pet(name="Buddy", species="Dog")
    assert len(pet.get_tasks()) == 0

    pet.add_task(Task(name="Walk", duration_minutes=30))

    assert len(pet.get_tasks()) == 1


def test_add_task_stamps_pet_name():
    """add_task() should automatically set the task's pet_name field."""
    pet = Pet(name="Whiskers", species="Cat")
    task = Task(name="Feeding", duration_minutes=10)

    pet.add_task(task)

    assert task.pet_name == "Whiskers"


def test_add_multiple_tasks():
    """Adding three tasks should result in a count of 3."""
    pet = Pet(name="Buddy", species="Dog")
    for i in range(3):
        pet.add_task(Task(name=f"Task {i}", duration_minutes=10))

    assert len(pet.get_tasks()) == 3


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------

def test_generate_plan_respects_available_time():
    """Scheduled tasks must not exceed available_minutes in total."""
    tasks = [
        Task(name="Walk",      duration_minutes=30, priority="high"),
        Task(name="Feeding",   duration_minutes=10, priority="high"),
        Task(name="Playtime",  duration_minutes=40, priority="medium"),
    ]
    scheduler = Scheduler(available_minutes=50)
    result = scheduler.generate_plan(tasks)

    total = sum(t.duration_minutes for t in result.scheduled)
    assert total <= 50


def test_generate_plan_prioritises_high_priority():
    """High-priority tasks must appear in the plan before lower-priority ones."""
    tasks = [
        Task(name="Low task",  duration_minutes=10, priority="low"),
        Task(name="High task", duration_minutes=10, priority="high"),
        Task(name="Med task",  duration_minutes=10, priority="medium"),
    ]
    scheduler = Scheduler(available_minutes=60)
    result = scheduler.generate_plan(tasks)

    names = [t.name for t in result.scheduled]
    assert names.index("High task") < names.index("Med task")
    assert names.index("Med task") < names.index("Low task")


def test_completed_tasks_excluded_from_plan():
    """Tasks already marked complete should never appear in the schedule."""
    done = Task(name="Done task", duration_minutes=10, status="completed")
    pending = Task(name="Pending task", duration_minutes=10, priority="high")

    scheduler = Scheduler(available_minutes=60)
    result = scheduler.generate_plan([done, pending])

    scheduled_names = [t.name for t in result.scheduled]
    assert "Done task" not in scheduled_names
    assert "Pending task" in scheduled_names


def test_owner_get_all_tasks_aggregates_across_pets():
    """Owner.get_all_tasks() must return tasks from every pet combined."""
    owner = Owner(name="Alex")
    dog = Pet(name="Buddy", species="Dog")
    cat = Pet(name="Whiskers", species="Cat")

    dog.add_task(Task(name="Walk", duration_minutes=30))
    cat.add_task(Task(name="Feeding", duration_minutes=10))
    cat.add_task(Task(name="Playtime", duration_minutes=15))

    owner.add_pet(dog)
    owner.add_pet(cat)

    assert len(owner.get_all_tasks()) == 3
