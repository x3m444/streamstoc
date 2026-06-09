# Kubernetes Deployment Guide

## Overview

This guide covers deploying your multi-service application (Django Stoc, Lotus, Traefik, DuckDNS) to Kubernetes. The manifests support production deployments with high availability, automatic scaling, and Let's Encrypt SSL.

## Prerequisites

1. **Kubernetes Cluster**: v1.24+
   - Local: Docker Desktop, Minikube, Kind
   - Cloud: EKS, AKS, GKE, DigitalOcean Kubernetes

2. **Tools**:
   ```bash
   kubectl version --client
   helm version  # Optional, for package management
   ```

3. **Docker Images**: Build and push to a registry
   ```bash
   docker build -t your-registry/stoc-django:latest ./django_app
   docker build -t your-registry/lotus-app:latest ./djangolotus
   docker push your-registry/stoc-django:latest
   docker push your-registry/lotus-app:latest
   ```

## Pre-Deployment Setup

### 1. Update Secrets

Edit `k8s-deployment.yaml` and replace placeholder values in the `django-secrets` Secret:

```yaml
stringData:
  SECRET_KEY: "your-secure-32-char-key-generated-with-openssl"
  DB_USER: "postgres"
  DB_PASS: "your-secure-database-password"
  DUCKDNS_TOKEN: "your-actual-duckdns-token"
```

Generate a secure SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Or
openssl rand -base64 32
```

### 2. Update Image Registry

Replace `your-registry` with your Docker registry (Docker Hub, ECR, GCR, etc.):

```bash
# If using Docker Hub
sed -i 's|your-registry|yourusername|g' k8s-deployment.yaml

# If using private registry, create a pull secret
kubectl create secret docker-registry regcred \
  --docker-server=your.registry.com \
  --docker-username=USERNAME \
  --docker-password=PASSWORD \
  --docker-email=your@email.com \
  -n stoc-app
```

### 3. Configure Domain Names

Update the Ingress resource to match your DuckDNS domain:

```yaml
- host: stoc.incercari.duckdns.org  # Replace with your domain
  http:
    paths:
    - path: /
      pathType: Prefix
      backend:
        service:
          name: django-stoc
          port:
            number: 8000
```

## Deployment Steps

### 1. Apply Manifests

```bash
kubectl apply -f k8s-deployment.yaml
```

This creates:
- `stoc-app` namespace
- PostgreSQL database with persistent storage
- Traefik Ingress Controller
- DuckDNS DNS updater
- Django Stoc deployment (2 replicas)
- Lotus deployment (2 replicas)
- Services for each component
- Ingress rules with TLS/SSL
- Horizontal Pod Autoscalers (HPA)

### 2. Verify Deployment

```bash
# Check namespace and resources
kubectl get ns
kubectl get all -n stoc-app

# Watch pod startup
kubectl get pods -n stoc-app -w

# Check pod status
kubectl describe pod <pod-name> -n stoc-app

# View logs
kubectl logs <pod-name> -n stoc-app -f

# Check Ingress
kubectl get ingress -n stoc-app
kubectl describe ingress stoc-ingress -n stoc-app
```

### 3. Database Initialization

Wait for PostgreSQL to be ready (~30s):

```bash
kubectl get pods -n stoc-app | grep postgres

# Run database migrations (if using Django)
kubectl exec -it deployment/django-stoc -n stoc-app -- python manage.py migrate
```

### 4. Access the Application

After Traefik and DuckDNS are running:

```bash
# Get Traefik external IP
kubectl get svc traefik -n stoc-app

# Access via browser
https://stoc.incercari.duckdns.org
https://lotus.incercari.duckdns.org
```

## Scaling & Monitoring

### Manual Scaling

```bash
# Scale Django deployment to 5 replicas
kubectl scale deployment django-stoc --replicas=5 -n stoc-app

# Scale Lotus to 3 replicas
kubectl scale deployment lotus --replicas=3 -n stoc-app
```

### Auto-Scaling (HPA)

HPAs are configured for CPU (70%) and memory (80%) thresholds. Monitor:

```bash
kubectl get hpa -n stoc-app
kubectl describe hpa django-stoc-hpa -n stoc-app
kubectl top pods -n stoc-app --containers
```

### Monitoring Logs

```bash
# View all logs
kubectl logs deployment/django-stoc -n stoc-app --all-containers=true

# Tail logs with label selector
kubectl logs -l app=django-stoc -n stoc-app -f

# View Traefik logs
kubectl logs deployment/traefik -n stoc-app -f
```

## Production Considerations

### 1. Resource Quotas

Limit resource usage per namespace:

```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: ResourceQuota
metadata:
  name: stoc-quota
  namespace: stoc-app
spec:
  hard:
    requests.cpu: "10"
    requests.memory: "20Gi"
    limits.cpu: "20"
    limits.memory: "40Gi"
    pods: "50"
EOF
```

### 2. Pod Disruption Budgets

Ensure minimum availability during node maintenance:

```bash
kubectl apply -f - <<EOF
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: django-stoc-pdb
  namespace: stoc-app
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: django-stoc
EOF
```

### 3. Persistent Storage

For production, use cloud storage instead of local `emptyDir`:

```yaml
# Change for PostgreSQL
volumes:
- name: postgres-storage
  awsElasticBlockStore:  # AWS
    volumeID: vol-xxxxx
    fsType: ext4
  # OR
  gcePersistentDisk:  # GCP
    pdName: postgres-disk
    fsType: ext4
```

### 4. SSL/TLS Certificates

Manifests use Let's Encrypt + DuckDNS DNS challenge. For production:

- Install cert-manager (if not using Traefik ACME):
  ```bash
  helm repo add jetstack https://charts.jetstack.io
  helm install cert-manager jetstack/cert-manager --create-namespace --namespace cert-manager
  ```

- Verify certificates:
  ```bash
  kubectl get secret duckdns-tls -n stoc-app -o yaml
  ```

### 5. Backup & Disaster Recovery

```bash
# Backup PostgreSQL
kubectl exec deployment/postgres -n stoc-app -- pg_dump -U postgres stoc_db > backup.sql

# Restore
kubectl exec -i deployment/postgres -n stoc-app -- psql -U postgres stoc_db < backup.sql
```

## Troubleshooting

### Pods Not Starting

```bash
# Check events
kubectl get events -n stoc-app --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod <pod-name> -n stoc-app

# Check resource availability
kubectl top nodes
kubectl top pods -n stoc-app
```

### Ingress Not Working

```bash
# Check Ingress
kubectl describe ingress stoc-ingress -n stoc-app

# Check service endpoints
kubectl get endpoints -n stoc-app

# Test connectivity to service
kubectl run -it --rm debug --image=busybox:1.28 --restart=Never -- wget -O- http://django-stoc:8000
```

### Certificate Issues

```bash
# Check certificate status
kubectl get certificate -n stoc-app

# View cert details
kubectl describe certificate duckdns-tls -n stoc-app

# Restart Traefik to re-issue
kubectl rollout restart deployment/traefik -n stoc-app
```

### Database Connection Errors

```bash
# Check PostgreSQL logs
kubectl logs deployment/postgres -n stoc-app

# Test connectivity
kubectl run -it --rm debug --image=postgres:15-alpine --restart=Never -- \
  psql -h postgres.stoc-app.svc.cluster.local -U postgres -d stoc_db -c "SELECT 1"
```

## Cleanup

```bash
# Delete all resources in namespace
kubectl delete namespace stoc-app

# Or delete specific resources
kubectl delete -f k8s-deployment.yaml
```

## Next Steps

- Set up ingress-nginx for additional ingress controller features
- Add network policies to restrict inter-pod communication
- Implement persistent volume snapshots for backups
- Configure log aggregation (ELK, Loki, Splunk)
- Add Prometheus/Grafana for metrics monitoring
- Set up CI/CD pipeline to auto-deploy on image push (ArgoCD, Flux)
