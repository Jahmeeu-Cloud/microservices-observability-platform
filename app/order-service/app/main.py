
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


SERVICE_NAME = "order-service"
PAYMENT_SERVICE_URL = os.getenv(
    "PAYMENT_SERVICE_URL",
    "http://localhost:8002",
)

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

ORDERS_CREATED_TOTAL = Counter(
    "orders_created_total",
    "Total number of successfully created orders",
)

ORDERS_FAILED_TOTAL = Counter(
    "orders_failed_total",
    "Total number of failed order attempts",
)


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
            "order_id",
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
    logger.info("Order Service started")

    yield

    await app.state.http_client.aclose()
    logger.info("Order Service stopped")


# OpenTelemetry distributed tracing.
app = FastAPI(
    title="Microservices Observability Platform - Order Service",
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

        route = request.scope.get("route")
        if route is not None:
            route_path = getattr(route, "path", route_path)

        return response

    finally:
        duration = time.perf_counter() - start_time

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
        payment_response = await client.post(
            f"{PAYMENT_SERVICE_URL}/payments",
            json={
                "customer_id": order.customer_id,
                "amount": order.amount,
                "item": order.item,
                "quantity": order.quantity,
            },
        )

        try:
            payment_data = payment_response.json()
        except ValueError:
            ORDERS_FAILED_TOTAL.inc()
            raise HTTPException(
                status_code=502,
                detail="Invalid response from Payment Service",
            )

        if payment_response.status_code >= 400:
            ORDERS_FAILED_TOTAL.inc()
            raise HTTPException(
                status_code=payment_response.status_code,
                detail={
                    "message": "Payment failed",
                    "payment_response": payment_data,
                },
            )

        order_id = f"order-{int(time.time() * 1000)}"

        ORDERS_CREATED_TOTAL.inc()

        logger.info(
            "Order created successfully",
            extra={"order_id": order_id},
        )

        return {
            "status": "success",
            "order_id": order_id,
            "customer_id": order.customer_id,
            "item": order.item,
            "quantity": order.quantity,
            "amount": order.amount,
            "payment": payment_data,
        }

    except httpx.TimeoutException:
        ORDERS_FAILED_TOTAL.inc()
        logger.error(
            "Payment Service request timed out",
            extra={"error": "Upstream timeout"},
        )
        raise HTTPException(
            status_code=504,
            detail="Payment Service timed out",
        )

    except httpx.ConnectError:
        ORDERS_FAILED_TOTAL.inc()
        logger.error(
            "Could not connect to Payment Service",
            extra={"error": "Upstream connection failed"},
        )
        raise HTTPException(
            status_code=503,
            detail="Payment Service is unavailable",
        )
