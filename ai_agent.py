from dataclasses import dataclass
import json
import os
import re
from typing import Any

try:
    from google import genai
    from google.genai import types
except ImportError:  # Keep app usable without Gemini dependency installed.
    genai = None
    types = None

from guardrails import (
    EMERGENCY_WARNING,
    MEDICAL_DISCLAIMER,
    detect_emergency_content,
    detect_medical_content,
    validate_plan_input,
)
from retriever import retrieve_context, RetrievedChunk


@dataclass(frozen=True)
class AgentStep:
    name: str
    status: str
    details: str


@dataclass(frozen=True)
class AgentResult:
    user_input: str
    structured_plan: dict[str, Any]
    retrieved_context: list[dict[str, Any]]
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    steps: list[AgentStep]


TASK_PATTERNS = [
    {
        "keywords": {"medicine", "medication", "pill", "pills"},
        "task": {
            "name": "Give medication",
            "duration": 10,
            "priority": "high",
            "time_of_day": "anytime",
            "recurrence": "daily",
        },
    },
    {
        "keywords": {"feed", "feeding", "food"},
        "task": {
            "name": "Feed pet",
            "duration": 10,
            "priority": "high",
            "time_of_day": "morning",
            "recurrence": "daily",
        },
    },
    {
        "keywords": {"water", "refill"},
        "task": {
            "name": "Check and refill water",
            "duration": 5,
            "priority": "high",
            "time_of_day": "anytime",
            "recurrence": "daily",
        },
    },
    {
        "keywords": {"walk", "walking"},
        "task": {
            "name": "Walk dog",
            "duration": 30,
            "priority": "medium",
            "time_of_day": "evening",
            "recurrence": "daily",
        },
    },
    {
        "keywords": {"litter", "box"},
        "task": {
            "name": "Clean litter box",
            "duration": 10,
            "priority": "high",
            "time_of_day": "anytime",
            "recurrence": "daily",
        },
    },
    {
        "keywords": {"groom", "grooming", "brush", "bath"},
        "task": {
            "name": "Groom pet",
            "duration": 30,
            "priority": "low",
            "time_of_day": "anytime",
            "recurrence": "weekly",
        },
    },
    {
        "keywords": {"play", "playtime", "enrichment"},
        "task": {
            "name": "Pet playtime",
            "duration": 15,
            "priority": "medium",
            "time_of_day": "anytime",
            "recurrence": "daily",
        },
    },
]


def extract_available_minutes(user_input: str, default_minutes: int = 60) -> int:
    """
    Extract available time from natural language.

    Examples:
        "I have 45 minutes" -> 45
        "I only have 1 hour" -> 60
    """
    lowered = user_input.lower()

    minute_match = re.search(r"(\d+)\s*(minute|minutes|min|mins)", lowered)
    if minute_match:
        return int(minute_match.group(1))

    hour_match = re.search(r"(\d+)\s*(hour|hours|hr|hrs)", lowered)
    if hour_match:
        return int(hour_match.group(1)) * 60

    standalone_numbers = re.findall(r"\b\d+\b", lowered)
    for number_text in standalone_numbers:
        number = int(number_text)
        if 5 <= number <= 300:
            return number

    return default_minutes


def extract_pet_type(user_input: str) -> str:
    lowered = user_input.lower()

    if "cat" in lowered:
        return "cat"

    if "dog" in lowered:
        return "dog"

    return "pet"


def extract_pet_name(user_input: str, default_name: str = "Pet") -> str:
    """
    Extract a simple pet name from phrases like:
        "dog named Max"
        "cat named Milo"
        "my dog Max"

    This is intentionally simple and deterministic for the first version.
    """
    named_match = re.search(
        r"(?:named|name is)\s+([A-Z][a-zA-Z]+)",
        user_input,
    )
    if named_match:
        return named_match.group(1)

    my_pet_match = re.search(
        r"my\s+(?:dog|cat|pet)\s+([A-Z][a-zA-Z]+)",
        user_input,
    )
    if my_pet_match:
        return my_pet_match.group(1)

    return default_name


def detect_tasks(user_input: str) -> list[dict[str, Any]]:
    lowered = user_input.lower()
    tasks: list[dict[str, Any]] = []
    seen_task_names = set()

    for pattern in TASK_PATTERNS:
        if any(keyword in lowered for keyword in pattern["keywords"]):
            task = dict(pattern["task"])

            if task["name"] not in seen_task_names:
                tasks.append(task)
                seen_task_names.add(task["name"])

    if not tasks:
        tasks.append(
            {
                "name": "General pet check-in",
                "duration": 10,
                "priority": "medium",
                "time_of_day": "anytime",
                "recurrence": "daily",
            }
        )

    return tasks


def parse_user_request(user_input: str) -> dict[str, Any]:
    """
    Convert natural language into a structured plan.

    This is a deterministic parser for the first version of the project.
    Later, this can be replaced or enhanced with an LLM parser.
    """
    available_minutes = extract_available_minutes(user_input)
    pet_type = extract_pet_type(user_input)
    pet_name = extract_pet_name(user_input)
    tasks = detect_tasks(user_input)

    return {
        "owner_name": "User",
        "available_minutes": available_minutes,
        "pets": [
            {
                "name": pet_name,
                "type": pet_type,
                "tasks": tasks,
            }
        ],
    }


def parse_user_request_with_gemini(
    user_input: str,
    retrieved_context: list[dict[str, Any]],
) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    if genai is None or types is None:
        raise RuntimeError("google-genai SDK is not installed.")

    client = genai.Client()

    response_schema = {
        "type": "object",
        "properties": {
            "owner_name": {"type": "string"},
            "available_minutes": {"type": "integer"},
            "pets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "duration": {"type": "integer"},
                                    "priority": {
                                        "type": "string",
                                        "enum": ["high", "medium", "low"],
                                    },
                                    "time_of_day": {
                                        "type": "string",
                                        "enum": ["morning", "afternoon", "evening", "anytime"],
                                    },
                                    "recurrence": {
                                        "type": "string",
                                        "enum": ["once", "daily", "weekly", "monthly"],
                                    },
                                },
                                "required": [
                                    "name",
                                    "duration",
                                    "priority",
                                    "time_of_day",
                                    "recurrence",
                                ],
                            },
                        },
                    },
                    "required": ["name", "type", "tasks"],
                },
            },
        },
        "required": ["owner_name", "available_minutes", "pets"],
    }

    prompt = (
        "You are converting a pet-care request into structured scheduling JSON.\n"
        "Use retrieved context only to inform task priority and safety-sensitive interpretation.\n"
        "Do not provide veterinary advice.\n"
        "Do not invent medication dosage, diagnosis, or treatment.\n"
        "If available time is missing, use 60.\n"
        "If pet name is missing, use 'Pet'.\n"
        "If pet type is missing, use 'pet'.\n"
        "Return only JSON matching the requested schema.\n\n"
        f"USER REQUEST:\n{user_input}\n\n"
        f"RETRIEVED CONTEXT:\n{json.dumps(retrieved_context, ensure_ascii=True)}"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
        ),
    )

    parsed = getattr(response, "parsed", None)
    if parsed is None:
        text = getattr(response, "text", "")
        if not text:
            raise ValueError("Gemini returned empty response.")
        parsed = json.loads(text)

    if not isinstance(parsed, dict):
        raise ValueError("Gemini response is not a JSON object.")

    required_keys = {"owner_name", "available_minutes", "pets"}
    if not required_keys.issubset(parsed.keys()):
        raise ValueError("Gemini response missing required plan fields.")

    return parsed


def serialize_retrieved_context(chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
    return [
        {
            "source": chunk.source,
            "heading": chunk.heading,
            "text": chunk.text,
            "score": chunk.score,
        }
        for chunk in chunks
    ]


def run_agent(user_input: str) -> AgentResult:
    """
    Run the first version of the PawPal AI agentic workflow.

    Workflow:
        1. Retrieve relevant pet-care knowledge.
        2. Parse user request into structured task data.
        3. Validate structured data with guardrails.
        4. Return observable steps, warnings, and retrieved context.
    """
    steps: list[AgentStep] = []

    retrieved_chunks = retrieve_context(user_input, top_k=3)
    steps.append(
        AgentStep(
            name="retrieve_context",
            status="success",
            details=f"Retrieved {len(retrieved_chunks)} relevant knowledge chunks.",
        )
    )

    serialized_context = serialize_retrieved_context(retrieved_chunks)

    try:
        structured_plan = parse_user_request_with_gemini(user_input, serialized_context)
        steps.append(
            AgentStep(
                name="parse_user_request_with_gemini",
                status="success",
                details="Gemini converted the request into structured task JSON.",
            )
        )
    except Exception as exc:
        structured_plan = parse_user_request(user_input)
        reason = str(exc).strip() or "Gemini parsing failed"
        steps.append(
            AgentStep(
                name="parse_user_request_with_gemini",
                status="fallback",
                details=f"Used deterministic parser fallback: {reason}.",
            )
        )

    is_valid, errors, warnings = validate_plan_input(structured_plan)
    if detect_medical_content(user_input) and MEDICAL_DISCLAIMER not in warnings:
        warnings.append(MEDICAL_DISCLAIMER)
    if detect_emergency_content(user_input) and EMERGENCY_WARNING not in warnings:
        warnings.append(EMERGENCY_WARNING)
    steps.append(
        AgentStep(
            name="validate_plan",
            status="success" if is_valid else "failed",
            details=f"Found {len(errors)} errors and {len(warnings)} warnings.",
        )
    )

    final_status = "ready_for_scheduler" if is_valid else "blocked_by_guardrails"
    steps.append(
        AgentStep(
            name="agent_decision",
            status=final_status,
            details=(
                "The plan is ready for scheduling."
                if is_valid
                else "The plan should not be scheduled until errors are fixed."
            ),
        )
    )

    return AgentResult(
        user_input=user_input,
        structured_plan=structured_plan,
        retrieved_context=serialized_context,
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        steps=steps,
    )


def print_agent_result(result: AgentResult) -> None:
    print("PawPal AI Agent Result")
    print("=" * 40)
    print(f"Input: {result.user_input}")
    print()

    print("Agent Steps:")
    for step in result.steps:
        print(f"- {step.name}: {step.status} | {step.details}")

    parser_step = next(
        (step for step in result.steps if step.name == "parse_user_request_with_gemini"),
        None,
    )
    if parser_step is not None:
        print()
        print(f"Parser mode: {parser_step.status}")

    print()
    print("Structured Plan:")
    print(result.structured_plan)

    print()
    print("Retrieved Context:")
    for chunk in result.retrieved_context:
        print(f"- {chunk['source']} — {chunk['heading']} | score={chunk['score']}")

    print()
    print("Warnings:")
    if result.warnings:
        for warning in result.warnings:
            print(f"- {warning}")
    else:
        print("- None")

    print()
    print("Errors:")
    if result.errors:
        for error in result.errors:
            print(f"- {error}")
    else:
        print("- None")


if __name__ == "__main__":
    sample_input = (
        "I have a dog named Max. I have 45 minutes today. "
        "He needs medicine, feeding, walking, and grooming."
    )

    agent_result = run_agent(sample_input)
    print_agent_result(agent_result)
