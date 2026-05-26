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


from collections.abc import Callable
from typing import TypeAlias

import PySpin

from .nodes import NodePtr
from .schemas import FuncResult
from .utils.logs import spincam_logger

NodeCallbackFunc: TypeAlias = Callable[[NodePtr], FuncResult]


class NodeCallback(PySpin.NodeCallback):
    def __init__(
        self,
        cam_name: str,
        func: NodeCallbackFunc,
        node_ptr: NodePtr
    ) -> None:
        self._cam_name: str = cam_name
        self._func = func
        self._node_ptr: NodePtr = node_ptr
        super().__init__()

    @property
    def cam_name(self) -> str:
        return self._cam_name.strip()

    def CallbackFunction(self, node: PySpin.INode) -> None:
        self._func(self._node_ptr)

    def register(self) -> FuncResult:
        try:
            PySpin.RegisterNodeCallback(self._node_ptr.get_node(), self)
        except PySpin.SpinnakerException as e:
            msg: str = f'{self.cam_name}: Unable to register "{self._node_ptr.name}" node callback. {e}.'
            spincam_logger.error(msg)
            return FuncResult.ERROR
        msg: str = f'{self.cam_name}: "{self._node_ptr.name}" node callback registered.'
        spincam_logger.info(msg)
        return FuncResult.SUCCESS

    def unregister(self) -> FuncResult:
        try:
            PySpin.DeregisterNodeCallback(self)
        except PySpin.SpinnakerException as e:
            msg: str = f'{self.cam_name}: Unable to unregister "{self._node_ptr.name}" node callback. {e}.'
            spincam_logger.error(msg)
            return FuncResult.ERROR
        msg: str = f'{self.cam_name}: "{self._node_ptr.name}" node callback unregistered.'
        spincam_logger.info(msg)
        return FuncResult.SUCCESS


class NodeCallbackReg:
    def __init__(self, cam_name: str) -> None:
        self._cam_name: str = cam_name
        self._callbacks: dict[str, NodeCallback] = {}

    @property
    def cam_name(self) -> str:
        return self._cam_name.strip()

    @property
    def callbacks(self) -> dict[str, NodeCallback]:
        return self._callbacks

    def register(self, func: NodeCallbackFunc, node_ptr: NodePtr) -> FuncResult:
        node_route: str = node_ptr.route
        if node_route in self._callbacks.keys():
            msg: str = f'{self.cam_name}: Callback for "{node_ptr.name}" has already been registered. It will be overwritten.'
            spincam_logger.warning(msg)
            self._callbacks[node_route].unregister()
        self._callbacks[node_route] = NodeCallback(
            cam_name= self.cam_name,
            func= func,
            node_ptr= node_ptr
        )
        return self._callbacks[node_route].register()

    def unregister(self, route: str) -> FuncResult:
        callback: NodeCallback | None = self._callbacks.get(route, None)
        if callback is None:
            msg: str = f'{self.cam_name}: Unable to unregister "{route}" callback. Callback not found.'
            spincam_logger.warning(msg)
            return FuncResult.SUCCESS
        return callback.unregister()

    def unregister_all(self) -> None:
        for callback in self._callbacks.values():
            callback.unregister()
