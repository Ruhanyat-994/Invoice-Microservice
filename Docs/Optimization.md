# Walkthrough: Invoice Generator Microservice Architecture

I have successfully implemented a full-scale, decoupled, event-driven microservice system for generating invoices and converting them into professional formats (PDF and Excel), following the design pattern from the provided image.

## Features Implemented

*   **Asynchronous Processing**: Invoices are generated in the background, keeping the API responsive.
*   **Professional Invoice Layout**: PDFs are generated using `ReportLab`, matching the standard business invoice structure (Company details, Bill To/Ship To, Itemized table, and Totals).
*   **Excel Export Support**: The worker service includes logic to generate Excel files using `OpenPyXL`.
*   **Stateless Authentication**: JWT-based security managed by a dedicated Auth Service.
*   **Distributed Storage**: Raw JSON data and processed invoices are stored in MongoDB GridFS, separate from the application logic.
*   **Containerized & Orchestrated**: Every service is Dockerized and comes with production-ready Kubernetes manifests.
*   **Infrastructure Management**: Helm charts for PostgreSQL (Auth), MongoDB (Storage), and RabbitMQ (Messaging) are included.

## Directory Structure

```text
invoice-generator/
├── Helm_charts/            # Infrastructure charts
│   ├── MongoDB/
│   ├── Postgres/
│   └── RabbitMQ/
└── src/                    # Microservices
    ├── auth-service/       # Identity & JWT
    ├── gateway-service/    # API Entry & GridFS Proxy
    ├── invoice-worker/     # PDF/Excel Generation Logic
    └── notification-service/ # Email Alerts
```

## How to Deploy and Run

### 1. Infrastructure Setup
Navigate to the `Helm_charts` directory and install the components:
```bash
helm install postgres ./Postgres
helm install mongo ./MongoDB
helm install rabbitmq ./RabbitMQ
```

### 2. Deploy Microservices
Apply the manifests for each service:
```bash
kubectl apply -f src/auth-service/manifest/k8s.yaml
kubectl apply -f src/gateway-service/manifest/k8s.yaml
kubectl apply -f src/invoice-worker/manifest/k8s.yaml
kubectl apply -f src/notification-service/manifest/k8s.yaml
```

### 3. Usage Flow

#### Step 1: Login
Authenticate to get a JWT token:
```bash
curl -X POST http://<GATEWAY_IP>:8080/login -u email:password
```

#### Step 2: Upload Invoice Data
Upload your invoice details in JSON format:
```bash
curl -X POST -F 'file=@invoice_data.json' -H 'Authorization: Bearer <TOKEN>' http://<GATEWAY_IP>:8080/upload
```

#### Step 3: Notification & Download
*   The **Worker** will consume the data, generate a PDF, and store it in MongoDB.
*   The **Notification Service** will send an email (if configured) with the file ID.
*   Download the final invoice:
```bash
curl -H 'Authorization: Bearer <TOKEN>' http://<GATEWAY_IP>:8080/download?fid=<FILE_ID>
```

## Visual Representation of Generated Invoice
The worker service uses a template that reconstructs the layout seen in your uploaded image, including:
- Bold company headers and professional typography.
- Alternating colors and boxed layouts for BillTo/ShipTo.
- Navy blue headers for the item table.
- Calculated subtotals and tax rates.
