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


from enum import IntEnum
from typing import Protocol

import PySpin


class FuncResult(IntEnum):
    ERROR = -1
    SUCCESS = 0

    def is_ok(self) -> bool:
        return self.value >= 0

    def is_error(self) -> bool:
        return self.value < 0


class GenericPtr(Protocol):
    def __init__(self, *args) -> None: ...
    def GetDisplayName(self) -> str: ...


class NodeStatus(IntEnum):
    UNKNOWN = 0
    R = 1
    RW = 2

    def can_read(self) -> bool:
        return self.value > 0

    def can_write(self) -> bool:
        return self.value == 2


class NODE_PTR_TYPES(IntEnum):
    CATEGORY = PySpin.intfICategory
    COMMAND = PySpin.intfICommand
    ENUM = PySpin.intfIEnumeration
    BOOL = PySpin.intfIBoolean
    INT = PySpin.intfIInteger
    FLOAT = PySpin.intfIFloat
    STRING = PySpin.intfIString
    REGISTER = PySpin.intfIRegister
