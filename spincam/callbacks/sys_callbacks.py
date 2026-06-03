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


from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Protocol

import PySpin

from ..interface import Iface
from ..schemas import FuncResult

if TYPE_CHECKING:
    from ..system import System


class SysEventCallback(Protocol):
    def __call__(self, sys: System, iface: Iface) -> FuncResult: ...


class SysEventHandler(PySpin.SystemEventHandler):
    def __init__(
        self,
        system: System,
        iface_arrival_callback: SysEventCallback | None = None,
        iface_removal_callback: SysEventCallback | None = None
    ) -> None:
        self._sys: System = system
        if iface_arrival_callback is None:
            iface_arrival_callback = self._dummy_callback
        if iface_removal_callback is None:
            iface_removal_callback = self._dummy_callback
        self._arr_callback: SysEventCallback = iface_arrival_callback
        self._rm_callback: SysEventCallback = iface_removal_callback
        super().__init__()

    @staticmethod
    def _dummy_callback(sys: System, iface: Iface) -> FuncResult:
        return FuncResult.SUCCESS

    def set_arr_callback(self, callback: SysEventCallback | None = None) -> None:
        if callback is None:
            callback = self._dummy_callback
        self._arr_callback = callback

    def set_rm_callback(self, callback: SysEventCallback | None = None) -> None:
        if callback is None:
            callback = self._dummy_callback
        self._rm_callback = callback

    def OnInterfaceArrival(self, pInterface: PySpin.InterfacePtr) -> None:
        iface = Iface(sys= self._sys, ptr= pInterface)
        sys_iface: Iface | None = self._sys.get_iface_by_id(iface.id)
        if sys_iface is None:
            return
        threading.Thread(
            target= self._arr_callback,
            args=(self._sys, sys_iface,),
            daemon= True
        ).start()

    def OnInterfaceRemoval(self, pInterface: PySpin.InterfacePtr) -> None:
        self._sys._update_ifaces()
        iface = Iface(sys= self._sys, ptr= pInterface)
        threading.Thread(
            target= self._rm_callback,
            args=(self._sys, iface,),
            daemon= True
        ).start()
