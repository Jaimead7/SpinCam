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

import PySpin

from .nodes import CategoryPtr, NodePtr, NodePtrReg
from .schemas import FuncResult
from .system import get_sys
from .utils.logs import Styles, spincam_logger


class Iface:
    def __init__(self, ptr: PySpin.InterfacePtr) -> None:
        self._ptr: PySpin.InterfacePtr = ptr
        self._node_ptrs: dict[str, NodePtr] = self._root_node_ptrs()
        self._create_nodemap()

    def __str__(self) -> str:
        return f'Iface {self.name}'

    def __repr__(self) -> str:
        return self.get_nodes_repr()

    @property
    def name(self) -> str:
        return f'{self.display_name} ({self.id})'

    @property
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

    @property
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

    @property
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
            msg: str = f'{self}: Can\'t find "{route}" in the interface nodes.'
            spincam_logger.error(msg)
        return result

    def clear(self) -> None:
        del self._ptr


def get_available_iface_ids() -> list[str]:
    _list: list = []
    with get_iface_list() as iface_list:
        num_ifaces: int = iface_list.GetSize()
        if num_ifaces == 0:
            msg: str = 'Didn\'t find any interface.'
            spincam_logger.error(msg)
            raise RuntimeError(msg)
        msg: str = f'Found {num_ifaces} {"interface" if num_ifaces == 1 else "interfaces"}.'
        spincam_logger.info(msg)
        for iface_ptr in iface_list:
            iface = Iface(iface_ptr)
            _list.append(iface.id)
            iface.clear()
        try:
            del iface_ptr  # type: ignore
        except NameError:
            pass
    return _list

def get_available_ifaces_names() -> list[str]:
    _list: list = []
    with get_iface_list() as iface_list:
        num_ifaces: int = iface_list.GetSize()
        if num_ifaces == 0:
            msg: str = 'Didn\'t find any interface.'
            spincam_logger.error(msg)
            raise RuntimeError(msg)
        msg: str = f'Found {num_ifaces} {"interface" if num_ifaces == 1 else "interfaces"}.'
        spincam_logger.info(msg)
        for iface_ptr in iface_list:
            iface = Iface(iface_ptr)
            _list.append(iface.name)
            iface.clear()
        try:
            del iface_ptr  # type: ignore
        except NameError:
            pass
    return _list

def get_iface_list_repr() -> str:
    iface_list_str = '\nInterfaces list:'
    for iface_name in get_available_ifaces_names():
        iface_list_str += f'\n  • {iface_name}'
    iface_list_str += '\n'
    return iface_list_str

@contextmanager
def get_iface_list() -> Generator[PySpin.InterfaceList, None, None]:
    with get_sys() as system:
        try:
            iface_list: PySpin.InterfaceList = system.GetInterfaces()
            yield iface_list
        finally:
            try:
                iface_list.Clear()  # type: ignore
            except NameError:
                pass
            except PySpin.SpinnakerException:
                msg: str = 'Can\'t clear interfaces list. Something still holds a reference.'
                spincam_logger.error(msg)
                raise RuntimeError(msg)
            msg: str = f'Interfaces list cleared.'
            spincam_logger.debug(msg, Styles.SUCCEED)


@contextmanager
def get_iface(id: str) -> Generator[Iface, None, None]:
    with get_iface_list() as iface_list:
        try:
            ptr: PySpin.InterfacePtr = iface_list.GetByInterfaceID(id)
            iface = Iface(ptr)
            del ptr
            yield iface
        except RuntimeError:
            raise
        except ValueError:
            raise
        finally:
            try:
                iface.clear()  # type: ignore
            except NameError:
                pass
            msg: str = f'Interface "{id}" cleared.'
            spincam_logger.debug(msg, Styles.SUCCEED)
