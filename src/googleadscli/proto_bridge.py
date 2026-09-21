"""Generische JSON<->Protobuf-Bruecke fuer beliebige Google-Ads-API-Ressourcen/Services.

Kernidee: Statt fuer jede der >50 Services / hunderte Ressourcen eigenen Code zu
schreiben, wird die GAPIC-Namenskonvention der Google Ads API per Reflection
ausgenutzt:

- Jede mutierbare Ressource ``x`` (snake_case) hat einen eponymen Service
  ``XService`` mit genau einer ``mutate_*``-Methode, deren Request ein
  ``operations``-Feld vom Typ ``XOperation`` besitzt.
- Jede generierte Service-Methode hat die Signatur
  ``method(request: Union[XyzRequest, dict, None] = None, ...)`` -- daraus laesst
  sich der Request-Typ dynamisch extrahieren.

Alle Messages sind proto-plus-Typen (``use_proto_plus=True``, siehe config.py),
die eigene ``to_dict``/``from_json``/dict-Konstruktoren mitbringen und damit eine
robuste generische JSON<->Message-Konvertierung ohne Sonderfaelle ermoeglichen.
"""

from __future__ import annotations

import inspect
import pkgutil
import typing
from dataclasses import dataclass
from typing import Any

import proto
from google.api_core import protobuf_helpers
from google.api_core.operation import Operation as LRO

DEFAULT_VERSION = "v25"

_TO_DICT_KWARGS = {
    "use_integers_for_enums": False,
    "preserving_proto_field_name": True,
    "always_print_fields_with_no_presence": False,
}


class BridgeError(Exception):
    """Fehler bei der Aufloesung oder Ausfuehrung eines generischen API-Aufrufs."""


def to_camel(resource_key: str) -> str:
    return "".join(part.capitalize() for part in resource_key.split("_"))


def _extract_message_class(annotation: Any) -> type | None:
    for arg in typing.get_args(annotation):
        if isinstance(arg, type) and issubclass(arg, proto.Message):
            return arg
    return None


def _request_class_of(method: Any) -> type | None:
    sig = inspect.signature(method)
    request_param = sig.parameters.get("request")
    if request_param is None:
        return None
    return _extract_message_class(request_param.annotation)


@dataclass
class MutateTarget:
    service: Any
    method_name: str
    operation_cls: type
    request_cls: type

    @property
    def method(self) -> Any:
        return getattr(self.service, self.method_name)


def _services_package(version: str):
    return __import__(
        f"google.ads.googleads.{version}.services.services",
        fromlist=["services"],
    )


def _iter_all_service_names(version: str) -> list[str]:
    """Listet alle Service-Namen (PascalCase) der gegebenen API-Version auf."""
    pkg = _services_package(version)
    names = []
    for module_info in pkgutil.iter_modules(pkg.__path__):
        snake = module_info.name
        camel = "".join(part.capitalize() for part in snake.split("_"))
        names.append(camel)
    return sorted(set(names))


def _find_mutate_method(service: Any, operation_type_name: str) -> tuple[str, type] | None:
    for attr in dir(service):
        if not attr.startswith("mutate_"):
            continue
        method = getattr(service, attr)
        if not callable(method):
            continue
        request_cls = _request_class_of(method)
        if request_cls is None:
            continue
        operations_field = request_cls.pb().DESCRIPTOR.fields_by_name.get("operations")
        if operations_field is None:
            continue
        if operations_field.message_type.name == operation_type_name:
            return attr, request_cls
    return None


def resolve_mutate_target(client, resource_key: str, version: str = DEFAULT_VERSION) -> MutateTarget:
    """Findet Service + Mutate-Methode + Operation-Typ fuer eine Ressource.

    Versucht zuerst den eponymen Service (schnell, funktioniert fuer praktisch
    alle Ressourcen). Faellt andernfalls auf einen Scan ueber alle Services
    zurueck (Robustheit gegen zukuenftige Namenskonvention-Ausnahmen).
    """
    camel = to_camel(resource_key)
    operation_type_name = f"{camel}Operation"
    service_name = f"{camel}Service"

    try:
        service = client.get_service(service_name, version=version)
    except ValueError:
        service = None

    if service is not None:
        found = _find_mutate_method(service, operation_type_name)
        if found:
            method_name, request_cls = found
            operation_cls = type(client.get_type(operation_type_name, version=version))
            return MutateTarget(
                service=service, method_name=method_name, operation_cls=operation_cls, request_cls=request_cls
            )

    for candidate_service_name in _iter_all_service_names(version):
        try:
            candidate_service = client.get_service(candidate_service_name, version=version)
        except ValueError:
            continue
        found = _find_mutate_method(candidate_service, operation_type_name)
        if found:
            method_name, request_cls = found
            operation_cls = type(client.get_type(operation_type_name, version=version))
            return MutateTarget(
                service=candidate_service,
                method_name=method_name,
                operation_cls=operation_cls,
                request_cls=request_cls,
            )

    raise BridgeError(
        f"Keine mutate-faehige Ressource '{resource_key}' gefunden "
        f"(erwarteter Operation-Typ: {operation_type_name})."
    )


def build_operation(target: MutateTarget, op_dict: dict) -> Any:
    """Baut eine <Resource>Operation-Instanz aus einem JSON-Operationsdict.

    Erwartetes Format: {"create": {...}} | {"update": {...}, "update_mask": [...]}
    | {"remove": "resource_name"}. Bei "update" ohne explizite update_mask wird
    die Maske automatisch aus den gesetzten Feldern abgeleitet (wie in den
    offiziellen Google-Ads-Python-Beispielen).
    """
    keys = {"create", "update", "remove"} & op_dict.keys()
    if len(keys) != 1:
        raise BridgeError(
            "Jede Operation braucht genau eines von 'create', 'update', 'remove': "
            f"erhalten wurde {sorted(op_dict.keys())}"
        )

    if "create" in op_dict:
        return target.operation_cls(create=op_dict["create"])

    if "remove" in op_dict:
        return target.operation_cls(remove=op_dict["remove"])

    update_payload = op_dict["update"]
    if "resource_name" not in update_payload:
        raise BridgeError("'update'-Operationen benoetigen ein 'resource_name'-Feld im Payload.")
    operation = target.operation_cls(update=update_payload)
    update_mask = op_dict.get("update_mask")
    if update_mask is not None:
        operation.update_mask.paths.extend(update_mask)
    else:
        resource_cls = type(operation.update)
        derived_mask = protobuf_helpers.field_mask(None, resource_cls.pb(operation.update))
        operation.update_mask.paths.extend(derived_mask.paths)
    return operation


def message_to_dict(message: Any) -> dict:
    return type(message).to_dict(message, **_TO_DICT_KWARGS)


def run_mutate(
    client,
    resource_key: str,
    customer_id: str,
    operations: list[dict],
    *,
    partial_failure: bool = False,
    validate_only: bool = False,
    version: str = DEFAULT_VERSION,
) -> dict:
    target = resolve_mutate_target(client, resource_key, version=version)
    built_operations = [build_operation(target, op) for op in operations]
    request = target.request_cls(
        customer_id=customer_id,
        operations=built_operations,
        partial_failure=partial_failure,
        validate_only=validate_only,
    )
    response = target.method(request=request)
    return message_to_dict(response)


def resolve_call_target(client, service_name: str, method_name: str, version: str = DEFAULT_VERSION):
    try:
        service = client.get_service(service_name, version=version)
    except ValueError as exc:
        raise BridgeError(str(exc)) from exc

    method = getattr(service, method_name, None)
    if method is None or not callable(method):
        available = sorted(a for a in dir(service) if not a.startswith("_") and callable(getattr(service, a)))
        raise BridgeError(
            f"Service '{service_name}' hat keine Methode '{method_name}'. "
            f"Verfuegbare Methoden: {available}"
        )

    request_cls = _request_class_of(method)
    return service, method, request_cls


def normalize_response(
    response: Any,
    *,
    wait_for_operation: bool = True,
    operation_timeout: float | None = None,
) -> Any:
    if isinstance(response, LRO):
        if not wait_for_operation:
            return {"long_running_operation": response.operation.name, "done": response.done()}
        return normalize_response(
            response.result(timeout=operation_timeout),
            wait_for_operation=wait_for_operation,
            operation_timeout=operation_timeout,
        )

    if isinstance(response, proto.Message):
        as_dict = message_to_dict(response)
        if "results" in as_dict and isinstance(as_dict["results"], list):
            return as_dict["results"]
        return as_dict

    if isinstance(response, (str, bytes, dict)):
        return response

    if hasattr(response, "__iter__"):
        rows: list[Any] = []
        for item in response:
            normalized = normalize_response(
                item, wait_for_operation=wait_for_operation, operation_timeout=operation_timeout
            )
            if isinstance(normalized, list):
                rows.extend(normalized)
            else:
                rows.append(normalized)
        return rows

    return response


def invoke_call(
    client,
    service_name: str,
    method_name: str,
    payload: dict | None = None,
    *,
    wait_for_operation: bool = True,
    operation_timeout: float | None = None,
    version: str = DEFAULT_VERSION,
) -> Any:
    _service, method, request_cls = resolve_call_target(client, service_name, method_name, version=version)
    payload = payload or {}
    request = request_cls(payload) if request_cls is not None else payload
    response = method(request=request)
    return normalize_response(
        response, wait_for_operation=wait_for_operation, operation_timeout=operation_timeout
    )


def list_service_names(version: str = DEFAULT_VERSION) -> list[str]:
    return _iter_all_service_names(version)


def list_service_methods(client, service_name: str, version: str = DEFAULT_VERSION) -> list[str]:
    try:
        service = client.get_service(service_name, version=version)
    except ValueError as exc:
        raise BridgeError(str(exc)) from exc
    return sorted(
        attr
        for attr in dir(service)
        if not attr.startswith("_") and callable(getattr(service, attr))
    )
