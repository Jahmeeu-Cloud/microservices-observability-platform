# Runbook: Excessive Pod Restarts

## 1. Alert Overview

- **Alert:** Excessive Pod Restarts
- **Severity:** Critical
- **Trigger:** A container experiences more than 3 restarts within 1 hour.
- **Affected namespace:** microservices.

## 2. Impact

- Application availability may be reduced.
- Requests may fail while containers restart.
- Services may become temporarily unavailable.
- Repeated crashes may indicate application or infrastructure problems.

## 3. Possible Causes

- Application crashes or unhandled exceptions.
- Out-of-memory termination (OOMKilled).
- Failed liveness probes.
- Incorrect application configuration.
- Missing environment variables or secrets.
- Dependency connectivity problems.
- Insufficient CPU or memory resources.

## 4. Investigation

### Step 1: Identify affected pods

```bash
kubectl get pods -n microservices
```

Check the RESTARTS column.

### Step 2: Inspect pod details

```bash
kubectl describe pod <pod-name> -n microservices
```

Inspect:

- Last State.
- Reason for termination.
- Restart count.
- Events.
- Liveness and readiness probe failures.

### Step 3: Inspect current container logs

```bash
kubectl logs <pod-name> -n microservices --tail=100
```

### Step 4: Inspect previous container logs

```bash
kubectl logs <pod-name> -n microservices --previous
```

This can reveal the reason for a previous crash.

### Step 5: Check resource utilisation

```bash
kubectl top pods -n microservices
kubectl top nodes
```

Look for memory or CPU pressure.

### Step 6: Inspect restart metrics

In Grafana → Explore → Prometheus:

```promql
sum by (namespace, pod, container) (
  increase(
    kube_pod_container_status_restarts_total{
      namespace="microservices"
    }[1h]
  )
)
```

## 5. Recovery Actions

Depending on the cause:

- Fix application exceptions or configuration errors.
- Correct missing or invalid environment variables.
- Investigate OOMKilled events and resource usage.
- Review and correct failing health probes.
- Restore connectivity to unavailable dependencies.
- Roll back a problematic deployment when appropriate.

Do not repeatedly delete pods without investigating why they are restarting.

## 6. Verification

```bash
kubectl get pods -n microservices
kubectl get deployments -n microservices
```

Check the affected deployment rollout:

```bash
kubectl rollout status deployment/<deployment-name> \
  -n microservices
```

Confirm that:

- Pods remain Ready.
- Restart counts stop increasing.
- Application health checks succeed.
- The alert returns to Normal.

## 7. Escalation

If restarts continue:

- Preserve current and previous container logs.
- Capture pod descriptions and Kubernetes events.
- Record the affected deployment and restart count.
- Escalate to the application or platform engineering team.

## 8. Related Resources

- Grafana: http://localhost:3001
- Kubernetes namespace: microservices
- Prometheus: Grafana Explore
- Loki: Grafana Explore
