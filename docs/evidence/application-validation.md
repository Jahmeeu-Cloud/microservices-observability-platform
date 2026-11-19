## Kubernetes Deployment Validation

Date: 2026-11-17

Successfully deployed all three microservices to the
Minikube Kubernetes cluster in the `microservices` namespace.

Deployments:

- API Gateway: 1/1 Ready
- Order Service: 1/1 Ready
- Payment Service: 1/1 Ready

Kubernetes Services:

- api-gateway: ClusterIP, port 8000
- order-service: ClusterIP, port 8001
- payment-service: ClusterIP, port 8002

Security validation:

- All containers run as non-root UID/GID 999.
- Privilege escalation is disabled.
- Root filesystem is read-only.
- All Linux capabilities are dropped.
- RuntimeDefault seccomp profile is enabled.
- CPU and memory requests and limits are configured.

End-to-end Kubernetes test:

- API Gateway health endpoint: HTTP 200
- Order request: HTTP 200
- Order ID: order-1794908140429
- Payment ID: pay-8b6429fc516b
- Payment status: approved (simulated)

The complete request successfully traversed the API Gateway,
Order Service, and Payment Service using Kubernetes
ClusterIP Services and internal DNS.

No real payment provider is integrated.



# Application Validation Evidence

Date: 2026-11-17

## Docker Images

Three application images built successfully:

- observability-api-gateway:1.0
- observability-order-service:1.0
- observability-payment-service:1.0

All three images run as the non-root user `appuser`.

## Docker Compose

All three containers started successfully and passed
their configured health checks.

- API Gateway: healthy
- Order Service: healthy
- Payment Service: healthy

The services communicate over the dedicated Docker bridge
network `observability-platform_observability-network`.

## End-to-End Test

A POST request to `/orders` through the API Gateway returned HTTP 200.

Order ID: order-1794906644877

Payment ID: pay-c98db02a7429

Payment status: approved

## Application Metrics

Verified metrics include:

- http_requests_total
- http_request_duration_seconds
- orders_created_total
- orders_failed_total
- payments_approved_total
- payments_declined_total

The successful test recorded:

- orders_created_total: 1
- orders_failed_total: 0
- payments_approved_total: 1
- payments_declined_total: 0

## Application Logs

Verified structured JSON application logs from:

- API Gateway
- Order Service
- Payment Service

Verified business events:

- Order created successfully
- Payment approved

Uvicorn access logs are also emitted to container stdout.

## Limitations

The payment service currently simulates approval.
It does not integrate with a real payment provider.

These results validate the local Docker Compose application,
not yet the Kubernetes or observability deployment.

## Recovery Validation

After restarting Minikube and increasing its Docker memory
limit to 8 GiB, the Docker Compose application remained available.

- API Gateway health endpoint: HTTP 200
- End-to-end order request: successful
- Payment status: approved

Recovery test identifiers:

- Order ID: order-1794907496811
- Payment ID: pay-a53d4412f305

This confirms that the application running outside Kubernetes
remained operational during the Minikube restart.

## Kubernetes Deployment Validation

Date: 2026-11-17

Successfully deployed all three microservices to the
Minikube Kubernetes cluster in the `microservices` namespace.

Deployments:

- API Gateway: 1/1 Ready
- Order Service: 1/1 Ready
- Payment Service: 1/1 Ready

Kubernetes Services:

- api-gateway: ClusterIP, port 8000
- order-service: ClusterIP, port 8001
- payment-service: ClusterIP, port 8002

Security validation:

- All containers run as non-root UID/GID 999.
- Privilege escalation is disabled.
- Root filesystem is read-only.
- All Linux capabilities are dropped.
- RuntimeDefault seccomp profile is enabled.
- CPU and memory requests and limits are configured.

End-to-end Kubernetes test:

- API Gateway health endpoint: HTTP 200
- Order request: HTTP 200
- Order ID: order-1794908140429
- Payment ID: pay-8b6429fc516b
- Payment status: approved (simulated)

The complete request successfully traversed the API Gateway,
Order Service, and Payment Service using Kubernetes
ClusterIP Services and internal DNS.

No real payment provider is integrated.
