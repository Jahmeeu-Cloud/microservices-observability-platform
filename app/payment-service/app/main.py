
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, Response
from app.tracing import configure_tracing
from pydantic import BaseModel, Field
from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)


SERVICE_NAME = "payment-service"

# Prometheus metrics
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["service", "method", "route", "status"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["service", "method", "route"],
)

PAYMENTS_APPROVED = Counter(
    "payments_approved_total",
    "Total number of approved payments",
)

PAYMENTS_DECLINED = Counter(
    "payments_declined_total",
    "Total number of declined payments",
)


# Structured JSON logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": SERVICE_NAME,
            "message": record.getMessage(),
        }

        if hasattr(record, "payment_id"):
            log_entry["payment_id"] = record.payment_id

        if hasattr(record, "customer_id"):
            log_entry["customer_id"] = record.customer_id

        if hasattr(record, "status"):
            log_entry["status"] = record.status

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
    logger.info("Payment Service started")
    yield
    logger.info("Payment Service stopped")


# OpenTelemetry distributed tracing.
app = FastAPI(
    title="Payment Service",
    description="Simulated payment processing microservice",
    version="1.0.0",
    lifespan=lifespan,
)


# Payment request validation
configure_tracing(app)

class PaymentRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    item: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    amount: float = Field(gt=0)


# Request metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    start_time = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = time.perf_counter() - start_time

        HTTP_REQUESTS.labels(
            service=SERVICE_NAME,
            method=request.method,
            route=request.url.path,
            status=str(status_code),
        ).inc()

        HTTP_REQUEST_DURATION.labels(
            service=SERVICE_NAME,
            method=request.method,
            route=request.url.path,
        ).observe(duration)


@app.get("/health")
async def health():
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


@app.post("/payments")
async def process_payment(payment: PaymentRequest):
    payment_id = f"pay-{uuid.uuid4().hex[:12]}"

    # This project simulates payment approval.
    # No real payment provider or financial transaction is involved.
    PAYMENTS_APPROVED.inc()

    logger.info(
        "Payment approved",
        extra={
            "payment_id": payment_id,
            "customer_id": payment.customer_id,
            "status": "approved",
        },
    )

    return {
        "payment_id": payment_id,
        "status": "approved",
        "customer_id": payment.customer_id,
        "item": payment.item,
        "quantity": payment.quantity,
        "amount": payment.amount,
    }
