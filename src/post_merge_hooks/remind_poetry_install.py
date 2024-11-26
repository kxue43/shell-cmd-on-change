# Builtin
from __future__ import annotations
import argparse
from pathlib import PurePath
from typing import List, Optional, Sequence

# Own
from .utils import (
    InvalidCommitHashException,
    NoHeadRefLogException,
    WrongHeadRefLogTypeException,
    get_this_merge_commits,
    message_renderer_factory,
    watched_files_changed,
)

HOOK_NAME = "remind-poetry-install"


def _get_watched_files(work_dir: Optional[str]) -> List[str]:
    target = ["pyproject.toml", "poetry.lock"]
    if work_dir is None:
        return target
    folder = PurePath(work_dir)
    if folder.is_absolute():
        raise Exception("--work-dir must be a relative path.")
    return [str(folder.joinpath(item)) for item in target]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    parser.add_argument("--work-dir", type=str, required=False)
    namespace, remainder = parser.parse_known_args(argv)
    watched_files = _get_watched_files(namespace.work_dir)
    poetry_command = (
        f"poetry install {' '.join(remainder)}" if remainder else "poetry install"
    )
    render = message_renderer_factory(
        highlights=["git pull", poetry_command, *watched_files]
    )
    try:
        latest_commit, second_latest_commit = get_this_merge_commits()
    except NoHeadRefLogException as exc:
        render(
            f"""
            {exc.message}. If `pyproject.toml` and/or `poetry.lock` changed after
            `git pull` or `git merge`. Please run `{poetry_command}` to update
            local virtual environment.
            """
        )
        return 1
    except WrongHeadRefLogTypeException as exc:
        render(
            f"""
            {exc.message}. This is a bug of either `pre-commit` or this hook.
            Please report it at https://github.com/kxue43/post-merge-hooks/issues.
            """
        )
        return 1
    except InvalidCommitHashException as exc:
        render(
            f"""
            {exc.message}. This is a bug of this hook.
            Please report it at https://github.com/kxue43/post-merge-hooks/issues.
            """
        )
        return 1
    if not watched_files_changed(watched_files, latest_commit, second_latest_commit):
        render(
            """
            `pyproject.toml` and `poetry.lock` did not change after `git pull`.
            No need to update virtual environment.
            """
        )
        return 0
    render(
        f"""
        `pyproject.toml` and/or `poetry.lock` changed after `git pull`.
        Please run `{poetry_command}` to update local virtual environment.
        """
    )
    return 1
