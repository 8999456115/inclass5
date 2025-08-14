import { loadScript } from 'https://cdn.jsdelivr.net/npm/@paypal/paypal-js@8.1.2/+esm';
import {
    tracer,
    logger,
    paypalButtonClicks,
    paypalOrderCreations,
    paypalOrderCaptures,
    paypalErrors,
    paypalTransactionDuration,
} from './tracing.js';

class Year extends HTMLElement {
    connectedCallback() {
        this.innerHTML = new Date().getFullYear();
    }
}

customElements.define("x-date", Year);

class PayPal extends HTMLElement {
    static observedAttributes = ["amount"];

    constructor() {
        // Always call super first in constructor
        super();
    }
    async connectedCallback() {
        // Create a span for the PayPal component initialization
        const initSpan = tracer.startSpan('paypal_component_init');
        
        try {
            logger.info('Initializing PayPal component', {
                amount: this.getAttribute("amount"),
                currency: this.getAttribute("currency")
            });

        const res = await fetch(import.meta.url.replace("index.js", "clientid"));
        const oClient = await res.json();
        const nAmount = this.getAttribute("amount");
        const sCurrency = this.getAttribute("currency");
            
        this.innerHTML = `
        <div id="paypal-button-container"></div>

        <p id="result-message"></p>
         `
        let paypal;
        try {
            paypal = await loadScript({ clientId: oClient.clientid, currency: sCurrency });
            paypal.resultMessage = (sMessage) => document.querySelector("#result-message").innerHTML = sMessage;
                
                logger.info('PayPal SDK loaded successfully', {
                    clientId: oClient.clientid,
                    currency: sCurrency
                });
        } catch (error) {
                logger.error('Failed to load PayPal SDK', { error: error.message });
                paypalErrors.add(1, { error_type: 'sdk_load_failure' });
            console.error("failed to load the PayPal JS SDK script", error);
        }

        if (paypal) {
            try {
                await paypal.Buttons({
                    style: {

                        shape: "rect",

                        layout: "vertical",

                        color: "gold",

                        label: "paypal",

                    },

                    message: {

                        amount: nAmount,

                    },

                    async createOrder() {
                            // Create a span for order creation
                            const orderSpan = tracer.startSpan('paypal_create_order');
                            const startTime = performance.now();
                            
                            try {
                                logger.info('Creating PayPal order', {
                                    amount: nAmount,
                                    currency: sCurrency
                                });
                                
                                paypalButtonClicks.add(1, { action: 'create_order' });

                            const response = await fetch(import.meta.url.replace("index.js", "orders"), {

                                method: "POST",

                                headers: {

                                    "Content-Type": "application/json",

                                },

                                // use the "body" param to optionally pass additional order information

                                // like product ids and quantities

                                body: JSON.stringify({

                                    cart: [

                                        {

                                            id: "YOUR_PRODUCT_ID",

                                            quantity: "YOUR_PRODUCT_QUANTITY",

                                            amount: nAmount,

                                            currency: sCurrency,

                                        },

                                    ],

                                }),

                            });


                            const orderData = await response.json();


                            if (orderData.id) {
                                    paypalOrderCreations.add(1, { status: 'success' });
                                    logger.info('PayPal order created successfully', {
                                        orderId: orderData.id,
                                        amount: nAmount,
                                        currency: sCurrency
                                    });
                                    
                                    const duration = performance.now() - startTime;
                                    paypalTransactionDuration.record(duration, {
                                        operation: 'create_order',
                                        status: 'success'
                                    });
                                    
                                    orderSpan.setAttributes({
                                        'paypal.order.id': orderData.id,
                                        'paypal.order.amount': nAmount,
                                        'paypal.order.currency': sCurrency,
                                        'paypal.order.duration_ms': duration
                                    });

                                return orderData.id;
                            }

                            const errorDetail = orderData?.details?.[0];

                            const errorMessage = errorDetail

                                ? `${errorDetail.issue} ${errorDetail.description} (${orderData.debug_id})`

                                : JSON.stringify(orderData);

                                paypalErrors.add(1, { error_type: 'order_creation_failed' });
                                logger.error('PayPal order creation failed', {
                                    error: errorMessage,
                                    orderData: orderData
                                });

                            throw new Error(errorMessage);

                        } catch (error) {
                                paypalErrors.add(1, { error_type: 'order_creation_exception' });
                                logger.error('Exception during PayPal order creation', {
                                    error: error.message,
                                    stack: error.stack
                                });
                                
                                const duration = performance.now() - startTime;
                                paypalTransactionDuration.record(duration, {
                                    operation: 'create_order',
                                    status: 'error'
                                });
                                
                                orderSpan.setAttributes({
                                    'error': true,
                                    'error.message': error.message,
                                    'paypal.order.duration_ms': duration
                                });

                            console.error(error);

                            paypal.resultMessage(`Could not initiate PayPal Checkout...<br><br>${error}`);
                            } finally {
                                orderSpan.end();
                        }
                    },


                    async onApprove(data, actions) {
                            // Create a span for order capture
                            const captureSpan = tracer.startSpan('paypal_capture_order');
                            const startTime = performance.now();

                        try {
                                logger.info('Capturing PayPal order', {
                                    orderId: data.orderID
                                });
                                
                                paypalButtonClicks.add(1, { action: 'capture_order' });

                            const response = await fetch(

                                import.meta.url.replace("index.js", `capture/${data.orderID}`),

                                {

                                    method: "POST",

                                    headers: {

                                        "Content-Type": "application/json",

                                    },

                                }

                            );


                            const orderData = await response.json();

                            // Three cases to handle:

                            //   (1) Recoverable INSTRUMENT_DECLINED -> call actions.restart()

                            //   (2) Other non-recoverable errors -> Show a failure message

                            //   (3) Successful transaction -> Show confirmation or thank you message


                            const errorDetail = orderData?.details?.[0];


                            if (errorDetail?.issue === "INSTRUMENT_DECLINED") {

                                // (1) Recoverable INSTRUMENT_DECLINED -> call actions.restart()

                                // recoverable state, per

                                // https://developer.paypal.com/docs/checkout/standard/customize/handle-funding-failures/

                                    logger.warn('PayPal instrument declined, restarting', {
                                        orderId: data.orderID,
                                        error: errorDetail
                                    });

                                return actions.restart();

                            } else if (errorDetail) {

                                // (2) Other non-recoverable errors -> Show a failure message

                                    paypalErrors.add(1, { error_type: 'capture_failed' });
                                    logger.error('PayPal capture failed', {
                                        orderId: data.orderID,
                                        error: errorDetail
                                    });

                                throw new Error(

                                    `${errorDetail.description} (${orderData.debug_id})`

                                );

                            } else if (!orderData.purchase_units) {

                                    paypalErrors.add(1, { error_type: 'invalid_capture_response' });
                                    logger.error('Invalid PayPal capture response', {
                                        orderId: data.orderID,
                                        orderData: orderData
                                    });

                                throw new Error(JSON.stringify(orderData));

                            } else {

                                // (3) Successful transaction -> Show confirmation or thank you message

                                // Or go to another URL:  actions.redirect('thank_you.html');

                                const transaction =

                                    orderData?.purchase_units?.[0]?.payments

                                        ?.captures?.[0] ||

                                    orderData?.purchase_units?.[0]?.payments

                                        ?.authorizations?.[0];
                                            
                                    paypalOrderCaptures.add(1, { status: 'success' });
                                    logger.info('PayPal transaction completed successfully', {
                                        orderId: data.orderID,
                                        transactionId: transaction.id,
                                        status: transaction.status
                                    });
                                    
                                    const duration = performance.now() - startTime;
                                    paypalTransactionDuration.record(duration, {
                                        operation: 'capture_order',
                                        status: 'success'
                                    });
                                    
                                    captureSpan.setAttributes({
                                        'paypal.order.id': data.orderID,
                                        'paypal.transaction.id': transaction.id,
                                        'paypal.transaction.status': transaction.status,
                                        'paypal.transaction.duration_ms': duration
                                    });

                                paypal.resultMessage(

                                    `Transaction ${transaction.status}: ${transaction.id}<br>
            
                      <br>See console for all available details`

                                );

                                console.log(

                                    "Capture result",

                                    orderData,

                                    JSON.stringify(orderData, null, 2)

                                );

                            }

                        } catch (error) {
                                paypalErrors.add(1, { error_type: 'capture_exception' });
                                logger.error('Exception during PayPal capture', {
                                    orderId: data.orderID,
                                    error: error.message,
                                    stack: error.stack
                                });
                                
                                const duration = performance.now() - startTime;
                                paypalTransactionDuration.record(duration, {
                                    operation: 'capture_order',
                                    status: 'error'
                                });
                                
                                captureSpan.setAttributes({
                                    'error': true,
                                    'error.message': error.message,
                                    'paypal.order.id': data.orderID,
                                    'paypal.transaction.duration_ms': duration
                                });

                            console.error(error);

                            paypal.resultMessage(

                                `Sorry, your transaction could not be processed...<br><br>${error}`

                            );

                            } finally {
                                captureSpan.end();
                        }
                    },

                }
                ).render("#paypal-button-container");
            } catch (error) {
                    paypalErrors.add(1, { error_type: 'button_render_failure' });
                    logger.error('Failed to render PayPal buttons', {
                        error: error.message,
                        stack: error.stack
                    });
                console.error("failed to render the PayPal Buttons", error);
                }
            }
        } catch (error) {
            paypalErrors.add(1, { error_type: 'component_init_failure' });
            logger.error('Failed to initialize PayPal component', {
                error: error.message,
                stack: error.stack
            });
        } finally {
            initSpan.end();
        }
    }
}

customElements.define("x-paypal", PayPal)