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

from ..camera import Camera
from ..schemas import FuncResult
from ..utils.logs import spincam_logger

if TYPE_CHECKING:
    from ..interface import Iface
    from ..system import System


class IfaceEventCallback(Protocol):
    def __call__(self, iface: Iface, cam: Camera) -> FuncResult: ...


class InterfaceEventHandler(PySpin.InterfaceEventHandler):
    def __init__(
        self,
        sys: System,
        iface_id: str,
        device_arrival_callback: IfaceEventCallback | None = None,
        device_removal_callback: IfaceEventCallback | None = None
    ) -> None:
        self._sys: System = sys
        self._iface_id: str = iface_id
        if device_arrival_callback is None:
            device_arrival_callback = self._dummy_callback
        if device_removal_callback is None:
            device_removal_callback = self._dummy_callback
        self._arr_callback: IfaceEventCallback = device_arrival_callback
        self._rm_callback: IfaceEventCallback = device_removal_callback
        super().__init__()

    @property
    def iface(self) -> Iface | None:
        return self._sys.get_iface_by_id(self._iface_id)

    @staticmethod
    def _dummy_callback(iface: Iface, cam: Camera) -> FuncResult:
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
            iface: Iface | None = self.iface
            if iface is None:
                msg: str = 'Error getting interface.'
                raise ValueError(msg)
            cam = Camera(sys= self._sys, iface_id= iface.id, ptr= pCamera)
            iface_cam: Camera | None = iface.get_cam_by_serial_number(cam.serial_number)
            if iface_cam is None:
                msg: str = f'Error getting camera {cam.serial_number}.'
                raise ValueError(msg)
            threading.Thread(
                target= self._arr_callback,
                args=(iface, iface_cam,),
                daemon= True
            ).start()
        except Exception as e:
            msg: str = f'{self.iface}: Unable to execute OnDeviceArrival callback. {e}'
            spincam_logger.error(msg)
        finally:
            try:
                cam.clear()  # type: ignore
                del cam  # type: ignore
            except NameError:
                pass

    def OnDeviceRemoval(self, pCamera: PySpin.CameraPtr) -> None:
        try:
            iface: Iface | None = self.iface
            if iface is None:
                msg: str = 'Error getting interface.'
                raise ValueError(msg)
            iface.update_cameras()
            cam = Camera(
                sys= self._sys,
                iface_id= self._iface_id,
                ptr= pCamera
            )
            threading.Thread(
                target= self._rm_callback,
                args=(iface, cam,),
                daemon= True
            ).start()
        except Exception as e:
            msg: str = f'{self.iface}: Unable to execute OnDeviceRemoval callback. {e}'
            spincam_logger.error(msg)
        finally:
            try:
                cam.clear()  # type: ignore
            except NameError:
                pass
