import json
from copy import copy
from typing import Final, Callable, Any, Iterable


_JSONRPC_REQUEST_FIELDS: Final[set] = {"jsonrpc", "method", "params", "id"}


def prepare_batch(objs: Iterable[bytes | bytearray | None]) -> bytes:
    string = ",\n    ".join([str(obj, encoding="utf-8").strip() for obj in objs if obj])
    return bytes(f"[\n    {string}\n]", encoding="utf-8")


def prepare_raw_object(obj: Any) -> bytes:
    return bytes(json.dumps(obj), encoding="utf-8")


def prepare_error(code: int, message: str, id: str | int | None = None) -> bytes:
    return prepare_raw_object({
        "jsonrpc": "2.0",
        "error": {
            "code": code,
            "message": message
        },
        "id": id
    })


def prepare_response(result: Any, id: str | int | None = None) -> bytes:
    return prepare_raw_object({
        "jsonrpc": "2.0",
        "result": result,
        "id": id,
    })


def prepare_request(
        method: str,
        params: tuple[Any, ...] | list[Any] | dict[str, Any] | None = None,
        id: str | int | None = None) -> bytes:
    obj = {
        "jsonrpc": "2.0",
        "method": method,
    }
    if params is not None:
        obj["params"] = params
    obj["id"] = id
    return prepare_raw_object(obj)


def prepare_notification(
        method: str,
        params: tuple[Any, ...] | list[Any] | dict[str, Any] | None = None) -> bytes:
    obj = {
        "jsonrpc": "2.0",
        "method": method,
    }
    if params is not None:
        obj["params"] = params
    return prepare_raw_object(obj)


class JSONRPCError:

    def __init__(self):
        raise RuntimeError(f"{self.__qualname__} cannot be instantiated")

    ParseError: Final[int] = -32_700
    InvalidRequest: Final[int] = -32_600
    MethodNotFound: Final[int] = -32_601
    InvalidParams: Final[int] = -32_602
    InternalError: Final[int] = -32_603


class JSONRPCProvider:

    _methods: dict[str, Callable[..., Any]] = {}

    @property
    def methods(self) -> dict[str, Callable[..., Any]]:
        return copy(self._methods)

    def add_method(self, method: Callable[..., Any], alias: str | None = None) -> bool:
        if not callable(method):
            return False
        if not alias:
            alias = method.__name__
        if alias in self._methods:
            return False
        self._methods[alias] = method

    def remove_method(self, method_or_alias: Callable[..., Any] | str):
        if not isinstance(method_or_alias, str):
            if not callable(method_or_alias):
                return False
            method_or_alias = method_or_alias.__name__
        if method_or_alias in self._methods:
            del self._methods[method_or_alias]
            return True
        return False

    def process_request(
            self,
            raw_request: bytes | bytearray | memoryview
            ) -> bytes | bytearray | None:
        try:
            request_str = str(raw_request, encoding="utf-8").strip("\0\r\n\t ")
        except UnicodeDecodeError as e:
            return prepare_error(
                JSONRPCError.ParseError,
                f"Parse error: {e}"
            )
        try:
            request = json.loads(request_str)
        except json.JSONDecodeError as e:
            return prepare_error(
                JSONRPCError.ParseError,
                f"Parse error: {e}"
            )
        try:
            if isinstance(request, list):
                return self._process_batch(request)
            return self._process_single(request)
        except Exception as e:
            return prepare_error(
                JSONRPCError.InternalError,
                f"Internal error: {e}"
            )

    def _process_batch(self, requests: list[dict[str, Any]]) -> bytearray | None:
        results = [self._process_single(request) for request in requests if request]
        if len(results):
            return prepare_batch(results)
        return None

    def _process_single(self, request: dict[str, Any]) -> bytes | None:
        is_notification: Final[bool] = ("id" not in request)
        id = request["id"] if not is_notification else None
        if "jsonrpc" not in request:
            return prepare_error(
                JSONRPCError.InvalidRequest,
                "Invalid request: 'jsonrpc' key missing",
                id
            )
        if request["jsonrpc"] != "2.0":
            return prepare_error(
                JSONRPCError.InvalidRequest,
                "Invalid request: 'jsonrpc' must be exactly '2.0'",
                id
            )
        if "method" not in request:
            return prepare_error(
                JSONRPCError.InvalidRequest,
                "Invalid request: 'method' key missing",
                id
            )
        if not set(request).issubset(_JSONRPC_REQUEST_FIELDS):
            unknown_fields = set(request).difference(_JSONRPC_REQUEST_FIELDS)
            if len(unknown_fields) > 1:
                _m = f"unknown keys {', '.join(repr(k) for k in unknown_fields)}"
            else:
                _m = f"unknown key {unknown_fields[0]!r}"
            return prepare_error(
                JSONRPCError.InvalidRequest,
                f"Invalid request: {_m}"
            )
        if request["method"] not in self._methods:
            return prepare_error(
                JSONRPCError.MethodNotFound,
                f"Method not found: no method named {request['method']!r}",
                id
            )
        method = request["method"]
        params = request["params"] if "params" in request else None
        try:
            # print("Calling method:", method, "with params:", params)
            if not params:
                result = self._methods[method]()
            elif isinstance(params, list):
                result = self._methods[method](*params)
            elif isinstance(params, dict):
                result = self._methods[method](**params)
            else:
                return prepare_error(
                    JSONRPCError.InvalidRequest,
                    "Invalid request: 'params' must be absent, array or object"
                )
            if is_notification:
                return None
            return prepare_response(result, id)
        except (TypeError, ValueError) as e:
            return prepare_error(
                JSONRPCError.InvalidParams,
                f"Invalid params: {e}"
            )
        except Exception as e:
            print("EXCEPTION:", e)
            return prepare_error(
                JSONRPCError.InternalError,
                f"Internal error: {e}"
            )
