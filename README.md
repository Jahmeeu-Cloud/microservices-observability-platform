## Building an Observability Platform for a Microservices Application: A Hands-On Assignment from Zero to Implementation

## Introduction

One of the things I have come to appreciate while learning Platform, Cloud and DevOps Engineering is that deploying an application is only one part of the work. Knowing whether that application is healthy, understanding what happens when a request fails, identifying performance problems and receiving notifications before an issue becomes serious are equally important.


---

**The Assignment**

### Assignment Instructions

# Assignment: Build an Observability Platform for a Microservices App

## Overview

Deploy a complete observability platform for a microservices application with metrics, logs, traces, dashboards, and alerts that enable rapid incident detection and resolution.

## Requirements

### Deliverables

1. **Observability stack deployment** (Helm values or manifests)
2. **Grafana dashboards** (exported JSON) covering RED metrics, infrastructure, and logs
3. **Alert rules** with routing configuration
4. **Runbook** for each critical alert
5. **README.md** with architecture diagram and setup instructions

### Technical Requirements

**Stack:**

- Prometheus for metrics collection
- Grafana for visualization
- Loki or EFK for log aggregation
- Jaeger or Tempo for distributed tracing

**Dashboards (minimum 3):**

1. Service overview: request rate, error rate, latency (RED method)
2. Infrastructure: node CPU, memory, disk, network
3. Application logs: error count, log volume, recent errors

**Alerts (minimum 5):**

1. High error rate (> 5% for 5 minutes)
2. High latency (p99 > 1s for 5 minutes)
3. Pod crash looping (> 3 restarts in 1 hour)
4. Node not ready
5. Disk space low (< 10% free)

**Each alert must have:**

- Severity label (critical/warning/info)
- Summary and description annotations
- Routing to appropriate channel
- Associated runbook

### Bonus (optional)

- SLO dashboard (error budget, burn rate)
- Custom application metrics (business metrics)
- Trace-to-log correlation working in Grafana
- On-call rotation setup with PagerDuty or Opsgenie

---

Imagine an online shopping application. A customer places an order, the application processes the request, the order service communicates with a payment service, and a response is returned to the customer.

Everything may appear to be working from the customer's perspective. But what happens when the request takes too long? What if the payment service becomes unavailable? What if one of the application containers keeps restarting? What if the application starts returning HTTP 500 errors?

Without proper monitoring and observability, identifying the source of these problems can become difficult. A developer might know that something has gone wrong but not know where to begin investigating.

That is the problem this assignment was designed to address.

The task was to build an observability platform for a microservices application. The objective was not simply to install Grafana and Prometheus. It was to create an environment where application performance, infrastructure health, logs, distributed traces and alerts could be observed from a central location.

I approached the assignment as a practical implementation exercise. I started with the local development environment, created the microservices, containerised them, deployed them to Kubernetes, integrated the observability tools, configured dashboards and alerts, and then tested the complete application flow.

This article explains what I built, why I chose each component, how the components work together, the problems I encountered and how I validated the implementation.

The goal is to make the process understandable to someone who is new to observability while still providing enough technical information for developers, DevOps engineers, Cloud Engineers and recruiters.

## 1. Understanding the assignment

Before writing application code or installing any monitoring tools, I first needed to understand what the assignment required.

The central requirement was to build an observability platform around a microservices application.

The assignment required the following capabilities:

- Application metrics and performance monitoring.
- Infrastructure monitoring.
- Centralised application log collection.
- Distributed tracing across multiple services.
- Grafana dashboards.
- Alerting for important application and infrastructure conditions.
- Notification delivery.
- Operational runbooks.
- Documentation explaining the architecture and implementation.

It also required at least three Grafana dashboards:

1. A service overview dashboard showing request rate, error rate and latency.
2. An infrastructure dashboard showing CPU, memory, disk and network usage.
3. An application logs dashboard showing log volume, error counts and recent errors.

The alerting requirements included five important conditions:

| Alert | Required condition |
|---|---|
| High HTTP error rate | Error rate above 5% for 5 minutes |
| High p99 latency | 99th percentile latency above 1 second for 5 minutes |
| Excessive pod restarts | More than 3 restarts within 1 hour |
| Kubernetes node not ready | A Kubernetes node reports a NotReady condition |
| Low disk space | Less than 10% disk space available |

The assignment also required the alerts to have appropriate severity information, descriptions, notification routing and runbooks.

I treated these requirements as the acceptance criteria for the implementation. This helped me avoid installing tools without a clear reason for using them.

## 2. Architecture and technology selection

I selected a local Kubernetes environment so I could build and test the complete solution without depending on a cloud account or incurring cloud infrastructure costs.

The application was designed around three services:

- API Gateway
- Order Service
- Payment Service

The observability platform was built around six main components:

- Prometheus
- Grafana
- Loki
- Grafana Alloy
- Tempo
- OpenTelemetry

Alertmanager was also included as part of the monitoring and notification stack.

### 2.1 Application architecture

The application represents a simplified e-commerce ordering process.

A customer sends a request to the API Gateway. The API Gateway forwards the request to the Order Service. The Order Service processes the order and communicates with the Payment Service. The Payment Service processes the payment and returns its response.

The request flow is:

```text
Customer
   |
   v
API Gateway
   |
   v
Order Service
   |
   v
Payment Service
   |
   v
Payment Response
   |
   v
Order Response
   |
   v
Customer
```

I deliberately separated the application into services instead of putting all the business logic into a single application.

This makes it possible to observe each service independently while also understanding how a request moves between them.

For example, if an order request takes too long, I can investigate whether the delay happened at the API Gateway, inside the Order Service or while communicating with the Payment Service.

### 2.2 Observability architecture

The observability components have different responsibilities.

| Component | Responsibility |
|---|---|
| Prometheus | Collects and stores time-series metrics |
| Grafana | Displays dashboards, queries data and manages alerts |
| Loki | Stores and queries application logs |
| Grafana Alloy | Collects and forwards Kubernetes container logs |
| Tempo | Stores and retrieves distributed traces |
| OpenTelemetry | Instruments the application and sends trace data |
| Alertmanager | Handles alert notifications in the monitoring stack |

The high-level relationship is:

```text
                  CUSTOMER
                      |
                      v
              +---------------+
              |  API Gateway  |
              +---------------+
                      |
                      v
              +---------------+
              | Order Service|
              +---------------+
                      |
                      v
              +---------------+
              |Payment Service|
              +---------------+


              OBSERVABILITY LAYER

Application Metrics
        |
        v
   Prometheus
        |
        v
     Grafana
        |
        +---------------------------+
        |                           |
        v                           v
  Dashboards                   Alert Rules
                                    |
                                    v
                               Notifications


Application Logs
        |
        v
  Grafana Alloy
        |
        v
      Loki
        |
        v
     Grafana


Application Traces
        |
        v
  OpenTelemetry
        |
        v
      Tempo
        |
        v
     Grafana
```

The important thing to understand is that these tools complement one another.

Prometheus helps answer questions about numerical performance. Loki helps answer questions about what the application recorded. Tempo helps explain how requests travelled between services. Grafana brings these different sources together.

## 3. Preparing the development environment

I used Windows Subsystem for Linux with Ubuntu 24.04 as my development environment.

The main tools were:

- Ubuntu 24.04.3 on WSL.
- Docker 29.1.3.
- Minikube v1.38.1.
- Kubernetes v1.35.1.
- kubectl v1.36.3.
- Helm v4.3.2.
- Python and FastAPI.
- Grafana.

Minikube provided the local Kubernetes cluster, while Docker was used to build and run application containers.

Helm simplified the installation and management of the observability components.

### 3.1 Checking the environment

I used the following commands to verify the main tools:

```bash
docker --version
minikube version
kubectl version --client
helm version
python3 --version
```

I also checked the Kubernetes cluster:

```bash
kubectl get nodes
kubectl get namespaces
```

An important decision during this assignment was to preserve my existing Minikube cluster and its workloads.

I already had other Kubernetes workloads running in the environment, so I did not delete the cluster or reset the existing namespaces simply to start the assignment.

Instead, I created dedicated namespaces for the application and observability components.

### 3.2 Creating the project directory

I created the project workspace:

```bash
mkdir -p ~/microservices-observability-platform

cd ~/microservices-observability-platform
```

The main directories were organised around the different responsibilities of the assignment.

```text
microservices-observability-platform/
│
├── app/
│   ├── api-gateway/
│   ├── order-service/
│   └── payment-service/
│
├── docker/
│   └── docker-compose.yml
│
├── kubernetes/
│   ├── application/
│   ├── namespaces/
│   └── resources/
│
├── observability/
│   ├── alertmanager/
│   ├── alerts/
│   ├── alloy/
│   ├── grafana/
│   ├── loki/
│   ├── prometheus/
│   └── tempo/
│
├── runbooks/
│
├── scripts/
│
├── docs/
│   ├── architecture/
│   ├── evidence/
│   └── screenshots/
│
├── .gitignore
├── LICENSE
└── README.md
```

This structure makes it easier to understand where the application code ends and where the Kubernetes and observability configuration begins.

It also makes the repository easier for another developer to navigate.


![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/3tfm10kppxlvank0la82.png)


![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/ul0uzltlfo9dfr0psrnw.png)


![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/h2wdmqs3ch9f4tz025n7.png)


![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/bar5bsjs57juxfk4b5ck.png)



## 4. Building the microservices application

The next stage was to build the application that the observability platform would monitor.

I used Python and FastAPI because they made it straightforward to create lightweight HTTP services and expose application endpoints.

The application consisted of three separate services.

### 4.1 API Gateway

The API Gateway is the entry point for requests coming from the customer or client.

Instead of allowing clients to communicate directly with every internal service, the API Gateway receives requests and forwards them to the appropriate service.

In this assignment, it forwards order requests to the Order Service.

Its responsibilities include:

- Receiving HTTP requests.
- Exposing a health endpoint.
- Forwarding order requests.
- Handling upstream service communication errors.
- Recording request metrics.
- Generating structured application logs.
- Participating in distributed tracing.

The health endpoint makes it possible to check whether the service is responding.

A simplified FastAPI health endpoint looks like this:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "api-gateway"
    }
```

The actual implementation also includes request forwarding, error handling, metrics and tracing instrumentation.

![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/3tfm10kppxlvank0la82.png)

### 4.2 Order Service

The Order Service handles the order creation process.

When the API Gateway receives an order request, it forwards the request to this service.

The Order Service processes the order information and communicates with the Payment Service.

The responsibilities include:

- Receiving order requests.
- Processing order information.
- Communicating with the Payment Service.
- Recording successful and failed order metrics.
- Recording structured logs.
- Propagating distributed trace context.
- Exposing health and metrics endpoints.

Some of the business metrics implemented in this service include:

```python
orders_created_total
orders_failed_total
```

These counters make it possible to monitor the number of successfully created orders and failed orders.

A simplified order request might contain:

```json
{
  "customer_id": "customer-001",
  "item": "observability-test-product",
  "quantity": 2,
  "amount": 150.00
}
```

The Order Service forwards the payment request and processes the response.

This service is important because it sits between the API Gateway and Payment Service. It allows us to observe how one service depends on another.

![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/ul0uzltlfo9dfr0psrnw.png)


### 4.3 Payment Service

The Payment Service handles payment processing.

For the purpose of this assignment, the service implements a simplified payment approval flow.

It receives payment information from the Order Service, processes the request and returns a response.

The implementation includes the business metric:

```python
payments_approved_total
```

This counter allows Prometheus to track approved payments over time.

The service also records structured application logs, including payment approval events.

A simplified response looks like this:

```json
{
  "payment_id": "pay-example",
  "status": "approved",
  "customer_id": "customer-001",
  "amount": 150.00
}
```

This is an educational application used to demonstrate observability. It is not a real payment gateway and does not process actual financial transactions.

![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/h2wdmqs3ch9f4tz025n7.png)

## 5. Containerising the application with Docker

After implementing the services, I prepared Dockerfiles so that each service could run in its own container.

Containerisation gives each service a consistent runtime environment and makes it easier to deploy the same application image to Kubernetes.

The project contains separate Dockerfiles for:

```text
app/
├── api-gateway/
│   └── Dockerfile
│
├── order-service/
│   └── Dockerfile
│
└── payment-service/
    └── Dockerfile
```

The application images were built with version tags, including `1.0` and `1.1`.

The services were subsequently deployed using version `1.1`.

### 5.1 Container security

I did not want the containers to run with unnecessary privileges.

The container configuration uses a non-root application user, UID 999 and GID 999.

The Kubernetes security configuration also includes:

- Non-root execution.
- Disabled privilege escalation.
- Read-only root filesystem.
- Dropped Linux capabilities.
- RuntimeDefault seccomp profile.

These settings reduce the privileges available to the application containers.

A simplified Dockerfile pattern is:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

RUN groupadd -g 999 appgroup && \
    useradd -u 999 -g appgroup appuser

USER 999:999

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

This is an illustrative Dockerfile pattern. The individual service Dockerfiles in the repository are the authoritative build definitions.

### 5.2 Building the images

The general Docker build pattern is:

```bash
docker build -t api-gateway:1.1 ./app/api-gateway

docker build -t order-service:1.1 ./app/order-service

docker build -t payment-service:1.1 ./app/payment-service
```

Because the deployment was running on Minikube, I also needed to make the images available to the cluster.

The images were loaded into Minikube and the Kubernetes deployments were configured to use them.

This allowed the cluster to run the application without requiring the images to be downloaded from a public registry.

**[Insert Screenshot 8: Dockerfiles and container build configuration]**

## 6. Preparing Kubernetes for the application

With the application containerised, I moved to Kubernetes deployment.

I used two dedicated namespaces:

```text
microservices
observability
```

The `microservices` namespace contains the three application services.

The `observability` namespace contains the monitoring and logging infrastructure.

This separation makes it easier to manage workloads and understand which components belong to the application and which belong to its monitoring platform.

### 6.1 Creating the namespaces

The namespace configuration is maintained in:

```text
kubernetes/namespaces/namespaces.yaml
```

A simplified version looks like:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: microservices
---
apiVersion: v1
kind: Namespace
metadata:
  name: observability
```

Apply the configuration using:

```bash
kubectl apply -f kubernetes/namespaces/namespaces.yaml
```

Verify the namespaces:

```bash
kubectl get namespaces
```

### 6.2 Deploying the application

The application deployment configuration is stored in:

```text
kubernetes/application/deployments.yaml
```

The service definitions are stored in:

```text
kubernetes/application/services.yaml
```

The application uses three Kubernetes Deployments:

- `api-gateway`
- `order-service`
- `payment-service`

Each deployment was configured with one replica for this local assignment environment.

The services communicate using Kubernetes DNS names.

For example:

```text
http://order-service:8001
```

and:

```text
http://payment-service:8002
```

The API Gateway uses the Order Service URL, while the Order Service uses the Payment Service URL.

This avoids hardcoding individual pod IP addresses. Kubernetes Services provide stable internal names even when pods are replaced.

### 6.3 Application resource management

I configured CPU and memory requests and limits for the application containers.

The application resource settings included:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 64Mi
  limits:
    cpu: 500m
    memory: 128Mi
```

Requests help Kubernetes understand the resources a container needs when scheduling workloads.

Limits help prevent a container from consuming unlimited CPU or memory.

### 6.4 Health checks

I also configured readiness and liveness probes.

These probes use the application's `/health` endpoint.

A readiness probe tells Kubernetes whether a container is ready to receive traffic.

A liveness probe helps Kubernetes identify a container that is no longer functioning properly and may need to be restarted.

These checks are particularly useful when working with microservices because an application can be running as a process without necessarily being ready to serve requests.

### 6.5 Kubernetes security context

The deployment configuration includes security settings similar to:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 999
  runAsGroup: 999
  seccompProfile:
    type: RuntimeDefault
```

Container-level settings include:

```yaml
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL
```

These settings were part of the effort to apply basic container security practices rather than deploying privileged containers by default.


![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/ek4ftasv5pux8pl0ylry.png)


Kubernetes deployments and security configuration

### 6.6 Kubernetes resource quotas

I also created resource quota configuration under:

```text
kubernetes/resources/resource-quotas.yaml
```

Resource quotas help control the total resource consumption of workloads in a namespace.

This is useful in shared Kubernetes environments where several applications may compete for cluster resources.

The local environment had limited resources, so resource management was important when deploying Prometheus, Grafana, Loki, Alloy and Tempo alongside the application.

### 6.7 Validating the deployments

I used:

```bash
kubectl get pods -n microservices

kubectl get services -n microservices

kubectl get deployments -n microservices
```

![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/fe69ntezk106kwte2lsb.png)


The three application pods eventually reached:

```text
api-gateway       1/1 Running
order-service     1/1 Running
payment-service   1/1 Running
```

This confirmed that the application workloads were running successfully in Kubernetes.

## 7. Installing Prometheus and Grafana

The next major stage was building the monitoring layer.

I used Prometheus to collect application and infrastructure metrics and Grafana to visualise those metrics.

### 7.1 What is Prometheus?

Prometheus is an open-source monitoring and time-series database system.

In simple terms, it collects numerical information about an application or infrastructure and stores that information over time.

For example, Prometheus can collect:

- How many requests an application receives.
- How many requests fail.
- How long requests take.
- How much CPU a node uses.
- How much memory is available.
- How many times a container restarts.

These values can then be queried to understand the behaviour of the system.

### 7.2 What is Grafana?

Grafana is the visualisation and observability interface.

Instead of manually reading hundreds of numerical values, Grafana allows an engineer to create dashboards containing charts, tables and other visual panels.

Grafana also provides Explore, where an engineer can write queries directly against Prometheus, Loki or Tempo.

For this assignment, Grafana was the central interface for monitoring, logs, traces and alert management.

### 7.3 Installing kube-prometheus-stack

I used the `kube-prometheus-stack` Helm chart from the Prometheus Community repository.

The chart provides an integrated monitoring stack, including Prometheus, Grafana, Alertmanager, node-exporter, kube-state-metrics and supporting components.

I added the Helm repository:

```bash
helm repo add prometheus-community \
  https://prometheus-community.github.io/helm-charts

helm repo update
```


![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/2k47f77wx4bb4in1x08h.png)



The Helm values were maintained in:

```text
observability/kube-prometheus-stack-values.yaml
```

I used a custom values file to configure the stack and keep its resource requirements appropriate for the local environment.

The Helm release was installed in the observability namespace.

The general deployment pattern is:

```bash
helm upgrade --install observability \
  prometheus-community/kube-prometheus-stack \
  --namespace observability \
  --create-namespace \
  -f observability/kube-prometheus-stack-values.yaml
```

![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/l3dbcd0qb59ky84x1ju0.png)


The exact chart configuration is maintained in the repository values file.

### 7.4 Verifying Prometheus

After deployment, I checked the monitoring pods:

```bash
kubectl get pods -n observability
```

![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/br3fso8epfsfdpriotst.png)


I also checked the ServiceMonitors:

```bash
kubectl get servicemonitors -n observability
```

Prometheus was able to discover monitoring targets and collect metrics.

One important point during validation was that some Kubernetes control-plane targets reported as unavailable in the local Minikube environment. This did not prevent the application metrics or the required dashboards from working.

### 7.5 Application metrics

The application exposes a `/metrics` endpoint for Prometheus to scrape.

The main HTTP metrics are:

```text
http_requests_total
http_request_duration_seconds
```

The HTTP request counter uses labels such as:

- `service`
- `method`
- `route`
- `status`

This allows requests to be grouped by service, HTTP method, route and response status.

The request duration histogram allows latency to be measured and percentiles such as p99 to be calculated.

The business metrics include:

```text
orders_created_total
orders_failed_total
payments_approved_total
payments_declined_total
```

These metrics provide information about application behaviour beyond basic infrastructure monitoring.

For example, CPU usage can tell us that a container is consuming resources, but `orders_created_total` tells us whether the application is successfully processing its intended business activity.

### 7.6 Understanding the RED method

I used the RED method for the service overview dashboard.

RED stands for:

- **Rate:** How many requests are being handled?
- **Errors:** How many requests are failing?
- **Duration:** How long do requests take?

These three measurements provide a useful overview of a service's health.

A service may be receiving many requests but also returning a high number of errors.

Another service may have a low error rate but be taking several seconds to respond.

Looking at these measurements together provides a better understanding than looking at request counts alone.

## 8. Building the Grafana dashboards

The assignment required three dashboards.

I created the dashboards in Grafana and used Prometheus and Loki as their data sources.

### 8.1 Infrastructure Monitoring dashboard

The first dashboard focuses on the Kubernetes infrastructure.

It contains four panels:

1. CPU usage.
2. Memory usage.
3. Disk usage.
4. Network traffic.

The purpose is to understand whether the underlying infrastructure has enough resources to support the application and observability workloads.

For example, if memory usage becomes unusually high, it may explain why a container is being terminated or restarted.

If disk space becomes low, it may affect applications that depend on persistent storage.

The network panels help identify changes in traffic entering and leaving the node.

For network traffic, I used Prometheus queries similar to:

```promql
rate(node_network_receive_bytes_total{device="eth0"}[5m])
```

```promql
rate(node_network_transmit_bytes_total{device="eth0"}[5m])
```

These queries calculate the rate of network bytes received and transmitted over a five-minute window.

The disk dashboard was configured for the actual Minikube filesystem mount being monitored:

```promql
node_filesystem_avail_bytes{
  mountpoint="/data",
  fstype="ext4",
  device="/dev/sdd"
}
```

The exact filesystem selectors matter. A query using the wrong device or mount point may return no data or monitor the wrong filesystem.


![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/naxibtvpsldwt5gousug.png)

Infrastructure Monitoring dashboard



### 8.2 Service Overview (RED) dashboard

The second dashboard focuses on application performance.

It contains:

- Request Rate by Service.
- Error Rate by Service.
- Request Latency p99 by Service.

#### Request rate

The query groups request rates by service:

```promql
sum by (service) (
  rate(http_requests_total[5m])
)
```

This shows the approximate number of requests handled per second by each service over the selected five-minute window.

#### Error rate

The error rate measures the percentage of HTTP 5xx responses.

The query uses the total request rate as the denominator and the 5xx request rate as the numerator.

The implementation includes zero-filling so that services without observed 5xx responses can still appear in the result.

```promql
(
  (
    sum by (service) (
      rate(http_requests_total{status=~"5.."}[5m])
    )
    or
    (
      0 * sum by (service) (
        rate(http_requests_total[5m])
      )
    )
  )
  /
  clamp_min(
    sum by (service) (
      rate(http_requests_total[5m])
    ),
    0.000001
  )
) * 100
```

The result is multiplied by 100 to display a percentage.

#### p99 latency

The p99 latency query is:

```promql
histogram_quantile(
  0.99,
  sum by (le, service) (
    rate(http_request_duration_seconds_bucket[5m])
  )
)
```

The 99th percentile indicates the latency below which approximately 99% of observed requests fall, based on the histogram distribution.

For example, a p99 latency of one second means that approximately 99% of the requests in the measured distribution completed within one second.

This is useful because averages can hide slow requests. A service may have a good average response time while a small percentage of users experience very slow requests.



![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/hi102w3175lqokfm2g86.png)


Service Overview (RED) dashboard


### 8.3 Application Logs dashboard

The third dashboard focuses on application logs.

It contains:

- Application Log Volume by Service.
- Application Error Count by Service.
- Recent Application Errors.

This dashboard uses Loki as its data source.

The purpose is to make application activity easier to investigate without manually logging into each Kubernetes pod.

For example, if the error rate suddenly increases, an engineer can inspect the logs to understand what the application recorded around that time.

The log volume panel shows how many application log entries are being generated.

The error count panel filters records with the `ERROR` level.

The recent errors panel displays the actual matching log messages.


![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/ohcsp5n5hay6j6u5z7x4.png)


Application Logs dashboard

## 9. Centralised logging with Loki and Grafana Alloy

Monitoring metrics alone is not enough to understand every application problem.

Metrics can tell us that errors are increasing, but they do not necessarily explain what happened inside the application.

This is where centralised logging becomes useful.


### 9.1 What is Loki?

Loki is a log aggregation system.

It stores application logs and allows users to query them using LogQL.

Rather than logging into each application container individually, an engineer can search logs centrally through Grafana.

### 9.2 What is Grafana Alloy?

Grafana Alloy is the telemetry collector used in this assignment to collect Kubernetes container logs and forward them to Loki.

I deployed Alloy as a Kubernetes DaemonSet.

A DaemonSet ensures that the log collector runs on the Kubernetes nodes so it can discover and collect container logs from the node.

The configuration is stored in:

```text
observability/alloy/values.yaml
```

The log collection pipeline was configured to:

1. Discover Kubernetes pods.
2. Keep logs from the `microservices` namespace.
3. Extract useful Kubernetes metadata.
4. Read container log files.
5. Parse the container runtime log format.
6. Forward the logs to Loki.

The Loki push endpoint used was:

```text
http://loki.observability.svc.cluster.local:3100/loki/api/v1/push
```

This uses Kubernetes internal DNS rather than an external address.

### 9.3 Understanding structured logs

The application writes structured JSON logs.

A simplified example is:

```json
{
  "timestamp": "2026-11-19T15:51:29.842863+00:00",
  "level": "INFO",
  "service": "payment-service",
  "message": "Payment approved",
  "payment_id": "pay-example",
  "customer_id": "customer-001",
  "status": "approved"
}
```

Structured logging is useful because the information is organised into fields.

Instead of searching an unstructured paragraph of text, I can filter by:

- Service name.
- Log level.
- Message.
- Status.
- Other available fields.

### 9.4 An important log parsing challenge

One of the issues I encountered was that the application JSON was not immediately available as the top-level JSON structure in Loki.

The Kubernetes container log collector wrapped the application output in another log record.

The application JSON was contained in the outer `log` field.

This meant that simply applying a JSON parser once did not expose the application fields in the way I expected.

I corrected the query by extracting the inner log content and parsing it again.

The working LogQL pipeline was:

```logql
{namespace="microservices"}
| json
| line_format "{{.log}}"
|~ "^\\{"
| json
```

This pipeline:

1. Selects logs from the `microservices` namespace.
2. Parses the outer container log record.
3. Extracts the inner application log.
4. Filters for JSON-formatted application messages.
5. Parses the application JSON fields.

To display only application error records, I added:

```logql
| level="ERROR"
```

This was an important lesson: log collection and log parsing are two different things. A log can successfully arrive in Loki while still requiring the correct parsing pipeline before its fields can be queried.

### 9.5 Application log volume query

The log volume panel uses a query similar to:

```logql
sum by (service) (
  count_over_time(
    {namespace="microservices"}
    | json
    | line_format "{{.log}}"
    |~ "^\\{"
    | json
    [5m]
  )
)
```

This counts application log entries over a five-minute window and groups the results by service.

### 9.6 Application error count query

The error count panel uses:

```logql
sum by (service) (
  count_over_time(
    {namespace="microservices"}
    | json
    | line_format "{{.log}}"
    |~ "^\\{"
    | json
    | level="ERROR"
    [5m]
  )
)
```

This filters the structured application logs to entries whose level is `ERROR`.

### 9.7 Recent error logs

To display recent errors, I used:

```logql
{namespace="microservices"}
| json
| line_format "{{.log}}"
|~ "^\\{"
| json
| level="ERROR"
```

This makes it possible to see the actual error records instead of only a numerical error count.

### 9.8 Validating log collection

I generated a controlled synthetic error event in the Order Service container to validate the logging pipeline.

The command used was:

```bash
kubectl exec -n microservices deployment/order-service -- \
  sh -c 'printf "%s\n" '\''{"level":"ERROR","service":"order-service","message":"Controlled observability test error","error":"Synthetic observability validation event"}'\'' > /proc/1/fd/2'
```

This writes the test JSON record to the main process's standard error stream.

I then queried Loki using the structured error filter.

The record appeared successfully.

This confirmed that Alloy was collecting the container output, forwarding it to Loki and making the structured error fields available for querying.

It is important to distinguish this from a real application failure: the event was deliberately generated to test log collection and filtering. It was not a failed customer transaction or an HTTP 500 response.

## 10. Distributed tracing with OpenTelemetry and Tempo

Metrics show what is happening numerically. Logs show what the application recorded. Distributed tracing helps explain how an individual request moves through multiple services.

This is particularly important in a microservices architecture.

### 10.1 What is distributed tracing?

Imagine a customer sends an order request.

The request reaches the API Gateway, which forwards it to the Order Service. The Order Service then sends a request to the Payment Service.

From the customer's perspective, this is one request.

From the application's perspective, it involves several separate HTTP operations.

Without distributed tracing, investigating a slow request could require checking several services independently and trying to match their log timestamps.

Distributed tracing provides a way to connect those operations under one trace.

A trace is made up of spans. Each span represents an operation that took place during the request.

The spans can show:

- Which service handled the operation.
- What operation was performed.
- When it started.
- How long it took.
- How it relates to other operations.

### 10.2 What is OpenTelemetry?

OpenTelemetry is an open-source observability framework used to generate and export telemetry data.

In this assignment, it was used for distributed tracing.

The Python services were instrumented so that incoming HTTP requests and outgoing HTTPX requests could participate in trace generation and context propagation.

The services were configured to send trace data to Tempo through the OpenTelemetry Protocol (OTLP).

The configured endpoint was:

```text
http://tempo.observability.svc.cluster.local:4317
```

Port `4317` is used for OTLP over gRPC.

### 10.3 What is Tempo?

Tempo is Grafana's distributed tracing backend.

It receives trace data, stores it and allows Grafana to search and display the traces.

I deployed Tempo using Helm.

The local assignment configuration used:

- One Tempo replica.
- Local storage.
- A 2 GiB persistent volume claim.
- A 24-hour trace retention configuration.
- OTLP ports 4317 and 4318.
- Query port 3200.
- Configured CPU and memory resources.

The Tempo service was available internally at:

```text
tempo.observability.svc.cluster.local:3200
```

The persistent volume claim was successfully bound, and the Tempo pod reached the Running state.

### 10.4 Connecting Tempo to Grafana

I added Tempo as a Grafana data source using its Kubernetes internal service address.

Grafana was able to connect successfully.

This allowed me to search for traces through:

```text
Grafana → Explore → Tempo
```

### 10.5 Trace context propagation

A critical part of distributed tracing is context propagation.

When the API Gateway sends a request to the Order Service, the trace context must travel with that request.

The Order Service must then propagate the same context when it communicates with the Payment Service.

Without context propagation, each service might generate a separate trace, making it difficult to understand the complete request path.

The application instrumentation used OpenTelemetry, with HTTPX instrumentation to support outgoing HTTP request tracing and propagation.

### 10.6 Validating the complete trace

I generated an order request through the API Gateway and searched for it in Grafana Tempo.

One of the verified traces had the following information:

```text
Trace ID:
adb027267de3250bbde84835176e50d8

Start time:
2026-11-19 17:37:37.371

Duration:
183.71 ms

Services:
3

Spans:
14

Route:
/orders
```

The trace detail showed:

```text
api-gateway
POST /orders
```

The earlier trace also displayed the complete service path:

```text
api-gateway POST /orders
    |
    v
order-service POST /orders
    |
    v
payment-service POST /payments
```

The trace showed three services and 14 spans.

This was one of the most important validation points in the assignment because it demonstrated that tracing was not simply installed as an independent tool. It was receiving traces from the actual application request flow.

The total trace duration and individual span durations also helped demonstrate how time was distributed across the services.

For example, the earlier trace showed an overall duration of approximately 288 milliseconds, with the Order Service and Payment Service operations visible within the same trace.

This is the practical value of distributed tracing: instead of guessing which service caused a delay, an engineer can inspect the individual operations that made up the request.


## 11. Configuring Grafana alerting

Monitoring is useful, but someone cannot sit in front of a dashboard all day waiting for a problem to happen.

That is why alerting is important.

An alert rule checks a condition and changes state when the condition is met.

For example, if the HTTP error rate stays above a defined threshold for a period of time, Grafana can trigger an alert and send a notification.

I configured five Grafana-managed alert rules in a folder named:

```text
Microservices Observability
```

The rules were configured through the Grafana interface.

### 11.1 High HTTP Error Rate

**Purpose:** Detect when a service starts returning too many HTTP 5xx responses.

The alert condition was:

```text
Error rate > 5%
For 5 minutes
```

The PromQL expression uses the same service-level error rate calculation used by the RED dashboard.

The purpose is to avoid treating one isolated error as an immediate incident.

A sustained error rate above the threshold is more likely to indicate a service problem that needs investigation.

Possible investigation areas include:

- Application logs in Loki.
- Distributed traces in Tempo.
- Kubernetes pod status.
- Upstream service availability.
- Recent deployment changes.


### 11.2 High p99 Latency

**Purpose:** Detect when application requests become unusually slow.

The alert condition was:

```text
p99 latency > 1 second
For 5 minutes
```

The rule uses the histogram-based latency calculation.

This is useful because average latency can hide a small group of very slow requests.

A sustained increase in p99 latency may indicate:

- Slow downstream services.
- Resource constraints.
- Application performance problems.
- Network delays.
- Database or dependency delays.

### 11.3 Excessive Pod Restarts

**Purpose:** Identify containers that repeatedly restart.

The query used was:

```promql
sum by (namespace, pod, container) (
  increase(
    kube_pod_container_status_restarts_total{
      namespace="microservices"
    }[1h]
  )
)
```

The condition was:

```text
More than 3 restarts within 1 hour
```

Repeated restarts may indicate:

- Application crashes.
- Failed health checks.
- Out-of-memory termination.
- Configuration problems.
- Dependency failures.

The alert helps an engineer identify unstable workloads before they create a bigger application problem.

### 11.4 Kubernetes Node Not Ready

**Purpose:** Detect when a Kubernetes node is no longer reporting itself as ready.

The query used was:

```promql
kube_node_status_condition{
  condition="Ready",
  status="false"
}
```

The condition checks for a value above zero and was configured with a five-minute pending period.

This is useful because a node becoming NotReady can affect the scheduling and availability of workloads.

During configuration, I encountered a query issue where filtering the condition with an additional equality check returned no data.

The reason was that the relevant `status="false"` series existed with a value of zero during normal operation.

I adjusted the query to evaluate the series directly.

The alert subsequently settled into the Normal state when the node was healthy.

### 11.5 Low Disk Space

**Purpose:** Detect when the monitored filesystem has less than 10% available space.

The query was:

```promql
(
  node_filesystem_avail_bytes{
    mountpoint="/data",
    fstype="ext4",
    device="/dev/sdd"
  }
  /
  node_filesystem_size_bytes{
    mountpoint="/data",
    fstype="ext4",
    device="/dev/sdd"
  }
) * 100
```

The alert condition was:

```text
Available disk space < 10%
```

The query calculates the percentage of available space rather than the percentage already used.

This distinction is important.

For example, a filesystem with 90% available space is not close to the alert threshold, while a filesystem with only 5% available space is.

I checked the actual filesystem with:

```bash
minikube ssh -- df -h /data
```

The observed filesystem had approximately 90.5% available space, so the alert correctly remained Normal.

### 11.6 Alert severity and descriptions

The rules included labels and annotations to help identify the type and importance of an alert.

Examples of labels used included:

```text
team=platform
environment=local
severity=critical
alert_type=node_health
```

The alert descriptions were written to explain what had happened and provide an investigation direction.

For example, an HTTP error rate alert should tell the engineer which service has exceeded the threshold and where to begin investigating.

### 11.7 Alert state validation

After configuring the five rules, I checked their states in Grafana.

All five rules were in the Normal state during the final validation.

This was the expected result because the test environment was healthy and the alert thresholds were not being exceeded.

An alert being Normal does not mean the alert is unnecessary. It means the monitored condition is currently below its configured threshold.

## 12. Notification routing and email delivery

An alert is more useful when the right person receives a notification.

I configured a Grafana contact point named:

```text
Observability-notification
```

The notification recipient was the configured project email address.

I also configured a notification policy with a child route matching:

```text
team=platform
```

This route directs matching alerts to the configured contact point.

### 12.1 SMTP configuration

The initial SMTP setup used Gmail SMTP.

The connection to Gmail was established, but the authentication attempts were unsuccessful in the environment.

Rather than spending the entire assignment troubleshooting the original SMTP provider, I moved to Brevo's SMTP relay.

I configured Grafana to use:

```text
smtp-relay.brevo.com:587
```

The SMTP credentials were stored in a Kubernetes Secret named:

```text
grafana-smtp
```

The Grafana Helm values referenced the secret through environment variables.

A simplified example of the configuration pattern is:

```yaml
grafana:
  grafana.ini:
    smtp:
      enabled: true
      host: smtp-relay.brevo.com:587
      user: $__env{GF_SMTP_USER}
      password: $__env{GF_SMTP_PASSWORD}
      from_address: sender@example.com
      from_name: Microservices Observability
      startTLS_policy: MandatoryStartTLS
```

The actual username and password were supplied through Kubernetes Secret references rather than being written directly into the configuration file.

This is important because SMTP credentials should not be committed to GitHub or exposed in project screenshots.

### 12.2 Troubleshooting SMTP authentication

The first Brevo test returned an authentication error indicating that the connecting IP address was not authorised.

I checked the Brevo security settings and authorised the blocked IP address.

After that, the Grafana contact point test succeeded and the notification arrived in the configured Gmail inbox.

The received email had the Grafana test notification subject:

```text
[FIRING:1] TestAlert Grafana
```

This confirmed that Grafana could communicate with the SMTP relay and deliver an email notification.

The successful test validated the contact point and email delivery path. It was a contact-point test, not a demonstration of a real production incident triggering an alert.

## 13. Writing operational runbooks

Configuring alerts is only part of an operational monitoring solution.

When an alert fires, an engineer needs to know what to do next.

That is why I created five runbooks.

A runbook is a practical guide that explains how to investigate and respond to a particular problem.

The runbooks were stored in:

```text
runbooks/
```

The files created were:

```text
runbooks/
├── high-http-error-rate.md
├── high-p99-latency.md
├── pod-excessive-restarts.md
├── kubernetes-node-not-ready.md
└── low-disk-space.md
```

Each runbook includes:

- Overview of the alert.
- Severity.
- Trigger condition.
- Potential impact.
- Possible causes.
- Investigation steps.
- Relevant Grafana queries.
- Kubernetes commands.
- Recovery guidance.
- Verification steps.
- Escalation guidance.

### 13.1 Example: investigating pod restarts

When the excessive pod restarts alert fires, the first step is to identify the affected pod.

```bash
kubectl get pods -n microservices
```

Then inspect the pod:

```bash
kubectl describe pod <pod-name> -n microservices
```

Check the previous container logs:

```bash
kubectl logs <pod-name> \
  -n microservices \
  --previous
```

The previous logs are useful because a container may restart before an engineer has an opportunity to inspect its current output.

The next step is to inspect the pod events and determine whether the restart was caused by an application crash, a failed probe, an out-of-memory condition or another issue.

### 13.2 Why runbooks matter

A monitoring dashboard tells an engineer what is happening.

An alert tells the engineer that something needs attention.

A runbook helps the engineer decide what to do next.

This reduces the time spent guessing during an incident and makes operational response more consistent.

## 14. Testing the complete application

After configuring the application and observability stack, I moved to validation.

I did not want to finish the assignment with a collection of running pods and dashboards that had never been tested against real application activity.

The purpose of validation was to confirm that the application worked and that the observability tools were receiving useful data.

### 14.1 Checking Kubernetes workloads

I checked the application pods:

```bash
kubectl get pods -n microservices
```

I checked the application services:

```bash
kubectl get services -n microservices
```

I also checked the observability pods:

```bash
kubectl get pods -n observability
```

The three application pods were running successfully.

The observability workloads, including Prometheus, Grafana, Loki, Alloy and Tempo, were also running.

### 14.2 Accessing the API Gateway

I used Kubernetes port forwarding to access the API Gateway locally.

```bash
kubectl port-forward \
  -n microservices \
  service/api-gateway \
  8081:8000
```

The port-forward process needs to remain open while testing through localhost.

I tested the health endpoint:

```bash
curl -i http://localhost:8081/health
```

The service returned:

```http
HTTP/1.1 200 OK
```

With a response similar to:

```json
{
  "status": "healthy",
  "service": "api-gateway"
}
```

This confirmed that the API Gateway was responding.

### 14.3 Testing the order workflow

I then sent an order request through the API Gateway.

The test request was:

```bash
curl -i -X POST http://localhost:8081/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "customer-001",
    "item": "observability-test-product",
    "quantity": 2,
    "amount": 150.00
  }'
```

The first request I attempted during testing used the wrong field name, `product_id`, and returned HTTP 422.

After inspecting the expected request structure, I corrected the field to `item`.

The corrected request returned HTTP 200 and a successful order response.

The response included an order ID and an approved payment response.

This confirmed the application flow:

```text
API Gateway
     |
     v
Order Service
     |
     v
Payment Service
     |
     v
Approved Payment
     |
     v
Successful Order Response
```

This was an educational test transaction, not an actual financial payment.

## 15. Validating Prometheus application metrics

After generating application traffic, I opened Grafana Explore and selected Prometheus.

I queried the application request counter:

```promql
sum by (service) (
  increase(http_requests_total[5m])
)
```

This returned request activity for the three services.

I also checked the order business metric:

```promql
increase(orders_created_total[5m])
```

And the payment business metric:

```promql
increase(payments_approved_total[5m])
```

The results showed activity for:

- `api-gateway`
- `order-service`
- `payment-service`

The order and payment counters also recorded the test transaction.

One detail worth understanding is that Prometheus `increase()` can return fractional values for counters.

For example, a result may show approximately `1.04` rather than exactly `1`.

This does not mean the application created a fraction of an order. Prometheus estimates counter increases over the selected range and extrapolates at the boundaries.

The important validation was that the metrics were being collected and that the expected service and business metrics were present.

## 16. Validating Loki application logs

I opened Grafana Explore and selected Loki.

I first checked the namespace logs:

```logql
{namespace="microservices"}
```

This confirmed that application container logs were reaching Loki.

I then used the structured parsing pipeline to inspect the application messages.

For example, I searched for order-related request logs and confirmed that the API Gateway and Order Service had recorded the successful request.

The Payment Service also produced an application log indicating that the payment was approved.

The log included fields such as:

```json
{
  "level": "INFO",
  "service": "payment-service",
  "message": "Payment approved",
  "status": "approved"
}
```

I also verified that the controlled synthetic error event could be found using the `level="ERROR"` filter.

This confirmed that the logging pipeline could handle both normal application events and structured error records.

## 17. Validating Tempo distributed traces

I opened Grafana Explore and selected Tempo.

I searched for the API Gateway operation:

```text
Service Name = api-gateway
Span Name = POST /orders
```

Tempo returned traces for the order requests.

One of the latest validated traces showed:

```text
Trace ID:
adb027267de3250bbde84835176e50d8

Duration:
183.71 ms

Services:
3

Spans:
14
```

The earlier trace showed the complete service breakdown, including the API Gateway, Order Service and Payment Service.

This was important because it demonstrated that the trace context was being propagated across the service boundaries.

The trace was not just a collection of unrelated operations. It represented the same order request moving through the microservices application.

## 18. Final assignment validation

By the end of the implementation, the main assignment requirements had been configured and validated.

| Assignment requirement | Implementation result |
|---|---|
| Microservices application | Three FastAPI services deployed |
| Containerisation | Docker images built and deployed to Minikube |
| Kubernetes deployment | Application deployed in `microservices` namespace |
| Metrics collection | Prometheus collecting application metrics |
| Infrastructure monitoring | CPU, memory, disk and network panels configured |
| Service monitoring | Request rate, error rate and p99 latency panels configured |
| Centralised logging | Alloy collecting logs and forwarding to Loki |
| Log exploration | Structured application logs queryable in Grafana |
| Distributed tracing | OpenTelemetry traces stored in Tempo |
| Trace correlation across services | Three-service trace verified |
| Grafana dashboards | Three dashboards configured |
| Alert rules | Five Grafana-managed rules configured |
| Notification delivery | Contact point email test successful |
| Runbooks | Five operational runbooks created |
| Documentation | Project structure and evidence folders prepared |

The five alert rules were in the Normal state during final validation.

The application health check returned HTTP 200.

The end-to-end order request succeeded.

Prometheus returned application and business metric series.

Loki returned structured application logs.

Tempo returned distributed traces involving the three application services.

The contact point email test was successful.

These results provided evidence that the different parts of the platform were integrated rather than merely installed.

## 19. Challenges encountered and lessons learned

This assignment involved more than following installation instructions. Several issues required investigation and adjustment.

### 19.1 Managing local Kubernetes resources

Running an application, Prometheus, Grafana, Loki, Alloy and Tempo together on Minikube requires careful resource management.

The cluster was limited to a local development environment, so I configured resource requests and limits and used relatively small deployments.

I also kept the existing cluster and namespaces intact rather than deleting workloads to make room for the assignment.

**Lesson:** Resource planning matters even in local Kubernetes environments. Observability tools also consume CPU, memory and storage.

### 19.2 Application request validation

My first order test returned HTTP 422 because I used `product_id` instead of the expected `item` field.

I inspected the request structure and corrected the payload.

**Lesson:** An HTTP error does not always mean the application is broken. Sometimes the client is sending data that does not match the API contract.

### 19.3 Loki JSON parsing

The application logs were being collected, but the application JSON was nested inside the container log record.

I had to adjust the LogQL pipeline to extract the inner log and parse it again.

**Lesson:** Successful log collection does not automatically mean the log fields are immediately queryable. Understanding the structure of the collected log is essential.

### 19.4 Testing error logs

The application did not naturally generate an error during the successful order workflow.

I used a controlled synthetic JSON event written to the application process's standard error stream to validate the logging pipeline.

**Lesson:** Test data can help validate observability components, but it should be clearly distinguished from real application failures.

### 19.5 Prometheus alert queries

The Kubernetes Node Not Ready query initially returned no useful result because the condition series existed with a value of zero.

I adjusted the expression to evaluate the relevant series directly.

**Lesson:** Understanding the meaning of a Prometheus metric is just as important as knowing its name. A query can be syntactically correct and still produce the wrong result.

### 19.6 SMTP notification delivery

The initial Gmail SMTP authentication attempts were unsuccessful.

I moved to Brevo SMTP, stored the credentials in a Kubernetes Secret and authorised the blocked connecting IP address in Brevo.

The Grafana contact point test then succeeded.

**Lesson:** Notification configuration involves more than entering SMTP credentials. Provider security restrictions, sender verification and network authorisation can also affect delivery.

### 19.7 Trace verification

The first Tempo search results included background health and metrics requests.

I narrowed the search using the API Gateway service name and `POST /orders` span name.

This made it easier to locate the order request and inspect the trace details.

**Lesson:** Distributed tracing is most useful when searches are narrowed to the operation being investigated.

## 20. Security and operational considerations

Although this was a local assignment, I included several practices that are important when building real environments.

### Container security

The application containers run as a non-root user.

The Kubernetes security context disables privilege escalation, drops Linux capabilities and uses a read-only root filesystem.

### Kubernetes separation

Application workloads and observability workloads are separated into different namespaces.

### Resource limits

CPU and memory requests and limits were configured to help control resource usage.

### Credential management

SMTP credentials were stored in a Kubernetes Secret and referenced through the Grafana configuration.

Credentials should not be committed to source control.

### Local environment limitations

This assignment was validated on Minikube.

A production deployment would require additional work around high availability, persistent storage, backups, access control, retention, disaster recovery, scaling, network security and operational ownership.

The local implementation should therefore be understood as a working educational environment, not a production-ready multi-node observability service.

## 21. What I learned from this assignment

The most valuable part of this exercise was understanding how the different observability signals work together.

Before building the platform, it was easy to think of monitoring, logging and tracing as separate tools.

Working through the implementation made their relationship clearer.

Consider a situation where an application starts responding slowly.

**Prometheus** can show that request latency has increased.

**Grafana** can display the latency trend and show which service is affected.

**Loki** can help identify errors or unusual events recorded by the application.

**Tempo** can show how the request travelled between services and which operation consumed the most time.

**Alerting** can notify the responsible engineer when a defined threshold is exceeded.

**Runbooks** can guide the investigation and recovery process.

Together, these capabilities provide a more complete picture of an application than any one monitoring tool can provide on its own.

I also gained practical experience with:

- Building and containerising Python microservices.
- Deploying application workloads to Kubernetes.
- Managing Helm releases.
- Configuring Prometheus metrics.
- Writing PromQL and LogQL queries.
- Building Grafana dashboards.
- Collecting Kubernetes logs using Grafana Alloy.
- Instrumenting applications with OpenTelemetry.
- Searching and inspecting distributed traces in Tempo.
- Configuring Grafana alert rules and notification policies.
- Integrating SMTP email notifications.
- Writing operational runbooks.
- Validating an end-to-end application workflow.

## 22. Repository structure and important files

The implementation is organised into the following main areas:

```text

microservices-observability-platform/
│
├── app/
│   ├── api-gateway/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   └── main.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .dockerignore
│   │
│   ├── order-service/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   └── main.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .dockerignore
│   │
│   └── payment-service/
│       ├── app/
│       │   ├── __init__.py
│       │   └── main.py
│       ├── requirements.txt
│       ├── Dockerfile
│       └── .dockerignore
│
├── docker/
│   └── docker-compose.yml
│
├── kubernetes/
│   ├── application/
│   │   ├── deployments.yaml
│   │   └── services.yaml
│   ├── namespaces/
│   │   └── namespaces.yaml
│   └── resources/
│       └── resource-quotas.yaml
│
├── observability/
│   ├── alertmanager/
│   ├── alerts/
│   ├── alloy/
│   │   └── values.yaml
│   ├── grafana/
│   │   ├── dashboards/
│   │   └── datasources/
│   ├── loki/
│   ├── prometheus/
│   ├── tempo/
│   └── kube-prometheus-stack-values.yaml
│
├── runbooks/
│   ├── high-http-error-rate.md
│   ├── high-p99-latency.md
│   ├── pod-excessive-restarts.md
│   ├── kubernetes-node-not-ready.md
│   └── low-disk-space.md
│
├── scripts/
│
├── docs/
│   ├── architecture/
│   ├── evidence/
│   └── screenshots/
│
├── .gitignore
├── LICENSE
└── README.md
```

The main application source code is under `app/`.

The Kubernetes deployment manifests are under `kubernetes/`.

The observability configuration is under `observability/`.

The operational response documentation is under `runbooks/`.

This organisation keeps the application, deployment, monitoring and operational documentation easy to locate.

## 23. Useful commands from the implementation

These are some of the commands used to inspect and operate the environment.

### Check application pods

```bash
kubectl get pods -n microservices
```

### Check application services

```bash
kubectl get services -n microservices
```

### Check observability workloads

```bash
kubectl get pods -n observability
```

### Check deployments

```bash
kubectl get deployments -n microservices
```

### Check service monitors

```bash
kubectl get servicemonitors -n observability
```

### Inspect application logs

```bash
kubectl logs deployment/api-gateway -n microservices
```

```bash
kubectl logs deployment/order-service -n microservices
```

```bash
kubectl logs deployment/payment-service -n microservices
```

### Inspect pod events and configuration

```bash
kubectl describe pod <pod-name> -n microservices
```

### Port-forward Grafana

```bash
kubectl port-forward \
  -n observability \
  svc/observability-grafana \
  3001:80
```

Grafana was accessed locally at:

```text
http://localhost:3001
```

### Port-forward the API Gateway

```bash
kubectl port-forward \
  -n microservices \
  service/api-gateway \
  8081:8000
```

The application health endpoint was then available at:

```text
http://localhost:8081/health
```

### Check Helm releases

```bash
helm list -n observability
```

These commands are useful starting points when another engineer wants to inspect the running environment.





## 24. Conclusion

Building this observability platform gave me an opportunity to connect several important areas of Cloud Engineering and DevOps in one practical assignment.

I started with a simple three-service application and gradually built the infrastructure needed to monitor it.

I containerised the services, deployed them to Kubernetes, installed the observability stack, exposed application metrics, collected structured logs, implemented distributed tracing, created Grafana dashboards, configured alert rules and tested email notification delivery.

More importantly, I validated the components using actual application activity.

I confirmed that the API Gateway could receive an order request, that the Order Service could communicate with the Payment Service, that Prometheus collected the application metrics, that Loki received the application logs and that Tempo captured traces involving all three services.

I also learned that observability is not simply about collecting data. It is about making that data useful when someone needs to understand or troubleshoot an application.



![Image description](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/hwty77aujy1n6l4avy7j.png)



A dashboard should answer a question. An alert should identify a condition that needs attention. A log should provide useful context. A trace should help explain how a request travelled through the system. A runbook should help an engineer decide what to do next.

That is the bigger lesson I took from this assignment.

The work has also given me a stronger practical foundation for the next stage of my Cloud and DevOps learning journey, particularly around Kubernetes, monitoring, logging, distributed systems and operational troubleshooting.

**This completes my hands-on assignment: Build an Observability Platform for a Microservices App.**

---

## Author

**Jamiu Olatunji Bakre**  
Cloud & DevOps Engineer | Kubernetes | Docker | AWS | Terraform | CI/CD

Technical brand: **CloudWithHorla**

Portfolio: https://jahmeeu-cloud.github.io/portfolio-project/  
Dev.to: https://dev.to/jamiu_cloud/  
Docker Hub: https://hub.docker.com/u/horlacloud

## License

This assignment documentation and its associated project materials are released under the MIT License.

See the `LICENSE` file in the repository for the full license text.

---

*Thank you for reading. I hope this walkthrough helps another engineer understand not only how to deploy an observability stack, but also why metrics, logs, traces and alerting are important when operating a microservices application.*

---

**Author:** Jamiu Olatunji Bakre  
**Technical Brand:** CloudWithHorla  
**Assignment:** Build an Observability Platform for a Microservices App  
**Environment:** Ubuntu 24.04 on WSL, Docker, Minikube, Kubernetes and Helm  
**Application Stack:** Python, FastAPI, HTTPX  
**Observability Stack:** Prometheus, Grafana, Loki, Grafana Alloy, Tempo, OpenTelemetry and Alertmanager  
**License:** MIT
