# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

Beyond the basic daily plan, `pawpal_system.py` includes several algorithms that make the scheduler more intelligent:

| Feature | Method | Description |
|---|---|---|
| **Priority + time-of-day sort** | `generate_plan` | Sorts pending tasks by priority first, then morning → afternoon → evening, then shortest duration as a tiebreaker — maximises tasks completed in the available window |
| **HH:MM clock sort** | `sort_by_time` | Orders tasks by their `start_time` field using zero-padded string comparison; tasks without a start time sink to the end |
| **Status filtering** | `filter_by_status` | Returns only `pending` or `completed` tasks — used to show "what's left today" vs "what's done" |
| **Recurring task spawning** | `complete_task` / `spawn_next` | When a recurring task is marked complete, a fresh copy is automatically created with its `due_date` advanced using `timedelta` (daily +1 day, weekly +7 days) |
| **Time-overlap detection** | `detect_time_overlaps` | Uses a sort-then-sweep algorithm (O(n log n)) to find pairs of tasks whose scheduled windows overlap, returning human-readable warnings without crashing |
| **Multi-level conflict check** | `check_conflicts` | Combines four independent checks: total time overflow, single task too long to fit, high-priority tasks at risk of exclusion, and time-window overlaps |

## Testing PawPal+

Run the full test suite with:

```bash
python -m pytest
```

### What the tests cover

| Category | Tests | Description |
|---|---|---|
| **Task lifecycle** | `test_mark_complete_*`, `test_update_changes_fields` | Verifies that `mark_complete()` flips status to `completed` (and is idempotent), and that `update()` only overwrites supplied fields |
| **Pet task management** | `test_add_task_*` | Confirms that adding tasks increases the pet's task list, auto-stamps the pet name on each task, and supports multiple tasks |
| **Scheduler — basic plan** | `test_generate_plan_*`, `test_completed_tasks_excluded_*` | Checks that the generated plan respects `available_minutes`, orders tasks high → medium → low priority, and skips already-completed tasks |
| **Owner aggregation** | `test_owner_get_all_tasks_*` | Ensures `Owner.get_all_tasks()` combines tasks from all pets |
| **Time sorting** | `test_sort_by_time_*` | Validates chronological HH:MM ordering and that tasks without a `start_time` sink to the end |
| **Recurrence spawning** | `test_complete_daily_*`, `test_complete_weekly_*`, `test_complete_nonrecurring_*` | Confirms daily tasks advance `due_date` by 1 day, weekly by 7 days, and non-recurring tasks spawn nothing |
| **Overlap detection** | `test_detect_overlap_*`, `test_no_overlap_*`, `test_completed_tasks_ignored_*` | Verifies the sweep algorithm catches same-start and partial overlaps, allows back-to-back tasks, and ignores completed tasks |

**Total: 20 unit tests** across `Task`, `Pet`, `Owner`, and `Scheduler`.

### Confidence Level

**★★★★☆ (4 / 5)**

The core scheduling logic — priority ordering, time-budget enforcement, recurrence spawning, and overlap detection — is thoroughly covered by focused, deterministic unit tests. The suite catches regressions in all critical paths. A full 5 stars would require additional edge-case coverage (e.g., empty task lists, invalid inputs, and boundary conditions on available time).

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
