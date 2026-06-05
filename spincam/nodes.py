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

from collections.abc import Callable, Sequence
from functools import cached_property
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Protocol, TypeVar

import PySpin
from typing_extensions import Self

from .schemas import NODE_PTR_TYPES, FuncResult, NodeStatus
from .utils.logs import spincam_logger

if TYPE_CHECKING:
    from .camera import Camera
    from .interface import Iface
    from .system import System


class GenericNode(Protocol):
    def __init__(self, *args) -> None: ...
    def GetDisplayName(self) -> str: ...
    def GetNode(self) -> PySpin.INode: ...


T = TypeVar('T', bound= GenericNode)


class Node(Generic[T]):
    PYSPIN_CLS: ClassVar[type[GenericNode]]
    node: T

    def __init__(
        self,
        *,
        sys: System,
        parent_id: str,
        route: str,
        nodemap: PySpin.INodeMap,
        default_val: Any = None,
    ) -> None:
        self._sys: System = sys
        self._parent_id: str = parent_id
        self._route: str = route
        self._nodemap: PySpin.INodeMap = nodemap
        self._status: NodeStatus = NodeStatus.UNKNOWN
        self.default_val: Any = default_val
        self.lvl: int = max(route.count('.') - 1, 0)

    def __str__(self) -> str:
        ret: FuncResult
        value: Any
        ret, value = self.get_value()
        if ret.is_error():
            value = ''
        return f'{self.display_name}: type= "{self.__class__.__name__}", value="{value}", default="{self.default_val}"'

    def __repr__(self) -> str:
        result: str = f'{self.__class__.__name__}'
        result += f'(route="{self.route}", camera="{self.parent}", status="{self.status}" default="{self.default_val}")'
        return result

    @cached_property
    def parent(self) -> Iface | Camera | None:
        ret: Iface | Camera | None = None
        ret = self._sys.get_cam_by_serial_number(self._parent_id)
        if ret is None:
            ret = self._sys.get_iface_by_id(self._parent_id)
        return ret

    @cached_property
    def name(self) -> str:
        return self.route.split('.')[-1].strip()

    @cached_property
    def parent_node_route(self) -> str:
        return '.'.join(self.route.split('.')[:-1]).strip()

    @cached_property
    def route(self) -> str:
        return self._route

    @property
    def nodemap(self) -> PySpin.INodeMap:
        return self._nodemap

    @property
    def status(self) -> NodeStatus:
        self._update_status()
        return self._status

    @cached_property
    def display_name(self) -> str:
        try:
            display_name: str = self.node.GetDisplayName()
            if display_name == 'Root':
                display_name = self.parent_node_route
            return display_name
        except PySpin.SpinnakerException:
            msg: str = f'{self.parent}: Unable to get display name for "{self.name}" node.'
            spincam_logger.error(msg)
            return self.name

    def _update_status(self) -> None:
        try:
            self._status = NodeStatus.get_status(
                read= PySpin.IsReadable(self.node),
                write= PySpin.IsWritable(self.node)
            )
        except Exception:
            self._status = NodeStatus.UNKNOWN

    def get_node(self) -> PySpin.INode:
        return self.node.GetNode()

    # CategoryPtr
    def get_subnodes(self) -> dict[str, Self]:
        msg: str = f'{self.parent}: "{self.__class__.__name__}" nodes don\'t have subnodes.'
        spincam_logger.warning(msg)
        return {}

    def get_features(self) -> tuple[FuncResult, Sequence[PySpin.IValue]]:
        msg: str = f'{self.parent}: Features not defined for "{self.__class__.__name__}" nodes.'
        spincam_logger.warning(msg)
        return FuncResult.ERROR, []

    def get_childrens(self) -> tuple[FuncResult, Sequence[PySpin.INode]]:
        msg: str = f'{self.parent}: Childrens not defined for "{self.__class__.__name__}" nodes.'
        spincam_logger.warning(msg)
        return FuncResult.ERROR, []

    # Value Ptr's
    def get_value(self) -> tuple[FuncResult, Any]:
        msg: str = f'{self.parent}: Value not defined for "{self.__class__.__name__}" nodes.'
        spincam_logger.warning(msg)
        return FuncResult.ERROR, None

    def set_value(self, value: Any = None) -> tuple[FuncResult, Any]:
        if value is None:
            return FuncResult.ERROR, None
        msg: str = f'{self.parent}: Value not defined for "{self.__class__.__name__}" nodes.'
        spincam_logger.warning(msg)
        return FuncResult.ERROR, None

    # Command Ptr's
    def execute(self) -> FuncResult:
        msg: str = f'{self.parent}: Execute not defined for "{self.__class__.__name__}" nodes.'
        spincam_logger.warning(msg)
        return FuncResult.ERROR


class NodeTypes:
    _ptrs: ClassVar[dict[str, type[Node]]] = {}

    def __new__(cls) -> Self:
        msg: str = f'"{cls.__name__}" is not instantiable.'
        spincam_logger.critical(msg)
        raise RuntimeError(msg)

    @staticmethod
    def _parse_name(name: Any) -> str:
        return str(name).upper()

    @classmethod
    def register(cls, name: Any) -> Callable[[type[Node]], type[Node]]:
        name = cls._parse_name(name)
        def decorator(cls_type: type[Node]) -> type[Node]:
            if name in cls._ptrs:
                msg: str = f'NodePtr "{name}" is already registered. It will be overwritten.'
                spincam_logger.warning(msg)
            cls._ptrs[name] = cls_type
            msg: str = f'NodePtr "{name}" registered.'
            spincam_logger.debug(msg)
            return cls_type
        return decorator

    @classmethod
    def unregister(cls, name: Any) -> None:
        name = cls._parse_name(name)
        result: type[Node] | None = cls._ptrs.pop(name, None)
        if result is not None:
            msg: str = f'NodePtr "{name}" unregistered.'
            spincam_logger.debug(msg)

    @classmethod
    def get(cls, name: Any) -> type[Node]:
        name = cls._parse_name(name)
        ptr_cls: type[Node] | None = cls._ptrs.get(name, None)
        if ptr_cls is None:
            msg: str = f'"{name}" is not a valid NodePtr.'
            spincam_logger.error(msg)
            raise ValueError(msg)
        return ptr_cls

    @classmethod
    def list(cls) -> list[str]:
        return sorted(cls._ptrs.keys())

    @classmethod
    def clear(cls) -> None:
        cls._ptrs.clear()


@NodeTypes.register(NODE_PTR_TYPES.CATEGORY.value)
class CategoryNode(Node[PySpin.CCategoryPtr]):
    PYSPIN_CLS = PySpin.CCategoryPtr

    def __init__(
        self,
        *,
        sys: System,
        parent_id: str,
        route: str,
        nodemap: PySpin.INodeMap,
        default_val: Any = None,
    ) -> None:
        super().__init__(
            sys= sys,
            parent_id= parent_id,
            route= route,
            nodemap= nodemap,
            default_val= default_val
        )
        raw_node: PySpin.INode = nodemap.GetNode(self.name)
        self.node: PySpin.CCategoryPtr = PySpin.CCategoryPtr(raw_node)
        self._update_status()

    def get_value(self) -> tuple[FuncResult, Any]:
        return FuncResult.SUCCESS, ''

    def get_features(self) -> tuple[FuncResult, Sequence[PySpin.IValue]]:
        try:
            features: Sequence[PySpin.IValue] = self.node.GetFeatures()
        except PySpin.SpinnakerException as e:
            msg: str = f'{self.parent}: Can\'t extract features from {self.name} node. {e}'
            spincam_logger.error(msg)
            return FuncResult.ERROR, []
        return FuncResult.SUCCESS, features

    def get_childrens(self) -> tuple[FuncResult, Sequence[PySpin.INode]]:
        try:
            childrens: Sequence[PySpin.IValue] = self.node.GetChildren()
        except PySpin.SpinnakerException as e:
            msg: str = f'{self.parent}: Can\'t get childrens from {self.name} node. {e}'
            spincam_logger.error(msg)
            return FuncResult.ERROR, []
        return FuncResult.SUCCESS, childrens

    def get_subnodes(self) -> dict[str, Node]:
        result: dict[str, Node] = {}
        ret: FuncResult
        childrens: Sequence[PySpin.INode]
        ret, childrens = self.get_childrens()
        if ret.is_error():
            return result
        for child in childrens:
            name: str = child.GetName()
            iface_type: Any = child.GetPrincipalInterfaceType()
            try:
                NODE_PTR_TYPE: type[Node] = NodeTypes.get(iface_type)
            except ValueError:
                continue
            node_ptr: Node = NODE_PTR_TYPE(
                sys= self._sys,
                parent_id= self._parent_id,
                route= f'{self.route}.{name}',
                nodemap= self.nodemap,
            )
            result[node_ptr.route] = node_ptr
            if NODE_PTR_TYPE == self.__class__:
                subnodes: dict[str, Node] = node_ptr.get_subnodes()
                result.update(subnodes)
        return result


@NodeTypes.register(NODE_PTR_TYPES.ENUM.value)
class EnumerationNode(Node[PySpin.CEnumerationPtr]):
    PYSPIN_CLS = PySpin.CEnumerationPtr

    def __init__(
        self,
        *,
        sys: System,
        parent_id: str,
        route: str,
        nodemap: PySpin.INodeMap,
        default_val: Any = None,
    ) -> None:
        super().__init__(
            sys= sys,
            parent_id= parent_id,
            route= route,
            nodemap= nodemap,
            default_val= default_val
        )
        raw_node: PySpin.INode = nodemap.GetNode(self.name)
        self.node = PySpin.CEnumerationPtr(raw_node)
        self._update_status()

    def _get_int_value(self, value: str) -> int:
        try:
            entry: PySpin.IEnumEntry = self.node.GetEntryByName(value)
            if entry is None:
                raise PySpin.SpinnakerException('Option not found.')
            node_opt = PySpin.CEnumEntryPtr(entry)
            if not PySpin.IsReadable(node_opt):
                raise PySpin.SpinnakerException('It is not a readeble node.')
            return node_opt.GetValue()
        except PySpin.SpinnakerException as e:
            msg: str = f'{self.parent}: Couldn\'t get "{value}" option from "{self.name}" node. {e}'
            spincam_logger.error(msg)
            return -1

    def _validate_value(self, value: Any) -> int:
        if value is None:
            msg: str = f'"None" is not a valid value.'
            raise ValueError(msg)
        int_value: int = self._get_int_value(str(value))
        if int_value < 0:
            msg: str = f'"{value}" is not a valid value.'
            raise ValueError(msg)
        return int_value

    def get_value(self) -> tuple[FuncResult, Any]:
        if not self.status.can_read():
            msg: str = f'{self.parent}: Unable to get "{self.name}" node. It is not a read node.'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        value: str = self.node.GetCurrentEntry().GetSymbolic()
        return FuncResult.SUCCESS, value

    def set_value(self, value: Any = None) -> tuple[FuncResult, Any]:
        if value is None:
            value = self.default_val
        if value is None:
            return FuncResult.ERROR, None
        try:
            int_value: int = self._validate_value(value)
        except ValueError as e:
            msg: str = f'{self.parent}: Unable to set "{self.name}" node. {e}'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        if not self.status.can_write():
            msg: str = f'{self.parent}: Unable to set "{self.name}" node. It is not a write node.'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        try:
            self.node.SetIntValue(int_value)
        except PySpin.SpinnakerException as e:
            msg: str = f'{self.parent}: Unable to set "{value}" to "{self.name}" node. {e}'
            spincam_logger.error(msg)
            return FuncResult.ERROR, None
        ret: FuncResult
        ret, value = self.get_value()
        msg: str = f'{self.parent}: "{self.name}" set to "{value}".'
        spincam_logger.info(msg)
        return FuncResult.SUCCESS, value


@NodeTypes.register(NODE_PTR_TYPES.BOOL.value)
class BoolNode(Node[PySpin.CBooleanPtr]):
    PYSPIN_CLS = PySpin.CBooleanPtr

    def __init__(
        self,
        *,
        sys: System,
        parent_id: str,
        route: str,
        nodemap: PySpin.INodeMap,
        default_val: Any = None,
    ) -> None:
        super().__init__(
            sys= sys,
            parent_id= parent_id,
            route= route,
            nodemap= nodemap,
            default_val= default_val
        )
        raw_node: PySpin.INode = nodemap.GetNode(self.name)
        self.node = PySpin.CBooleanPtr(raw_node)
        self._update_status()

    def _validate_value(self, value: Any) -> bool:
        try:
            value = bool(value)
        except (ValueError, TypeError):
            msg: str = f'Expected an boolean, got "{value}".'
            raise ValueError(msg)
        return value

    def get_value(self) -> tuple[FuncResult, Any]:
        if not self.status.can_read():
            msg: str = f'{self.parent}: Unable to get "{self.name}" node. It is not a read node.'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        value: bool = self.node.GetValue()
        try:
            value = bool(value)
        except (ValueError, TypeError):
            msg: str = f'{self.parent}: Unable to get "{self.name}" node value. Can\'t convert {type(value)} to bool.'
            spincam_logger.error(msg)
            return FuncResult.ERROR, None
        return FuncResult.SUCCESS, value

    def set_value(self, value: Any = None) -> tuple[FuncResult, Any]:
        if value is None:
            value = self.default_val
        if value is None:
            return FuncResult.ERROR, None
        try:
            value = self._validate_value(value)
        except ValueError as e:
            msg: str = f'{self.parent}: Unable to set "{self.name}" node. {e}'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        if not self.status.can_write():
            msg: str = f'{self.parent}: Unable to set "{self.name}" node. It is not a write node.'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        try:
            self.node.SetValue(value)
        except PySpin.SpinnakerException as e:
            msg: str = f'{self.parent}: Unable to set "{value}" to "{self.name}" node. {e}'
            spincam_logger.error(msg)
            return FuncResult.ERROR, None
        ret: FuncResult
        ret, value = self.get_value()
        msg: str = f'{self.parent}: "{self.name}" set to "{value}".'
        spincam_logger.info(msg)
        return FuncResult.SUCCESS, value


@NodeTypes.register(NODE_PTR_TYPES.INT.value)
class IntNode(Node[PySpin.CIntegerPtr]):
    PYSPIN_CLS = PySpin.CIntegerPtr

    def __init__(
        self,
        *,
        sys: System,
        parent_id: str,
        route: str,
        nodemap: PySpin.INodeMap,
        default_val: Any = None,
    ) -> None:
        super().__init__(
            sys= sys,
            parent_id= parent_id,
            route= route,
            nodemap= nodemap,
            default_val= default_val
        )
        raw_node: PySpin.INode = nodemap.GetNode(self.name)
        self.node = PySpin.CIntegerPtr(raw_node)
        self._update_status()

    def _validate_value(self, value: Any) -> int:
        try:
            value = int(value)
        except (ValueError, TypeError):
            msg: str = f'Expected an integer, got "{value}".'
            raise ValueError(msg)
        try:
            min_val: int = self.node.GetMin()
            max_val: int = self.node.GetMax()
            if value < min_val:
                msg: str = f'{self.parent}: "{value}" is lower than "{self.name}" min value. "{min_val}" will be used.'
                spincam_logger.warning(msg)
                value = min_val
            if value > max_val:
                msg: str = f'{self.parent}: "{value}" is grater than "{self.name}" max value. "{max_val}" will be used.'
                spincam_logger.warning(msg)
                value = max_val
        except PySpin.SpinnakerException:
            msg: str = f'{self.parent}: Unable to get min and max values for "{self.name}" node. Value will not be validated.'
            spincam_logger.warning(msg)
        return value

    def get_value(self) -> tuple[FuncResult, Any]:
        if not self.status.can_read():
            msg: str = f'{self.parent}: Unable to get "{self.name}" node. It is not a read node.'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        value: int = self.node.GetValue()
        try:
            value = int(value)
        except (ValueError, TypeError):
            msg: str = f'{self.parent}: Unable to get "{self.name}" node value. Can\'t convert {type(value)} to int.'
            spincam_logger.error(msg)
            return FuncResult.ERROR, None
        return FuncResult.SUCCESS, value

    def set_value(self, value: Any = None) -> tuple[FuncResult, Any]:
        if value is None:
            value = self.default_val
        if value is None:
            return FuncResult.ERROR, None
        try:
            value = self._validate_value(value)
        except ValueError as e:
            msg: str = f'{self.parent}: Unable to set "{self.name}" node. {e}'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        if not self.status.can_write():
            msg: str = f'{self.parent}: Unable to set "{self.name}" node. It is not a write node.'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        try:
            self.node.SetValue(value)
        except PySpin.SpinnakerException as e:
            msg: str = f'{self.parent}: Unable to set "{value}" to "{self.name}" node. {e}'
            spincam_logger.error(msg)
            return FuncResult.ERROR, None
        ret: FuncResult
        ret, value = self.get_value()
        msg: str = f'{self.parent}: "{self.name}" set to "{value}".'
        spincam_logger.info(msg)
        return FuncResult.SUCCESS, value


@NodeTypes.register(NODE_PTR_TYPES.FLOAT.value)
class FloatNode(Node[PySpin.CFloatPtr]):
    PYSPIN_CLS = PySpin.CFloatPtr

    def __init__(
        self,
        *,
        sys: System,
        parent_id: str,
        route: str,
        nodemap: PySpin.INodeMap,
        default_val: Any = None,
    ) -> None:
        super().__init__(
            sys= sys,
            parent_id= parent_id,
            route= route,
            nodemap= nodemap,
            default_val= default_val
        )
        raw_node: PySpin.INode = nodemap.GetNode(self.name)
        self.node = PySpin.CFloatPtr(raw_node)
        self._update_status()

    def _validate_value(self, value: Any) -> float:
        try:
            value = float(value)
        except (ValueError, TypeError):
            msg: str = f'Expected a float, got "{value}".'
            raise ValueError(msg)
        try:
            min_val: int = self.node.GetMin()
            max_val: int = self.node.GetMax()
            if value < min_val:
                msg: str = f'{self.parent}: "{value}" is lower than "{self.name}" min value. "{min_val}" will be used.'
                spincam_logger.warning(msg)
                value = min_val
            if value > max_val:
                msg: str = f'{self.parent}: "{value}" is grater than "{self.name}" max value. "{max_val}" will be used.'
                spincam_logger.warning(msg)
                value = max_val
        except PySpin.SpinnakerException:
            msg: str = f'{self.parent}: Unable to get min and max values for "{self.name}" node. Value will not be validated.'
            spincam_logger.warning(msg)
        return value

    def get_value(self) -> tuple[FuncResult, Any]:
        if not self.status.can_read():
            msg: str = f'{self.parent}: Unable to get "{self.name}" node. It is not a read node.'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        value: float = self.node.GetValue()
        try:
            value = float(value)
        except (ValueError, TypeError):
            msg: str = f'{self.parent}: Unable to get "{self.name}" node value. Can\'t convert {type(value)} to float.'
            spincam_logger.error(msg)
            return FuncResult.ERROR, None
        return FuncResult.SUCCESS, value

    def set_value(self, value: Any = None) -> tuple[FuncResult, Any]:
        if value is None:
            value = self.default_val
        if value is None:
            return FuncResult.ERROR, None
        try:
            value = self._validate_value(value)
        except ValueError as e:
            msg: str = f'{self.parent}: Unable to set "{self.name}" node. {e}'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        if not self.status.can_write():
            msg: str = f'{self.parent}: Unable to set "{self.name}" node. It is not a write node.'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        try:
            self.node.SetValue(value)
        except PySpin.SpinnakerException as e:
            msg: str = f'{self.parent}: Unable to set "{value}" to "{self.name}" node. {e}'
            spincam_logger.error(msg)
            return FuncResult.ERROR, None
        ret: FuncResult
        ret, value = self.get_value()
        msg: str = f'{self.parent}: "{self.name}" set to "{value}".'
        spincam_logger.info(msg)
        return FuncResult.SUCCESS, value


@NodeTypes.register(NODE_PTR_TYPES.STRING.value)
class StrNode(Node[PySpin.CStringPtr]):
    PYSPIN_CLS = PySpin.CStringPtr

    def __init__(
        self,
        *,
        sys: System,
        parent_id: str,
        route: str,
        nodemap: PySpin.INodeMap,
        default_val: Any = None,
    ) -> None:
        super().__init__(
            sys= sys,
            parent_id= parent_id,
            route= route,
            nodemap= nodemap,
            default_val= default_val
        )
        raw_node: PySpin.INode = nodemap.GetNode(self.name)
        self.node = PySpin.CStringPtr(raw_node)
        self._update_status()

    def _validate_value(self, value: Any) -> str:
        try:
            value = str(value)
        except (ValueError, TypeError):
            msg: str = f'Expected an string, got "{value}".'
            raise ValueError(msg)
        return value

    def get_value(self) -> tuple[FuncResult, Any]:
        if not self.status.can_read():
            msg: str = f'{self.parent}: Unable to get "{self.name}" node. It is not a read node.'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        value: str = self.node.GetValue()
        try:
            value = str(value)
        except (ValueError, TypeError):
            msg: str = f'{self.parent}: Unable to get "{self.name}" node value. Can\'t convert {type(value)} to str.'
            spincam_logger.error(msg)
            return FuncResult.ERROR, None
        return FuncResult.SUCCESS, value

    def set_value(self, value: Any = None) -> tuple[FuncResult, Any]:
        if value is None:
            value = self.default_val
        if value is None:
            return FuncResult.ERROR, None
        try:
            value = self._validate_value(value)
        except ValueError as e:
            msg: str = f'{self.parent}: Unable to set "{self.name}" node. {e}'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        if not self.status.can_write():
            msg: str = f'{self.parent}: Unable to set "{self.name}" node. It is not a write node.'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        try:
            self.node.SetValue(value)
        except PySpin.SpinnakerException as e:
            msg: str = f'{self.parent}: Unable to set "{value}" to "{self.name}" node. {e}'
            spincam_logger.error(msg)
            return FuncResult.ERROR, None
        ret: FuncResult
        ret, value = self.get_value()
        msg: str = f'{self.parent}: "{self.name}" set to "{value}".'
        spincam_logger.info(msg)
        return FuncResult.SUCCESS, value


@NodeTypes.register(NODE_PTR_TYPES.COMMAND.value)
class CommandNode(Node[PySpin.CCommandPtr]):
    PYSPIN_CLS = PySpin.CCommandPtr

    def __init__(
        self,
        *,
        sys: System,
        parent_id: str,
        route: str,
        nodemap: PySpin.INodeMap,
        default_val: Any = None,
    ) -> None:
        super().__init__(
            sys= sys,
            parent_id= parent_id,
            route= route,
            nodemap= nodemap,
            default_val= default_val
        )
        raw_node: PySpin.INode = nodemap.GetNode(self.name)
        self.node = PySpin.CCommandPtr(raw_node)
        self._update_status()

    def get_value(self) -> tuple[FuncResult, Any]:
        return FuncResult.SUCCESS, 'Execute'

    def execute(self) -> FuncResult:
        if not self.status.can_write():
            msg: str = f'{self.parent}: Unable to execute "{self.name}" node. It is not a write node.'
            spincam_logger.error(msg)
            return FuncResult.ERROR
        try:
            self.node.Execute()
        except PySpin.SpinnakerException as e:
            msg: str = f'{self.parent}: Unable execute "{self.name}" node. {e}'
            spincam_logger.error(msg)
            return FuncResult.ERROR
        return FuncResult.SUCCESS


@NodeTypes.register(NODE_PTR_TYPES.REGISTER.value)
class RegisterNode(Node[PySpin.CRegisterPtr]):
    PYSPIN_CLS = PySpin.CRegisterPtr

    def __init__(
        self,
        *,
        sys: System,
        parent_id: str,
        route: str,
        nodemap: PySpin.INodeMap,
        default_val: Any = None,
    ) -> None:
        super().__init__(
            sys= sys,
            parent_id= parent_id,
            route= route,
            nodemap= nodemap,
            default_val= default_val
        )
        raw_node: PySpin.INode = nodemap.GetNode(self.name)
        self.node = PySpin.CRegisterPtr(raw_node)
        self._update_status()

    def __str__(self) -> str:
        ret: FuncResult
        value: Any
        ret, value = self.get_value()
        if ret.is_error():
            value = ''
        return f'{self.display_name}: type= "{self.__class__.__name__}", value="{type(value)}", default="{self.default_val}"'

    @property
    def length(self) -> int:
        return int(self.node.GetLength())

    def _validate_value(self, value: Any) -> bytearray:
        if not isinstance(value, bytearray):
            msg: str = f'Expected an bytearray, got "{value}".'
            raise ValueError(msg)
        return value

    def get_value(self) -> tuple[FuncResult, Any]:
        if not self.status.can_read():
            msg: str = f'{self.parent}: Unable to get "{self.name}" node. It is not a read node.'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        value: bytearray = self.node.Get(self.length, True, True)
        if not isinstance(value, bytearray):
            msg: str = f'{self.parent}: Unable to get "{self.name}" node value. Can\'t convert {type(value)} to bytearray.'
            spincam_logger.error(msg)
            return FuncResult.ERROR, None
        return FuncResult.SUCCESS, value

    def set_value(self, value: Any = None) -> tuple[FuncResult, Any]:
        if value is None:
            value = self.default_val
        if value is None:
            return FuncResult.ERROR, None
        try:
            value = self._validate_value(value)
        except ValueError as e:
            msg: str = f'{self.parent}: Unable to set "{self.name}" node. {e}'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        if not self.status.can_write():
            msg: str = f'{self.parent}: Unable to set "{self.name}" node. It is not a write node.'
            spincam_logger.warning(msg)
            return FuncResult.ERROR, None
        try:
            self.node.Set(value)
        except PySpin.SpinnakerException as e:
            msg: str = f'{self.parent}: Unable to set "{value}" to "{self.name}" node. {e}'
            spincam_logger.error(msg)
            return FuncResult.ERROR, None
        ret: FuncResult
        ret, value = self.get_value()
        msg: str = f'{self.parent}: "{self.name}" set to "{value}".'
        spincam_logger.info(msg)
        return FuncResult.SUCCESS, value
