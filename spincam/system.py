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


from collections.abc import Generator
from contextlib import contextmanager

import PySpin

from .utils.logs import Styles, spincam_logger


@contextmanager
def get_sys() -> Generator[PySpin.System, None, None]:
    try:
        system: PySpin.System = PySpin.System.GetInstance()
        yield system
    finally:
        try:
            system.ReleaseInstance()  # type: ignore
        except NameError:
            pass
        except PySpin.SpinnakerException:
            msg: str = 'Can\'t clear system. Something still holds a reference.'
            spincam_logger.error(msg)
            raise RuntimeError(msg)
        msg: str = f'PySpin system cleared.'
        spincam_logger.debug(msg, Styles.SUCCEED)
