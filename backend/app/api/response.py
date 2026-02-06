from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request


def build_request_id(request: Request | None = None) -> str:
    if request is not None:
        request_id = request.headers.get("X-Request-ID") or request.headers.get("x-request-id")
        if request_id:
            return request_id
    return f"req_{uuid.uuid4().hex[:12]}"


def ok(data: Any = None, message: str = "ok", request: Request | None = None) -> dict[str, Any]:
    return {
        "code": 0,
        "message": message,
        "data": data,
        "request_id": build_request_id(request),
    }
