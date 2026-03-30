# PawPal+

**A daily pet-care planner powered by intelligent scheduling.**

PawPal+ helps busy pet owners stay consistent with animal care. Enter your pets and their tasks, tell the app how much time you have today, and it generates a priority-ordered plan — complete with conflict warnings and automatic recurrence tracking.

---

## 📸 Demo

**Owner & Pet Setup**
<a href="/course_images/ai110/pawpal_screenshot_1.png" target="_blank"><img src='/course_images/ai110/pawpal_screenshot_1.png' title='PawPal App - Owner and Pet Setup' width='' alt='PawPal App - Owner and Pet Setup' class='center-block' /></a>

**Task Management**
<a href="/course_images/ai110/pawpal_screenshot_2.png" target="_blank"><img src='/course_images/ai110/pawpal_screenshot_2.png' title='PawPal App - Task Management' width='' alt='PawPal App - Task Management' class='center-block' /></a>

**Generated Schedule & Conflict Warnings**
<a href="/course_images/ai110/pawpal_screenshot_3.png" target="_blank"><img src='/course_images/ai110/pawpal_screenshot_3.png' title='PawPal App - Schedule' width='' alt='PawPal App - Schedule' class='center-block' /></a>

---

## Features

### Owner & Multi-Pet Management
Create an owner profile and register as many pets as you like (dog, cat, bird, rabbit, or other). Each pet carries its own health notes and task list. Tasks from all pets are automatically aggregated when generating the schedule.

### Task Creation with Rich Metadata
Every task stores:
- **Name** and **duration** (minutes)
- **Priority** — `high`, `medium`, or `low`
- **Time-of-day slot** — `morning`, `afternoon`, `evening`, or `anytime`
- **Start time** — optional HH:MM clock time (e.g. `07:30`)
- **Recurrence** — `none`, `daily`, or `weekly`

### Priority-Aware Daily Scheduling
`Scheduler.generate_plan()` sorts pending tasks by:
1. **Priority** — `high` before `medium` before `low`
2. **Time-of-day slot** — `morning` → `afternoon` → `evening` → `anytime`
3. **Duration** — shortest first as a tiebreaker (maximises tasks completed)

It greedily fills the available time window and returns a `ScheduleResult` with both the scheduled tasks and every excluded task paired with a plain-English reason explaining why it was dropped.

### Sorting by Time (HH:MM Clock Sort)
`Scheduler.sort_by_time()` orders tasks by their `start_time` field using zero-padded string comparison. Tasks without a start time automatically sink to the end, so the display always shows a clean chronological to-do list followed by flexible items.

### Sorting by Time-of-Day Slot
`Scheduler.sort_by_time_of_day()` orders tasks by their day-part slot (`morning` → `afternoon` → `evening` → `anytime`) — useful for viewing the full task list in a natural daily rhythm independent of clock times.

### Daily & Weekly Recurrence
`Scheduler.complete_task()` marks a task done then calls `Task.spawn_next()` to create a fresh copy automatically:
- **Daily** — `due_date` advances by 1 day
- **Weekly** — `due_date` advances by 7 days
- **None** — no copy is created

The new occurrence is added directly to the pet's task list. No manual re-entry required.

### Conflict Warnings
`Scheduler.check_conflicts()` runs four independent checks and returns human-readable warnings:

| Check | What it catches |
|---|---|
| **Total time overflow** | All pending tasks together exceed the available window |
| **Single task too long** | One task alone is longer than the entire available window |
| **High-priority tasks at risk** | High-priority tasks combined exceed available time — some will be dropped |
| **Time-window overlaps** | Two tasks whose `start_time + duration` windows collide |

### Time-Overlap Detection
`Scheduler.detect_time_overlaps()` uses a **sort-then-sweep** algorithm (O(n log n)) to find every pair of pending tasks whose scheduled windows overlap. Tasks are sorted by start time once; for each task only forward neighbours are checked, and the inner loop breaks the moment a non-overlapping task is reached — making it efficient even for long task lists.

### Status Filtering (Pending / Completed Tabs)
`Scheduler.filter_by_status()` returns only `pending` or `completed` tasks. The UI uses this to power separate tabs so owners can instantly see what's left today versus what's already done.

---

## Architecture

```
pawpal_system.py   — backend logic (Task, Pet, Owner, Scheduler, ScheduleResult)
app.py             — Streamlit UI; imports from pawpal_system only
```

| Class | Responsibility |
|---|---|
| `Task` | Holds care-item data; marks itself complete, updates fields, spawns next recurrence |
| `Pet` | Owns a list of Tasks; auto-stamps each task with the pet's name on add |
| `Owner` | Owns a list of Pets; aggregates all tasks across pets into one flat list |
| `Scheduler` | Planning brain — sorts, filters, detects conflicts, generates the daily plan |
| `ScheduleResult` | Return value of `generate_plan`: scheduled tasks + excluded tasks with reasons |

---

## Getting Started

### Setup

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### Run

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Testing PawPal+

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

**Confidence: ★★★★☆ (4/5)** — core scheduling paths are thoroughly covered by focused, deterministic tests. A fifth star would require additional edge-case coverage (empty task lists, invalid inputs, boundary conditions on available time).

---

## Project Files

```
ai110-module2show-pawpal-starter/
├── app.py               # Streamlit front-end
├── pawpal_system.py     # Backend logic layer
├── test_pawpal.py       # Pytest unit tests (20 tests)
├── uml_final.mmd        # Final UML diagram source (Mermaid)
├── uml_final.png        # Final UML diagram (rendered)
├── reflection.md        # Design decisions & AI collaboration notes
├── requirements.txt
└── README.md
```

---

## Algorithm Summary

| Feature | Method | Complexity |
|---|---|---|
| Priority + time-of-day + duration sort | `generate_plan` | O(n log n) |
| Clock-time sort (HH:MM) | `sort_by_time` | O(n log n) |
| Time-of-day slot sort | `sort_by_time_of_day` | O(n log n) |
| Priority sort | `sort_by_priority` | O(n log n) |
| Duration sort | `sort_by_duration` | O(n log n) |
| Status filtering | `filter_by_status` | O(n) |
| Per-pet filtering | `filter_by_pet` | O(n) |
| Time-overlap detection (sort-then-sweep) | `detect_time_overlaps` | O(n log n) |
| Multi-level conflict check | `check_conflicts` | O(n log n) |
| Recurrence spawning | `complete_task` / `spawn_next` | O(1) per task |
