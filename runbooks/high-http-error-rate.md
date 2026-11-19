# Runbook: High HTTP Error Rate

## 1. Alert Overview

- **Alert:** High HTTP Error Rate
- **Severity:** Critical
- **Trigger:** HTTP 5xx error rate exceeds 5% for 5 minutes.
- **Affected services:** API Gateway, Order Service, Payment Service.

## 2. Impact

- Requests may fail or return server errors.
- Customers may be unable to create orders.
- Payment processing may fail.
- Dependent services may experience cascading failures.

## 3. Possible Causes

- Application exceptions or bugs.
- A downstream service is unavailable.
- Database connectivity problems.
- Invalid application configuration or environment variables.
- CPU or memory resource exhaustion.
- A recent deployment introducing a regression.

## 4. Investigation

### Step 1: Identify the affected service

Open Grafana at http://localhost:3001.

Navigate to Dashboards → Service Overview (RED).

Inspect the Error Rate by Service panel.

### Step 2: Inspect application logs

Open Grafana → Explore → Loki.

Run:

```logql
{namespace="microservices"} | json | level="ERROR"
```

Inspect recent errors and identify the affected service.

### Step 3: Check Kubernetes pods

```bash
kubectl get pods -n microservices
```

### Step 4: Inspect service logs

Replace <pod-name> with the affected pod:

```bash
kubectl logs <pod-name> -n microservices --tail=100
```

For logs from a previous container:

```bash
kubectl logs <pod-name> -n microservices --previous
```

### Step 5: Inspect distributed traces

Open Grafana → Explore → Tempo.

Inspect failed or unusually slow traces across:

API Gateway → Order Service → Payment Service.

## 5. Recovery Actions

Depending on the identified cause:

- Correct application configuration or environment variables.
- Restore connectivity to unavailable dependencies.
- Investigate database connectivity and availability.
- Roll back a recent deployment if it introduced the problem.
- Investigate unhealthy pods before restarting or replacing them.

Avoid restarting all services without identifying the cause.

## 6. Verification

```bash
kubectl get pods -n microservices
curl -i http://localhost:8081/health
```

Review the Service Overview dashboard.

Confirm that:

- HTTP 5xx error rate falls below 5%.
- Requests are succeeding.
- Affected pods are healthy.
- The alert returns to Normal.

## 7. Escalation

If the issue persists:

- Preserve relevant application logs and trace IDs.
- Record the affected service and incident start time.
- Escalate to the application or platform engineering team.

## 8. Related Resources

- Grafana: http://localhost:3001
- Kubernetes namespace: microservices
- Loki: Grafana Explore
- Tempo: Grafana Explore
