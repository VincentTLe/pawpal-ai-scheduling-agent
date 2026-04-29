import json

from logger import log_run


def test_log_run_writes_jsonl_record(tmp_path):
    log_path = tmp_path / "pawpal_runs.jsonl"

    log_run(
        user_input="My dog needs feeding.",
        result_status="success",
        details={"warnings": [], "retrieved_sources": ["dog_care.md"]},
        log_path=log_path,
    )

    lines = log_path.read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[0])

    assert len(lines) == 1
    assert record["user_input"] == "My dog needs feeding."
    assert record["status"] == "success"
    assert record["details"]["retrieved_sources"] == ["dog_care.md"]
    assert "timestamp" in record


def test_log_run_appends_records(tmp_path):
    log_path = tmp_path / "pawpal_runs.jsonl"

    log_run("first", "success", {}, log_path=log_path)
    log_run("second", "failed", {"errors": ["bad input"]}, log_path=log_path)

    lines = log_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 2
    assert json.loads(lines[1])["status"] == "failed"
