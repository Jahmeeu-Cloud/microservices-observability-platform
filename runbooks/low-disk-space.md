# Runbook: Low Disk Space

## 1. Alert Overview

- **Alert:** Low Disk Space
- **Severity:** Critical
- **Trigger:** Filesystem available space falls below 10%.
- **Monitored filesystem:** Minikube /data mount.

## 2. Impact

- Applications may fail to write files.
- Container workloads may fail.
- Kubernetes components may experience disk pressure.
- Logs and persistent data may stop being written.
- Pods may be evicted if node storage becomes critically low.

## 3. Possible Causes

- Excessive application logs.
- Accumulation of unused container images.
- Large temporary files.
- Growing persistent volumes.
- Uncontrolled application data growth.
- Insufficient disk capacity.

## 4. Investigation

### Step 1: Check the filesystem

```bash
minikube ssh -- df -h /data
```

Inspect total, used and available space.

### Step 2: Inspect filesystem metrics

In Grafana → Explore → Prometheus:

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

This query reports available filesystem space as a percentage.

### Step 3: Inspect Kubernetes node conditions

```bash
kubectl describe node minikube
```

Look for DiskPressure.

### Step 4: Inspect persistent volumes

```bash
kubectl get pvc -A
kubectl get pv
```

Identify storage claims and volumes that may be consuming capacity.

### Step 5: Inspect container storage

```bash
minikube ssh -- sudo du -sh /var/lib/docker 2>/dev/null
```

Use this as an initial size check; investigate large directories before removing anything.

## 5. Recovery Actions

Depending on the identified cause:

- Identify and safely remove unnecessary temporary files.
- Review excessive log generation and retention.
- Identify unused container images before considering cleanup.
- Investigate persistent volume growth.
- Expand storage capacity when necessary and supported.

Never manually delete Kubernetes-managed data or persistent volume contents without confirming ownership and backup requirements.

Avoid broad Docker prune commands on this shared Minikube cluster.

## 6. Verification

```bash
minikube ssh -- df -h /data
kubectl describe node minikube
kubectl get pods -A
```

Confirm that:

- Available filesystem space is above 10%.
- DiskPressure is false.
- Workloads remain healthy.
- The alert returns to Normal.

## 7. Escalation

If disk usage continues increasing:

- Record filesystem usage and growth rate.
- Identify the largest consumers.
- Preserve relevant logs and storage information.
- Escalate to the platform engineering team.

## 8. Related Resources

- Grafana: http://localhost:3001
- Kubernetes node: minikube
- Monitored mount: /data
- Prometheus: Grafana Explore
