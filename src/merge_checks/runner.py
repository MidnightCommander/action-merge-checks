import logging
import os
from dataclasses import asdict, dataclass
from enum import StrEnum, auto

import github
from github.Repository import Repository

from merge_checks.commit_checks import get_base_sha, get_commit_checks_result, get_commits
from merge_checks.commit_status_setter import set_commit_status

logger = logging.getLogger(__name__)

STATUS_NAME = "Merge checks / Result"
STATUS_DESCRIPTION = "Merge checks running"


@dataclass
class Commit:
    repository: str
    commit_sha: str
    token: str


@dataclass
class Status:
    status_name: str
    details_url: str


class State(StrEnum):
    PENDING = auto()
    SUCCESS = auto()
    FAILURE = auto()
    ERROR = auto()


def get_commit_and_status() -> tuple[Commit, Status]:
    commit = Commit(
        repository=os.environ["GITHUB_REPOSITORY"],
        token=os.environ["GITHUB_TOKEN"],
        commit_sha=os.environ["HEAD_SHA"],
    )

    status = Status(
        status_name=STATUS_NAME,
        details_url=f"{os.environ['GITHUB_SERVER_URL']}/{commit.repository}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
    )

    return commit, status


def get_repository(commit: Commit) -> Repository:
    return github.Github(login_or_token=commit.token).get_repo(commit.repository)


def run():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    commit, status = get_commit_and_status()

    set_commit_status(
        **(asdict(commit) | asdict(status)),
        state=State.PENDING,
        description=STATUS_DESCRIPTION,
    )

    repository = get_repository(commit=commit)
    base_sha = get_base_sha(repository=repository)

    if commit.commit_sha == base_sha:
        logger.warning(f"HEAD identical with {repository.default_branch}, no commits to check")
        checks_passed, summary = (True, "No commits to check")
    else:
        checks_passed, summary = get_commit_checks_result(
            commits=get_commits(repository=repository, base_sha=base_sha, head_hash=commit.commit_sha),
        )
    logger.info(f"Merge checks summary: {summary}")

    set_commit_status(
        **(asdict(commit) | asdict(status)),
        state=State.SUCCESS if checks_passed else State.FAILURE,
        description=summary,
    )
