import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { getWebAutoInstrumentations } from '@opentelemetry/auto-instrumentations-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { ZoneContextManager } from '@opentelemetry/context-zone';
import { trace, metrics, logs } from '@opentelemetry/api';

// Create a resource with simple attributes
const resource = new Resource({
  'service.name': 'paypal-microfrontend-browser',
  'service.version': '1.0.0',
  'deployment.environment': 'development'
});

// Create a tracer provider
const provider = new WebTracerProvider({
  resource: resource,
});

// Configure the OTLP exporter with fallback to console
let otlpExporter;
try {
          // Console exporter for telemetry (no SigNoz needed)
        otlpExporter = {
          export: (spans) => {
            console.log('📊 OpenTelemetry Spans:', spans);
            return Promise.resolve();
          },
          shutdown: () => Promise.resolve()
        };
} catch (error) {
  console.warn('OTLP exporter not available, using console exporter');
  // Fallback to console exporter if OTLP is not available
  otlpExporter = {
    export: (spans) => {
      console.log('OpenTelemetry Spans:', spans);
      return Promise.resolve();
    },
    shutdown: () => Promise.resolve()
  };
}

// Add the BatchSpanProcessor to the provider
provider.addSpanProcessor(new BatchSpanProcessor(otlpExporter));

// Register the provider
provider.register({
  contextManager: new ZoneContextManager(),
});

// Get the tracer
const tracer = trace.getTracer('paypal-microfrontend-browser');

// Get the meter
const meter = metrics.getMeter('paypal-microfrontend-browser');

// Get the logger
const logger = logs.getLogger('paypal-microfrontend-browser');

// Create metrics with error handling
let paypalButtonClicks, paypalOrderCreations, paypalOrderCaptures, paypalErrors, paypalTransactionDuration;

try {
  paypalButtonClicks = meter.createCounter('paypal_button_clicks', {
    description: 'Number of PayPal button clicks',
  });

  paypalOrderCreations = meter.createCounter('paypal_order_creations', {
    description: 'Number of PayPal order creations',
  });

  paypalOrderCaptures = meter.createCounter('paypal_order_captures', {
    description: 'Number of PayPal order captures',
  });

  paypalErrors = meter.createCounter('paypal_errors', {
    description: 'Number of PayPal errors',
  });

  paypalTransactionDuration = meter.createHistogram('paypal_transaction_duration', {
    description: 'Duration of PayPal transactions',
    unit: 'ms',
  });
} catch (error) {
  console.warn('Metrics creation failed, using mock metrics');
  // Create mock metrics if real ones fail
  const mockMetric = {
    add: (value, attributes) => console.log('Mock Metric:', { value, attributes }),
    record: (value, attributes) => console.log('Mock Histogram:', { value, attributes })
  };
  paypalButtonClicks = paypalOrderCreations = paypalOrderCaptures = paypalErrors = paypalTransactionDuration = mockMetric;
}

// Register auto-instrumentations with error handling
try {
  registerInstrumentations({
    instrumentations: [
      getWebAutoInstrumentations({
        // Enable fetch instrumentation
        '@opentelemetry/instrumentation-fetch': {
          enabled: true,
        },
        // Enable XMLHttpRequest instrumentation
        '@opentelemetry/instrumentation-xml-http-request': {
          enabled: true,
        },
      }),
    ],
  });
} catch (error) {
  console.warn('Auto-instrumentations not available:', error);
}

// Export the tracer, meter, logger, and metrics for use in index.js
export {
  tracer,
  meter,
  logger,
  paypalButtonClicks,
  paypalOrderCreations,
  paypalOrderCaptures,
  paypalErrors,
  paypalTransactionDuration,
};
