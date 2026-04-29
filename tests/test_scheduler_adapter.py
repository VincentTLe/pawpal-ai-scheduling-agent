from scheduler_adapter import schedule_structured_plan


def test_valid_plan_produces_scheduled_tasks():
    plan = {
        "owner_name": "User",
        "available_minutes": 45,
        "pets": [
            {
                "name": "Max",
                "type": "dog",
                "tasks": [
                    {
                        "name": "Feed pet",
                        "duration": 10,
                        "priority": "high",
                        "time_of_day": "morning",
                        "recurrence": "daily",
                    }
                ],
            }
        ],
    }

    result = schedule_structured_plan(plan)

    assert result["scheduled_tasks"]
    assert result["scheduled_tasks"][0]["task"] == "Feed pet"
    assert result["skipped_tasks"] == []


def test_limited_available_minutes_skips_tasks():
    plan = {
        "owner_name": "User",
        "available_minutes": 15,
        "pets": [
            {
                "name": "Max",
                "type": "dog",
                "tasks": [
                    {
                        "name": "Feed pet",
                        "duration": 10,
                        "priority": "high",
                        "time_of_day": "morning",
                        "recurrence": "daily",
                    },
                    {
                        "name": "Walk dog",
                        "duration": 30,
                        "priority": "medium",
                        "time_of_day": "evening",
                        "recurrence": "daily",
                    },
                ],
            }
        ],
    }

    result = schedule_structured_plan(plan)

    assert len(result["scheduled_tasks"]) == 1
    assert result["skipped_tasks"]
    assert "Not enough time" in result["skipped_tasks"][0]["reason"]


def test_high_priority_medication_scheduled_before_low_priority_grooming():
    plan = {
        "owner_name": "User",
        "available_minutes": 10,
        "pets": [
            {
                "name": "Max",
                "type": "dog",
                "tasks": [
                    {
                        "name": "Groom pet",
                        "duration": 10,
                        "priority": "low",
                        "time_of_day": "anytime",
                        "recurrence": "weekly",
                    },
                    {
                        "name": "Give medication",
                        "duration": 10,
                        "priority": "high",
                        "time_of_day": "anytime",
                        "recurrence": "daily",
                    },
                ],
            }
        ],
    }

    result = schedule_structured_plan(plan)
    scheduled_names = [task["task"] for task in result["scheduled_tasks"]]
    skipped_names = [task["task"] for task in result["skipped_tasks"]]

    assert scheduled_names == ["Give medication"]
    assert "Groom pet" in skipped_names
