# Builtin
from textwrap import dedent


class RootException(Exception):
    def __init__(self, msg: str, /):
        self._msg = dedent(msg).replace("\n", " ").strip()
        super().__init__(self._msg)

    @property
    def message(self) -> str:
        return self._msg
