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

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Any

import numpy as np
import PySpin

from spincam.nodes import Node

from .callbacks.node_callbacks import NodeCallbackFunc, NodeCallbackReg
from .nodes import CategoryNode
from .schemas import FuncResult
from .utils.logs import spincam_logger
from .utils.timing import time_group

if TYPE_CHECKING:
    from .interface import Iface
    from .system import System


@dataclass
class CamConfigStep:
    step: int
    route: str
    value: Any

    def __lt__(self, other: CamConfigStep) -> bool:
        if not isinstance(other, CamConfigStep):
            return NotImplemented
        return self.step < other.step

    def __le__(self, other: CamConfigStep) -> bool:
        if not isinstance(other, CamConfigStep):
            return NotImplemented
        return self.step <= other.step

    def __gt__(self, other: CamConfigStep) -> bool:
        if not isinstance(other, CamConfigStep):
            return NotImplemented
        return self.step > other.step

    def __ge__(self, other: CamConfigStep) -> bool:
        if not isinstance(other, CamConfigStep):
            return NotImplemented
        return self.step >= other.step

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, CamConfigStep):
            raise NotImplementedError(f'{self.__class__.__name__} doesn\'t implement eq')
        return self.step == other.step


class CamConfigSeq:
    def __init__(self, steps: Iterable[Any] = ()) -> None:
        self._seq: list[CamConfigStep] = []
        self._seq.extend(steps)
        self._seq.sort()

    @property
    def seq(self) -> tuple[CamConfigStep, ...]:
        return tuple(self._seq)

    @seq.setter
    def seq(self, steps: Iterable[Any]) -> None:
        self._seq.clear()
        self._seq.extend(steps)
        self._seq.sort()

    def append(self, step: CamConfigStep) -> None:
        self._seq.append(step)
        self._seq.sort()

    def extend(self, steps: Iterable[Any]) -> None:
        for step in steps:
            if isinstance(step, CamConfigStep):
                self._seq.append(step)
                continue
            if isinstance(step, dict):
                self._seq.append(CamConfigStep(**step))
                continue
            if isinstance(step, Iterable):
                try:
                    self._seq.append(CamConfigStep(*step))
                except Exception as e:
                    msg: str = f'Can\'t create {CamConfigStep.__name__} from {step}. {e}'
                    spincam_logger.warning(msg)
                continue
        self._seq.sort()

    def __len__(self) -> int:
        return len(self._seq)

    def __getitem__(self, index: int) -> CamConfigStep:
        return self._seq[index]

    def __iter__(self) -> Iterator[CamConfigStep]:
        return iter(self._seq)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._seq})'


class Camera:
    def __init__(self, sys: System, iface_id: str, ptr: PySpin.CameraPtr) -> None:
        self._sys: System = sys
        self._iface_id: str = iface_id
        self._ptr: PySpin.CameraPtr = ptr
        self.init()
        self._node_ptrs: dict[str, Node] = self._root_node_ptrs()
        self._create_nodemap()
        self._node_callback_reg: NodeCallbackReg = NodeCallbackReg(
            sys= self._sys,
            parent_id= self.serial_number
        )
        self._config_seq: CamConfigSeq = CamConfigSeq()

    def __str__(self) -> str:
        return f'Camera {self.name}'

    def __repr__(self) -> str:
        return self.get_nodes_repr(['Device.Root.DeviceInformation'])

    @cached_property
    def name(self) -> str:
        return f'{self.model_name} ({self.serial_number})'

    @cached_property
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

    @cached_property
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
    def sys(self) -> System:
        return self._sys

    @property
    def iface(self) -> Iface | None:
        return self._sys.get_iface_by_id(self._iface_id)

    @property
    def nodemap(self) -> PySpin.INodeMap | None:
        try:
            if not self._ptr.IsInitialized():
                raise PySpin.SpinnakerException('Camera not initialized.')
            return self._ptr.GetNodeMap()
        except PySpin.SpinnakerException as e:
            msg: str = f'{self}: Can\'t get the NodeMap. {e}'
            spincam_logger.error(msg)
            return None

    @property
    def tl_device_nodemap(self) -> PySpin.INodeMap | None:
        try:
            if not self._ptr.IsInitialized():
                raise PySpin.SpinnakerException('Camera not initialized.')
            return self._ptr.GetTLDeviceNodeMap()
        except PySpin.SpinnakerException as e:
            msg: str = f'{self}: Can\'t get the TLDeviceNodeMap. {e}'
            spincam_logger.error(msg)
            return None

    @property
    def tl_stream_nodemap(self) -> PySpin.INodeMap | None:
        try:
            if not self._ptr.IsInitialized():
                raise PySpin.SpinnakerException('Camera not initialized.')
            return self._ptr.GetTLStreamNodeMap()
        except PySpin.SpinnakerException as e:
            msg: str = f'{self}: Can\'t get the TLStreamNodeMap. {e}'
            spincam_logger.error(msg)
            return None

    def _root_node_ptrs(self) -> dict[str, Node]:
        nodemap: PySpin.INodeMap | None = self.nodemap
        tl_device_nodemap: PySpin.INodeMap | None = self.tl_device_nodemap
        tl_stream_nodemap: PySpin.INodeMap | None = self.tl_stream_nodemap
        result: dict[str, Node] = {}
        if nodemap is not None:
            result['App.Root'] = CategoryNode(
                sys= self._sys,
                parent_id= self.serial_number,
                route= 'App.Root',
                nodemap= nodemap,
            )
        if tl_device_nodemap is not None:
            result['Device.Root'] = CategoryNode(
                sys= self._sys,
                parent_id= self.serial_number,
                route= 'Device.Root',
                nodemap= tl_device_nodemap,
            )
        if tl_stream_nodemap is not None:
            result['Stream.Root'] = CategoryNode(
                sys= self._sys,
                parent_id= self.serial_number,
                route= 'Stream.Root',
                nodemap= tl_stream_nodemap,
            )
        return result

    def _create_nodemap(self) -> None:
        root_node_ptrs: dict[str, Node] = self._node_ptrs.copy()
        for node_ptr in root_node_ptrs.values():
            new_nodes: dict[str, Node] = node_ptr.get_subnodes()
            self._node_ptrs.update(new_nodes)

    def _get_node_tree(self, node_name: str) -> str:
        node_ptr: Node | None = self.get_node_ptr(node_name)
        if node_ptr is None:
            return ''
        result: str = f'\n{"    "*(node_ptr.lvl+1)}• {node_ptr.route}'
        child_nodes_names: list[str] = [
            key
            for key, value in self._node_ptrs.items()
            if value.parent_node_route == node_name
        ]
        for child in child_nodes_names:
            result += self._get_node_tree(child)
        return result

    def init(self) -> FuncResult:
        try:
            self._ptr.Init()
            if not self._ptr.IsInitialized():
                msg: str = 'Camera not initialized.'
                raise PySpin.SpinnakerException(msg)
        except PySpin.SpinnakerException as e:
            msg: str = f'{self}: Unable to init. {e}'
            spincam_logger.error(msg)
            return FuncResult.ERROR
        return FuncResult.SUCCESS

    def clear(self) -> None:
        self.stop_acq()
        self.unregister_all_node_callbacks()
        self._ptr.DeInit()
        del self._ptr

    def get_nodes_repr(self, nodes: Iterable[str] | None = None) -> str:
        if nodes is None:
            nodes = tuple(self._root_node_ptrs().keys())
        result: str = f'\n{self}:'
        for node_name in nodes:
            result += self._get_node_tree(node_name)
        result += '\n'
        return result

    def get_node_ptr(self, route: str) -> Node | None:
        result: Node | None = self._node_ptrs.get(route, None)
        if result is None:
            msg: str = f'{self}: Can\'t find "{route}" in the camera nodes.'
            spincam_logger.error(msg)
        return result

    def start_acq(self) -> FuncResult:
        self.stop_acq()
        try:
            self._ptr.BeginAcquisition()
            if not self._ptr.IsStreaming():
                raise PySpin.SpinnakerException('Camera is not streaming.')
            msg: str = f'{self}: Camera acquisition started.'
            spincam_logger.info(msg)
        except Exception as e:
            msg: str = f'{self}: Can\'t start camera acquisition. {e}'
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

    def execute_node(self, route: str) -> FuncResult:
        node_ptr: Node | None = self.get_node_ptr(route)
        if node_ptr is None:
            msg: str = f'{self}: Unable to execute "{route}" node. Node not found.'
            spincam_logger.error(msg)
            return FuncResult.ERROR
        return node_ptr.execute()

    def get_node_value(self, route: str) -> tuple[FuncResult, Any]:
        node_ptr: Node | None = self.get_node_ptr(route)
        if node_ptr is None:
            return FuncResult.ERROR, None
        ret: FuncResult
        name: Any
        ret, name = node_ptr.get_value()
        return ret, name

    def set_node_value(
        self, route: str, value: Any = None) -> tuple[FuncResult, Any]:
        node_ptr: Node | None = self.get_node_ptr(route)
        if node_ptr is None:
            return FuncResult.ERROR, None
        ret: FuncResult
        res: Any
        ret, res = node_ptr.set_value(value)
        return ret, res

    def update_nodes_default_values(
        self,
        default_values: dict[str, Any]
    ) -> FuncResult:
        if not isinstance(default_values, dict):
            msg: str = f'{self}: Invalid node data. Expected "dict", got "{type(default_values)}".'
            spincam_logger.warning(msg)
            return FuncResult.ERROR
        fun_res: FuncResult = FuncResult.SUCCESS
        for route, default_val in default_values.items():
            current_node: Node | None = self._node_ptrs.get(str(route), None)
            if current_node is None:
                msg: str = f'{self}: Can\'t find "{route}" in the camera nodes.'
                spincam_logger.error(msg)
                fun_res &= FuncResult.ERROR
                continue
            current_node.default_val = default_val
        return fun_res

    def set_nodes_default_values(self) -> FuncResult:
        fun_res: FuncResult = FuncResult.SUCCESS
        for node_ptr in self._node_ptrs.values():
            ret: FuncResult
            res: Any
            ret, res = node_ptr.set_value()
            fun_res &= ret
        return fun_res

    def set_config_seq(self, steps: Iterable[Any]) -> FuncResult:
        try:
            self._config_seq = CamConfigSeq(steps)
        except Exception as e:
            msg: str = f'{self}: Unable to set the configuration sequence. {e}'
            spincam_logger.error(msg)
            return FuncResult.ERROR
        return FuncResult.SUCCESS

    def execute_config_seq(self) -> FuncResult:
        result: FuncResult = FuncResult.SUCCESS
        for step in self._config_seq.seq:
            ret: FuncResult
            res: Any
            ret, res = self.set_node_value(
                route= step.route,
                value= step.value
            )
            result &= ret
        return result

    def register_node_callback(
        self,
        route: str,
        callback: NodeCallbackFunc
    ) -> FuncResult:
        return self._node_callback_reg.register(
            route= route,
            callback= callback
        )

    def unregister_node_callback(self, route: str) -> FuncResult:
        return self._node_callback_reg.unregister(route= route)

    def unregister_all_node_callbacks(self) -> FuncResult:
        return self._node_callback_reg.unregister_all()


class CameraReg:
    def __init__(self, sys: System, iface_id: str) -> None:
        self._sys: System = sys
        self._iface_id: str = iface_id
        self._cams: dict[str, Camera] = {}

    @property
    def cams(self) -> dict[str, Camera]:
        return self._cams

    @property
    def sys(self) -> System:
        return self._sys

    @property
    def iface(self) -> Iface | None:
        return self._sys.get_iface_by_id(self._iface_id)

    def clear(self) -> None:
        for cam in self._cams.values():
            cam.clear()
        try:
            del cam  # type: ignore
        except NameError:
            pass
        del self._cams

    def get(self, serial_number: str) -> Camera | None:
        cam: Camera | None = self._cams.get(serial_number, None)
        return cam

    def update(self, cam_list: PySpin.CameraList) -> FuncResult:
        current_cams: dict[str, Camera] = {
            cam.serial_number: cam
            for cam in [
                Camera(sys= self._sys, iface_id= self._iface_id, ptr= cam_ptr)
                for cam_ptr in cam_list
            ]
        }
        to_rm: set[str] = set(self._cams.keys()) - set(current_cams.keys())
        to_add: set[str] =  set(current_cams.keys()) - set(self._cams.keys())
        ret: FuncResult = FuncResult.SUCCESS
        for cam_serial_number in to_rm:
            ret &= self.unregister(cam_serial_number)
        for cam_serial_number in to_add:
            self._cams[cam_serial_number] = current_cams[cam_serial_number]
        del current_cams
        return ret

    def register(self, cam_ptr: PySpin.CameraPtr) -> FuncResult:
        cam: Camera = Camera(
            sys= self._sys,
            iface_id= self._iface_id,
            ptr= cam_ptr
        )
        if cam.serial_number in self._cams.keys():
            del cam
            return FuncResult.ERROR
        self._cams[cam.serial_number] = cam
        return FuncResult.SUCCESS

    def unregister(self, serial_number: str) -> FuncResult:
        cam: Camera | None = self._cams.pop(serial_number, None)
        if cam is None:
            msg: str = f'{self.iface}: Can\'t unregister camera "{serial_number}". Camera not found.'
            spincam_logger.warning(msg)
            return FuncResult.SUCCESS
        cam.clear()
        del cam
        return FuncResult.SUCCESS


def get_cam_list_repr(cams: Iterable[Camera]) -> str:
    cam_list_str = '\nCameras list:'
    for cam in cams:
        cam_list_str += f'\n  • {cam}'
    cam_list_str += '\n'
    return cam_list_str
