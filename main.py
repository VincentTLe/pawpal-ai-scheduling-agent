"""
main.py
-------
Demo / smoke-test script for PawPal+ logic layer.
Run with:  python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    # ------------------------------------------------------------------ setup
    owner = Owner(name="Alex", contact_info="alex@email.com")

    buddy = Pet(name="Buddy", species="Dog", health_notes="Needs joint supplement")
    whiskers = Pet(name="Whiskers", species="Cat")

    owner.add_pet(buddy)
    owner.add_pet(whiskers)

    # ------------------------------------------------------------ add tasks
    buddy.add_task(Task(name="Morning walk",      duration_minutes=30, priority="high"))
    buddy.add_task(Task(name="Joint supplement",  duration_minutes=5,  priority="high"))
    buddy.add_task(Task(name="Fetch / playtime",  duration_minutes=20, priority="medium"))
    buddy.add_task(Task(name="Evening walk",      duration_minutes=30, priority="medium"))

    whiskers.add_task(Task(name="Breakfast feeding", duration_minutes=10, priority="high"))
    whiskers.add_task(Task(name="Litter box clean",  duration_minutes=10, priority="medium"))
    whiskers.add_task(Task(name="Laser pointer play",duration_minutes=15, priority="low"))

    # ------------------------------------------------- run scheduler (60 min)
    scheduler = Scheduler(available_minutes=60)
    all_tasks = owner.get_all_tasks()
    plan = scheduler.generate_plan(all_tasks)

    # ----------------------------------------------------------- print report
    total_scheduled = sum(t.duration_minutes for t in plan.scheduled)

    print("=" * 50)
    print(f"  PawPal+ - Today's Schedule for {owner.name}")
    print(f"  Available time: {scheduler.available_minutes} min")
    print("=" * 50)

    if plan.scheduled:
        print(f"\n[SCHEDULED]  ({total_scheduled} min used)\n")
        for i, task in enumerate(plan.scheduled, start=1):
            print(f"  {i}. [{task.priority.upper():6}] {task.name}"
                  f"  ({task.duration_minutes} min)  - {task.pet_name}")
    else:
        print("\n  No tasks could be scheduled.")

    if plan.excluded:
        print(f"\n[EXCLUDED]  ({len(plan.excluded)} task(s) didn't fit)\n")
        for task, reason in plan.excluded:
            print(f"  x {task.name} ({task.pet_name}): {reason}")

    warnings = scheduler.check_conflicts(all_tasks)
    if warnings:
        print("\n[WARNINGS]")
        for w in warnings:
            print(f"  ! {w}")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
