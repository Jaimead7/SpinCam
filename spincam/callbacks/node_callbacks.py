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
from functools import cached_property
from typing import TYPE_CHECKING, Protocol

import PySpin

from ..nodes import NodePtr
from ..schemas import FuncResult
from ..utils.logs import spincam_logger

if TYPE_CHECKING:
    from ..camera import Camera
    from ..interface import Iface
    from ..system import System


class NodeCallbackFunc(Protocol):
    def __call__(self, node: NodePtr) -> FuncResult: ...


class NodeCallback(PySpin.NodeCallback):
    def __init__(
        self,
        sys: System,
        parent_id: str,
        route: str,
        callback: NodeCallbackFunc,
    ) -> None:
        self._sys: System = sys
        self._parent_id: str = parent_id
        self._route: str = route
        self._callback: NodeCallbackFunc = callback
        super().__init__()

    @cached_property
    def parent(self) -> Iface | Camera | None:
        ret: Iface | Camera | None = None
        ret = self._sys.get_cam_by_serial_number(self._parent_id)
        if ret is None:
            ret = self._sys.get_iface_by_id(self._parent_id)
        return ret

    def CallbackFunction(self, node: PySpin.INode) -> None:
        try:
            parent: Iface | Camera | None = self.parent
            if parent is None:
                msg: str = 'Error getting node parent.'
                raise ValueError(msg)
            parent_node: NodePtr | None = parent.get_node_ptr(self._route)
            if parent_node is None:
                msg: str = f'Error getting node {self._route} from {self._parent_id}.'
                raise ValueError(msg)
            threading.Thread(
                target= self._callback,
                args=(parent_node,),
                daemon= True
            ).start()
        except Exception as e:
            msg: str = f'{self.parent}: Unable to execute CallbackFunction for node {self._route}. {e}'
            spincam_logger.error(msg)

    def register(self) -> FuncResult:
        try:
            parent: Iface | Camera | None = self.parent
            if parent is None:
                msg: str = 'Error getting node parent.'
                raise ValueError(msg)
            parent_node: NodePtr | None = parent.get_node_ptr(self._route)
            if parent_node is None:
                msg: str = f'Error getting node {self._route} from {self._parent_id}.'
                raise ValueError(msg)
            PySpin.RegisterNodeCallback(parent_node.get_node(), self)
        except Exception as e:
            msg: str = f'{self.parent}: Unable to register "{self._route}" node callback. {e}.'
            spincam_logger.error(msg)
            return FuncResult.ERROR
        msg: str = f'{self.parent}: "{self._route}" node callback registered.'
        spincam_logger.info(msg)
        return FuncResult.SUCCESS

    def unregister(self) -> FuncResult:
        try:
            PySpin.DeregisterNodeCallback(self)
        except PySpin.SpinnakerException as e:
            msg: str = f'{self.parent}: Unable to unregister "{self._route}" node callback. {e}.'
            spincam_logger.error(msg)
            return FuncResult.ERROR
        msg: str = f'{self.parent}: "{self._route}" node callback unregistered.'
        spincam_logger.info(msg)
        return FuncResult.SUCCESS


class NodeCallbackReg:
    def __init__(self, sys: System, parent_id: str) -> None:
        self._sys: System = sys
        self._parent_id: str = parent_id
        self._callbacks: dict[str, NodeCallback] = {}

    @property
    def parent(self) -> Iface | Camera | None:
        return self._sys.get_cam_by_serial_number(self._parent_id)

    @property
    def callbacks(self) -> dict[str, NodeCallback]:
        return self._callbacks

    def register(self, route: str, callback: NodeCallbackFunc) -> FuncResult:
        if route in self._callbacks.keys():
            msg: str = f'{self.parent}: Callback for "{route}" has already been registered. It will be overwritten.'
            spincam_logger.warning(msg)
            self._callbacks[route].unregister()
        self._callbacks[route] = NodeCallback(
            sys= self._sys,
            parent_id= self._parent_id,
            route= route,
            callback= callback,
        )
        return self._callbacks[route].register()

    def unregister(self, route: str) -> FuncResult:
        callback: NodeCallback | None = self._callbacks.pop(route, None)
        if callback is None:
            msg: str = f'{self.parent}: Unable to unregister "{route}" callback. Callback not found.'
            spincam_logger.warning(msg)
            return FuncResult.SUCCESS
        return callback.unregister()

    def unregister_all(self) -> None:
        for callback in self._callbacks.values():
            callback.unregister()
