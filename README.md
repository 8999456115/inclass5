# PayPal Microfrontend with OpenTelemetry Instrumentation

This project implements a PayPal microfrontend component with comprehensive OpenTelemetry instrumentation for both browser and server-side observability. The component is designed to be deployed on a cluster with HTTP interfaces exposed for TrueNAS and Cloudflare integration.

## Features

- **Browser-side instrumentation**: Metrics, traces, logs, and exception handling
- **Server-side instrumentation**: FastAPI with OpenTelemetry integration
- **OpenTelemetry Collector**: HTTP interface exposed for TrueNAS and Cloudflare integration
- **SigNoz observability backend**: Complete observability solution
- **PayPal integration**: Complete payment processing workflow

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

## Quick Start

### 1. Environment Setup

Create a `.env` file with your PayPal credentials:

```bash
PAYPAL_CLIENT_ID=your_paypal_client_id_here
PAYPAL_CLIENT_SECRET=your_paypal_client_secret_here
```

### 2. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Browser dependencies (optional)
npm install
```

### 3. Start Observability Stack

```bash
# Start OpenTelemetry Collector and SigNoz
docker-compose up -d otel-collector signoz postgres
```

### 4. Run Application

```bash
# Start the FastAPI server
python app.py
```

Access the application at:
- **PayPal Microfrontend**: http://localhost:3000
- **SigNoz Dashboard**: http://localhost:3301

## OpenTelemetry Instrumentation Details

### Browser-side (index.js)

**Metrics:**
- `paypal_button_clicks`: Number of PayPal button interactions
- `paypal_order_creations`: Number of order creation attempts
- `paypal_order_captures`: Number of order capture attempts
- `paypal_errors`: Error count by type
- `paypal_transaction_duration`: Transaction duration histogram

**Traces:**
- `paypal_component_init`: Component initialization
- `paypal_create_order`: Order creation process
- `paypal_capture_order`: Order capture process

**Logs:**
- Structured logging for all operations
- Error tracking with stack traces
- Performance monitoring

### Server-side (app.py)

**Metrics:**
- `paypal_requests_total`: Total API requests
- `paypal_order_creations_total`: Order creation count
- `paypal_order_captures_total`: Order capture count
- `paypal_errors_total`: Error count
- `paypal_request_duration_seconds`: Request duration histogram

**Traces:**
- `get_client_id`: Client ID retrieval
- `create_paypal_order`: Order creation with detailed attributes
- `capture_paypal_order`: Order capture with transaction details

**Logs:**
- Structured logging for all API operations
- Error tracking and debugging information
- Performance metrics

## HTTP Interface for TrueNAS/Cloudflare

The OpenTelemetry Collector exposes the following HTTP endpoints:

- **OTLP HTTP**: 
  - Traces: `http://localhost:4318/v1/traces`
  - Metrics: `http://localhost:4318/v1/metrics`
  - Logs: `http://localhost:4318/v1/logs`
- **Prometheus**: `http://localhost:8889/metrics`
- **Health Check**: `http://localhost:13133`

These endpoints are configured with CORS support for cross-origin requests from TrueNAS and Cloudflare.

## Testing

1. Open http://localhost:3000
2. Click on a PayPal button
3. Complete a test payment using PayPal sandbox
4. Monitor telemetry data in SigNoz dashboard

## Monitoring with SigNoz

1. Access SigNoz at http://localhost:3301
2. View traces, metrics, and logs from both browser and server
3. Create custom dashboards and alerts
4. Analyze performance patterns and error rates

## Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PAYPAL_CLIENT_ID=your_client_id
export PAYPAL_CLIENT_SECRET=your_client_secret

# Run the application
python app.py
```

## Configuration

### OpenTelemetry Collector

The collector configuration (`otel-collector-config.yaml`) includes:

- CORS support for browser requests
- Batch processing for efficiency
- Memory limiting for resource management
- Prometheus metrics export
- SigNoz integration

### Environment Variables

- `PAYPAL_CLIENT_ID`: PayPal API client ID
- `PAYPAL_CLIENT_SECRET`: PayPal API client secret
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OpenTelemetry collector endpoint
- `OTEL_SERVICE_NAME`: Service name for telemetry
- `OTEL_RESOURCE_ATTRIBUTES`: Additional resource attributes

## Security Considerations

- Use environment variables for sensitive data
- Configure CORS properly for production
- Enable TLS for production deployments
- Use proper authentication for SigNoz in production
- Validate PayPal webhook signatures

## Troubleshooting

1. **PayPal API Errors**: Check credentials in `.env` file
2. **OpenTelemetry Issues**: Verify collector is running on port 4318
3. **CORS Issues**: Collector is configured to allow all origins for development
4. **SigNoz Access**: Ensure PostgreSQL is running and accessible

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
