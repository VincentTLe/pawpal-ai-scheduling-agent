from __future__ import annotations

import os
from dataclasses import dataclass

from ai_agent import run_agent
from scheduler_adapter import schedule_structured_plan


@dataclass(frozen=True)
class EvalCase:
    name: str
    prompt: str
    expected_task_keywords: tuple[str, ...] = ()
    expected_warning_keywords: tuple[str, ...] = ()
    expected_skipped_keywords: tuple[str, ...] = ()


CASES = [
    # ── Core happy-path cases ─────────────────────────────────────────────────
    EvalCase(
        name="simple dog feeding and walking",
        prompt="I have a dog named Max. I have 45 minutes today. He needs feeding and walking.",
        expected_task_keywords=("feed", "walk"),
    ),
    EvalCase(
        name="cat litter cleaning",
        prompt="I have a cat named Milo. I have 20 minutes. He needs litter box cleaning.",
        expected_task_keywords=("litter",),
    ),
    EvalCase(
        name="water refill for cat",
        prompt="I have a cat named Luna. I have 15 minutes. She needs water.",
        expected_task_keywords=("water",),
    ),
    EvalCase(
        name="playtime only — no medical content",
        prompt="My dog Rex has 20 minutes. He needs playtime.",
        expected_task_keywords=("play",),
        expected_warning_keywords=(),
    ),
    EvalCase(
        name="cat full routine fits in 30 minutes",
        prompt=(
            "I have a cat named Milo. I have 30 minutes. "
            "He needs litter box cleaning, water refill, and playtime."
        ),
        expected_task_keywords=("litter", "water", "play"),
    ),
    # ── Guardrail cases ───────────────────────────────────────────────────────
    EvalCase(
        name="dog medication warning",
        prompt="My dog Luna needs medicine and feeding. I have 30 minutes.",
        expected_task_keywords=("medication", "feed"),
        expected_warning_keywords=("veterinary",),
    ),
    EvalCase(
        name="emergency seizure warning",
        prompt="My cat had a seizure and needs help.",
        expected_warning_keywords=("emergency", "veterinarian"),
    ),
    # ── Prioritization and scheduling logic ───────────────────────────────────
    EvalCase(
        name="limited time keeps medication before grooming",
        prompt="I have a dog named Max. I have 10 minutes. He needs medicine and grooming.",
        expected_task_keywords=("medication",),
        expected_warning_keywords=("veterinary",),
        expected_skipped_keywords=("groom",),
    ),
    EvalCase(
        name="multi-task overflow schedules high priority first",
        prompt="My dog Max has 25 minutes. He needs medicine, feeding, walking, and grooming.",
        expected_task_keywords=("medication", "feed"),
        expected_warning_keywords=("veterinary",),
        expected_skipped_keywords=("walk",),
    ),
]


def _contains_all(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return all(kw.lower() in lowered for kw in keywords)


def run_case(case: EvalCase) -> tuple[bool, list[str], dict]:
    agent_result = run_agent(case.prompt)
    schedule_result = (
        schedule_structured_plan(agent_result.structured_plan)
        if agent_result.is_valid
        else None
    )

    failures: list[str] = []
    scheduled_text = ""
    skipped_text = ""

    if schedule_result is not None:
        scheduled_text = " ".join(t["task"] for t in schedule_result["scheduled_tasks"])
        skipped_text   = " ".join(t["task"] for t in schedule_result["skipped_tasks"])

    warnings_text = " ".join(agent_result.warnings)

    if case.expected_task_keywords and not _contains_all(scheduled_text, case.expected_task_keywords):
        failures.append(f"scheduled tasks missing {case.expected_task_keywords}")

    if case.expected_warning_keywords and not _contains_all(warnings_text, case.expected_warning_keywords):
        failures.append(f"warnings missing {case.expected_warning_keywords}")

    if case.expected_skipped_keywords and not _contains_all(skipped_text, case.expected_skipped_keywords):
        failures.append(f"skipped tasks missing {case.expected_skipped_keywords}")

    detail = {
        "scheduled": scheduled_text or "(none)",
        "skipped":   skipped_text   or "(none)",
        "warnings":  warnings_text  or "(none)",
    }
    return not failures, failures, detail


def main() -> None:
    # Reliability evaluation must be reproducible without external API access.
    os.environ.pop("GEMINI_API_KEY", None)

    W = 62
    SEP = "─" * W

    print()
    print("=" * W)
    print("  PawPal AI  —  Reliability Evaluation Harness")
    print(f"  {len(CASES)} cases  ·  deterministic fallback parser (no API key)")
    print("=" * W)

    passed = 0
    for i, case in enumerate(CASES, 1):
        ok, failures, detail = run_case(case)
        if ok:
            passed += 1
            status = "PASS"
        else:
            status = "FAIL"

        print()
        print(f"  [{i:02d}/{len(CASES)}] {status}  {case.name}")
        print(f"        Scheduled : {detail['scheduled']}")
        if detail["skipped"] != "(none)":
            print(f"        Skipped   : {detail['skipped']}")
        if detail["warnings"] != "(none)":
            first = detail["warnings"].split(".")[0].strip() + "."
            print(f"        Warnings  : {first}")
        if failures:
            for f in failures:
                print(f"        ✘ {f}")

    print()
    print(SEP)
    all_passed = passed == len(CASES)
    result_line = f"  {passed} / {len(CASES)} cases passed"
    if all_passed:
        result_line += "  — all checks green"
    print(result_line)
    print("=" * W)
    print()


if __name__ == "__main__":
    main()
