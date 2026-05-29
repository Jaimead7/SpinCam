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


import PySpin

from .utils.logs import spincam_logger


class System:
    def __init__(self, sys: PySpin.System) -> None:
        self._sys: PySpin.System = sys
        self._cam_list: PySpin.CameraList =  self._sys.GetCameras()
        self._iface_list: PySpin.InterfaceList = self._sys.GetInterfaces()

    @property
    def cam_list(self) -> PySpin.CameraList:
        self._update_cams()
        return self._cam_list

    @property
    def iface_list(self) -> PySpin.InterfaceList:
        self._update_ifaces()
        return self._iface_list

    def clear(self) -> None:
        self._cam_list.Clear()
        self._iface_list.Clear()
        self._sys.ReleaseInstance()

    def _update_cams(self) -> None:
        try:
            self._cam_list = self._sys.GetCameras()
        except PySpin.SpinnakerException as e:
            msg: str = f'Can\'t update system cameras. {e}'
            spincam_logger.warning(msg)

    def _update_ifaces(self) -> None:
        try:
            self._iface_list = self._sys.GetInterfaces()
        except PySpin.SpinnakerException as e:
            msg: str = f'Can\'t update system interfaces. {e}'
            spincam_logger.warning(msg)
