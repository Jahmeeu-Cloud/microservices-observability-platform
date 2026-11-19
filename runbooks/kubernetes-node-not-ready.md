# Runbook: Kubernetes Node Not Ready

## 1. Alert Overview

- **Alert:** Kubernetes Node Not Ready
- **Severity:** Critical
- **Trigger:** A Kubernetes node reports Ready=false for 5 minutes.
- **Environment:** Local Minikube cluster.

## 2. Impact

- Pods may become unavailable.
- New workloads may not be scheduled.
- Existing applications may experience disruption.
- Cluster capacity may be reduced.

## 3. Possible Causes

- Kubelet failure.
- Node resource exhaustion.
- Container runtime problems.
- Network connectivity problems.
- Disk or memory pressure.
- Minikube or Docker host resource constraints.

## 4. Investigation

### Step 1: Check node status

```bash
kubectl get nodes -o wide
```

Identify nodes that are NotReady.

### Step 2: Inspect node conditions

```bash
kubectl describe node minikube
```

Inspect:

- Conditions.
- Ready status.
- MemoryPressure.
- DiskPressure.
- PIDPressure.
- Events.

### Step 3: Check system pods

```bash
kubectl get pods -n kube-system
```

Look for unhealthy system components.

### Step 4: Check Minikube status

```bash
minikube status
```

### Step 5: Inspect node resources

```bash
minikube ssh -- free -h
minikube ssh -- df -h
```

Check available memory and disk space.

### Step 6: Inspect node health metrics

In Grafana → Explore → Prometheus:

```promql
kube_node_status_condition{
  condition="Ready",
  status="false"
}
```

A value above zero indicates a NotReady condition.

## 5. Recovery Actions

Depending on the identified cause:

- Investigate and restore kubelet health.
- Resolve confirmed disk or memory pressure.
- Investigate Docker resource constraints.
- Restore container runtime or network functionality.
- Check system component logs and events.

For this local Minikube environment, inspect the cause before considering a Minikube restart.

Do not delete or recreate the cluster as an initial recovery action.

## 6. Verification

```bash
kubectl get nodes
kubectl get pods -A
minikube status
```

Confirm that:

- The node reports Ready.
- Critical system pods are healthy.
- Microservices workloads are available.
- The alert returns to Normal.

## 7. Escalation

If the node remains NotReady:

- Capture node descriptions and events.
- Record Minikube status and resource utilisation.
- Preserve relevant system pod logs.
- Escalate to the platform engineering team.

## 8. Related Resources

- Grafana: http://localhost:3001
- Kubernetes node: minikube
- Kubernetes system namespace: kube-system
- Application namespace: microservices
