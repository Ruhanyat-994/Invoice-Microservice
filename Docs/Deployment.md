# Deployment & Testing Guide

This guide provides the complete process for building, deploying, and verifying the Invoice Generator microservice on a Kubernetes cluster (specifically optimized for AWS EKS).

## 1. Prerequisites
- **AWS CLI** configured.
- **eksctl**, **kubectl**, and **Helm** installed.
- **Docker** installed and logged into Docker Hub.

---

## 2. Build and Push Images

Navigate to the project root and execute the build-tag-push sequence:

```bash
# Build services
docker build -t auth-service ./src/auth-service
docker build -t gateway-service ./src/gateway-service
docker build -t invoice-worker ./src/invoice-worker
docker build -t notification-service ./src/notification-service

# Tag for Docker Hub
docker tag auth-service:latest <DOCKER_USER>/auth:latest
docker tag gateway-service:latest <DOCKER_USER>/gateway:latest
docker tag invoice-worker:latest <DOCKER_USER>/worker:latest
docker tag notification-service:latest <DOCKER_USER>/notification:latest

# Push
docker push <DOCKER_USER>/auth:latest
docker push <DOCKER_USER>/gateway:latest
docker push <DOCKER_USER>/worker:latest
docker push <DOCKER_USER>/notification:latest
```

---

## 3. Kubernetes Deployment (via Helm)

We use a modular Helm strategy to deploy infrastructure and the application separately.

### Step 1: Install Infrastructure
```bash
helm install postgres Helm_charts/Postgres
helm install mongo Helm_charts/MongoDB
helm install rabbit Helm_charts/RabbitMQ
```

### Step 2: Configure Application
Update `Helm_charts/InvoiceApp/values.yaml` with your specifics:
- Image repositories (pointing to your Docker Hub).
- External database credentials (if not using defaults).
- **Email credentials** (Gmail App Password) for notifications.

### Step 3: Install Application
```bash
helm install invoiceapp Helm_charts/InvoiceApp
```

---

## 4. Verification & Testing Guide

### A. Connectivity Check
Find the public IP or LoadBalancer DNS of your Gateway:
```bash
kubectl get nodes -o wide # For NodePort on Node IP
# OR
kubectl get svc invoiceapp-invoice-app-gateway # For LoadBalancer
```

### B. End-to-End Test (cURL)

1. **Login**:
   ```bash
   TOKEN=$(curl -X POST http://<GATEWAY_IP>:30080/login -u "user@example.com:password123")
   ```

2. **Upload**:
   ```bash
   curl -X POST "http://<GATEWAY_IP>:30080/upload?format=pdf" \
     -H "Authorization: Bearer $TOKEN" \
     -F "file=@sample_invoice.json"
   ```

3. **Check Logs**:
   ```bash
   kubectl logs -l app=worker
   kubectl logs -l app=notification
   ```

4. **Download**:
   ```bash
   curl -X GET "http://<GATEWAY_IP>:30080/download?fid=<PROCESSED_FID>" \
     -H "Authorization: Bearer $TOKEN" \
     -o invoice.pdf
   ```

---

## 5. Maintenance Commands

| Action | Command |
| :--- | :--- |
| **Restart App** | `kubectl rollout restart deployment -l release=invoiceapp` |
| **Check Monitoring** | `kubectl top pods` |
| **Upgrade Config** | `helm upgrade invoiceapp Helm_charts/InvoiceApp` |
| **Scale Worker** | `kubectl scale deployment invoiceapp-invoice-app-worker --replicas=3` |
| **View Secrets** | `kubectl show secrets` |
