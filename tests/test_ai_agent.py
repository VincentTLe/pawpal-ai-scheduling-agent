from ai_agent import (
    detect_tasks,
    extract_available_minutes,
    extract_pet_name,
    extract_pet_type,
    parse_user_request,
    run_agent,
)


def test_extract_available_minutes_detects_minutes():
    assert extract_available_minutes("I have 45 minutes.") == 45


def test_extract_pet_type_detects_cat():
    assert extract_pet_type("My cat needs feeding") == "cat"


def test_extract_pet_name_detects_named_pattern():
    assert extract_pet_name("I have a dog named Max") == "Max"


def test_detect_tasks_detects_medicine_and_walk():
    tasks = detect_tasks("My dog needs medicine and walking")
    task_names = {task["name"] for task in tasks}
    assert "Give medication" in task_names
    assert "Walk dog" in task_names


def test_parse_user_request_returns_expected_shape():
    parsed = parse_user_request("I have a cat named Milo. I have 30 minutes. Needs feeding.")

    assert parsed["owner_name"] == "User"
    assert isinstance(parsed["available_minutes"], int)
    assert isinstance(parsed["pets"], list)
    assert len(parsed["pets"]) >= 1


def test_gemini_parser_falls_back_when_api_key_missing(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = run_agent("I have a dog named Max. I have 45 minutes. He needs medicine and walking.")

    assert result.is_valid is True
    parse_steps = [step for step in result.steps if step.name == "parse_user_request_with_gemini"]
    assert parse_steps
    assert parse_steps[0].status == "fallback"


def test_run_agent_has_retrieval_parse_validation_decision_steps(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = run_agent("I have a cat named Milo. I have 60 minutes for feeding and playtime.")
    step_names = [step.name for step in result.steps]

    assert "retrieve_context" in step_names
    assert "parse_user_request_with_gemini" in step_names
    assert "validate_plan" in step_names
    assert "agent_decision" in step_names


def test_run_agent_adds_emergency_warning_from_raw_input(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    result = run_agent("My cat had a seizure and needs help.")

    assert any("emergency" in warning.lower() for warning in result.warnings)
