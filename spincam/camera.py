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


from collections.abc import Generator, Sequence
from contextlib import contextmanager
from typing import Any

import numpy as np
import PySpin
from typing_extensions import Self

from spincam.nodes import NodePtr

from .callbacks import NodeCallbackFunc, NodeCallbackReg
from .nodes import CategoryPtr
from .schemas import FuncResult
from .system import get_sys
from .utils.logs import Styles, spincam_logger
from .utils.timing import time_group


class Camera:
    def __init__(self, ptr: PySpin.CameraPtr) -> None:
        try:
            self._ptr: PySpin.CameraPtr = ptr
            self._ptr.Init()
        except PySpin.SpinnakerException as e:
            msg: str = f'Unable to init ptr "{self._ptr}".'
            spincam_logger.error(msg)
            raise ValueError(msg) from e
        self._node_ptrs: dict[str, NodePtr] = self._root_node_ptrs()
        self._create_nodemap()
        self._node_callback_reg: NodeCallbackReg = NodeCallbackReg(
            cam_name= str(self)
        )

    def __str__(self) -> str:
        return f'Camera {self.name}'

    def __repr__(self) -> str:
        return self.get_nodes_repr(['Device.Root.DeviceInformation'])

    @property
    def name(self) -> str:
        return f'{self.model_name} ({self.serial_number})'

    @property
    def model_name(self) -> str:
        try:
            tl_iface: PySpin.TransportLayerInterface = self._ptr.TLDevice
            model_name_node: PySpin.IString = tl_iface.DeviceModelName
            if model_name_node.GetAccessMode() != PySpin.RO:
                raise PySpin.SpinnakerException('It is not a read node.')
            return model_name_node.ToString().strip()
        except PySpin.SpinnakerException as e:
            msg: str = f'Can\'t get the device model name.'
            spincam_logger.warning(msg)
            return 'Unknown'

    @property
    def serial_number(self) -> str:
        try:
            tl_iface: PySpin.TransportLayerInterface = self._ptr.TLDevice
            serial_number_node: PySpin.IString = tl_iface.DeviceSerialNumber
            if serial_number_node.GetAccessMode() != PySpin.RO:
                raise PySpin.SpinnakerException('It is not a read node.')
            return serial_number_node.ToString().strip()
        except PySpin.SpinnakerException as e:
            msg: str = f'Can\'t get the device serial number. {e}'
            spincam_logger.warning(msg)
            return 'Unknown'

    @property
    def nodemap(self) -> PySpin.INodeMap:
        try:
            if not self._ptr.IsInitialized():
                raise PySpin.SpinnakerException('Camera not initialized.')
            return self._ptr.GetNodeMap()
        except PySpin.SpinnakerException as e:
            msg: str = f'{self}: Can\'t get the NodeMap. {e}'
            spincam_logger.error(msg)
            raise RuntimeError(msg)

    @property
    def tl_device_nodemap(self) -> PySpin.INodeMap:
        try:
            if not self._ptr.IsInitialized():
                raise PySpin.SpinnakerException('Camera not initialized.')
            return self._ptr.GetTLDeviceNodeMap()
        except PySpin.SpinnakerException as e:
            msg: str = f'{self}: Can\'t get the TLDeviceNodeMap. {e}'
            spincam_logger.error(msg)
            raise RuntimeError(msg)

    @property
    def tl_stream_nodemap(self) -> PySpin.INodeMap:
        try:
            if not self._ptr.IsInitialized():
                raise PySpin.SpinnakerException('Camera not initialized.')
            return self._ptr.GetTLStreamNodeMap()
        except PySpin.SpinnakerException as e:
            msg: str = f'{self}: Can\'t get the TLStreamNodeMap. {e}'
            spincam_logger.error(msg)
            raise RuntimeError(msg)

    def _root_node_ptrs(self) -> dict[str, NodePtr]:
        return {
            f'App.Root': CategoryPtr(
                route= 'App.Root',
                cam_name= str(self),
                nodemap= self.nodemap,
            ),
            f'Device.Root': CategoryPtr(
                route= 'Device.Root',
                cam_name= str(self),
                nodemap= self.tl_device_nodemap,
            ),
            f'Stream.Root': CategoryPtr(
                route= 'Stream.Root',
                cam_name= str(self),
                nodemap= self.tl_stream_nodemap,
            )
        }

    def _create_nodemap(self) -> None:
        root_node_ptrs: dict[str, NodePtr] = self._root_node_ptrs()
        for node_ptr in root_node_ptrs.values():
            new_nodes: dict[str, NodePtr] = node_ptr.get_subnodes()
            self._node_ptrs.update(new_nodes)

    def _get_node_tree(self, node_name: str) -> str:
        node_ptr: NodePtr | None = self.get_node_ptr(node_name)
        if node_ptr is None:
            return ''
        result: str = f'\n{"    "*(node_ptr.lvl+1)}• {node_ptr.route}'
        child_nodes_names: list[str] = [
            key
            for key, value in self._node_ptrs.items()
            if value.parent_route == node_name
        ]
        for child in child_nodes_names:
            result += self._get_node_tree(child)
        return result

    def get_nodes_repr(self, nodes: Sequence[str] | None = None) -> str:
        if nodes is None:
            nodes = tuple(self._root_node_ptrs().keys())
        result: str = f'\n{self}:'
        for node_name in nodes:
            result += self._get_node_tree(node_name)
        result += '\n'
        return result

    def get_node_ptr(self, route: str) -> NodePtr | None:
        result: NodePtr | None = self._node_ptrs.get(route, None)
        if result is None:
            msg: str = f'{self}: Can\'t find "{route}" in the camera nodes.'
            spincam_logger.error(msg)
        return result

    def start_acq(self) -> FuncResult:
        try:
            self._ptr.BeginAcquisition()
            msg: str = f'{self}: Camera acquisition started.'
            spincam_logger.info(msg)
        except PySpin.SpinnakerException:
            pass
        if not self._ptr.IsStreaming():
            msg: str = f'{self}: Can\'t start camera acquisition.'
            spincam_logger.error(msg)
            return FuncResult.ERROR
        return FuncResult.SUCCESS

    def stop_acq(self) -> FuncResult:
        try:
            self._ptr.EndAcquisition()
            msg: str = f'{self}: Camera acquisition stopped.'
            spincam_logger.info(msg)
        except PySpin.SpinnakerException:
            pass
        if self._ptr.IsStreaming():
            msg: str = f'{self}: Can\'t stop camera acquisition.'
            spincam_logger.error(msg)
            return FuncResult.ERROR
        return FuncResult.SUCCESS

    def get_last_img(self) -> np.ndarray | None:
        with time_group(f'{self}: Image capture') as _:
            if not self._ptr.IsStreaming():
                msg: str = f'{self}: Acquisition not started. Call {self.__class__.__name__}.{self.start_acq.__name__}().'
                spincam_logger.error(msg)
                return None
            ms_timeout: int = 500
            stream_id: int = 0
            img_res: PySpin.ImagePtr = self._ptr.GetNextImage(ms_timeout, stream_id)
            if img_res.IsIncomplete():
                img_status: int = img_res.GetImageStatus()
                msg: str = f'{self}: Image incomplete with image status {img_status}.'
                spincam_logger.error(msg)
                return None
            img_array: np.ndarray = img_res.GetNDArray()
            img_res.Release()
        return img_array

    def clear(self) -> None:
        self.stop_acq()
        self._node_callback_reg.unregister_all()
        self._ptr.DeInit()
        del self._ptr

    def get_node_value(
        self,
        node_route: str
    ) -> tuple[FuncResult, Any]:
        node_ptr: NodePtr | None = self.get_node_ptr(node_route)
        if node_ptr is None:
            return FuncResult.ERROR, None
        ret: FuncResult
        name: Any
        ret, name = node_ptr.get_value()
        return ret, name

    def set_node_value(
        self,
        node_route: str,
        value: Any = None
    ) -> tuple[FuncResult, Any]:
        node_ptr: NodePtr | None = self.get_node_ptr(node_route)
        if node_ptr is None:
            return FuncResult.ERROR, None
        ret: FuncResult
        res: Any
        ret, res = node_ptr.set_value(value)
        return ret, res

    def update_nodes_default_values(
        self,
        default_values: dict[str, Any]
    ) -> Self:
        if not isinstance(default_values, dict):
            msg: str = f'{self}: Invalid node data. Expected "dict", got "{type(default_values)}".'
            spincam_logger.warning(msg)
            return self
        for route, default_val in default_values.items():
            current_node: NodePtr | None = self._node_ptrs.get(str(route), None)
            if current_node is None:
                msg: str = f'{self}: Can\'t find "{route}" in the camera nodes.'
                spincam_logger.error(msg)
                continue
            current_node.default_val = default_val
        return self

    def set_nodes_default_values(self) -> Self:
        for node_ptr in self._node_ptrs.values():
            node_ptr.set_value()
        return self

    def register_node_callback(
        self,
        node_route: str,
        func: NodeCallbackFunc
    ) -> FuncResult:
        node_ptr: NodePtr | None = self.get_node_ptr(node_route)
        if node_ptr is None:
            msg: str = f'{self}: Unable to register "{node_route}" node callback. Node not found.'
            spincam_logger.error(msg)
            return FuncResult.ERROR
        return self._node_callback_reg.register(
            func= func,
            node_ptr= node_ptr
        )

    def unregister_node_callback(
        self,
        node_route: str
    ) -> FuncResult:
        return self._node_callback_reg.unregister(route= node_route)

    def execute_node(self, node_route: str) -> FuncResult:
        node_ptr: NodePtr | None = self.get_node_ptr(node_route)
        if node_ptr is None:
            msg: str = f'{self}: Unable to execute "{node_route}" node. Node not found.'
            spincam_logger.error(msg)
            return FuncResult.ERROR
        return node_ptr.execute()


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
    for cam_serial_number in get_available_cam_names():
        cam_list_str += f'\n  • Camera "{cam_serial_number}"'
    cam_list_str += '\n'
    return cam_list_str

@contextmanager
def get_cam_list() -> Generator[PySpin.CameraList, None, None]:
    with get_sys() as system:
        try:
            cam_list: PySpin.CameraList = system.GetCameras()
            yield cam_list
        finally:
            try:
                cam_list.Clear()  # type: ignore
            except NameError:
                pass
            except PySpin.SpinnakerException:
                msg: str = 'Can\'t clear cameras list. Something still holds a reference.'
                spincam_logger.error(msg)
                raise RuntimeError(msg)
            msg: str = f'Cameras list cleared.'
            spincam_logger.debug(msg, Styles.SUCCEED)

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
