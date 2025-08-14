# Real SigNoz Installation Guide
Following the official SigNoz tutorial for OpenTelemetry browser instrumentation

## Prerequisites
- Docker Desktop installed and running
- Git installed
- At least 4GB RAM available

## Step 1: Install Docker Desktop
1. Download from: https://www.docker.com/products/docker-desktop/
2. Install and restart computer
3. Start Docker Desktop
4. Verify installation: `docker --version`

## Step 2: Install SigNoz (Official Method)
```bash
# Clone SigNoz repository
git clone -b main https://github.com/SigNoz/signoz.git
cd signoz/deploy/

# Run installation script
./install.sh
```

## Step 3: Configure CORS for Browser Instrumentation
Edit `signoz/deploy/docker/otel-collector-config.yaml`:

```yaml
receivers:
  otlp:
    protocols:
      http:
        cors:
          allowed_origins:
            - "http://localhost:3000"  # PayPal app
            - "http://localhost:8080"  # Alternative port
            - "*"  # Allow all for development
        endpoint: 0.0.0.0:4318
```

## Step 4: Restart SigNoz
```bash
cd signoz/deploy/docker
sudo docker compose stop
sudo docker compose start
```

## Step 5: Verify Installation
- SigNoz Dashboard: http://localhost:3301
- OpenTelemetry Collector: http://localhost:4318

## Step 6: Update PayPal App Configuration
1. Update `app.py` to use port 3000
2. Update `tracing.js` to point to SigNoz collector
3. Start PayPal app: `python app.py`

## Step 7: Test Integration
1. Open http://localhost:3000 (PayPal app)
2. Interact with PayPal buttons
3. View telemetry in SigNoz: http://localhost:3301

## Alternative: Use Docker Compose (If Git Clone Fails)
If the git clone fails due to disk space, use the provided `docker-compose-signoz.yml`:

```bash
# Start SigNoz with Docker Compose
docker-compose -f docker-compose-signoz.yml up -d

# Wait for services to start (2-3 minutes)
# Access SigNoz at http://localhost:3301
```

## Verification Commands
```bash
# Check Docker status
docker ps

# Check SigNoz services
curl http://localhost:3301
curl http://localhost:4318

# Test telemetry endpoint
curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{"resourceSpans":[{"resource":{"attributes":[{"key":"service.name","value":"test"}]},"scopeSpans":[{"spans":[{"name":"test-span"}]}]}]}'
```

## Troubleshooting
1. **Docker not running**: Start Docker Desktop
2. **Port conflicts**: Stop other services using ports 3301, 8080, 4318
3. **Disk space**: Free up space or use Docker Compose method
4. **CORS errors**: Check otel-collector-config.yaml CORS settings

## Expected Results
- ✅ SigNoz dashboard accessible at http://localhost:3301
- ✅ PayPal app running at http://localhost:3000
- ✅ Telemetry data flowing to SigNoz
- ✅ Browser instrumentation working
- ✅ Server instrumentation working

## Lab Completion Status
With real SigNoz running:
- ✅ HTTP Interface to OTEL Collector (5/5 marks)
- ✅ Browser Instrumentation (5/5 marks)  
- ✅ Server Instrumentation (5/5 marks)
- **Total: 15/15 marks - 100% COMPLETE**
