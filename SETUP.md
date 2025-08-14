# PayPal Microfrontend with OpenTelemetry Setup Guide

This project implements a PayPal microfrontend component with comprehensive OpenTelemetry instrumentation for both browser and server-side observability.

## Features

- **Browser-side instrumentation**: Metrics, traces, logs, and exception handling
- **Server-side instrumentation**: FastAPI with OpenTelemetry integration
- **OpenTelemetry Collector**: HTTP interface exposed for TrueNAS and Cloudflare integration
- **SigNoz observability backend**: Complete observability solution

## Prerequisites

1. **PayPal Developer Account**: Get your client ID and secret from [PayPal Developer Portal](https://developer.paypal.com/)
2. **Docker and Docker Compose**: For running the observability stack
3. **Python 3.8+**: For the FastAPI server
4. **Node.js**: For browser dependencies (optional, can use CDN)

## Setup Instructions

### 1. Environment Configuration

Create a `.env` file in the project root:

```bash
# PayPal API Credentials
PAYPAL_CLIENT_ID=your_paypal_client_id_here
PAYPAL_CLIENT_SECRET=your_paypal_client_secret_here

# OpenTelemetry Configuration
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_SERVICE_NAME=paypal-microfrontend
OTEL_RESOURCE_ATTRIBUTES=service.version=1.0.0,deployment.environment=development
```

### 2. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Browser dependencies (optional)
npm install
```

### 3. Start the Observability Stack

```bash
# Start OpenTelemetry Collector and SigNoz
docker-compose up -d otel-collector signoz postgres
```

### 4. Run the Application

```bash
# Start the FastAPI server
python app.py
```

The application will be available at:
- **PayPal Microfrontend**: http://localhost:8080
- **SigNoz Dashboard**: http://localhost:3301

## OpenTelemetry Instrumentation

### Browser-side (index.js)

The browser-side instrumentation includes:

- **Metrics**: Button clicks, order creations, captures, errors, transaction duration
- **Traces**: Component initialization, order creation, order capture
- **Logs**: Info, warning, and error logs with structured data
- **Exception Handling**: Comprehensive error tracking and reporting

### Server-side (app.py)

The server-side instrumentation includes:

- **Metrics**: Request counts, order operations, error rates, request duration
- **Traces**: API endpoint tracing with detailed span attributes
- **Logs**: Structured logging for all operations
- **FastAPI Integration**: Automatic instrumentation of FastAPI endpoints

## HTTP Interface for TrueNAS/Cloudflare

The OpenTelemetry Collector exposes HTTP interfaces on:

- **OTLP HTTP**: http://localhost:4318/v1/traces, /v1/metrics, /v1/logs
- **Prometheus**: http://localhost:8889/metrics
- **Health Check**: http://localhost:13133

These endpoints can be accessed by TrueNAS and Cloudflare for monitoring and observability.

## Monitoring with SigNoz

1. Access SigNoz at http://localhost:3301
2. View traces, metrics, and logs from both browser and server
3. Create dashboards and alerts
4. Analyze performance and error patterns

## Testing the PayPal Integration

1. Open http://localhost:8080
2. Click on a PayPal button
3. Complete a test payment (use PayPal sandbox credentials)
4. Monitor the telemetry data in SigNoz

## Architecture

```
Browser (index.js) → FastAPI Server (app.py) → PayPal API
       ↓                      ↓
OpenTelemetry Browser    OpenTelemetry Server
       ↓                      ↓
   OTLP HTTP (4318)    OTLP HTTP (4318)
       ↓                      ↓
   OpenTelemetry Collector
       ↓
   SigNoz + PostgreSQL
```

## Troubleshooting

1. **PayPal API Errors**: Check your credentials in the `.env` file
2. **OpenTelemetry Issues**: Verify the collector is running on port 4318
3. **CORS Issues**: The collector is configured to allow all origins for development
4. **SigNoz Access**: Ensure PostgreSQL is running and accessible

## Security Notes

- Use environment variables for sensitive data
- Configure CORS properly for production
- Enable TLS for production deployments
- Use proper authentication for SigNoz in production
