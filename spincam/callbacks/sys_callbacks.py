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


import threading
from collections.abc import Callable
from typing import TypeAlias

import PySpin

from ..interface import Iface
from ..schemas import FuncResult

SysEventFunc: TypeAlias = Callable[[Iface], FuncResult]


class SysEventHandler(PySpin.SystemEventHandler):
    def __init__(
        self,
        iface_arrival_func: SysEventFunc | None = None,
        iface_removal_func: SysEventFunc | None = None
    ) -> None:
        if iface_arrival_func is None:
            iface_arrival_func = self._dummy_callback
        if iface_removal_func is None:
            iface_removal_func = self._dummy_callback
        self._arr_func: SysEventFunc = iface_arrival_func
        self._rm_func: SysEventFunc = iface_removal_func
        super().__init__()

    @staticmethod
    def _dummy_callback(iface: Iface) -> FuncResult:
        return FuncResult.SUCCESS

    def set_arr_func(self, func: SysEventFunc | None = None) -> None:
        if func is None:
            func = self._dummy_callback
        self._arr_func = func

    def set_rm_func(self, func: SysEventFunc | None = None) -> None:
        if func is None:
            func = self._dummy_callback
        self._rm_func = func

    def OnInterfaceArrival(self, pInterface: PySpin.InterfacePtr) -> None:
        iface = Iface(ptr= pInterface)
        threading.Thread(
            target= self._arr_func,
            args=(iface,),
            daemon= True
        ).start()

    def OnInterfaceRemoval(self, pInterface: PySpin.InterfacePtr) -> None:
        iface = Iface(ptr= pInterface)
        threading.Thread(
            target= self._rm_func,
            args=(iface,),
            daemon= True
        ).start()
