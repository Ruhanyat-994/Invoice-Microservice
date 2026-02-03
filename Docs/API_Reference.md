# API Reference

The Invoice Generator application provides a RESTful API handled by the `gateway-service`. All requests require JWT authentication except for the `/login` endpoint.

## Base URL
`http://<GATEWAY_IP>:<PORT>`
*(Default Port: 30080 for NodePort, 80 for LoadBalancer)*

---

## Authentication

### User Login
Obtains a JWT token for authorized requests.

- **Endpoint**: `POST /login`
- **Authentication**: HTTP Basic Auth (`email:password`)
- **Success Response**: `JWT_TOKEN_STRING`
- **Error Response**: `401 Unauthorized`

---

## Invoice Management

### Upload Invoice Data
Uploads a JSON file containing invoice data to be processed into a specific format.

- **Endpoint**: `POST /upload`
- **Headers**: 
  - `Authorization: Bearer <TOKEN>`
- **Query Parameters**:
  - `format`: Desired output format (`pdf`, `excel`, `csv`). Default: `pdf`.
- **Body**: `multipart/form-data`
  - `file`: The `.json` file containing invoice details.
- **Success Response**: `success!` (200 OK)
- **Workflow**: 
  1. File is stored in raw-storage (MongoDB).
  2. Processing task is queued in RabbitMQ.

### Download Processed Invoice
Retrieves a successfully processed invoice file.

- **Endpoint**: `GET /download`
- **Headers**: 
  - `Authorization: Bearer <TOKEN>`
- **Query Parameters**:
  - `fid`: The File ID of the processed document (received via notification).
- **Success Response**: Binary file download (application/pdf, etc.).
- **Error Response**: `404 Not Found` if the file doesn't exist or isn't processed yet.

---

## Error Codes

| Code | Meaning |
| :--- | :--- |
| **400** | Bad Request (missing file, invalid format) |
| **401** | Unauthorized (expired or missing token) |
| **403** | Forbidden (user lacks admin permissions) |
| **500** | Internal Server Error (infrastructure failure) |
