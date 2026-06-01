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


from collections.abc import Generator, Iterable
from contextlib import contextmanager

import PySpin

from .callbacks.sys_callbacks import SysEventCallback, SysEventHandler
from .camera import Camera
from .interface import Iface, IfaceReg
from .schemas import FuncResult
from .utils.logs import Styles, spincam_logger


class System:
    def __init__(self, sys: PySpin.System) -> None:
        self._sys: PySpin.System = sys
        self._iface_reg = IfaceReg()
        self._callbacks: SysEventHandler = SysEventHandler()

    @property
    def ifaces(self) -> Iterable[Iface]:
        self._update_ifaces()
        return self._iface_reg.ifaces.values()

    @property
    def ifaces_ids(self) -> Iterable[str]:
        self._update_ifaces()
        return self._iface_reg.ifaces.keys()

    @property
    def cameras(self) -> Iterable[Camera]:
        cam_list: Iterable[Camera] = []
        for iface in self.ifaces:
            cam_list.extend(iface.cameras)
        return cam_list

    @property
    def cameras_serial_numbers(self) -> Iterable[str]:
        serial_numbers: Iterable[str] = []
        for iface in self.ifaces:
            serial_numbers.extend(iface.cameras_serial_numbers)
        return serial_numbers

    def _update_ifaces(self) -> None:
        try:
            iface_list: PySpin.InterfaceList = self._sys.GetInterfaces()
            for iface in iface_list:
                self._iface_reg.register(iface_ptr= iface)
        except PySpin.SpinnakerException as e:
            msg: str = f'Can\'t update system interfaces. {e}'
            spincam_logger.warning(msg)
        finally:
            try:
                del iface  # type: ignore
            except NameError:
                pass
            try:
                iface_list.Clear()  # type: ignore
            except (NameError, PySpin.SpinnakerException):
                pass
            try:
                del iface_list  # type: ignore
            except NameError:
                pass

    def clear(self) -> None:
        self._iface_reg.clear()
        del self._iface_reg
        self.unregister_events()
        del self._callbacks
        self._sys.ReleaseInstance()

    def get_iface_by_id(self, id: str) -> Iface | None:
        self._update_ifaces()
        return self._iface_reg.get(id)

    def get_cam_by_serial_number(self, serial_number: str) -> Camera | None:
        for iface in self.ifaces:
            cam: Camera | None = iface.get_cam_by_serial_number(serial_number)
            if cam is None:
                continue
            return cam
        msg: str = f'Camera "{serial_number}" not found.'
        spincam_logger.warning(msg)
        return None

    def register_iface_events(
        self,
        iface_arrival_callback: SysEventCallback | None = None,
        iface_removal_callback: SysEventCallback | None = None
    ) -> FuncResult:
        if iface_arrival_callback is not None:
            self._callbacks.set_arr_callback(iface_arrival_callback)
        if iface_removal_callback is not None:
            self._callbacks.set_rm_callback(iface_removal_callback)
        try:
            self._sys.RegisterEventHandler(self._callbacks)
        except PySpin.SpinnakerException as e:
            msg: str = f'Can\'t register system events. {e}'
            spincam_logger.error(msg)
            return FuncResult.ERROR
        return FuncResult.SUCCESS

    def unregister_events(self) -> FuncResult:
        try:
            self._sys.UnregisterEventHandler(self._callbacks)
        except PySpin.SpinnakerException as e:
            msg: str = f'Can\'t unregister system events. {e}'
            spincam_logger.warning(msg)
            return FuncResult.ERROR
        return FuncResult.SUCCESS


@contextmanager
def get_sys() -> Generator[System, None, None]:
    try:
        sys: PySpin.System = PySpin.System.GetInstance()
        system: System = System(sys)
        yield system
    finally:
        try:
            system.clear()  # type: ignore
        except NameError:
            pass
        except PySpin.SpinnakerException:
            msg: str = 'Can\'t clear system. Something still holds a reference.'
            spincam_logger.error(msg)
            raise RuntimeError(msg)
        msg: str = f'PySpin system cleared.'
        spincam_logger.debug(msg, Styles.SUCCEED)
