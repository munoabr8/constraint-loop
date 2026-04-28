import pytest

from bin.run_constraint_loop.py import extract_counts
def test_raises_when_check_parsed_is_none():
    with pytest.raises(ValueError, match="check_parsed must be a dict"):
        extract_counts(None, {"blocking_count": 0, "nonblocking_count": 0,
                               "unknown_count": 0, "repair_action_count": 0})

def test_raises_when_handler_parsed_is_none():
    with pytest.raises(ValueError, match="handler_parsed must be a dict"):
        extract_counts({"violations": []}, None)

def test_valid_inputs():
    result = extract_counts(
        {"violations": ["v1", "v2"]},
        {"blocking_count": 1, "nonblocking_count": 0, "unknown_count": 0, "repair_action_count": 2},
    )
    assert result == {
        "violation_count": 2,
        "blocking_count": 1,
        "nonblocking_count": 0,
        "unknown_count": 0,
        "repair_action_count": 2,
    }