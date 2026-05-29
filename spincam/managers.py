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

from .camera import Camera
from .interface import Iface
from .system import System
from .utils.logs import Styles, spincam_logger


# ---------- SYSTEM ---------- #
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


# ---------- CAMERA ---------- #
def get_available_cam_serial_numbers() -> list[str]:
    _list: list = []
    with get_cam_list() as cam_list:
        num_cameras: int = cam_list.GetSize()
        if num_cameras == 0:
            msg: str = 'Didn\'t find any camera.'
            spincam_logger.error(msg)
            raise RuntimeError(msg)
        msg: str = f'Found {num_cameras} {"camera" if num_cameras == 1 else "cameras"}.'
        spincam_logger.info(msg)
        for cam_ptr in cam_list:
            cam = Camera(cam_ptr)
            _list.append(cam.serial_number)
            cam.clear()
        try:
            del cam_ptr  # type: ignore
        except NameError:
            pass
    return _list

def get_available_cam_names() -> list[str]:
    _list: list = []
    with get_cam_list() as cam_list:
        num_cameras: int = cam_list.GetSize()
        if num_cameras == 0:
            msg: str = 'Didn\'t find any camera.'
            spincam_logger.error(msg)
            raise RuntimeError(msg)
        msg: str = f'Found {num_cameras} {"camera" if num_cameras == 1 else "cameras"}.'
        spincam_logger.info(msg)
        for cam_ptr in cam_list:
            cam = Camera(cam_ptr)
            _list.append(cam.name)
            cam.clear()
        try:
            del cam_ptr  # type: ignore
        except NameError:
            pass
    return _list

def get_cam_list_repr() -> str:
    cam_list_str = '\nCameras list:'
    for cam_name in get_available_cam_names():
        cam_list_str += f'\n  • {cam_name}'
    cam_list_str += '\n'
    return cam_list_str

@contextmanager
def get_cam_list() -> Generator[PySpin.CameraList, None, None]:
    with get_sys() as system:
        yield system.cam_list

@contextmanager
def get_camera(serial_number: str) -> Generator[Camera, None, None]:
    with get_cam_list() as cam_list:
        try:
            ptr: PySpin.CameraPtr = cam_list.GetBySerial(serial_number)
            cam = Camera(ptr)
            del ptr
            yield cam
        except RuntimeError:
            raise
        except ValueError:
            raise
        finally:
            try:
                cam.clear()  # type: ignore
            except NameError:
                pass
            msg: str = f'Camera "{serial_number}" cleared.'
            spincam_logger.debug(msg, Styles.SUCCEED)
