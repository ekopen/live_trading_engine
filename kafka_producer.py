# kafka_producer.py
# starts the kafka producer and integrates it with Finnhub's API/Websocket

from config import KAFKA_BOOTSTRAP_SERVER
from kafka import KafkaProducer
import json, websocket, time, threading, logging
from datetime import datetime, timezone
logger = logging.getLogger(__name__)

# producer class
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    linger_ms=1, # trades off latency for throughput
    retries=1, # retry once on failure
    request_timeout_ms=2000,# wait for 2 seconds for a response
    max_block_ms=2000  # max time to block on send
)

def start_producer(SYMBOL, API_KEY, stop_event):

    logger.info("Producer thread started.")

    def on_message(ws, message):
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
                producer.send('price_ticks', payload) #sends to the Kafka topic
                logger.debug(f"Sent to Kafka: {payload}")

    # WebSocket event handlers
    def on_open(ws):
        logger.info("WebSocket connected.")
        ws.send(json.dumps({"type": "subscribe", "symbol": SYMBOL}))
        logger.info(f"Subscribing to {SYMBOL}")
    def on_close(ws, close_status_code, close_msg):
        logger.info("WebSocket closed: code=%s msg=%s", close_status_code, close_msg)
    def on_error(ws, err):
        logger.exception(f"WebSocket error: {err}")
    ws = websocket.WebSocketApp(f"wss://ws.finnhub.io?token={API_KEY}",
                                on_message=on_message,
                                on_open=on_open,
                                on_close=on_close,
                                on_error=on_error)

    # sub thread to keep the websocket alive
    threading.Thread(target=ws.run_forever, daemon=True).start()

    try:
        while not stop_event.is_set(): # keep the producer running
            time.sleep(0.1)
    finally:
        logger.info("Shutting down producer.")
        for action, func in [
            ("closing WebSocket", lambda: ws.close()),
            ("flushing producer", lambda: producer.flush(timeout=5)),
            ("closing producer", lambda: producer.close(timeout=5)),
        ]:
            try:
                func()
            except Exception:
                logger.exception(f"Error {action} during shutdown")

    
