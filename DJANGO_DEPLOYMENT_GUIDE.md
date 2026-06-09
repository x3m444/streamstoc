# Django Health Check Endpoint

Adaugă în `django_app/apps/stoc/views.py` sau crează nou `django_app/apps/stoc/health.py`:

```python
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Simple health check endpoint for Kubernetes probes."""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({"status": "healthy"}, status=200)
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=500)
```

Adaugă în `django_app/stoc_project/urls.py`:

```python
from django.contrib import admin
from django.urls import path
from apps.stoc.health import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    # ... alte routes
]
```

---

## Setup Automat — Steps

### 1. **Install Woodpecker CI pe K3s**

```bash
helm repo add woodpecker https://woodpecker-ci.github.io/helm-charts
helm install woodpecker woodpecker/woodpecker-server \
  --namespace ci --create-namespace \
  --set gitea.clientID=woodpecker \
  --set gitea.clientSecret=your-secret \
  --set gitea.server=https://gitea.kduner.duckdns.org
```

### 2. **Configure Woodpecker Secrets** (Docker Hub credentials)

```bash
woodpecker secret add \
  --event push \
  --event pull_request \
  docker_username your-docker-username

woodpecker secret add \
  --event push \
  --event pull_request \
  docker_password your-docker-token

woodpecker secret add \
  --event push \
  git_username your-gitea-user

woodpecker secret add \
  --event push \
  git_token your-gitea-token
```

### 3. **Push to Gitea**

```bash
# Structura repo
streamstoc/
├── .woodpecker.yml         # CI/CD pipeline
├── django_app/
│   ├── Dockerfile          # Updated multi-stage
│   ├── requirements.txt
│   ├── manage.py
│   ├── stoc_project/
│   ├── apps/
│   └── k8s/
│       ├── deployment.yaml # Kubernetes manifest
│       └── argocd-app.yaml # ArgoCD Application
├── djangolotus/
│   └── k8s/               # Similar structure
└── ...

git add .
git commit -m "Add CI/CD + Kubernetes manifests"
git push origin main
```

### 4. **Register Gitea Webhook** (Woodpecker → Git)

```bash
# Woodpecker bot se conectează la Gitea
# Au automat Gitea admin și setează webhook
# Alternativ manual în Gitea Settings → Webhooks
```

### 5. **Create ArgoCD Application**

```bash
kubectl apply -f django_app/k8s/argocd-app.yaml

# Sau manual în ArgoCD UI
# App: django-stoc
# Repo: https://gitea.kduner.duckdns.org/your-user/streamstoc
# Path: django_app/k8s/
# Sync: Automated
```

### 6. **Test Flow**

```bash
# Edit code
vi django_app/apps/stoc/views.py

# Commit & push
git add .
git commit -m "Add feature"
git push origin main

# Automat:
# 1. Gitea webhook → Woodpecker
# 2. Woodpecker builds Docker image
# 3. Woodpecker pushes to Docker Hub
# 4. Woodpecker updates k8s/deployment.yaml (image tag)
# 5. Git push → Gitea main branch
# 6. ArgoCD detectează schimbare
# 7. ArgoCD syncs K8s deployment
# 8. K3s pulls image și creează pod nou
```

---

## Workflow Final (Automația Completă)

```
You edit code locally
  ↓
git push origin main
  ↓
Gitea webhook triggers Woodpecker
  ↓
Woodpecker:
  - Builds Docker image (multi-stage, arm64)
  - Runs tests (migrations, checks)
  - Pushes to Docker Hub
  ↓
Woodpecker updates deployment.yaml + git push
  ↓
ArgoCD detects change
  ↓
ArgoCD applies to K3s
  ↓
Pod restarts cu imagine nouă
  ↓
Traefik routes trafic → new pod
  ↓
https://stoc.kduner.duckdns.org live
```

---

## Verificare

```bash
# ArgoCD status
kubectl get application -n argocd

# Woodpecker logs
kubectl logs -n ci deployment/woodpecker-server -f

# Django pod status
kubectl get pods -n default | grep django-stoc
kubectl logs deployment/django-stoc -n default

# Test health endpoint
curl https://stoc.kduner.duckdns.org/health/
```

---

## Cleanup Stari

Dacă ai pod vechi în rulare, Kubernetes va termina graceful și merge la nou:

```bash
# Manual rollout
kubectl rollout status deployment/django-stoc -n default

# Rollback daca ceva e greșit
kubectl rollout undo deployment/django-stoc -n default
```

---

## Setup checklist

- [ ] Dockerfile multi-stage în django_app/
- [ ] Health endpoint în views.py
- [ ] k8s/deployment.yaml + argocd-app.yaml
- [ ] .woodpecker.yml în root
- [ ] Woodpecker installed pe K3s
- [ ] Docker Hub secrets configured
- [ ] Gitea token secrets configured
- [ ] Push to main → test CI/CD
- [ ] ArgoCD syncs automatically
- [ ] Pod updated la fiecare git push

Cu asta, **ai full automation** — edit code, push, și e live în 2-3 minute.

Vrei să testezi flow-ul sau ai întrebări la setup?
