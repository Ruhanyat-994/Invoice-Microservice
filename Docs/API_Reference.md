# API Documentation & EKS Testing Guide

This document provides a comprehensive list of API endpoints, service URLs, and step-by-step instructions to verify your Invoice Generator deployment on an EKS cluster.

## 1. Service Endpoints (EKS/Public IP)

Assuming your EKS Node Public IP is `<PUBLIC_IP>`, the following services are accessible via the configured NodePorts:

| Service | Port | Protocol | Purpose |
| :--- | :--- | :--- | :--- |
| **API Gateway** | `30080` | HTTP | Main entry point for the application |
| **PostgreSQL** | `30003` | TCP | Auth Database (Postgres) |
| **MongoDB** | `30005` | TCP | File Storage (GridFS) |
| **RabbitMQ AMQP** | `30004` | TCP | Message Broker (AMQP) |
| **RabbitMQ UI** | `31672` | HTTP | RabbitMQ Management Console |

---

## 2. API Endpoints Reference

All application requests should be sent to the **API Gateway** (e.g., `http://<PUBLIC_IP>:30080`).

### A. Authentication
- **Endpoint**: `POST /login`
- **Auth**: Basic Auth (`username:password`)
- **Action**: Returns a JWT token for subsequent requests.
- **Default Credentials**: `user@example.com` / `password123` (as initialized in `src/auth-service/init.sql`)

### B. Upload Invoice Data
- **Endpoint**: `POST /upload`
- **Query Param**: `format=pdf` (supported options: `pdf`, `excel`, `csv`)
- **Header**: `Authorization: Bearer <JWT_TOKEN>`
- **Body**: Form-data with key `file` containing a JSON file (e.g., `sample_invoice.json`)
- **Action**: Stores raw JSON in MongoDB and queues a processing task.

### C. Download Processed Invoice
- **Endpoint**: `GET /download`
- **Query Param**: `fid=<processed_fid>`
- **Header**: `Authorization: Bearer <JWT_TOKEN>`
- **Action**: Downloads the generated PDF, Excel, or CSV file.

---

## 3. Step-by-Step Testing Guide (using cURL)

Follow these steps to verify the entire flow on your cluster.

### Step 1: Get your Cluster/Node IP
Find the public IP of one of your nodes (for NodePort) or the LoadBalancer DNS:
```bash
kubectl get nodes -o wide
# OR
kubectl get svc
```

### Step 2: Login and Get Token
Execute this command to receive your JWT token (replace `<IP>` with your actual IP):
```bash
# Store the token in a variable
TOKEN=$(curl -X POST http://<IP>:30080/login \
  -u "user@example.com:password123")

echo "Your Token: $TOKEN"
```

### Step 3: Upload an Invoice for Processing
Upload the provided `sample_invoice.json` file.
```bash
curl -X POST "http://<IP>:30080/upload?format=pdf" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_invoice.json"
```
*Expected Result: `success!`*

### Step 4: Verify Processing in RabbitMQ
1. Open your browser to `http://<IP>:31672`
2. Login with your configured RabbitMQ administrative credentials (default: `admin` / `your_rabbitmq_password`).
3. Click on the **Queues** tab.
4. You should see `invoices` and `notifications` queues being active.

### Step 5: Check Service Logs
Verify the worker processed the file and the notification service triggered:
```bash
# Check worker logs
kubectl logs -l app=worker

# Check notification logs
kubectl logs -l app=notification
```
*Look for the `processed_fid` in the logs to use for downloading.*

### Step 6: Download the Generated File
Use the `processed_fid` from the logs:
```bash
curl -X GET "http://<IP>:30080/download?fid=<PROCESSED_FID>" \
  -H "Authorization: Bearer $TOKEN" \
  -o generated_invoice.pdf
```

---

## 4. Health Check Commands (Kubernetes)

Use these commands to quickly verify the status of your infrastructure:

### Check Pod Status
```bash
kubectl get pods
```
*All pods should be `Running` with `1/1 READY`.*

### Check Service Mappings
```bash
kubectl get svc
```

### Check Detailed Pod Failures
If any pod is failing, use:
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name> --tail=50
```

---

## 5. Security Note for EKS

> [!IMPORTANT]
> Ensure your **Cloud Security Groups** (e.g., AWS Security Group) allow inbound traffic on the following ports:
| Service | Port |
| :--- | :--- |
| **API Gateway** | `30080` |
| **PostgreSQL** | `30003` |
| **RabbitMQ AMQP** | `30004` |
| **MongoDB** | `30005` |
| **RabbitMQ UI** | `31672` |
