from typing import Union, Optional


def output_as_str(string_like: Optional[Union[str, bytes]]) -> Optional[str]:
    if string_like is not None and type(string_like) != str:  # pylint: disable=unidiomatic-typecheck
        return string_like.decode("utf-8", errors="replace") # type: ignore
    else:
        return string_like


class UIError(Exception):

    def __init__(self, message, exception = None):
        super(UIError, self).__init__()
        self._message = message
        self._exception = exception

    @property
    def message(self):
        return self._message

    @property
    def source_exception(self):
        return self._exception

    def __str__(self):
        return self._message

    def __repr__(self):
        return f"UIError({self._message})"
