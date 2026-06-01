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

from ..camera import Camera
from ..schemas import FuncResult
from ..utils.logs import spincam_logger

IfaceEventCallback: TypeAlias = Callable[[Camera], FuncResult]


class InterfaceEventHandler(PySpin.InterfaceEventHandler):
    def __init__(
        self,
        parent: str,
        device_arrival_callback: IfaceEventCallback | None = None,
        device_removal_callback: IfaceEventCallback | None = None
    ) -> None:
        self._parent: str = parent
        if device_arrival_callback is None:
            device_arrival_callback = self._dummy_callback
        if device_removal_callback is None:
            device_removal_callback = self._dummy_callback
        self._arr_callback: IfaceEventCallback = device_arrival_callback
        self._rm_callback: IfaceEventCallback = device_removal_callback
        super().__init__()

    @staticmethod
    def _dummy_callback(cam: Camera) -> FuncResult:
        return FuncResult.SUCCESS

    def set_arr_callback(self, callback: IfaceEventCallback | None = None) -> None:
        if callback is None:
            callback = self._dummy_callback
        self._arr_callback = callback

    def set_rm_callback(self, callback: IfaceEventCallback | None = None) -> None:
        if callback is None:
            callback = self._dummy_callback
        self._rm_callback = callback

    def OnDeviceArrival(self, pCamera: PySpin.CameraPtr) -> None:
        try:
            cam = Camera(ptr= pCamera)
            threading.Thread(
                target= self._arr_callback,
                args=(cam,),
                daemon= True
            ).start()
        except Exception as e:
            msg: str = f'{self._parent}: Unable to execute OnDeviceArrival callback. {e}'
            spincam_logger.error(msg)
        finally:
            try:
                cam.clear()  # type: ignore
            except NameError:
                pass

    def OnDeviceRemoval(self, pCamera: PySpin.CameraPtr) -> None:
        try:
            cam = Camera(ptr= pCamera)
            threading.Thread(
                target= self._rm_callback,
                args=(cam,),
                daemon= True
            ).start()
        except Exception as e:
            msg: str = f'{self._parent}: Unable to execute OnDeviceRemoval callback. {e}'
            spincam_logger.error(msg)
        finally:
            try:
                cam.clear()  # type: ignore
            except NameError:
                pass
