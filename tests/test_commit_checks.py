from unittest.mock import Mock

import pytest

from merge_checks import commit_checks
from merge_checks.commit_checks import get_base_sha


@pytest.fixture
def mock():
    return Mock()


def test_get_base_sha_returns_expected_sha(mock):
    mock.repository.get_branch.return_value.commit.sha = "abc123"
    assert get_base_sha(mock.repository) == "abc123"


def test_happy_path(mock):
    mock.commit.commit.message = "feat(component): subject"
    mock.commit.parents = (Mock(),)

    assert commit_checks.get_commit_checks_result(commits=(mock.commit,)) == (True, "All checks passed")


def test_revert_commit_passes_checks(mock):
    mock.commit.commit.message = 'Revert "feat(component): subject"'
    mock.commit.parents = (Mock(),)

    assert commit_checks.get_commit_checks_result(commits=(mock.commit,)) == (True, "All checks passed")


def test_fixup_found(mock):
    mock.commit.commit.message = "fixup! feat(component): subject"

    assert commit_checks.get_commit_checks_result(commits=(mock.commit,)) == (
        False,
        "1 fixup and 0 squash commits found",
    )


def test_squash_found(mock):
    mock.commit.commit.message = "squash! feat(component): subject"

    assert commit_checks.get_commit_checks_result(commits=(mock.commit,)) == (
        False,
        "0 fixup and 1 squash commits found",
    )


@pytest.mark.parametrize(
    "attribution",
    [
        "Co-Authored-By: Claude Opus 5.5",
        "Co-authored-by: GitHub Copilot",
        "CO-AUTHORED-BY: OpenAI ChatGPT",
        "co-authored-by: claude",
    ],
)
def test_invalid_llm_attributions_found(mock, attribution):
    mock.commit.commit.message = f"feat(component): subject\n\n{attribution}"

    assert commit_checks.get_commit_checks_result(commits=(mock.commit,)) == (
        False,
        "Found 1 commit(s) with invalid LLM attributions, use `Assisted-By: Model X.Y`",
    )


def test_merge_commit_found(mock):
    mock.commit.commit.message = "feat(component): subject"
    mock.commit.parents = (Mock(), Mock())

    assert commit_checks.get_commit_checks_result(commits=(mock.commit,)) == (False, "Contains merge commits")


def test_has_duplicated_commit_messages(mock):
    mock.commit.commit.message = "feat(component): subject"
    mock.commit.parents = (Mock(),)

    assert commit_checks.get_commit_checks_result(commits=(mock.commit, mock.commit)) == (
        False,
        "Duplicated commit messages found",
    )
