"""
PawPal AI Demo — Video Walkthrough
Run:  python demo.py
No GEMINI_API_KEY required (forces reproducible fallback parser).
"""
from __future__ import annotations

import os
import time
from typing import Any

os.environ.pop("GEMINI_API_KEY", None)

from ai_agent import run_agent
from scheduler_adapter import schedule_structured_plan

# ── ANSI helpers ──────────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
CYAN    = "\033[96m"
MAGENTA = "\033[95m"
BLUE    = "\033[94m"


def c(text: str, *codes: str) -> str:
    return "".join(codes) + str(text) + RESET


def rule(char: str = "─", width: int = 62) -> str:
    return char * width


def banner(title: str) -> None:
    print()
    print(c(rule("═"), CYAN, BOLD))
    print(c(f"  {title}", CYAN, BOLD))
    print(c(rule("═"), CYAN, BOLD))


def sub(label: str) -> None:
    print()
    print(c(f"  ▸ {label}", BOLD))


def _step_icon(status: str) -> tuple[str, str]:
    if status in ("success", "ready_for_scheduler"):
        return "✔", GREEN
    if status == "fallback":
        return "↺", YELLOW
    return "✘", RED


def print_steps(steps: list) -> None:
    for step in steps:
        icon, col = _step_icon(step.status)
        print(f"    {c(icon, col)} {c(step.name, BOLD)}  {c(step.status, col)}")
        print(f"       {c(step.details, DIM)}")


def print_rag(chunks: list[dict]) -> None:
    for chunk in chunks:
        bar = c("█" * min(int(chunk["score"]), 18), DIM)
        print(
            f"    {c(chunk['source'], MAGENTA)}  ›  {chunk['heading']}"
            f"   score={c(chunk['score'], YELLOW)}  {bar}"
        )


def print_warnings(warnings: list[str]) -> None:
    for w in warnings:
        first_sentence = w.split(".")[0].strip() + "."
        print(f"    {c('⚠  ' + first_sentence, YELLOW, BOLD)}")


def print_errors(errors: list[str]) -> None:
    for e in errors:
        print(f"    {c('✘  ' + e, RED)}")


def print_schedule(result: dict[str, Any], available_minutes: int) -> None:
    scheduled = result["scheduled_tasks"]
    skipped   = result["skipped_tasks"]

    if scheduled:
        print(f"    {c('Scheduled:', GREEN, BOLD)}")
        for t in scheduled:
            pri = c(t["priority"], GREEN if t["priority"] == "high" else YELLOW)
            print(f"      {c('✔', GREEN)} {t['task']:<30} {t['duration_minutes']:>3} min   priority={pri}")
    else:
        print(f"    {c('No tasks scheduled.', DIM)}")

    if skipped:
        print(f"    {c('Skipped:', YELLOW, BOLD)}")
        for t in skipped:
            print(f"      {c('✘', YELLOW)} {t['task']:<30}  → {c(t['reason'], DIM)}")

    used = sum(t["duration_minutes"] for t in scheduled)
    pct  = int(used / available_minutes * 100) if available_minutes else 0
    bar  = c("█" * (pct // 5), GREEN) + c("░" * (20 - pct // 5), DIM)
    print(f"    {c('Time used:', BOLD)} {used}/{available_minutes} min  [{bar}]  {pct}%")


def run_demo(number: int, title: str, prompt: str, note: str) -> None:
    banner(f"DEMO {number} — {title}")
    print(c(f"  {note}", DIM))
    print()
    print(c("  INPUT:", BOLD))
    print(f"  \"{c(prompt, CYAN)}\"")

    result = run_agent(prompt)

    sub("Agent Steps")
    print_steps(result.steps)

    sub("Retrieved Context (RAG)")
    print_rag(result.retrieved_context)

    if result.warnings:
        sub("Guardrail Warnings")
        print_warnings(result.warnings)

    if result.errors:
        sub("Validation Errors")
        print_errors(result.errors)

    sub("Schedule Output")
    if result.is_valid:
        sched = schedule_structured_plan(result.structured_plan)
        avail = result.structured_plan.get("available_minutes", 60)
        print_schedule(sched, avail)
    else:
        print(f"    {c('Plan blocked by guardrails — no schedule generated.', RED)}")

    print()
    time.sleep(0.3)


DEMO_CASES = [
    (
        1,
        "Normal Dog Care",
        "I have a dog named Max. I have 45 minutes today. He needs feeding and walking.",
        "Happy path. Two tasks, plenty of time, no warnings.",
    ),
    (
        2,
        "Medical Guardrail — Medication Warning",
        "My dog Luna needs medicine and feeding. I have 30 minutes.",
        "Keyword 'medicine' triggers veterinary disclaimer. Medication is prioritized first.",
    ),
    (
        3,
        "Emergency Guardrail — Seizure Alert",
        "My cat had a seizure and needs help. I have 30 minutes.",
        "Keyword 'seizure' fires emergency escalation warning. System does not diagnose.",
    ),
    (
        4,
        "Time-Crunch Prioritization",
        "I have a dog named Max. I have 10 minutes. He needs medicine and grooming.",
        "10 min available. Medication (10 min, high) fits; grooming (30 min, low) is skipped.",
    ),
    (
        5,
        "Cat Full Routine",
        "I have a cat named Milo. I have 30 minutes. He needs litter box cleaning, water refill, and playtime.",
        "Three cat tasks. All fit in 30 minutes. No warnings.",
    ),
    (
        6,
        "Multi-Task Overflow — Smart Scheduling",
        "My dog Max has 25 minutes. He needs medicine, feeding, walking, and grooming.",
        "Four tasks, only 25 min. Scheduler fits medicine + feeding (20 min); walk and groom are skipped.",
    ),
]


def main() -> None:
    print()
    print(c(rule("═"), BOLD + BLUE))
    print(c("  PawPal AI  ·  Pet-Care Scheduling Agent", BOLD + BLUE))
    print(c("  RAG Retrieval  +  Gemini/Fallback Parser  +  Guardrails  +  Deterministic Scheduler", DIM))
    print(c(rule("═"), BOLD + BLUE))

    for args in DEMO_CASES:
        run_demo(*args)

    print(c(rule("═"), BOLD + GREEN))
    print(c(f"  {len(DEMO_CASES)} demo cases completed.", BOLD + GREEN))
    print(c("  Run  python eval_cases.py  to see the full reliability harness.", DIM))
    print(c(rule("═"), BOLD + GREEN))
    print()


if __name__ == "__main__":
    main()
