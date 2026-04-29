import streamlit as st
from datetime import date
import os
from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()

from ai_agent import run_agent
from logger import log_run
from pawpal_system import Owner, Pet, Task, Scheduler
from scheduler_adapter import schedule_structured_plan

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="")

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("PawPal+")
st.caption("A daily pet care planner")
st.divider()

# ---------------------------------------------------------------------------
# Section 1 — Owner setup
# ---------------------------------------------------------------------------
st.subheader("1. Owner")

with st.form("owner_form"):
    owner_name_input = st.text_input("Your name", value=owner.name or "")
    submitted_owner = st.form_submit_button("Save owner")

if submitted_owner and owner_name_input.strip():
    owner.name = owner_name_input.strip()
    st.success(f"Owner saved: {owner.name}")

if owner.name:
    st.write(f"Current owner: **{owner.name}**")

st.divider()

# ---------------------------------------------------------------------------
# Section 2 — Add a pet
# ---------------------------------------------------------------------------
st.subheader("2. Add a Pet")

with st.form("add_pet_form"):
    new_pet_name = st.text_input("Pet name")
    new_pet_species = st.selectbox("Species", ["dog", "cat", "bird", "rabbit", "other"])
    new_pet_notes = st.text_input("Health notes (optional)")
    submitted_pet = st.form_submit_button("Add pet")

if submitted_pet:
    if not new_pet_name.strip():
        st.warning("Please enter a pet name.")
    else:
        new_pet = Pet(
            name=new_pet_name.strip(),
            species=new_pet_species,
            health_notes=new_pet_notes.strip(),
        )
        owner.add_pet(new_pet)
        st.success(f"Added pet: {new_pet.name} ({new_pet.species})")

if owner.pets:
    st.write("**Your pets:**")
    for p in owner.pets:
        note = f" — {p.health_notes}" if p.health_notes else ""
        st.write(f"- {p.name} ({p.species}){note}")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3 — Add a task to a pet
# ---------------------------------------------------------------------------
st.subheader("3. Add a Task")

if not owner.pets:
    st.info("Add a pet first before adding tasks.")
else:
    pet_names = [p.name for p in owner.pets]

    with st.form("add_task_form"):
        selected_pet_name = st.selectbox("Assign task to", pet_names)
        task_name = st.text_input("Task name", value="Morning walk")
        task_duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        task_priority = st.selectbox("Priority", ["high", "medium", "low"])

        col1, col2 = st.columns(2)
        with col1:
            task_time_of_day = st.selectbox("Time of day", ["morning", "afternoon", "evening", "anytime"])
        with col2:
            task_start_time = st.text_input("Start time (HH:MM, optional)", placeholder="07:30")

        task_recurrence = st.selectbox("Recurrence", ["none", "daily", "weekly"])
        submitted_task = st.form_submit_button("Add task")

    if submitted_task:
        if not task_name.strip():
            st.warning("Please enter a task name.")
        else:
            target_pet = next(p for p in owner.pets if p.name == selected_pet_name)
            new_task = Task(
                name=task_name.strip(),
                duration_minutes=int(task_duration),
                priority=task_priority,
                time_of_day=task_time_of_day,
                start_time=task_start_time.strip(),
                recurrence=task_recurrence,
            )
            target_pet.add_task(new_task)
            st.success(f"Added '{new_task.name}' to {target_pet.name}")

    # --- Task display with pending / completed tabs ---
    all_tasks = owner.get_all_tasks()
    if all_tasks:
        scheduler_display = Scheduler(available_minutes=480)
        pending_tasks = scheduler_display.filter_by_status(all_tasks, "pending")
        completed_tasks = scheduler_display.filter_by_status(all_tasks, "completed")

        tab_pending, tab_completed = st.tabs(
            [f"Pending ({len(pending_tasks)})", f"Completed ({len(completed_tasks)})"]
        )

        def _task_rows(tasks):
            sorted_tasks = Scheduler(available_minutes=480).sort_by_time(tasks)
            return [
                {
                    "Pet": t.pet_name,
                    "Task": t.name,
                    "Start": t.start_time or "—",
                    "Duration (min)": t.duration_minutes,
                    "Priority": t.priority,
                    "Recurrence": t.recurrence,
                }
                for t in sorted_tasks
            ]

        with tab_pending:
            if pending_tasks:
                st.table(_task_rows(pending_tasks))
            else:
                st.info("No pending tasks.")

        with tab_completed:
            if completed_tasks:
                st.table(_task_rows(completed_tasks))
            else:
                st.info("No completed tasks yet.")
    else:
        st.info("No tasks yet.")

st.divider()

# ---------------------------------------------------------------------------
# Section 4 — Generate schedule
# ---------------------------------------------------------------------------
st.subheader("4. Generate Today's Schedule")

available_minutes = st.number_input(
    "Available time today (minutes)", min_value=10, max_value=480, value=60, step=5
)

if st.button("Generate schedule"):
    all_tasks = owner.get_all_tasks()
    if not all_tasks:
        st.warning("Add some tasks first.")
    else:
        scheduler = Scheduler(available_minutes=int(available_minutes))
        plan = scheduler.generate_plan(all_tasks)
        conflicts = scheduler.check_conflicts(all_tasks)

        # --- Conflict warnings grouped by severity ---
        if conflicts:
            overlap_warnings = [w for w in conflicts if w.startswith("TIME OVERLAP")]
            other_warnings = [w for w in conflicts if not w.startswith("TIME OVERLAP")]

            if other_warnings:
                st.warning("**Scheduling issues detected:**")
                for w in other_warnings:
                    st.warning(w)

            if overlap_warnings:
                st.error("**Time conflicts found — two or more tasks are scheduled at the same time:**")
                for w in overlap_warnings:
                    # Extract just the task names for a friendly message
                    st.error(w)
                st.info(
                    "**Tip:** Open the task form and adjust the Start Time of the conflicting tasks "
                    "so their windows do not overlap. For example, if Walk starts at 07:00 for 30 min, "
                    "the next task should start at 07:30 or later."
                )

        # --- Schedule result ---
        if plan.scheduled:
            total_time = sum(t.duration_minutes for t in plan.scheduled)
            st.success(
                f"Scheduled {len(plan.scheduled)} task(s) — "
                f"{total_time} of {available_minutes} min used."
            )

            # Display sorted by clock time so the owner sees a chronological to-do list
            sorted_plan = scheduler.sort_by_time(plan.scheduled)
            timed = [t for t in sorted_plan if t.start_time]
            untimed = [t for t in sorted_plan if not t.start_time]

            def _plan_rows(tasks):
                return [
                    {
                        "Pet": t.pet_name,
                        "Task": t.name,
                        "Start": t.start_time or "—",
                        "Duration (min)": t.duration_minutes,
                        "Priority": t.priority,
                        "Recurrence": t.recurrence,
                    }
                    for t in tasks
                ]

            if timed:
                st.write("**Scheduled tasks (by clock time):**")
                st.table(_plan_rows(timed))

            if untimed:
                st.write("**Flexible tasks (no fixed start time):**")
                st.table(_plan_rows(untimed))

        else:
            st.error("No tasks could fit in the available time.")

        # --- Excluded tasks ---
        if plan.excluded:
            st.warning(f"{len(plan.excluded)} task(s) could not fit today:")
            for task, reason in plan.excluded:
                st.warning(f"**{task.name}** ({task.pet_name}): {reason}")

st.divider()

# ---------------------------------------------------------------------------
# Section 5 - PawPal AI Agent
# ---------------------------------------------------------------------------
st.subheader("5. PawPal AI Agent")
st.caption("Describe a pet-care situation and let the agent retrieve context, parse tasks, validate safety, and schedule the plan.")

agent_request = st.text_area(
    "Describe your pet-care situation",
    placeholder=(
        "Example: I have a dog named Max. I have 45 minutes today. "
        "He needs medicine, feeding, walking, and grooming."
    ),
)

if st.button("Generate AI care plan"):
    if not agent_request.strip():
        st.warning("Enter a pet-care request first.")
    else:
        agent_result = run_agent(agent_request)
        schedule_result = None

        st.write("**Agent steps**")
        for step in agent_result.steps:
            st.write(f"- **{step.name}** - {step.status}: {step.details}")

        st.write("**Retrieved RAG context**")
        if agent_result.retrieved_context:
            for chunk in agent_result.retrieved_context:
                st.info(
                    f"{chunk['source']} - {chunk['heading']} "
                    f"(score: {chunk['score']})\n\n{chunk['text']}"
                )
        else:
            st.info("No relevant knowledge chunks were retrieved.")

        st.write("**Structured plan**")
        st.json(agent_result.structured_plan)

        if agent_result.warnings:
            st.warning("Guardrail warnings")
            for warning in agent_result.warnings:
                st.write(f"- {warning}")

        if agent_result.errors:
            st.error("Guardrail errors")
            for error in agent_result.errors:
                st.write(f"- {error}")

        if agent_result.is_valid:
            schedule_result = schedule_structured_plan(agent_result.structured_plan)

            st.write("**Final PawPal schedule**")
            st.success(schedule_result["summary"])

            if schedule_result["scheduled_tasks"]:
                st.write("Scheduled tasks")
                st.table(schedule_result["scheduled_tasks"])

            if schedule_result["skipped_tasks"]:
                st.warning("Skipped tasks")
                st.table(schedule_result["skipped_tasks"])

            if schedule_result["conflicts"]:
                st.warning("Scheduler conflicts")
                for conflict in schedule_result["conflicts"]:
                    st.write(f"- {conflict}")
        else:
            st.info("The scheduler was not run because guardrails found blocking errors.")

        log_run(
            user_input=agent_request,
            result_status="success" if agent_result.is_valid else "failed",
            details={
                "errors": agent_result.errors,
                "warnings": agent_result.warnings,
                "retrieved_sources": [
                    chunk["source"] for chunk in agent_result.retrieved_context
                ],
                "scheduled_count": (
                    len(schedule_result["scheduled_tasks"])
                    if schedule_result is not None
                    else 0
                ),
                "skipped_count": (
                    len(schedule_result["skipped_tasks"])
                    if schedule_result is not None
                    else 0
                ),
            },
        )
