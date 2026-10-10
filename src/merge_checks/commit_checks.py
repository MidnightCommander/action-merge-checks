import logging
from collections.abc import Sequence

from github.Commit import Commit
from github.Repository import Repository

logger = logging.getLogger(__name__)

LOGGING_PREFIX = "\n  "


def get_base_sha(repository: Repository) -> str:
    return repository.get_branch(repository.default_branch).commit.sha


def get_commits(repository: Repository, base_sha: str, head_hash: str) -> Sequence[Commit]:
    return tuple(repository.compare(base=base_sha, head=head_hash).commits)


def get_commit_messages(commits: Sequence[Commit]) -> Sequence[str]:
    logger.info("Getting commit messages...")
    return tuple(commit.commit.message for commit in commits)


def get_subject_markers(messages: Sequence[str]) -> Sequence[str]:
    logger.info("Getting subject markers...")
    return tuple(strip_allowed_markers(line).split(maxsplit=1)[0] for line in messages)


def has_merge_commits(commits: Sequence[Commit]) -> bool:
    logger.info("Checking for merge commits...")
    return any(len(parents) > 1 for parents in tuple(commit.parents for commit in commits))


def strip_allowed_markers(message: str) -> str:
    return message.removeprefix('Revert "').removesuffix('"')


def has_duplicated_commit_messages(messages: Sequence[str]) -> Sequence[str]:
    return tuple({message for message in messages if messages.count(message) > 1})


def get_commit_checks_result(commits: Sequence[Commit]) -> tuple[bool, str]:
    messages = get_commit_messages(commits)
    logger.info(
        f"Found the following commit messages in branch:{LOGGING_PREFIX}{LOGGING_PREFIX.join(messages)}",
    )

    subject_markers = get_subject_markers(messages)

    fixups, squashes = (
        sum(1 for subject_marker in subject_markers if subject_marker == marker) for marker in ("fixup!", "squash!")
    )

    if fixups or squashes:
        return False, f"{fixups} fixup and {squashes} squash commits found"
    else:
        logger.info("No fixups or squashes found, check passed!")

    if has_merge_commits(commits):
        return False, "Contains merge commits"
    else:
        logger.info("Branch does not contain merge commits, check passed!")

    if duplicated_messages := has_duplicated_commit_messages(messages):
        logger.info(
            f"Found duplicated commit message(s): {LOGGING_PREFIX}{LOGGING_PREFIX.join(duplicated_messages)}",
        )
        return False, "Duplicated commit messages found"

    return True, "All checks passed"
