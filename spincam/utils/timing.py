# MIT License

# Copyright (c) 2026 Jaime Álvarez Díaz
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from time import time
from typing import Any, Optional, TypeVar, Union, cast

from .logs import spincam_logger

F = TypeVar('F', bound= Callable[..., Any])

def time_func(_func: Optional[F] = None) -> Union[Callable[[F], F], F]:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start: float = time()
            result: Any = func(*args, **kwargs)
            end: float = time()
            spincam_logger.debug(f'"{func.__name__}" execution time: {end - start:.4f}s.')
            return result
        return cast(F, wrapper)
    if _func is None:
        return decorator
    return decorator(_func)

@contextmanager
def time_group(group_name: str) -> Generator[None, None, None]:
    start: float = time()
    yield None
    end: float = time()
    msg: str = f'{group_name} executed in {end - start:.4f}s.'
    spincam_logger.debug(msg)
    return None
