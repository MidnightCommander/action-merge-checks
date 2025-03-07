from unittest.mock import patch

from merge_checks import runner
from merge_checks.runner import Commit, Status, run


@patch.object(runner, "get_commit_checks_result")
@patch.object(runner, "get_base_sha")
@patch.object(runner, "get_repository")
@patch.object(runner, "get_commit_and_status")
@patch.object(runner, "set_commit_status")
def assert_expected_calls_and_result(
    mock_set_commit_status,
    mock_get_commit_and_status,
    mock_get_repository,
    mock_get_base_sha,
    mock_get_commit_checks_result,
    commit_checks_result,
    base_sha,
    n_expected_commit_check_calls,
    expected_commit_state,
):
    mock_get_commit_and_status.return_value = (
        Commit(repository="test", commit_sha="123", token="456"),
        Status(status_name="test status", details_url="example.com"),
    )
    mock_get_commit_checks_result.return_value = (commit_checks_result, "test summary")
    mock_get_base_sha.return_value = base_sha

    run()

    mock_get_repository.assert_called_once()
    mock_get_base_sha.assert_called_once()

    assert mock_set_commit_status.call_args_list[0].kwargs.get("state") == "pending"
    assert n_expected_commit_check_calls == len(mock_get_commit_checks_result.call_args_list)
    assert mock_set_commit_status.call_args_list[1].kwargs.get("state") == expected_commit_state


def test_result_state_success():
    assert_expected_calls_and_result(
        commit_checks_result=True,
        base_sha="456",
        n_expected_commit_check_calls=1,
        expected_commit_state="success",
    )


def test_no_commits_to_check():
    assert_expected_calls_and_result(
        commit_checks_result=True,
        base_sha="123",
        n_expected_commit_check_calls=0,
        expected_commit_state="success",
    )


def test_result_state_failure():
    assert_expected_calls_and_result(
        commit_checks_result=False,
        base_sha="456",
        n_expected_commit_check_calls=1,
        expected_commit_state="failure",
    )
