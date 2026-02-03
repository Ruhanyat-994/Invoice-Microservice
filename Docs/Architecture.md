# System Architecture

This document provides a detailed overview of the Invoice Generator microservice architecture, technical implementation, and technology stack.

## Architecture Overview

The system follows a **decoupled, event-driven microservices architecture** designed for scalability and fault tolerance. It is specifically designed to handle document generation tasks asynchronously to ensure high responsiveness.

### Infrastructure Diagram

![System Architecture](./assets/architecture.png)

### Data Flow

1.  **User Authentication**: The Gateway delegates login requests to the Auth Service, which verifies credentials against a PostgreSQL database and issues a stateless JWT token.
2.  **Invoice Request**: The user uploads invoice data (JSON) to the Gateway.
3.  **Storage & Queuing**: The Gateway stores the raw JSON in MongoDB (GridFS) and publishes a message to the `invoices` queue in RabbitMQ.
4.  **Asynchronous Processing**: The Invoice Worker consumes the message, retrieves the data from MongoDB, generates the invoice file (PDF/Excel/CSV), and stores the result back in MongoDB.
5.  **Notification Triggers**: Upon completion, the Worker publishes a completion message to the `notifications` queue.
6.  **User Notification**: The Notification Service picks up the message and sends an email to the user with the download link/ID.

---

## Technical Design Patterns

### 1. Asynchronous Task Processing
The architecture uses **RabbitMQ** as a message broker to decouple the API Gateway from the CPU-intensive generation process. This ensures that the gateway remains responsive while heavy lifting is done by dedicated workers.

### 2. Distributed Storage (GridFS)
To handle large files in an ephemeral container environment, file storage is externalized using **MongoDB GridFS**. This allows any service (Gateway or Worker) to access the files consistently without shared volumes.

### 3. Stateless Authentication
The system uses **JWT** for authentication, allowing microservices to verify user identity without performing database lookups on every request.

### 4. API Gateway Pattern
The `gateway-service` acts as a facade, providing a clean RESTful interface to the client while orchestrating internal service communication, storage access, and task queuing.

---

## Technology Stack

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python | Primary language for all microservices. |
| **Web Framework** | Flask | Lightweight framework for API development. |
| **Relational DB** | PostgreSQL | User authentication and metadata storage. |
| **NoSQL DB** | MongoDB (GridFS) | Distributed large file storage. |
| **Message Broker** | RabbitMQ | Asynchronous inter-service communication. |
| **Orchestration** | Kubernetes (EKS) | Container orchestration and scaling. |
| **Package Manager**| Helm | Infrastructure-as-Code for easy deployment. |
| **Authentication** | JWT (PyJWT) | Secure, stateless user sessions. |
| **Infrastructure** | Docker | Containerization of services. |

---

## Deployment Strategy

The project is designed as a cloud-native application:
- **Helm Charts**: Used to manage both infrastructure (RabbitMQ, Postgres, MongoDB) and application services.
- **ConfigMaps & Secrets**: All configurations are injected at runtime, ensuring the images are immutable and portable.
- **Persistence**: Kubernetes PVCs ensure data durability for stateful workloads.
