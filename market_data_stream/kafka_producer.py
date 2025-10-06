# kafka_producer.py
# starts the kafka producer and integrates it with Finnhub's API/Websocket

from config import KAFKA_BOOTSTRAP_SERVER
from kafka import KafkaProducer
import json, websocket, time, threading, logging
from datetime import datetime, timezone
logger = logging.getLogger(__name__)

# in case the producer fails, we need a function to recreate it
def make_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        linger_ms=50, # trades off latency for throughput
        batch_size=32768,
        retries=5, # retry once on failure
        retry_backoff_ms = 200, # wait between retries
        request_timeout_ms=10000, # wait for 210 seconds for a response
        max_block_ms=10000 # max time to block on send
    )

producer = make_producer()
last_message_time = time.time()
ws = None  # making the ws accessible for shutdown

def start_producer(SYMBOLS, API_KEY, stop_event):

    global producer, last_message_time, ws
    logger.info("Producer thread started.")

    def on_message(ws, message):
        global last_message_time, producer
        data = json.loads(message)
        if data.get('type') == 'trade': #checks to make sure the data is trade data
            received_at = datetime.now(timezone.utc) # get the current time in UTC, which we will reference as the time the data arrived
            for t in data['data']:
                tick_time = datetime.fromtimestamp(t['t'] / 1000, tz=timezone.utc) #get tick timestamp provided via the websocket in UTC
                # schema for passing to Kafka (even though technically Kafka is schemless)
                payload = {
                    'timestamp': tick_time.isoformat(),
                    'timestamp_ms': t['t'],
                    'symbol': t['s'],
                    'price': t['p'],
                    'volume': t['v'],
                    'received_at': received_at.isoformat()
                }
                future = producer.send('price_ticks', payload)
            last_message_time = time.time()

    # WebSocket event handlers
    def on_open(ws_inner):
        logger.info("WebSocket connected.")
        for symbol in SYMBOLS:
            ws_inner.send(json.dumps({"type": "subscribe", "symbol": symbol}))
            logger.info(f"Subscribing to {symbol}")


    def on_close(ws_inner, close_status_code, close_msg):
        logger.info("WebSocket closed: code=%s msg=%s", close_status_code, close_msg)
        
    def on_error(ws_inner, err):
        logger.exception(f"WebSocket error: {err}")

    def connect_ws():
        global ws
        while not stop_event.is_set():
            try:
                ws = websocket.WebSocketApp(
                    f"wss://ws.finnhub.io?token={API_KEY}",
                    on_message=on_message,
                    on_open=on_open,
                    on_close=on_close,
                    on_error=on_error
                )
                logger.info("Starting WebSocket connection...")
                ws.run_forever(
                    ping_interval=60,
                    ping_timeout = 30
                )
            except Exception as e:
                logger.exception(f"WebSocket crashed: {e}")
            if not stop_event.is_set():
                logger.warning("WebSocket disconnected. Reconnecting in 10 seconds...")
                time.sleep(10)

    # sub thread to keep the websocket alive
    threading.Thread(target=connect_ws, daemon=True).start()

    try:
        while not stop_event.is_set(): # keep the producer running
            # hearbeat watchdog
            if time.time() - last_message_time > 60:
                logger.warning("No data for 60s, restarting WebSocket...")
                if ws: ws.close()
                producer = make_producer()
                last_message_time = time.time()
            time.sleep(1)
    finally:
        logger.info("Shutting down producer.")
        try: 
            if ws: ws.close()
        except Exception: 
            logger.exception("Error closing WebSocket")
        try: 
            producer.flush(timeout=5)
            producer.close(timeout=5)
        except Exception:
            logger.exception("Error closing producer")
    
