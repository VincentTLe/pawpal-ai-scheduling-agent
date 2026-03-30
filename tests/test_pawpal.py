"""
tests/test_pawpal.py
--------------------
Unit tests for the PawPal+ logic layer.
Run with:  python -m pytest
"""

from datetime import date

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


# ---------------------------------------------------------------------------
# 1. SORTING CORRECTNESS — tasks must be returned in chronological order
# ---------------------------------------------------------------------------

def test_sort_by_time_chronological_order():
    """sort_by_time() must return tasks sorted by HH:MM in ascending order."""
    scheduler = Scheduler(available_minutes=120)
    tasks = [
        Task(name="Evening pill",   duration_minutes=5,  start_time="19:00"),
        Task(name="Morning walk",   duration_minutes=30, start_time="07:00"),
        Task(name="Afternoon feed", duration_minutes=10, start_time="13:30"),
    ]
    result = scheduler.sort_by_time(tasks)
    start_times = [t.start_time for t in result]
    assert start_times == ["07:00", "13:30", "19:00"]


def test_sort_by_time_no_start_time_sinks_to_end():
    """Tasks without a start_time must appear at the end after sort_by_time()."""
    scheduler = Scheduler(available_minutes=120)
    tasks = [
        Task(name="No time task",  duration_minutes=10, start_time=""),
        Task(name="Morning walk",  duration_minutes=30, start_time="07:00"),
    ]
    result = scheduler.sort_by_time(tasks)
    assert result[0].name == "Morning walk"
    assert result[1].name == "No time task"


# ---------------------------------------------------------------------------
# 2. RECURRENCE LOGIC — completing a recurring task must create the next occurrence
# ---------------------------------------------------------------------------

def test_complete_daily_task_creates_next_day_task():
    """Completing a daily task must create a new task with due_date = today + 1 day."""
    pet = Pet(name="Buddy", species="Dog")
    task = Task(name="Morning walk", duration_minutes=30, recurrence="daily")
    pet.add_task(task)

    scheduler = Scheduler(available_minutes=60)
    today = date(2026, 3, 30)
    next_task = scheduler.complete_task(task, pet, today=today)

    # Original task must be marked complete
    assert task.status == "completed"

    # New task must exist with the correct due_date
    assert next_task is not None
    assert next_task.due_date == date(2026, 3, 31)
    assert next_task.status == "pending"

    # New task must be registered on the pet
    assert next_task in pet.tasks


def test_complete_weekly_task_creates_next_week_task():
    """Completing a weekly task must create a new task with due_date = today + 7 days."""
    pet = Pet(name="Whiskers", species="Cat")
    task = Task(name="Bath time", duration_minutes=20, recurrence="weekly")
    pet.add_task(task)

    scheduler = Scheduler(available_minutes=60)
    today = date(2026, 3, 30)
    next_task = scheduler.complete_task(task, pet, today=today)

    assert next_task is not None
    assert next_task.due_date == date(2026, 4, 6)
    assert next_task.status == "pending"


def test_complete_nonrecurring_task_spawns_nothing():
    """Completing a non-recurring task (recurrence='none') must not create a new task."""
    pet = Pet(name="Buddy", species="Dog")
    task = Task(name="Vet visit", duration_minutes=60, recurrence="none")
    pet.add_task(task)

    scheduler = Scheduler(available_minutes=120)
    next_task = scheduler.complete_task(task, pet, today=date(2026, 3, 30))

    assert next_task is None
    # Task list must not grow — only the original (now completed) task remains
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# 3. CONFLICT DETECTION — Scheduler must flag tasks with overlapping times
# ---------------------------------------------------------------------------

def test_detect_overlap_same_start_time():
    """Two tasks with the same start_time must be flagged as overlapping."""
    scheduler = Scheduler(available_minutes=120)
    t1 = Task(name="Feed Buddy",    duration_minutes=10, start_time="07:00")
    t2 = Task(name="Walk Whiskers", duration_minutes=20, start_time="07:00")

    warnings = scheduler.detect_time_overlaps([t1, t2])

    assert len(warnings) == 1
    assert "07:00" in warnings[0]


def test_detect_overlap_partial_overlap():
    """A task starting at 07:00 for 30 min must overlap with a task starting at 07:20."""
    scheduler = Scheduler(available_minutes=120)
    t1 = Task(name="Morning walk", duration_minutes=30, start_time="07:00")
    t2 = Task(name="Feeding",      duration_minutes=10, start_time="07:20")

    warnings = scheduler.detect_time_overlaps([t1, t2])

    assert len(warnings) == 1


def test_no_overlap_sequential_tasks():
    """Two back-to-back tasks with no gap must not produce any overlap warning."""
    scheduler = Scheduler(available_minutes=120)
    t1 = Task(name="Morning walk", duration_minutes=30, start_time="07:00")
    t2 = Task(name="Feeding",      duration_minutes=10, start_time="07:30")

    warnings = scheduler.detect_time_overlaps([t1, t2])

    assert len(warnings) == 0


def test_completed_tasks_ignored_in_overlap_check():
    """Completed tasks must be excluded from the overlap check."""
    scheduler = Scheduler(available_minutes=120)
    done    = Task(name="Old walk", duration_minutes=30, start_time="07:00", status="completed")
    pending = Task(name="New walk", duration_minutes=30, start_time="07:00")

    warnings = scheduler.detect_time_overlaps([done, pending])

    # 'done' is skipped — only one pending task remains, no pair to compare
    assert len(warnings) == 0
