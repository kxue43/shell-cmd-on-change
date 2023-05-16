# Builtin
from __future__ import annotations
from typing import Sequence

# Own
from .utils import (
    get_last_pull_commits_sha,
    message_renderer_factory,
    watched_files_changed,
)

HOOK_NAME = "remind-poetry-install"


def main(argv: Sequence[str] | None = None) -> int:
    watched_files = ["pyproject.toml", "poetry.lock"]
    poetry_command = f"poetry install {' '.join(argv)}" if argv else "poetry install"
    render = message_renderer_factory(highlights=watched_files)
    render_error = message_renderer_factory(
        highlights=[poetry_command, *watched_files], error=True
    )
    latest_commit_sha, second_latest_commit_sha = get_last_pull_commits_sha()
    if latest_commit_sha is None or second_latest_commit_sha is None:
        return 0
    if not watched_files_changed(
        watched_files, latest_commit_sha, second_latest_commit_sha
    ):
        render(
            """
            `pyproject.toml` and `poetry.lock` did not change after `git pull`.
            No need to update virtual environment.
            """
        )
        return 0
    render_error(
        f"""
        `pyproject.toml` and/or `poetry.lock` changed after `git pull`.
        Please run `{poetry_command}` to update local virtual environment.
        """
    )
    return 1
