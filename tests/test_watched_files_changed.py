# Builtin
from __future__ import annotations
import os
from pathlib import Path, PurePath
from tempfile import TemporaryDirectory
from typing import Iterable, List, Tuple
from unittest.mock import call, MagicMock

# External
from pygit2 import Oid
import pytest
from pytest_mock import MockerFixture
from _pytest.fixtures import SubRequest

# Own
from post_merge_hooks.utils import EMPTY_HASH, Predicate, or_, watched_files_changed


def test_or_() -> None:
    # When `combined_predicate` returns True
    first_false = MagicMock(wraps=(lambda _: False))
    first_true = MagicMock(wraps=(lambda _: True))
    second_false = MagicMock(wraps=(lambda _: False))
    exhaustible_predicates = map(lambda x: x, [first_false, first_true, second_false])
    combined_predicate = or_(exhaustible_predicates)
    for i in range(1, 6):
        assert combined_predicate(i - 1)
        if i == 1:
            with pytest.raises(StopIteration):
                next(exhaustible_predicates)
        first_false.assert_has_calls([call(n) for n in range(i)])
        first_true.assert_has_calls([call(n) for n in range(i)])
        second_false.assert_not_called()
    # When `combined_predicate` returns False
    exhaustible_predicates = map(lambda x: x, [first_false, second_false])
    combined_predicate = or_(exhaustible_predicates)
    assert not combined_predicate(0)
    with pytest.raises(StopIteration):
        next(exhaustible_predicates)


@pytest.fixture(scope="module", autouse=True)
def temp_dir() -> Iterable[None]:
    cwd = Path(os.getcwd()).resolve()
    with TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        l1 = temp_dir.joinpath("l1")
        m1 = temp_dir.joinpath("m1")
        m1.mkdir()
        l2 = l1.joinpath("l2")
        l2.mkdir(parents=True)
        l1.joinpath("b1.txt").touch()
        l1.joinpath("b2.txt").touch()
        l1.joinpath("b3.py").touch()
        l2.joinpath("c1.txt").touch()
        l2.joinpath("c2.py").touch()
        m1.joinpath("d1.txt").touch()
        m1.joinpath("d2.txt").touch()
        temp_dir.joinpath("a1.txt").touch()
        os.chdir(temp_dir)
        yield
        os.chdir(cwd)


def test_predicate_class() -> None:
    predicates = [
        Predicate(path) for path in ["l1/b3.txt", "l1", "l1/l2/*.txt", "f1", "a1.txt"]
    ]
    p0, p1, p2, p3, p4 = predicates
    sorted_predicates = sorted(predicates, key=lambda x: x.sort_key)
    assert sorted_predicates == [p1, p2, p4, p0, p3]


@pytest.fixture(
    params=[
        (["l1"], ["l1/b1.txt"], True),
        (["l1"], ["m1/d1.txt"], False),
        (["l1"], ["m1/d1.txt", "l1/l2/c1.txt"], True),
        (["l1/l2/*.txt"], ["l1/l2/c1.txt"], True),
        (["l1/l2/*.txt"], ["l1/b2.txt"], False),
        (["l1/l2/*.txt"], ["a1.txt", "l1/l2/c1.txt"], True),
        (["l1/*.txt"], ["l1/b3.py", "a1.txt", "l1/l2/c1.txt"], False),
        (["l1/*.txt"], ["l1/b3.py", "l1/b2.txt"], True),
        (["m1/d1.txt"], ["a1.txt"], False),
        (["m1/d1.txt"], ["m1/d2.txt"], False),
        (["m1/d1.txt"], ["m1/d1.txt"], True),
        (["m1", "l1/l2/c1.txt"], ["m1/d1.txt"], True),
        (["m1", "l1/l2/c1.txt"], ["a1.txt", "l1/b1.txt"], False),
        (["m1", "l1/l2/c1.txt"], ["l1/l2/c1.txt"], True),
        (["l1/l2", "a1.txt"], ["l1/l2/c1.txt"], True),
        (["l1/l2", "a1.txt"], ["l1/b1.txt", "m1/d2.txt"], False),
        (["l1/**/*.txt", "a1.txt"], ["l1/l2/c2.py", "m1/d2.txt"], False),
        (["l1/**/*.txt", "a1.txt"], ["l1/l2/c2.py", "a1.txt"], True),
    ],
    ids=range(18),
)
def watched_and_changed(
    request: SubRequest, mocker: MockerFixture
) -> Iterable[Tuple[List[str], bool]]:
    mocker.patch(
        "post_merge_hooks.utils.get_changed_files_set_between_commits"
    ).return_value = [PurePath(path_str) for path_str in request.param[1]]
    yield request.param[0], request.param[2]


def test_watched_files_changed(watched_and_changed: Tuple[List[str], bool]):
    unused_oid = Oid(hex=EMPTY_HASH)
    watched_paths, changed = watched_and_changed
    assert watched_files_changed(watched_paths, unused_oid, unused_oid) == changed
