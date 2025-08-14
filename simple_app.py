import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging
import time
from datetime import datetime

# Simple OpenTelemetry setup without OTLP
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# PayPal SDK imports
from paypalserversdk.http.auth.o_auth_2 import ClientCredentialsAuthCredentials
from paypalserversdk.logging.configuration.api_logging_configuration import (
    LoggingConfiguration,
    RequestLoggingConfiguration,
    ResponseLoggingConfiguration,
)
from paypalserversdk.paypal_serversdk_client import PaypalServersdkClient
from paypalserversdk.controllers.orders_controller import OrdersController
from paypalserversdk.controllers.payments_controller import PaymentsController
from paypalserversdk.models.amount_with_breakdown import AmountWithBreakdown
from paypalserversdk.models.checkout_payment_intent import CheckoutPaymentIntent
from paypalserversdk.models.order_request import OrderRequest
from paypalserversdk.models.capture_request import CaptureRequest
from paypalserversdk.models.money import Money
from paypalserversdk.models.shipping_details import ShippingDetails
from paypalserversdk.models.shipping_option import ShippingOption
from paypalserversdk.models.shipping_type import ShippingType
from paypalserversdk.models.purchase_unit_request import PurchaseUnitRequest
from paypalserversdk.models.payment_source import PaymentSource
from paypalserversdk.models.card_request import CardRequest
from paypalserversdk.models.card_attributes import CardAttributes
from paypalserversdk.models.card_verification import CardVerification
from paypalserversdk.api_helper import ApiHelper

# Initialize OpenTelemetry with console exporters only
def setup_opentelemetry():
    # Create a resource
    resource = Resource.create({
        "service.name": "paypal-microfrontend-server",
        "service.version": "1.0.0",
        "deployment.environment": "development"
    })

    # Set up tracing with console exporter
    trace_exporter = ConsoleSpanExporter()
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Set up metrics with console exporter
    metric_exporter = ConsoleMetricExporter()
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    LoggingInstrumentor().instrument()

    return trace.get_tracer("paypal-microfrontend-server"), metrics.get_meter("paypal-microfrontend-server")

# Initialize OpenTelemetry
tracer, meter = setup_opentelemetry()

# Create metrics
paypal_requests = meter.create_counter("paypal_requests_total", description="Total number of PayPal API requests")
paypal_order_creations = meter.create_counter("paypal_order_creations_total", description="Total number of PayPal order creations")
paypal_order_captures = meter.create_counter("paypal_order_captures_total", description="Total number of PayPal order captures")
paypal_errors = meter.create_counter("paypal_errors_total", description="Total number of PayPal errors")
paypal_request_duration = meter.create_histogram("paypal_request_duration_seconds", description="Duration of PayPal requests")

load_dotenv()
app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app, tracer_provider=trace.get_tracer_provider())

# Initialize PayPal client
paypal_client: PaypalServersdkClient = PaypalServersdkClient(
    client_credentials_auth_credentials=ClientCredentialsAuthCredentials(
        o_auth_client_id=os.getenv("PAYPAL_CLIENT_ID", "demo_client_id"),
        o_auth_client_secret=os.getenv("PAYPAL_CLIENT_SECRET", "demo_client_secret"),
    ),
    logging_configuration=LoggingConfiguration(
        log_level=logging.INFO,
        mask_sensitive_headers=False,
        request_logging_config=RequestLoggingConfiguration(
            log_headers=True, log_body=True
        ),
        response_logging_config=ResponseLoggingConfiguration(
            log_headers=True, log_body=True
        ),
    ),
)

orders_controller: OrdersController = paypal_client.orders
payments_controller: PaymentsController = paypal_client.payments

@app.get("/clientid")
async def clientid():
    with tracer.start_as_current_span("get_client_id") as span:
        try:
            logging.info("Client ID requested")
            paypal_requests.add(1, {"endpoint": "clientid"})
            
            client_id = os.getenv('PAYPAL_CLIENT_ID', 'demo_client_id')
            span.set_attribute("paypal.client_id.present", bool(client_id))
            
            return {"clientid": client_id}
        except Exception as e:
            logging.error("Error getting PayPal client ID", {"error": str(e)})
            paypal_errors.add(1, {"error_type": "client_id_error"})
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            raise

@app.post("/orders")
async def create_order(request: Request):
    with tracer.start_as_current_span("create_paypal_order") as span:
        start_time = time.time()
        
        try:
            logging.info("Creating PayPal order")
            paypal_requests.add(1, {"endpoint": "orders"})
            paypal_order_creations.add(1, {"status": "started"})

            request_body = await request.json()
            cart = request_body["cart"]
            
            # Add span attributes
            span.set_attribute("paypal.order.amount", cart[0]['amount'])
            span.set_attribute("paypal.order.currency", cart[0]['currency'])
            span.set_attribute("paypal.order.product_id", cart[0].get('id', 'unknown'))

            logging.info("Processing order creation", {
                "amount": cart[0]['amount'],
                "currency": cart[0]['currency'],
                "product_id": cart[0].get('id', 'unknown')
            })

            order = orders_controller.orders_create({
                "body": OrderRequest(
                    intent=CheckoutPaymentIntent.CAPTURE,
                    purchase_units=[
                        PurchaseUnitRequest(
                            amount=AmountWithBreakdown(
                                currency_code=cart[0]['currency'],
                                value=cart[0]['amount'],
                            ),
                        )
                    ],
                )
            })

            duration = time.time() - start_time
            paypal_request_duration.record(duration, {"operation": "create_order", "status": "success"})
            paypal_order_creations.add(1, {"status": "success"})
            
            span.set_attribute("paypal.order.id", order.body.id)
            span.set_attribute("paypal.order.duration_seconds", duration)
            
            logging.info("PayPal order created successfully", {
                "order_id": order.body.id,
                "amount": cart[0]['amount'],
                "currency": cart[0]['currency'],
                "duration_seconds": duration
            })

            return order.body

        except Exception as e:
            duration = time.time() - start_time
            paypal_request_duration.record(duration, {"operation": "create_order", "status": "error"})
            paypal_errors.add(1, {"error_type": "order_creation_failed"})
            paypal_order_creations.add(1, {"status": "error"})
            
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            span.set_attribute("paypal.order.duration_seconds", duration)
            
            logging.error("Failed to create PayPal order", {
                "error": str(e),
                "cart": cart if 'cart' in locals() else None,
                "duration_seconds": duration
            })
            
            raise

@app.post("/capture/{order_id}")
def capture_order(order_id: str):
    with tracer.start_as_current_span("capture_paypal_order") as span:
        start_time = time.time()
        
        try:
            logging.info("Capturing PayPal order", {"order_id": order_id})
            paypal_requests.add(1, {"endpoint": "capture"})
            paypal_order_captures.add(1, {"status": "started"})
            
            span.set_attribute("paypal.order.id", order_id)

            order = orders_controller.orders_capture({
                "id": order_id, 
                "prefer": "return=representation"
            })

            duration = time.time() - start_time
            paypal_request_duration.record(duration, {"operation": "capture_order", "status": "success"})
            paypal_order_captures.add(1, {"status": "success"})
            
            span.set_attribute("paypal.order.duration_seconds", duration)
            
            # Extract transaction details
            transaction = None
            if order.body.purchase_units and order.body.purchase_units[0].payments:
                if order.body.purchase_units[0].payments.captures:
                    transaction = order.body.purchase_units[0].payments.captures[0]
                elif order.body.purchase_units[0].payments.authorizations:
                    transaction = order.body.purchase_units[0].payments.authorizations[0]
            
            if transaction:
                span.set_attribute("paypal.transaction.id", transaction.id)
                span.set_attribute("paypal.transaction.status", transaction.status)
                
                logging.info("PayPal order captured successfully", {
                    "order_id": order_id,
                    "transaction_id": transaction.id,
                    "transaction_status": transaction.status,
                    "duration_seconds": duration
                })

            return order.body

        except Exception as e:
            duration = time.time() - start_time
            paypal_request_duration.record(duration, {"operation": "capture_order", "status": "error"})
            paypal_errors.add(1, {"error_type": "order_capture_failed"})
            paypal_order_captures.add(1, {"status": "error"})
            
            span.set_attribute("error", True)
            span.set_attribute("error.message", str(e))
            span.set_attribute("paypal.order.duration_seconds", duration)
            
            logging.error("Failed to capture PayPal order", {
                "order_id": order_id,
                "error": str(e),
                "duration_seconds": duration
            })
            
            raise

app.mount('/', StaticFiles(directory=".", html=True), name="src")

if __name__ == "__main__":
    print("🚀 Starting PayPal Microfrontend with OpenTelemetry...")
    print("📊 Telemetry data will be logged to console")
    print("🌐 Access the app at: http://localhost:3000")
    print("⏹️  Press Ctrl+C to stop")
    uvicorn.run(app, host="0.0.0.0", port=3000)
