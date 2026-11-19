import json
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException, Request
from app.tracing import configure_tracing
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest


SERVICE_NAME = "api-gateway"
ORDER_SERVICE_URL = os.getenv(
    "ORDER_SERVICE_URL",
    "http://localhost:8001",
)

# Prometheus metrics.
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["service", "method", "route", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["service", "method", "route"],
)


# Structured JSON logging.
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": SERVICE_NAME,
            "message": record.getMessage(),
        }

        for field in (
            "method",
            "route",
            "status_code",
            "duration_seconds",
            "error",
        ):
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


logger = logging.getLogger(SERVICE_NAME)
logger.setLevel(logging.INFO)
logger.handlers.clear()

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.propagate = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(5.0),
    )
    logger.info("API Gateway started")

    yield

    await app.state.http_client.aclose()
    logger.info("API Gateway stopped")


# OpenTelemetry distributed tracing.
app = FastAPI(
    title="Microservices Observability Platform - API Gateway",
    version="1.0.0",
    lifespan=lifespan,
)


configure_tracing(app)

class OrderRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    item: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    amount: float = Field(gt=0)


@app.middleware("http")
async def observe_http_requests(request: Request, call_next):
    start_time = time.perf_counter()

    status_code = 500
    route_path = request.url.path

    try:
        response = await call_next(request)
        status_code = response.status_code

        # Use the registered route rather than arbitrary URL values.
        # This prevents high-cardinality Prometheus labels.
        route = request.scope.get("route")
        if route is not None:
            route_path = getattr(route, "path", route_path)

        return response

    finally:
        duration = time.perf_counter() - start_time

        # Do not count Prometheus scrapes as application traffic.
        if route_path != "/metrics":
            HTTP_REQUESTS_TOTAL.labels(
                service=SERVICE_NAME,
                method=request.method,
                route=route_path,
                status=str(status_code),
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                service=SERVICE_NAME,
                method=request.method,
                route=route_path,
            ).observe(duration)

            logger.info(
                "HTTP request completed",
                extra={
                    "method": request.method,
                    "route": route_path,
                    "status_code": status_code,
                    "duration_seconds": round(duration, 6),
                },
            )


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
    }


@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.post("/orders")
async def create_order(
    order: OrderRequest,
    request: Request,
):
    client: httpx.AsyncClient = request.app.state.http_client

    try:
        upstream_response = await client.post(
            f"{ORDER_SERVICE_URL}/orders",
            json=order.model_dump(),
        )

        try:
            response_data = upstream_response.json()
        except ValueError:
            logger.error(
                "Order Service returned an invalid response",
                extra={"error": "Invalid upstream JSON"},
            )
            raise HTTPException(
                status_code=502,
                detail="Invalid response from Order Service",
            )

        return JSONResponse(
            content=response_data,
            status_code=upstream_response.status_code,
        )

    except httpx.TimeoutException:
        logger.error(
            "Order Service request timed out",
            extra={"error": "Upstream timeout"},
        )
        raise HTTPException(
            status_code=504,
            detail="Order Service timed out",
        )

    except httpx.ConnectError:
        logger.error(
            "Could not connect to Order Service",
            extra={"error": "Upstream connection failed"},
        )
        raise HTTPException(
            status_code=503,
            detail="Order Service is unavailable",
        )
