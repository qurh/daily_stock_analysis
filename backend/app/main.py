from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.api.router import api_router
from backend.app.api.response import build_request_id, ok
from backend.app.db.api_database import init_database


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        init_database()
        yield

    app = FastAPI(title="daily_stock_analysis API", version="1.0.0", lifespan=lifespan)

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": str(exc.detail),
                "data": None,
                "request_id": build_request_id(request),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "code": 422,
                "message": "validation error",
                "data": {"errors": exc.errors()},
                "request_id": build_request_id(request),
            },
        )

    @app.get("/health")
    def health(request: Request):
        return ok(data={"status": "ok"}, request=request)

    app.include_router(api_router)
    return app


app = create_app()
