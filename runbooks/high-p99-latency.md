# Runbook: High p99 Latency

## 1. Alert Overview

- **Alert:** High p99 Latency
- **Severity:** Warning
- **Trigger:** The 99th-percentile HTTP request latency exceeds 1 second for 5 minutes.
- **Affected services:** API Gateway, Order Service, Payment Service.

## 2. Impact

- Users experience slow responses.
- Order creation may take longer than expected.
- Payment processing may be delayed.
- Requests may time out.
- Slow downstream services may affect the entire request flow.

## 3. Possible Causes

- Slow application code or inefficient processing.
- High CPU or memory utilisation.
- Slow database queries or connection problems.
- A downstream service responding slowly.
- Network latency between services.
- Increased request volume.
- A recent deployment introducing a performance regression.

## 4. Investigation

### Step 1: Identify the affected service

Open Grafana:

http://localhost:3001

Navigate to Dashboards → Service Overview (RED).

Inspect the Request Latency p99 by Service panel.

### Step 2: Inspect request latency metrics

In Grafana → Explore → Prometheus, run:

```promql
histogram_quantile(
  0.99,
  sum by (le, service) (
    rate(http_request_duration_seconds_bucket[5m])
  )
)
```

Compare latency across the three services.

### Step 3: Inspect application logs

Open Grafana → Explore → Loki.

Investigate recent warnings and errors around the affected service.

### Step 4: Check resource utilisation

```bash
kubectl top pods -n microservices
kubectl top nodes
```

Look for unusually high CPU or memory consumption.

### Step 5: Check Kubernetes pod health

```bash
kubectl get pods -n microservices
kubectl get events -n microservices --sort-by=.lastTimestamp
```

Look for restarts, scheduling problems and resource-related events.

### Step 6: Inspect distributed traces

Open Grafana → Explore → Tempo.

Find slow traces and compare the duration of:

- API Gateway
- Order Service
- Payment Service

Identify which service or operation contributes most to overall latency.

## 5. Recovery Actions

Depending on the identified cause:

- Investigate and optimise slow application operations.
- Resolve resource pressure where confirmed.
- Restore connectivity to slow or unavailable dependencies.
- Investigate slow database operations if applicable.
- Roll back a recent deployment if it introduced the regression.
- Scale a service only when workload and resource evidence justify it.

Avoid increasing resource limits or replicas without first checking the cause.

## 6. Verification

```bash
kubectl get pods -n microservices
kubectl top pods -n microservices
```

Review the Service Overview dashboard.

Confirm that:

- p99 latency falls below 1 second.
- Requests complete successfully.
- Affected services are healthy.
- The alert returns to Normal.

## 7. Escalation

If latency remains elevated:

- Record the affected service.
- Preserve slow trace IDs.
- Capture relevant logs and resource metrics.
- Escalate to the application or platform engineering team.

## 8. Related Resources

- Grafana: http://localhost:3001
- Kubernetes namespace: microservices
- Prometheus: Grafana Explore
- Loki: Grafana Explore
- Tempo: Grafana Explore
