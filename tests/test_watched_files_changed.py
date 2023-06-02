# Builtin
from __future__ import annotations
from unittest.mock import call, MagicMock

# External
import pytest

# Own
from post_merge_hooks.utils import or_


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
