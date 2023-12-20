# External
import pytest

# Own
from post_merge_hooks.remind_poetry_install import _get_watched_files


def test_get_watched_files_none() -> None:
    assert _get_watched_files(None) == ["pyproject.toml", "poetry.lock"]


def test_get_watched_files_relative() -> None:
    assert _get_watched_files("python") == [
        "python/pyproject.toml",
        "python/poetry.lock",
    ]


def test_get_watched_files_absolute() -> None:
    with pytest.raises(Exception, match=r"--work-dir must be a relative path"):
        _get_watched_files("/var")
