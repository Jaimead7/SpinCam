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

from collections.abc import Iterable
from functools import cached_property
from typing import TYPE_CHECKING, Any

import PySpin

from .callbacks.iface_callbacks import (IfaceEventCallback,
                                        InterfaceEventHandler)
from .camera import Camera, CameraReg
from .nodes import CategoryPtr, NodePtr, NodePtrReg
from .schemas import FuncResult
from .utils.logs import spincam_logger

if TYPE_CHECKING:
    from .system import System


class Iface:
    def __init__(
        self,
        sys: System,
        ptr: PySpin.InterfacePtr
    ) -> None:
        self._sys: System = sys
        self._ptr: PySpin.InterfacePtr = ptr
        self._node_ptrs: dict[str, NodePtr] = self._root_node_ptrs()
        self._create_nodemap()
        self._cam_reg = CameraReg(self._sys, self.id)
        self._iface_events: InterfaceEventHandler = InterfaceEventHandler(
            sys= self._sys,
            iface_id= self.id
        )

    def __str__(self) -> str:
        return f'Interface {self.name}'

    def __repr__(self) -> str:
        return self.get_nodes_repr()

    @cached_property
    def name(self) -> str:
        return f'{self.display_name} ({self.id})'

    @cached_property
    def id(self) -> str:
        try:
            raw_node: PySpin.INode = self.nodemap.GetNode('InterfaceID')
            iface_type: Any = raw_node.GetPrincipalInterfaceType()
            NODE_PTR_TYPE: type[NodePtr] = NodePtrReg.get(iface_type)
            interface_id_node: NodePtr = NODE_PTR_TYPE(
                route= 'Transport.Root.InterfaceInformation.InterfaceID',
                parent_name= 'Unknown',
                nodemap= self.nodemap
            )
            ret: FuncResult
            value: Any
            ret, value = interface_id_node.get_value()
            return str(value)
        except (PySpin.SpinnakerException, ValueError) as e:
            msg: str = f'Can\'t get the interface ID. {e}'
            spincam_logger.warning(msg)
            return 'Unknown'

    @cached_property
    def display_name(self) -> str:
        try:
            raw_node: PySpin.INode = self.nodemap.GetNode('InterfaceDisplayName')
            iface_type: Any = raw_node.GetPrincipalInterfaceType()
            NODE_PTR_TYPE: type[NodePtr] = NodePtrReg.get(iface_type)
            display_name_node: NodePtr = NODE_PTR_TYPE(
                route= 'Transport.Root.InterfaceInformation.InterfaceDisplayName',
                parent_name= 'Unknown',
                nodemap= self.nodemap
            )
            ret: FuncResult
            value: Any
            ret, value = display_name_node.get_value()
            return str(value)
        except (PySpin.SpinnakerException, ValueError) as e:
            msg: str = f'Can\'t get the interface display name. {e}'
            spincam_logger.warning(msg)
            return 'Unknown'

    @cached_property
    def nodemap(self) -> PySpin.INodeMap:
        try:
            return self._ptr.GetTLNodeMap()
        except PySpin.SpinnakerException as e:
            msg: str = f'{self}: Can\'t get the NodeMap. {e}'
            spincam_logger.error(msg)
            raise RuntimeError(msg)

    @property
    def cams(self) -> Iterable[Camera]:
        self.update_cams()
        return self._cam_reg.cams.values()

    @property
    def cams_serial_numbers(self) -> Iterable[str]:
        self.update_cams()
        return self._cam_reg.cams.keys()

    def _root_node_ptrs(self) -> dict[str, NodePtr]:
        return {
            'Transport.Root': CategoryPtr(
                route= 'Transport.Root',
                parent_name= str(self),
                nodemap= self.nodemap
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

    def clear(self) -> None:
        self._cam_reg.clear()
        del self._cam_reg
        self.unregister_events()
        del self._iface_events
        del self._ptr

    def update_cams(self) -> None:
        try:
            cam_list: PySpin.CameraList = self._ptr.GetCameras()
            self._cam_reg.update(cam_list)
        except PySpin.SpinnakerException as e:
            msg: str = f'{self}: Can\'t update cameras. {e}'
            spincam_logger.warning(msg)
        finally:
            try:
                cam_list.Clear()  # type: ignore
            except (NameError, PySpin.SpinnakerException):
                pass
            try:
                del cam_list  # type: ignore
            except NameError:
                pass

    def get_nodes_repr(self, nodes: Iterable[str] | None = None) -> str:
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
            msg: str = f'{self}: Can\'t find "{route}" in the interface nodes.'
            spincam_logger.error(msg)
        return result

    def get_cam_by_serial_number(self, serial_number: str) -> Camera | None:
        self.update_cams()
        return self._cam_reg.get(serial_number)

    def register_device_events(
        self,
        device_arrival_callback: IfaceEventCallback | None = None,
        device_removal_callback: IfaceEventCallback | None = None
    ) -> FuncResult:
        self.unregister_events()
        self._iface_events.set_arr_callback(device_arrival_callback)
        self._iface_events.set_rm_callback(device_removal_callback)
        try:
            self._ptr.RegisterEventHandler(self._iface_events)
        except PySpin.SpinnakerException as e:
            msg: str = f'{self}: Can\'t register device events. {e}'
            spincam_logger.error(msg)
            return FuncResult.ERROR
        return FuncResult.SUCCESS

    def unregister_events(self) -> FuncResult:
        try:
            self._ptr.UnregisterEventHandler(self._iface_events)
        except PySpin.SpinnakerException as e:
            if e.errorcode not in (-1003, -1014,):
                msg: str = f'{self}: Can\'t unregister device events. {e}'
                spincam_logger.warning(msg)
                return FuncResult.ERROR
        return FuncResult.SUCCESS


class IfaceReg:
    def __init__(self, sys: System) -> None:
        self._sys: System = sys
        self._ifaces: dict[str, Iface] = {}

    @property
    def ifaces(self) -> dict[str, Iface]:
        return self._ifaces

    def clear(self) -> None:
        for iface in self._ifaces.values():
            iface.clear()
        try:
            del iface  # type: ignore
        except NameError:
            pass
        del self._ifaces

    def get(self, id: str) -> Iface | None:
        iface: Iface | None = self._ifaces.get(id, None)
        if iface is None:
            msg: str = f'Interface "{id}" not found.'
            spincam_logger.warning(msg)
        return iface

    def update(self, iface_list: PySpin.InterfaceList) -> FuncResult:
        current_ifaces: dict[str, Iface] = {
            iface.id: iface
            for iface in [
                Iface(sys= self._sys, ptr= iface_ptr)
                for iface_ptr in iface_list
            ]
        }
        to_rm: set[str] = set(self._ifaces.keys()) - set(current_ifaces.keys())
        to_add: set[str] = set(current_ifaces.keys()) - set(self._ifaces.keys())
        ret: FuncResult = FuncResult.SUCCESS
        for iface_id in to_rm:
            ret &= self.unregister(iface_id)
        for iface_id in to_add:
            self._ifaces[iface_id] = current_ifaces[iface_id]
        del current_ifaces
        return ret

    def register(self, iface_ptr: PySpin.InterfacePtr) -> FuncResult:
        iface: Iface = Iface(sys= self._sys, ptr= iface_ptr)
        if iface.id in self._ifaces.keys():
            del iface
            return FuncResult.ERROR
        self._ifaces[iface.id] = iface
        return FuncResult.SUCCESS

    def unregister(self, id: str) -> FuncResult:
        iface: Iface | None = self._ifaces.pop(id, None)
        if iface is None:
            msg: str = f'Interface "{id}" not found.'
            spincam_logger.warning(msg)
            return FuncResult.SUCCESS
        iface.clear()
        del iface
        return FuncResult.SUCCESS


def get_iface_list_repr(ifaces: Iterable[Iface]) -> str:
    iface_list_str = '\nInterfaces list:'
    for iface in ifaces:
        iface_list_str += f'\n  • {iface}'
    iface_list_str += '\n'
    return iface_list_str
