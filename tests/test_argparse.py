# Builtin
from argparse import ArgumentParser
from typing import List

# External
import pytest


@pytest.fixture
def parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    parser.add_argument("--work-dir", type=str, required=False)
    return parser


@pytest.fixture
def with_work_dir() -> List[str]:
    return ["--work-dir", "python", "--with=doc"]


@pytest.fixture
def without_work_dir() -> List[str]:
    return ["--with=test", "--with=doc"]


@pytest.fixture
def with_work_dir_changed_order() -> List[str]:
    return ["--with=doc", "--work-dir", "python", "--with=test"]


def test_parse_known_args_with_work_dir(
    parser: ArgumentParser, with_work_dir: List[str]
) -> None:
    namespace, remainder = parser.parse_known_args(with_work_dir)
    assert namespace.filenames == []
    assert namespace.work_dir == "python"
    assert remainder == ["--with=doc"]


def test_parse_known_args_without_work_dir(
    parser: ArgumentParser, without_work_dir: List[str]
) -> None:
    namespace, remainder = parser.parse_known_args(without_work_dir)
    assert namespace.filenames == []
    assert namespace.work_dir is None
    assert remainder == ["--with=test", "--with=doc"]


def test_parse_known_args_with_work_dir_changed_order(
    parser: ArgumentParser, with_work_dir_changed_order: List[str]
) -> None:
    namespace, remainder = parser.parse_known_args(with_work_dir_changed_order)
    assert namespace.filenames == []
    assert namespace.work_dir == "python"
    assert remainder == ["--with=doc", "--with=test"]
