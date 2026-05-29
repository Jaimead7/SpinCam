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


from collections.abc import Iterable
from functools import cached_property
from typing import Any

import PySpin

from .nodes import CategoryPtr, NodePtr, NodePtrReg
from .schemas import FuncResult
from .utils.logs import spincam_logger


class Iface:
    def __init__(self, ptr: PySpin.InterfacePtr) -> None:
        self._ptr: PySpin.InterfacePtr = ptr
        self._node_ptrs: dict[str, NodePtr] = self._root_node_ptrs()
        self._create_nodemap()

    def __str__(self) -> str:
        return f'Iface {self.name}'

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

    def clear(self) -> None:
        del self._ptr


class IfaceReg:
    def __init__(self) -> None:
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
            spincam_logger.error(msg)
            return None
        return iface

    def register(self, iface_ptr: PySpin.InterfacePtr) -> FuncResult:
        iface: Iface = Iface(iface_ptr)
        if iface.id in self._ifaces.keys():
            iface.clear()
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
    for iface_name in ifaces:
        iface_list_str += f'\n  • {iface_name}'
    iface_list_str += '\n'
    return iface_list_str
