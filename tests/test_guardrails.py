from guardrails import (
    MEDICAL_DISCLAIMER,
    EMERGENCY_WARNING,
    detect_emergency_content,
    detect_medical_content,
    validate_plan_input,
    validate_task,
)


def test_validate_task_accepts_valid_task():
    task = {
        "name": "Feed Max",
        "duration": 10,
        "priority": "high",
        "time_of_day": "morning",
        "recurrence": "daily",
    }

    assert validate_task(task) == []


def test_validate_task_rejects_negative_duration():
    task = {
        "name": "Walk Max",
        "duration": -10,
        "priority": "medium",
        "time_of_day": "evening",
        "recurrence": "daily",
    }

    errors = validate_task(task)

    assert "Task duration must be a positive integer." in errors


def test_validate_task_rejects_invalid_priority():
    task = {
        "name": "Feed Max",
        "duration": 10,
        "priority": "urgent",
        "time_of_day": "morning",
        "recurrence": "daily",
    }

    errors = validate_task(task)

    assert "Task priority must be high, medium, or low." in errors


def test_detect_medical_content():
    assert detect_medical_content("My dog needs medication tonight.") is True


def test_detect_emergency_content():
    assert detect_emergency_content("My cat had a seizure.") is True


def test_validate_plan_adds_medical_warning():
    plan = {
        "available_minutes": 30,
        "pets": [
            {
                "name": "Max",
                "type": "dog",
                "tasks": [
                    {
                        "name": "Give medicine",
                        "duration": 10,
                        "priority": "high",
                        "time_of_day": "morning",
                        "recurrence": "daily",
                    }
                ],
            }
        ],
    }

    is_valid, errors, warnings = validate_plan_input(plan)

    assert is_valid is True
    assert errors == []
    assert MEDICAL_DISCLAIMER in warnings


def test_validate_plan_adds_emergency_warning():
    plan = {
        "available_minutes": 30,
        "pets": [
            {
                "name": "Milo",
                "type": "cat",
                "tasks": [
                    {
                        "name": "Check seizure symptoms",
                        "duration": 10,
                        "priority": "high",
                        "time_of_day": "anytime",
                        "recurrence": "once",
                    }
                ],
            }
        ],
    }

    is_valid, errors, warnings = validate_plan_input(plan)

    assert is_valid is True
    assert errors == []
    assert MEDICAL_DISCLAIMER in warnings
    assert EMERGENCY_WARNING in warnings


def test_validate_plan_rejects_missing_pet_list():
    plan = {
        "available_minutes": 30,
        "pets": [],
    }

    is_valid, errors, warnings = validate_plan_input(plan)

    assert is_valid is False
    assert "At least one pet is required." in errors
    assert warnings == []